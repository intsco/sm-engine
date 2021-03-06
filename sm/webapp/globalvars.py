#!/home/snikolenko/anaconda/bin/python
# -*- coding: utf8 -*
"""
.. module:: globalvars
    :synopsis: Global variables, mostly SQL queries.

.. moduleauthor:: Sergey Nikolenko <snikolenko@gmail.com>
"""

adducts = ["H", "Na", "K"]

sql_counts = dict(
    formulas="SELECT count(*) FROM formulas",
    formulas_search="SELECT count(*) FROM formulas WHERE lower(name) like '%%%s%%' OR lower(sf) like '%%%s%%' OR id like '%s%%'",
    substancejobs="SELECT count(*) FROM jobs WHERE formula_id='%s'",
    jobs="SELECT count(*) FROM jobs",
    datasets="SELECT count(*) FROM datasets",
    fullimages="SELECT count(*) FROM job_result_stats WHERE job_id=%s",
    # demobigtable="SELECT count(distinct sf_id) FROM iso_image_metrics"
)

sql_queries = dict(
    formulas="SELECT id,name,sf FROM formulas ",
    formulas_search="SELECT id,name,sf FROM formulas WHERE lower(name) like '%%%s%%' OR lower(sf) like '%%%s%%' OR id like '%s%%' ",
    substance='''SELECT
		f.id,f.sf_id,name,sf,peaks,ints,array_agg(s.job_id) as job_ids,
		array_agg(d.dataset_id) as dataset_ids,array_agg(dataset) as datasets,
		array_agg(stats) as stats
		FROM formulas f 
			JOIN mz_peaks p ON f.sf_id=p.sf_id
			LEFT JOIN job_result_stats s ON f.id=s.formula_id
			LEFT JOIN jobs j ON s.job_id=j.id
			LEFT JOIN datasets d ON j.dataset_id=d.dataset_id
			LEFT JOIN agg_formulas f on j.formula_id=f.id
		WHERE f.id='%s' GROUP BY f.id,f.sf_id,name,sf,peaks,ints
	''',
    jobstats="SELECT stats,peaks FROM job_result_stats s JOIN mz_peaks p ON s.formula_id=p.formula_id WHERE job_id=%s",
    substancejobs='''
		SELECT j.dataset_id,dataset,id,description,done,status,tasks_done,tasks_total,start,finish,id
		FROM jobs j
			LEFT JOIN datasets d on j.dataset_id=d.dataset_id
			LEFT JOIN job_types t on j.type=t.type
		WHERE formula_id='%s'
	''',
    jobs='''
		SELECT j.id as id,t.type,t.description,j.dataset_id,dataset,formula_id,f.sf as formula_name,done,status,tasks_done,tasks_total,start,finish,j.id as id
		FROM jobs j LEFT JOIN datasets d on j.dataset_id=d.dataset_id
		LEFT JOIN agg_formulas f on j.formula_id=f.id
		LEFT JOIN job_types t on t.type=j.type
	''',
    datasets='SELECT dataset_id,dataset,nrows,ncols,dataset_id FROM datasets',
    jobdescription='''
		SELECT j.dataset_id as dataset_id,dataset,description,done,status,tasks_done,tasks_total,start,finish
		FROM jobs j
			LEFT JOIN datasets d on j.dataset_id=d.dataset_id
			LEFT JOIN job_types t on j.type=t.type
		WHERE j.id=%s
	''',
    fullimages='''
		SELECT id,name,sf,stats->'entropies' as entropies,stats->'mean_ent' as mean_ent,stats->'corr_images' as corr_images,stats->'corr_int' as corr_int,id
		FROM job_result_stats j LEFT JOIN formulas f ON f.id=j.formula_id
		WHERE (stats->'mean_ent')::text::real > 0.0001 AND job_id=%s
	''',
    # demobigtable='''
    #     SELECT sf_db.name as db_name, ds.name as ds_name, f.sf, f.names, f.subst_ids,
    #         (m.stats->'chaos')::text::real AS chaos,
    #         (m.stats->'img_corr')::text::real AS image_corr,
    #         (m.stats->'pat_match')::text::real AS pattern_match,
    #         m.adduct AS adduct,
    #         j.id AS job_id,
    #         ds.id AS ds_id,
    #         f.id AS sf_id,
    #         m.peaks_n,
    #         sf_db.id AS db_id
    #     FROM iso_image_metrics m
    #     JOIN formula_db sf_db ON sf_db.id = m.db_id
    #     JOIN agg_formula f ON f.id = m.sf_id
    #     JOIN job j ON j.id = m.job_id
    #     JOIN dataset ds ON ds.id = j.ds_id
    #     ''',
    #  JOIN (
    #      SELECT j.db_id, ds.id as ds_id, ds.name as ds_name, max(j.id) as last_job_id
    #      FROM job j
    #      JOIN dataset ds on ds.id = j.ds_id
    #      GROUP BY j.db_id, ds.id, ds.name
    # ) ds_j ON ds_j.last_job_id = m.job_id AND db.id=ds_j.db_id

    demosubst='''SELECT s.job_id, s.sf_id, s.adduct, peak, intensities as ints
		FROM job_result_stat s
		JOIN job_result_data d ON s.job_id=d.job_id  and s.adduct=d.adduct
		JOIN job j ON d.job_id=j.id
		WHERE d.job_id=%d AND s.sf_id=%d AND d.sf_id=%d
		AND (s.stats->'spec')::text::real > 0.3 AND (s.stats->'spat')::text::real > 0.3
		ORDER BY peak
	''',
    demosubstpeaks="SELECT peaks,ints FROM mz_peaks WHERE formula_id='%s'",
    democoords="SELECT x,y FROM coordinates WHERE ds_id=%s ORDER BY index",
    randomstat="SELECT job_id,dataset_id,s.formula_id,adduct,param,json_array_length(s.stats->'entropies') FROM job_result_stats s JOIN jobs j ON s.job_id=j.id OFFSET random() * (SELECT count(*) FROM job_result_stats) LIMIT 1",
    onedata='''
		SELECT spectrum,value,x,y
		FROM job_result_data d 
			JOIN jobs j ON d.job_id=j.id 
			JOIN coordinates c ON j.dataset_id=c.dataset_id AND d.spectrum=c.index
		WHERE d.job_id=%d AND d.param=%d AND d.adduct=%d AND d.peak=%d
	''',
    mzimage2coords="SELECT index, row, column FROM coordinates WHERE dataset_id=%d"
)

sql_fields = dict(
    formulas=["id", "name", "sf"],
    substancejobs=["dataset_id", "dataset", "id", "description", "done", "status", "tasks_done", "tasks_total", "start",
                   "finish", "id"],
    jobs=["id", "type", "description", "dataset_id", "dataset", "formula_id", "formula_name", "done", "status",
          "tasks_done", "tasks_total", "start", "finish", "id"],
    datasets=["dataset_id", "dataset", "nrows", "ncols", "dataset_id"],
    fullimages=["id", "name", "sf", "entropies", "mean_ent", "corr_images", "corr_int", "id"],
    # demobigtable=["db_name", "ds_name", "sf", "names", "subst_ids", "chaos", "image_corr", "pattern_match",
    #               "msm",
    #               "adduct", "job_id", "ds_id", "sf_id", "peaks_n", "db_id"]
)
