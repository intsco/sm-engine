function initResultsTable() {
    return $('#results-table').DataTable( {
      ajax: {
        url: "/results_table/",
        type: "POST",
        data: function(data, settings) {
            data.fdr_thr = $("#fdr_thr_btn").text();
            return data
        }
//        dataFilter: function(data){
//            var json = jQuery.parseJSON( data );
//            json.recordsTotal = json.total;
//            json.recordsFiltered = json.total;
//            json.data = json.list;
//
//            return JSON.stringify( json ); // return JSON string
//        }
      },
      scroller: {
        loadingIndicator: true
      },
      scrollY: "200",
      dom: "rtiS",
      deferRender: true,
      processing: true,
      serverSide: true,
      colReorder: false,
      paging:     true,
      bSortCellsTop: true,
      bSearchable: false,
      bStateSave: false,  // server side filtering doesn't work with bStateSave=true
//      searching: false,
      order: [[ 10, "desc" ]],
      fnInitComplete: function(oSettings, json) {
        $('#results-table tbody tr:eq(0)').click();
      },
      columnDefs: [
        {"width": "15%", "targets": 3},
        { "render": function ( data, type, row ) {
          if (type === 'display') {
            return sin_render_sf(data);
          } else {
            return data;
          }
        }, "targets": [2] },
        { "render": function ( data, type, row ) {
          if (type === 'filter' || type === 'sort') {
            return data.join(" ");
          }
          if (data.length == 1) {
            return sin_render_substance_small(row[4][0], data[0]);
          }
          res = '<span style="margin:0 0px; white-space: pre-line;" rel="tooltip" data-html="true" title="'
            + data.join(", ") //.replace(/"/g, '\\"')
            + '">' + data.length.toString() + ' metabolite';
          if (data.length > 1) {
            res += 's';
          }
          return res + '</span>';
        }, "targets": [3] },
        { "render": function ( data, type, row ) {
          if (type === 'filter' || type === 'sort') {
            return data.join(" ");
          }
          if (data.length == 1) {
            return sin_render_substance_small(row[4][0], data[0]);
          }
          res = '<span style="margin:0 0px; white-space: pre-line;" rel="tooltip" data-html="true" title="'
            + data.join(", ").replace(/"/g, '\\"')
            + '">' + data.length.toString() + ' id';
          if (data.length > 1) {
            res += 's';
          }
          return res + '</span>';
        }, "targets": [4] },
        { "render": function ( data, type, row ) {
            return data;
        }, "targets": [5, 16] },
        { "visible": false,  "targets": [11, 12, 13, 14, 15, 16] }
      ],
      initComplete : function(oSettings, json) {
        $('#results-table').tooltip({
          selector: "span[rel=tooltip]",
          html: true
        });
      },
      fnRowCallback: function( row, data, iDisplayIndex, iDisplayIndexFull ) {
        if ( data[16] == "1" ) {
            row.classList.add('correct');
        }
        else if ( data[16] == "0" ) {
            row.classList.add('wrong');
        }
      }
    });
}

function fdrThrUpdate(results_table) {
    $(".dropdown-menu li a").click(function() {
      var selText = $(this).text();
      $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');

      results_table.ajax.reload();
    });
}

function addOndrawHandler(results_table) {
    results_table.on( 'draw', function () {
//        var first_visible_row_ind = parseInt($('.dataTables_info').text().match(/[0-9]+/g)[0]) - 1;
        $('#results-table tbody tr:eq(0)').click();
    } );
}

function initColumnFilters(results_table) {
    yadcf.init(results_table, [
      {
        column_number : 0,
        filter_type: "select",
        filter_delay: 500,
        filter_container_id: "fil-db",
        filter_reset_button_text: false,
        filter_default_label: 'Select...'
      },
      {
        column_number : 1,
        filter_type: "select",
        filter_delay: 500,
        filter_container_id: "fil-ds",
        filter_reset_button_text: false,
        filter_default_label: 'Select...',
//        filter_match_mode: "exact"
      },
      {
        column_number : 2,
        filter_type: "text",
        filter_delay: 500,
        filter_container_id: "fil-sf",
        filter_reset_button_text: false
      },
      {
        column_number : 3,
        filter_type: "text",
        filter_delay: 500,
        filter_container_id: "fil-nm",
        filter_reset_button_text: false
      },
      {
        column_number : 4,
        filter_type: "text",
        filter_delay: 500,
        filter_container_id: "fil-id",
        filter_reset_button_text: false
      },
      {
        column_number : 5,
        filter_type: "select",
        filter_delay: 500,
        filter_container_id: "fil-add",
        filter_reset_button_text: false,
        filter_default_label: 'all'
      },
      {
        column_number: 6,
        filter_type: "text",
        filter_delay: 500,
        filter_container_id: "fil-mz",
        filter_reset_button_text: false
      },
//      {column_number : 5, filter_type: "lower_bound_number", filter_container_id: "fil-chaos",
//        filter_reset_button_text: false, filter_default_label: ['&ge;']
//      },
//      {column_number : 6, filter_type: "lower_bound_number", filter_container_id: "fil-img-corr", filter_reset_button_text: false, filter_default_label: ['&ge;'] },
//      {column_number : 7, filter_type: "lower_bound_number", filter_container_id: "fil-pat-match", filter_reset_button_text: false, filter_default_label: ['&ge;']},
      {
        column_number : 10,
//        filter_type: "lower_bound_number",
        filter_type: "text",
        filter_delay: 500,
        filter_container_id: "fil-msm",
        filter_reset_button_text: false
//        filter_default_label: ['&ge;']
//        filter_default_label: ["0.5"]
      }
    ]);

    yadcf.exFilterColumn(results_table, [
        [10, "0.1"]
    ]);
}
