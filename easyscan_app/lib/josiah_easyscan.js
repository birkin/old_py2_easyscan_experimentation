console.log( "- easyscan.js START" );


var esyscn = new function() {
  /* Namespaces this file's function calls.
   *
   * See <http://stackoverflow.com/a/881611> for module-pattern reference.
   * Only check_already_run() can be called publicly, and only via ```esyscn.check_already_run();```.
   */

  var cell_position_map = { "location": 0, "callnumber": 1, "availability": 2, "barcode": 3 };
  var bibnum = null;

  this.check_already_run = function() {
    /* Checks to see if javascript has already been run.
     * Called by document.ready()
     */
    var all_html = $("body").html().toString();  // jquery already loaded (whew)
    var index = all_html.indexOf( "Request Scan" );
    if (index != -1) {
      console.log( "- aready run" );
    } else {
      console.log( "- not already run" );
    grab_title();
    }
  }

  var grab_title = function() {
    /* Grabs bib title; then continues processing.
     * Called by check_already_run()
     */
    var title = null;
    var els = document.querySelectorAll( ".bibInfoData" );
    if ( els.length > 0 ) {
      var el = els[0];
      title = el.textContent.trim();
    }
    console.log( "- title, " + title );
    if ( title == null ){
      grab_bib();
    } else {
      process_item_table( title );
    }
  }

  var grab_bib = function() {
    /* Grabs bibnum from holdings html; then continues processing.
     * Called by grab_title() if title is null
     */
    var dvs = document.querySelectorAll(".additionalCopiesNav");  // first of two identical div elements
    if ( dvs.length > 0 ) {
      dv = dvs[0]
      var el = dv.children[0];  // the div contains a link with the bibnum
      var text = el.toString();
      if ( text.split("/")[3] == "search~S7?" ) {
        var t = text.split("/")[4];  // eg ".b4069600"
        bibnum = t.slice( 1, 9 );
        console.log( "in grab_bib(); bibnum, " + bibnum );
      }
    }
    console.log( "in grab_bib(); bibnum grabbed; calling process_item_table()" );
    title = null;
    process_item_table( title );
  }

  var process_item_table = function( title ) {
    /* Updates bib-item list to show request-scan button.
     * Called by grab_title()
     */
    rows = $( ".bibItemsEntry" );
    for (var i = 0; i < rows.length; i++) {
      row = rows[i];
      row_dict = extract_row_data( row.getElementsByTagName("td") );
      if ( evaluate_row_data(row_dict)["show_scan_button"] == true ) {
        console.log( "- in process_item_table(); continuing row procesing" );
        console.log( "- in process_item_table(); title, `" + title + "`" );
        if ( title == null && bibnum == null ) {
          title = grab_ancestor_title( row );
        }
        update_row( title, row_dict )
      }
      row.deleteCell( cell_position_map["barcode"] );
    }
    delete_header_cell();
  }

  var grab_ancestor_title = function( row ) {
    var big_element = row.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;  // apologies to all sentient beings
    var title_td = big_element.querySelectorAll( ".briefcitDetail" )[0];
    var title_plus = title_td.textContent.trim();
    var title = title_plus.split("\n")[0];
    console.log( "- in grab_ancestor_title(); title, `" + title + "`" );
    return title;
  }

  // var process_item_table = function( title ) {
  //   /* Updates bib-item list to show request-scan button.
  //    * Called by grab_title()
  //    */
  //   rows = $( ".bibItemsEntry" );
  //   for (var i = 0; i < rows.length; i++) {
  //     row = rows[i];
  //     row_dict = extract_row_data( row.getElementsByTagName("td") );
  //     if ( evaluate_row_data(row_dict)["show_scan_button"] == true ) {
  //       console.log( "- continuing row procesing" );
  //       update_row( title, row_dict )
  //     }
  //     row.deleteCell( cell_position_map["barcode"] );
  //   }
  //   delete_header_cell();
  // }

  var extract_row_data = function( cells ) {
    /* Takes row dom-object; extracts and returns fielded data.
     * It runs through the labels of the `var cell_position_map` dict, and builds a row_data dict:
     *   each key is the label; each value is the correct cell's text.
     * Called by process_item_table()
     */
    var row_data = {}
    var map_keys = Object.keys( cell_position_map );  // yeilds [ "location", "callnumber", etc. ] - compatible with older browsers?
    for (var i = 0; i < map_keys.length; i++) {
      var key = map_keys[i];
      var value = cells[ cell_position_map[key] ].textContent.trim();
      if ( key == "barcode" ) { value = value.split(" ").join(""); } // removes whitespaces between digits.
      row_data[key] = value;
    }
    console.log( "- row_data, " + JSON.stringify(row_data, null, 4) );
    return row_data;
  }

  var evaluate_row_data = function( row_dict ) {
    /* Evaluates whether 'Request Scan' button should appear; returns boolean.
     * Called by process_item_table()
     */
    var row_evaluation = { "show_scan_button": false };
    if ( (row_dict["location"] == "ANNEX") && (row_dict["availability"] == "AVAILABLE") ) {
        row_evaluation = { "show_scan_button": true };
    }
    console.log( "- row_evaluation, " + row_evaluation );
    return row_evaluation;
  }

  var update_row = function( title, row_dict ) {
    /* Adds `Request Scan` link to row html.
     * Called by process_item_table()
     */
    link_html = build_link_html( title, row_dict )
    last_cell = row.getElementsByTagName("td")[cell_position_map["availability"]];
    $( last_cell ).after( link_html );
    console.log( "- request-scan link added" );
    return;
  }

  var build_link_html = function( title, row_dict ) {
    /* Takes row dict; returns html link.
     * Called by extract_row_data()
     */
    link = '<a href="http://HOST/easyscan/request?callnumber=THECALLNUMBER&barcode=THEBARCODE&title=THETITLE&bibnum=THEBIBNUM">Request Scan</a>';
    link = link.replace( "THECALLNUMBER", row_dict["callnumber"] );
    link = link.replace( "THEBARCODE", row_dict["barcode"] );
    link = link.replace( "THETITLE", title );
    link = link.replace( "THEBIBNUM", bibnum );
    console.log( "- link end, " + link );
    return link;
  }

  var delete_header_cell = function() {
    /* Deletes barcode header cell
     * Called by process_item_table()
     */
    var header_row = $( "tr.bibItemsHeader" )[0];
    console.log( "- header_row, " + header_row );
    if ( typeof header_row == "undefined" ) {
      return; }
    header_row.deleteCell( cell_position_map["barcode"] );
    console.log( "- barcode header cell deleted" );
  }

};  // end namespace esyscn, ```var esyscn = new function() {```


$(document).ready(
  function() {
    esyscn.check_already_run();
  }

);


console.log( "- easyscan.js END" );

// JSON.stringify(obj, null, 4)
