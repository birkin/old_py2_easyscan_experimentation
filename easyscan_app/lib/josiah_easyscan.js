console.log( "- josiah_easyscan.js START" );


var esyscn_flow_manager = new function() {
  /* Namespaces function calls.
   *
   * See <http://stackoverflow.com/a/881611> for module-pattern reference.
   * Only check_already_run() can be called publicly, and only via ```esyscn.check_already_run();```.
   *
   * Controller class flow description:
   * - Attempts to grab bib from permalink page
   * - If bib null, attempts to grab bib from where it might be on a holdings-page
   * - If bib null, attempts to grab bib from bib-page's html, getting there via holdings page link
   * - If bib null, proceeds to item-rows processing
   * - Finds all item-rows and for each row:
   *   - Calls namespace `esyscn_row_processor` to process the row
   *     - If bib null, row-processing tries to grab bib from multiple-result-page's enclosing element's input field
   *     - Row-processing then builds the links
   *   - Deletes item-barcode html
   *
   * Reference:
   * - items page: <http://josiah.brown.edu/record=b4069600>
   * - holdings page containing bib: <http://josiah.brown.edu/search~S7?/.b4069600/.b4069600/1,1,1,B/holdings~4069600&FF=&1,0,>
   * - holdings page without direct bib: <http://josiah.brown.edu/search~S7?/XAmerican+imago&searchscope=7&SORT=D/XAmerican+imago&searchscope=7&SORT=D&searchscope=07&SUBKEY=American+imago/1,53,53,B/holdings&FF=XAmerican+imago&2,2,>
   * - multiple results page: <http://josiah.brown.edu/search~S11/?searchtype=X&searcharg=zen&searchscope=11&sortdropdown=-&SORT=D&extended=1&SUBMIT=Search&searchlimits=&searchorigarg=tzen>
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
      grab_permalink_bib();
    }
  }

  var grab_permalink_bib = function() {
    /* Grabs bib via #recordnum; then continues processing.
     * Called by check_already_run()
     */
    var elmnt = document.querySelector( "#recordnum" );
    console.log( 'elmnt, ' + elmnt )
    if ( elmnt == null ) {
      check_holdings_html_for_bib();
    } else {
      var url_string = elmnt.href;
      var segments = url_string.split( "=" )[1];
      bibnum = segments.slice( 0,8 );
      console.log( "- bibnum, " + bibnum );
      if ( bibnum == null ) {
        check_holdings_html_for_bib();
      } else {
        process_item_table();
      }
    }
  }

  var check_holdings_html_for_bib = function() {
    /* Looks for presence of bib-page link (link may or may not contain bibnum).
     * Called by grab_permalink_bib() if bib is null.
     */
    var dvs = document.querySelectorAll(".additionalCopiesNav");  // first of two identical div elements
    if ( dvs.length > 0 ) {
      console.log( "in check_holdings_html_for_bib(); checking dvs" );
      var dv = dvs[0];
      var el = dv.children[0];  // the div contains a link with the bibnum
      var href_string = el.toString();
      console.log( "in check_holdings_html_for_bib(); href_string, " + href_string );
      grab_bib_from_holdings_html( href_string )
    }
    if ( bibnum == null ) {
      console.log( "in check_holdings_html_for_bib(); no bib luck yet" );
      grab_bib_from_following_href( href_string );
    } else {
      process_item_table();
    }
  }

  var grab_bib_from_holdings_html = function( href_string ) {
    /* Tries to determine bibnum from holdings html; then continues processing.
     * Called by grab_title() if title is null.
     */
    var segment = href_string.split("/")[4];  // eg ".b4069600"
    if ( segment.length == 9 && segment.slice( 0,2 ) == ".b" ) {
      bibnum = segment.slice( 1, 9 );  // updates module var
      console.log( "in grab_bib_from_holdings_html(); bibnum, " + bibnum );
    }
  }

  var grab_bib_from_following_href = function( href_string ) {
    /* Tries to load bib-page and grab bib from permalink element; then continues processing.
     * Called by grab_bib_from_holdings_html()
     */
    $.ajaxSetup( {async: false} );  // otherwise processing would immediately continue while $.get() makes it's request asynchronously
    $.get( href_string, function(data) {
      var div_temp = document.createElement( "div_temp" );
      div_temp.innerHTML = data;
      var nodes = div_temp.querySelectorAll( "#recordnum" );
      console.log( "nodes.length, " + nodes.length );
      if ( nodes.length > 0 ) {
        var bib_temp = nodes[0].href.split( "=" )[1];
        bibnum = bib_temp.slice( 0,8 );  // updates module's var
        console.log( "- in grab_bib_from_following_href(); outside of $.get(); bibnum is, " + bibnum );
      } else {
        console.log( "ah, the tricky multiple results page" );
      }
      process_item_table();  // process it either way
    } );
  }

  var process_item_table = function() {
    /* Updates bib-items to show request-scan links.
     * Called by grab_title() or grab_bib_from_holdings_html()
     */
    console.log( "- in process_item_table(); bibnum is, " + bibnum );
    var rows = $( ".bibItemsEntry" );
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      esyscn_row_processor.process_item( row, cell_position_map, bibnum );
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
      // return;
      request_item_flow_manager.check_url();  // // holding off on adding `request-item` functionality
    } else {
      header_row.deleteCell( cell_position_map["barcode"] );
      console.log( "- barcode header cell deleted" );
    }
  }

};  // end namespace esyscn_flow_manager, ```var esyscn_flow_manager = new function() {```


var esyscn_row_processor = new function() {
  /*
   * Class flow description:
   *   - Determines whether to show a scan button
   *   - If so, and if bib still blank, grabs bib from where it would be on a multiple-results page
   *   - Builds and displays 'Request Scan' link from bib and barcode and item-info in row's html
   *   - Calls the 'Request Item' link builder from `josiah_request_item.js`
   */

  var local_cell_position_map = null;
  var local_bibnum = null;


  this.process_item = function( row, cell_position_map, bibnum ) {
    /* Processes each row.
     * Called by esyscn_flow_manager.process_item_table()
     */
    init( cell_position_map, bibnum );
    var row_dict = extract_row_data( row );
    if ( evaluate_row_data(row_dict)["show_scan_button"] == true ) {
      if ( local_bibnum == null ) {
        console.log( "would handle blank bibnum here" );
        local_bibnum = grab_ancestor_bib( row );
      }
      update_row( row_dict, row );
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
    console.log( "- row_evaluation, " + JSON.stringify(row_evaluation, null, 4) );
    return row_evaluation;
  }

  var grab_ancestor_bib = function( row ) {
    /* Grabs bib on results page.
     * Called by process_item()
     */
    var big_element = row.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;  // apologies to all sentient beings
    console.log( "- in grab_ancestor_bib(); big_element, `" + big_element + "`" );
    var temp_bibnum = big_element.querySelector( "input" ).value;
    console.log( "- in grab_ancestor_bib(); temp_bibnum, `" + temp_bibnum + "`" );
    return temp_bibnum;
  }

  var update_row = function( row_dict, row ) {
    /* Adds `Request Scan` link to row html.
     * Triggers start of request-item link process.
     * Called by process_item()
     */
    link_html = build_link_html( row_dict );
    last_cell = row.getElementsByTagName("td")[local_cell_position_map["availability"]];
    console.log( "- in josiah_easyscan.esyscn_row_processor.update_row(); last_cell, " + last_cell.nodeName );
    $( last_cell ).after( link_html );
    console.log( "- request-scan link added" );
    easyscan_link_element = $(last_cell).next();
    console.log( "- in josiah_easyscan.esyscn_row_processor.update_row(); easyscan_link_element, " + easyscan_link_element );
    console.log( "- in josiah_easyscan.esyscn_row_processor.update_row(); easyscan_link_element context, " + easyscan_link_element.context );
    console.log( "- in josiah_easyscan.esyscn_row_processor.update_row(); easyscan_link_element context.nodeName, " + easyscan_link_element.context.nodeName );
    request_item_manager.display_request_link( row, local_bibnum, row_dict["barcode"] );
    return;
  }

  var build_link_html = function( row_dict ) {
    /* Takes row dict; returns html link.
     * Called by update_row()
     */
    // link = 'Request <a class="easyscan" href="http://HOST/easyscan/request?callnumber=THECALLNUMBER&barcode=THEBARCODE&title=THETITLE&bibnum=THEBIBNUM&volume_year=THEVOLYEAR">Scan</a>';
    link = 'Request <a class="easyscan" href="https://library.brown.edu/easyscan/request?callnumber=THECALLNUMBER&barcode=THEBARCODE&bibnum=THEBIBNUM&volume_year=THEVOLYEAR">Scan</a>';
    link = link.replace( "THECALLNUMBER", row_dict["callnumber"] );
    link = link.replace( "THEBARCODE", row_dict["barcode"] );
    link = link.replace( "THEBIBNUM", local_bibnum );
    link = link.replace( "THEVOLYEAR", row_dict["volume_year"] );
    console.log( "- link end, " + link );
    return link;
  }

};  // end namespace esyscn_row_processor


$(document).ready(
  function() {
    console.log( "- josiah_easyscan.js says document loaded" );
    // $.getScript( "SCHEME://HOST/easyscan/josiah_request_item.js",
    $.getScript( "https://library.brown.edu/easyscan/josiah_request_item.js",
      function() {  // what to do on success
        console.log( "- josiah_request_item.js loaded" );
        esyscn_flow_manager.check_already_run();
      }
    );
  }
);


console.log( "- josiah_easyscan.js END" );
