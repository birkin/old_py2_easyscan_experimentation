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

  this.check_permalink = function() {
      /* Controller.
       * Called by document.ready()
       */
      console.log( "- in request_item_flow_manager.check_permalink()" );
      // temp-testing start
      var all_html = $("body").html().toString();  // jquery already loaded (whew)
      var local_index = all_html.indexOf( "127.0.0.1" );
      if ( local_index == -1 ){
        return
      }
      // temp-testing end
      var index = all_html.indexOf( "PermaLink to this record" );
      if (index != -1) {
        console.log( "- permalink found" );
        grab_bib();
      } else {
        console.log( "- permalink not found" );
      }
  }

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
    /* Builds link html.
     * Called by grab_bib()
     */
    console.log( "- in request_item_flow_manager.build_link_html(); bib, " + bib );
    var initial_link = ' | <a href="https://josiah.brown.edu:444/search~S7?/.THE_BIB/.THE_BIB/1%2C1%2C1%2CB/request~THE_BIB">Item</a>';
    var link = initial_link.replace(/THE_BIB/g, bib);  // http://www.w3schools.com/jsref/jsref_replace.asp
    console.log( "- in request_item_flow_manager.build_link_html(); link, " + link );
    // next();
    var el = document.getElementsByTagName( "a" )[34];
    console.log( "- in request_item_flow_manager.build_link_html(); el, " + el );
    // $( last_cell ).after( link_html );
    $( el ).after( link );
  }

}  // end request_item_flow_manager()


// document-ready only for testing
$(document).ready(
  function() {
    console.log( "- josiah_request_item.js says document loaded" );
    request_item_flow_manager.check_permalink();
  }
);


console.log( "- josiah_request_item.js END" );
