"""
.. module::
    :synopsis:

.. moduleauthor:: Vitaly Kovalev <intscorpio@gmail.com>
"""
import json
from datetime import datetime
from os.path import join
from pprint import pformat

from sm.engine.dataset import Dataset
from sm.engine.db import DB
from sm.engine.fdr import FDR
from sm.engine.formula_imager_segm import compute_sf_images
from sm.engine.formula_img_validator import sf_image_metrics, sf_image_metrics_est_fdr, filter_sf_images, filter_sf_metrics
from sm.engine.formulas_segm import FormulasSegm
from sm.engine.search_results import SearchResults
from sm.engine.theor_peaks_gen import TheorPeaksGenerator
from sm.engine.util import local_path, proj_root, SMConfig, logger
from sm.engine.work_dir import WorkDirManager

from pyspark import SparkContext, SparkConf
from sm.engine.imzml_txt_converter import ImzmlTxtConverter

DS_ID_SEL = "SELECT id FROM dataset WHERE name = %s"
DB_ID_SEL = "SELECT id FROM formula_db WHERE name = %s"

DEL_JOB_SQL = 'DELETE FROM job WHERE id = %s'
JOB_INS = "INSERT INTO job VALUES (%s, %s, %s, 'SUCCEEDED', 0, 0, '2000-01-01 00:00:00', %s)"
ADDUCT_INS = 'INSERT INTO adduct VALUES (%s, %s)'


class SearchJob(object):
    """ Main class responsible for molecule search. Uses other modules of the engine.

    Args
    ----------
    ds_name : string
        A dataset short name
    """
    def __init__(self, client_email, ds_name):
        self.sm_config = SMConfig.get_conf()
        self.client_email = client_email
        self.ds_name = ds_name
        self.ds_id = None
        self.job_id = None
        self.sc = None
        self.db = None
        self.ds = None
        self.fdr = None
        self.formulas = None
        self.ds_config = None
        self.wd_manager = None

    def _read_ds_config(self):
        with open(self.wd_manager.ds_config_path) as f:
            self.ds_config = json.load(f)

    def _configure_spark(self):
        logger.info('Configuring Spark')
        sconf = SparkConf()
        for prop, value in self.sm_config['spark'].iteritems():
            if prop.startswith('spark.'):
                sconf.set(prop, value)

        if 'aws' in self.sm_config:
            sconf.set("spark.hadoop.fs.s3a.access.key", self.sm_config['aws']['aws_access_key_id'])
            sconf.set("spark.hadoop.fs.s3a.secret.key", self.sm_config['aws']['aws_secret_access_key'])
            sconf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

        # sconf.set("spark.python.profile", "true")
        self.sc = SparkContext(master=self.sm_config['spark']['master'], conf=sconf, appName='SM engine')
        if not self.sm_config['spark']['master'].startswith('local'):
            self.sc.addPyFile(join(local_path(proj_root()), 'sm.zip'))

    def _init_db(self):
        logger.info('Connecting to the DB')
        self.db = DB(self.sm_config['db'])
        self.sf_db_id = self.db.select_one(DB_ID_SEL, self.ds_config['database']['name'])[0]

    def run(self, input_path, ds_config_path, clean=False):
        """ Entry point of the engine. Molecule search is completed in several steps:
         * Copying input data to the engine work dir
         * Conversion input data (imzML+ibd) to plain text format. One line - one spectrum data
         * Generation and saving to the database theoretical peaks for all formulas from the molecule database
         * Molecules search. The most compute intensive part. Spark is used to run it in distributed manner.
         * Saving results (isotope images and their metrics of quality for each putative molecule) to the database

        Args
        -------
        input_path : string
            Path to the dataset folder with .imzML and .ibd files
        ds_config_path: string
            Path to the dataset config file
        clean : bool
            Clean all interim data files before starting molecule search
        """
        try:
            self.wd_manager = WorkDirManager(self.ds_name)
            if clean:
                self.wd_manager.clean()

            # if not self.wd_manager.exists(self.wd_manager.txt_path):
            self.wd_manager.copy_input_data(input_path, ds_config_path)

            self._read_ds_config()
            logger.info('Dataset config:\n%s', pformat(self.ds_config))

            self._configure_spark()
            self._init_db()

            if not self.wd_manager.exists(self.wd_manager.txt_path):
                imzml_converter = ImzmlTxtConverter(self.ds_name,
                                                    self.wd_manager.local_dir.imzml_path,
                                                    self.wd_manager.local_dir.txt_path,
                                                    self.wd_manager.local_dir.coord_path)
                imzml_converter.convert()

                if not self.wd_manager.local_fs_only:
                    self.wd_manager.upload_to_remote()

            self.ds = Dataset(self.sc, self.ds_name, self.client_email, self.ds_config, self.wd_manager, self.db)
            self.ds.save_ds_meta()

            self.store_job_meta()

            theor_peaks_gen = TheorPeaksGenerator(self.sc, self.sm_config, self.ds_config)
            theor_peaks_gen.run()

            target_adducts = self.ds_config['isotope_generation']['adducts']
            self.fdr = FDR(self.job_id, self.sf_db_id, decoy_sample_size=20, target_adducts=target_adducts, db=self.db)
            self.fdr.decoy_adduct_selection()
            self.formulas = FormulasSegm(self.job_id, self.sf_db_id, self.ds_config, self.db)

            search_results = self._search()
            self._store_results(search_results)

        except Exception as e:
            raise
        finally:
            if self.sc:
                # self.sc.show_profiles()
                self.sc.stop()
            if self.db:
                self.db.close()

    # TODO: add tests
    def store_job_meta(self):
        """ Store search job metadata in the database """
        logger.info('Storing job metadata')
        self.ds_id = int(self.db.select_one(DS_ID_SEL, self.ds_name)[0])
        self.job_id = self.ds_id
        self.db.alter(DEL_JOB_SQL, self.job_id)
        rows = [(self.job_id, self.sf_db_id, self.ds_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))]
        self.db.insert(JOB_INS, rows)

        rows = [(self.job_id, adduct) for adduct in self.ds_config['isotope_generation']['adducts']]
        self.db.insert(ADDUCT_INS, rows)

    def _search(self):
        logger.info('Running molecule search')
        sf_images = compute_sf_images(self.sc, self.ds, self.formulas.get_sf_peak_df(),
                                      self.ds_config['image_generation']['ppm'])
        all_sf_metrics_df = sf_image_metrics(sf_images, self.sc, self.formulas, self.ds, self.ds_config)
        sf_metrics_fdr_df = sf_image_metrics_est_fdr(all_sf_metrics_df, self.formulas, self.fdr)
        sf_metrics_fdr_df = filter_sf_metrics(sf_metrics_fdr_df)
        sf_images = filter_sf_images(sf_images, sf_metrics_fdr_df)

        return SearchResults(self.sf_db_id, self.ds_id, self.job_id,
                             sf_metrics_fdr_df, sf_images,
                             self.formulas.get_sf_adduct_peaksn(),
                             self.db, self.sm_config)

    def _store_results(self, search_results):
        logger.info('Storing search results to the DB')
        search_results.clear_old_results()
        search_results.store_sf_img_metrics()
        nrows, ncols = self.ds.get_dims()
        search_results.store_sf_iso_images(nrows, ncols)