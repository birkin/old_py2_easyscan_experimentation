console.log( "- josiah_request_item.js START" );


var request_item_flow_manager = new function() {
  /*
   * Class flow description:
   *   - Determines if there is a permalink
   *   - If so,
   *     - Grabs the bib
   *     - Builds and displays 'Request Item' link
   *   - If not,
   *     - Determines if its a Request Item page triggered by this js
   *     - If so,
   *       - Takes user directly to the login part of the process
   */

  var local_easyscan_link_element = null;

  this.check_permalink = function( easyscan_link_element ) {
      /* Controller.
       * Called by document.ready()
       */
      console.log( "- in request_item_flow_manager.check_permalink()" );
      local_easyscan_link_element = easyscan_link_element;  // used if adding item-link
      var all_html = $("body").html().toString();  // jquery already loaded (whew)
      var index = all_html.indexOf( "PermaLink to this record" );
      if (index != -1) {
        console.log( "- permalink found" );
        grab_bib();
      } else {
        console.log( "- permalink not found" );
        check_url();
      }
  }

  /* if no permalink found */

  var check_url = function() {
    /* Checks url to see if we're requesting an annex item.
     * If so, speeds user to necessary login section.
     * Called by check_permalink()
     */
     if ( location.toString().search("goal=request_annex_item") != -1 ){
       show( "annex" );  // in-page js function
       toggleLayer( "requestForm" );  // in-page js function
     }
     console.log( "- in request_item_flow_manager.check_url()" );
     return
  }

  /* if permalink found */

  var grab_bib = function() {
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

  var build_link_html = function( bib ) {
    /* Builds link html and appends it.
     * Called by grab_bib()
     */
    console.log( "- in request_item_flow_manager.build_link_html(); bib, " + bib );
    var initial_link = ' | <a href="https://josiah.brown.edu:444/search~S7?/.THE_BIB/.THE_BIB/1%2C1%2C1%2CB/request~THE_BIB&goal=request_annex_item">Item</a>';
    var item_link = initial_link.replace( /THE_BIB/g, bib );  // http://www.w3schools.com/jsref/jsref_replace.asp
    console.log( "- in request_item_flow_manager.build_link_html(); item_link, " + item_link );
    // $( local_last_cell ).next().after( link );
    $( local_easyscan_link_element ).after( item_link );
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
