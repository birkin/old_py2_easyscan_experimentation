console.log( "- josiah_request_item.js START" );


var request_item_flow_manager = new function() {
  /*
   * Class flow description:
   *   - Determines if there is a permalink
   *   - If so,
   *     - Grabs the bib
   *     - Builds and displays 'Request Item' link
   *   - Other code (will be put in a separate class):
   *     - Determines if its a Request Item page triggered by this js
   *     - If so, takes user directly to the login part of the process
   */

  var local_easyscan_link_element = null;

  this.check_permalink = function( easyscan_link_element ) {
      /* Controller to add `request-item` link to each available annex item.
       * Checks for permalink.
       * Called by josiah_easyscan.esyscn_flow_manager.update_row()
       */
      console.log( "- in request_item_flow_manager.check_permalink()" );
      local_easyscan_link_element = easyscan_link_element;  // used if adding item-link -- TODO: this 'renaming' seems unnecessary, but I have a recollection that the original var name didn't work. Test and simplify if possible.
      console.log( "- in request_item_flow_manager.check_permalink(); local_easyscan_link_element.context.nodeName, " + local_easyscan_link_element.context.nodeName );
      var all_html = $("body").html().toString();  // jquery already loaded (whew)
      var index = all_html.indexOf( "PermaLink to this record" );
      if (index != -1) {
        console.log( "- permalink found" );
        grab_bib_from_permalink();
      } else {
        console.log( "- permalink not found" );
        check_additionalCopiesNav_div( local_easyscan_link_element );
      }
  }

  var check_additionalCopiesNav_div = function( local_easyscan_link_element ) {
    /* Checks for a div where the bib might be.
     * Called by check_permalink() when it can't find a permalink.
     */
    var all_html = $("body").html().toString();  // jquery already loaded (whew)
    var index = all_html.indexOf( "class=\"additionalCopiesNav\"" );
    if (index != -1) {
      console.log( "- additionalCopiesNav_div found" );
      grab_bib_from_additionalCopiesNav_div();
    } else {
      console.log( "- additionalCopiesNav_div not found" );
      check_table_div( local_easyscan_link_element );
    }
  }

  var check_table_div = function( local_easyscan_link_element ) {
    /* Checks for a results-page enclosing table div.
     * Called by check_additionalCopiesNav_div() when it can't find an additionalCopiesNav div.
     */
    console.log( "- in request_item_flow_manager.check_table_div(); local_easyscan_link_element.context.nodeName, " + local_easyscan_link_element.context.nodeName );
    var tbody = local_easyscan_link_element.context.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;
    if ( tbody.nodeName == "TBODY" ) {
      console.log( "- in request_item_flow_manager.check_table_div(); tbody found" );
      grab_bib_from_results_page( tbody );
    } else {
      console.log( "- in request_item_flow_manager.check_table_div(); tbody not found" );
    }
  }

  var grab_bib_from_results_page = function( tbody ) {
    /* Parses bib from results page table div.
     * Called by check_table_div()
     */
    console.log( "foo" );
     var row = tbody.children[0];
     var b_el = row.querySelector( "input" );
     var bib = b_el.value;
     console.log( "- in request_item_flow_manager.grab_bib_from_results_page(); bib is, " + bib );
     build_link_html( bib );
  }

  var grab_bib_from_permalink = function() {
    /* Parses bib from permalink.
     * Called by check_permalink()
     */
    el = document.getElementById( "recordnum" );
    href_string = el.getAttribute( "href" );
    b_string = href_string.split( "=" )[1];
    bib = b_string.slice( 0,8 );
    console.log( "- in request_item_flow_manager.grab_bib(); bib is, " + bib );
    build_link_html( bib );
  }

  var grab_bib_from_additionalCopiesNav_div = function() {
    /* Parses bib from additionalCopiesNav div.
     * Called by check_additionalCopiesNav_div()
     */
    var els = document.querySelectorAll( ".additionalCopiesNav" );
    var el = els[0];
    var link = el.children[0];
    var link_text = link.href;
    var segment = link_text.split( "/" )[4];  // .b1234567
    var bib = segment.slice( 1, 9 );
    console.log( "- in request_item_flow_manager.grab_bib_from_additionalCopiesNav_div(); bib is, " + bib );
    build_link_html( bib );
  }

  var build_link_html = function( bib ) {
    /* Builds link html and appends it.
     * Called by grab_bib()
     */
    console.log( "- in request_item_flow_manager.build_link_html(); bib, " + bib );
    var initial_link = ' or <a href="https://josiah.brown.edu:444/search~S7?/.THE_BIB/.THE_BIB/1%2C1%2C1%2CB/request~THE_BIB&goal=request_annex_item">Item</a>';
    var item_link = initial_link.replace( /THE_BIB/g, bib );  // http://www.w3schools.com/jsref/jsref_replace.asp
    console.log( "- in request_item_flow_manager.build_link_html(); item_link, " + item_link );
    // $( local_last_cell ).next().after( link );
    $( local_easyscan_link_element ).after( item_link );
  }

  /* other code called by josiah_easyscan.esyscn_flow_manager
   * TODO: put in separate class.
   */

  var check_url = function() {
    /* Checks url to see if we're requesting an annex item.
     * If so, speeds user to necessary login section.
     * Called by esyscn_flow_manager.delete_header_cell()
     */
     if ( location.toString().search("goal=request_annex_item") != -1 ) {
      console.log( "- in request_item_flow_manager.check_url(); `goal=request_annex_item` found" );
      // show( "annex" );  // in-page js function
      // toggleLayer( "requestForm" );  // in-page js function
     }
     console.log( "- in request_item_flow_manager.check_url(); done" );
     return
  }

}  // end request_item_flow_manager()


/* document-ready only for testing */
// $(document).ready(
//   function() {
//     console.log( "- josiah_request_item.js says document loaded" );
//     request_item_flow_manager.check_permalink();
//   }
// );


console.log( "- josiah_request_item.js END" );
