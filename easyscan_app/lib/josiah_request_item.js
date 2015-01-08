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
      var all_html = $("body").html().toString();  // jquery already loaded (whew)
      var local_index = all_html.indexOf( "127.0.0.1" );
      if ( local_index == -1 ){
        return
      }
      var index = all_html.indexOf( "PermaLink to this record" );
      if (index != -1) {
        console.log( "- permalink found" );
        grab_bib();
      } else {
        console.log( "- permalink not found" );
      }
  }

  var grab_bib = function() {
    /* Returns bib from permalink.
     * Called by check_permalink()
     */
    el = document.getElementById( "recordnum" );
    href_string = el.getAttribute( "href" );
    b_string = href_string.split( "=" )[1];
    bib = b_string.slice( 0,8 );
    console.log( "- in request_item_flow_manager.grab_bib(); bib is, " + bib );
    return bib;
  }

}  // end request_item_flow_manager()


$(document).ready(
  function() {
    console.log( "- josiah_request_item.js says document loaded" );
    request_item_flow_manager.check_permalink();
  }
);


console.log( "- josiah_request_item.js END" );
