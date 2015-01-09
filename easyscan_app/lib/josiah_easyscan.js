console.log( "- josiah_easyscan.js START" );


var esyscn_flow_manager = new function() {
  /* Namespaces function calls.
   *
   * See <http://stackoverflow.com/a/881611> for module-pattern reference.
   * Only check_already_run() can be called publicly, and only via ```esyscn.check_already_run();```.
   *
   * Controller class flow description:
   * - Attempts to grab title from where it would be on an items page
   * - If title blank, attempts to grab the bibnumber from where it would be on a holdings page
   * - Finds all bib-rows and for each row:
   *   - Calls namespace `esyscn_row_processor` to process the row.
   *   - Deletes item-barcode
   *
   * Reference:
   * - items page: <http://josiah.brown.edu/record=b4069600>
   * - holdings page: <http://josiah.brown.edu/search~S7?/.b4069600/.b4069600/1,1,1,B/holdings~4069600&FF=&1,0,>
   * - results page: <http://josiah.brown.edu/search~S11/?searchtype=X&searcharg=zen&searchscope=11&sortdropdown=-&SORT=D&extended=1&SUBMIT=Search&searchlimits=&searchorigarg=tzen>
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
     * Called by grab_title() if title is null.
     */
    var dvs = document.querySelectorAll(".additionalCopiesNav");  // first of two identical div elements
    if ( dvs.length > 0 ) {
      var dv = dvs[0];
      var el = dv.children[0];  // the div contains a link with the bibnum
      var text = el.toString();
      var t = text.split("/")[4];  // eg ".b4069600"
      bibnum = t.slice( 1, 9 );  // updates module var
    }
    console.log( "in grab_bib(); bibnum, " + bibnum );
    title = null;
    process_item_table( title );
  }

  var process_item_table = function( title ) {
    /* Updates bib-items to show request-scan links.
     * Called by grab_title()
     */
    var rows = $( ".bibItemsEntry" );
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      esyscn_row_processor.process_item( row, title, cell_position_map, bibnum );
    }
    delete_header_cell();
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

};  // end namespace esyscn_flow_manager, ```var esyscn_flow_manager = new function() {```


var esyscn_row_processor = new function() {
  /*
   * Class flow description:
   *   - Determines whether to show a scan button
   *   - If so, and if title still blank, grabs title from where it would be on a results page
   *   - Builds and displays 'Request Scan' link from title, and barcode and item-info in row's html
   */

  var local_cell_position_map = null;
  var local_bibnum = null;

  this.process_item = function( row, title, cell_position_map, bibnum ) {
    /* Processes each row.
     * Called by esyscn_flow_manager.process_item_table()
     */
    init( cell_position_map, bibnum );
    var row_dict = extract_row_data( row );
    if ( evaluate_row_data(row_dict)["show_scan_button"] == true ) {
      if ( title == null && local_bibnum == null ) {
        title = grab_ancestor_title( row );
      }
      update_row( title, row_dict, row );
    }
    row.deleteCell( cell_position_map["barcode"] );
  }

  var init = function( cell_position_map, bibnum ) {
    /* Sets class variables.
     * Called by process_item()
     */
     local_cell_position_map = cell_position_map;
     local_bibnum = bibnum;
     return;
  }

  var extract_row_data = function( row ) {
    /* Takes row dom-object; extracts and returns fielded data.
     * First row.children[i] is a td-element.
     * Called by process_item()
     */
    var row_data = {};
    row_data["location"] = row.children[0].textContent.trim();
    row_data["availability"] = row.children[2].textContent.trim();
    var barcode = row.children[3].textContent.trim();
    row_data["barcode"] = barcode.split(" ").join("");
    var callnumber_node = row.children[1];
    row_data["callnumber"] = callnumber_node.childNodes[2].textContent.trim();
    var callnumber_child_nodes = callnumber_node.childNodes;
    for (var i = 0; i < callnumber_child_nodes.length; i++) {
      if ( callnumber_child_nodes[i].textContent.trim() == "field v" ) {
        if ( callnumber_child_nodes[i+1].textContent.trim() == "field #" ) {  // volume_year empty
          row_data["volume_year"] = "";
        } else {
          row_data["volume_year"] = callnumber_child_nodes[i+1].textContent.trim();
        }
      }
    };
    console.log( "- row_data, " + JSON.stringify(row_data, null, 4) );
    return row_data;
  }

  var evaluate_row_data = function( row_dict ) {
    /* Evaluates whether 'Request Scan' button should appear; returns boolean.
     * Called by process_item()
     */
    var row_evaluation = { "show_scan_button": false };
    if ( (row_dict["location"] == "ANNEX") && (row_dict["availability"] == "AVAILABLE") ) {
        row_evaluation = { "show_scan_button": true };
    }
    console.log( "- row_evaluation, " + row_evaluation );
    return row_evaluation;
  }

  var grab_ancestor_title = function( row ) {
    /* Grabs title on results page.
     * Called by process_item()
     */
    var big_element = row.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;  // apologies to all sentient beings
    console.log( "- in grab_ancestor_title(); big_element, `" + big_element + "`" );
    var title_td = big_element.querySelectorAll( ".briefcitDetail" )[0];
    console.log( "- in grab_ancestor_title(); title_td, `" + title_td + "`" );
    var title_plus = title_td.textContent.trim();
    var title = title_plus.split("\n")[0];
    console.log( "- in grab_ancestor_title(); title, `" + title + "`" );
    return title;
  }

  var update_row = function( title, row_dict, row ) {
    /* Adds `Request Scan` link to row html.
     * Triggers start of request-item link process.
     * Called by process_item()
     */
    link_html = build_link_html( title, row_dict )
    last_cell = row.getElementsByTagName("td")[local_cell_position_map["availability"]];
    $( last_cell ).after( link_html );
    console.log( "- request-scan link added" );
    easyscan_link_element = $(last_cell).next();
    request_item_flow_manager.check_permalink( easyscan_link_element );
    return;
  }

  var build_link_html = function( title, row_dict ) {
    /* Takes row dict; returns html link.
     * Called by update_row()
     */
    link = '<a class="easyscan" href="http://HOST/easyscan/request?callnumber=THECALLNUMBER&barcode=THEBARCODE&title=THETITLE&bibnum=THEBIBNUM&volume_year=THEVOLYEAR">Request Scan</a>';
    link = link.replace( "THECALLNUMBER", row_dict["callnumber"] );
    link = link.replace( "THEBARCODE", row_dict["barcode"] );
    link = link.replace( "THETITLE", title );
    link = link.replace( "THEBIBNUM", local_bibnum );
    link = link.replace( "THEVOLYEAR", row_dict["volume_year"] );
    console.log( "- link end, " + link );
    return link;
  }

};  // end namespace esyscn_row_processor


$(document).ready(
  function() {
    console.log( "- josiah_easyscan.js says document loaded" );
    $.getScript( "http://HOST/easyscan/josiah_request_item.js",
      function() {  // what to do on success
        console.log( "- josiah_request_item.js loaded" );
        esyscn_flow_manager.check_already_run();
      }
    );
  }
);

// $(document).ready(
//   function() {
//     console.log( "- josiah_easyscan.js says document loaded" );
//     esyscn_flow_manager.check_already_run();
//   }
// );


console.log( "- josiah_easyscan.js END" );

// JSON.stringify(obj, null, 4)
