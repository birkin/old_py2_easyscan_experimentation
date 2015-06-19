console.log( "- josiah_request_item.js START" );


var request_item_manager = new function() {
  /*
   * Class flow description:
   *   - builds link to easyRequest web-app
   *     - url takes bib and barcode params
   */

  /* set globals, essentially class attributes */
  var local_bibnum = null;
  var local_barcode = null;
  var local_row = null;

  this.display_request_link = function( easyscan_link_element, bibnum, barcode ) {
    /* Calls functions to add `request-item` link to each available annex item.
     * Called by josiah_easyscan.esyscn_row_processor.update_row()
     */
    console.log( "- in request_item_manager.display_request_link(); starting" );
    initialize( easyscan_link_element, bibnum, barcode );
    var url = build_url();
    var link_node = build_link_node( url );
    display_link( link_node );
    console.log( "- in request_item_manager.display_request_link(); done" );
  }

  var initialize = function( row_element, bibnum, barcode ) {
    /* Stores params to attributes.
     * Called by display_request_link()
     */
    local_bibnum = bibnum;
    local_barcode = barcode;
    local_row = row_element;
    return;
  }

  var build_url = function() {
    /* Builds url.
     * Called by display_request_link()
     */
    var url_a = 'https://worfdev.services.brown.edu/easyrequest/?bibnum=BIBNUM&barcode=BARCODE';
    var url_b = url_a.replace( /BIBNUM/g, local_bibnum );  // http://www.w3schools.com/jsref/jsref_replace.asp
    var url = url_b.replace( /BARCODE/g, local_barcode );
    console.log( "- in request_item_manager.build_url(); url, " + url );
    return url;
  }

  var build_link_node = function( url ) {
    /* Builds link node.
     * Called by display_request_link()
     */
    var a = document.createElement( "a" );
    a.href = url;
    a.setAttribute( "class", "annex_request_link" );
    var link_text = document.createTextNode( "Item" );
    a.appendChild( link_text );
    console.log( "- in request_item_manager.build_link_node(); built" );
    return a;
  }

  var display_link = function( link_node ) {
    /* Assembles nodes.
     * Called by display_request_link()
     */
    var pipe = document.createTextNode( " | " );
    local_row.appendChild( pipe );
    local_row.appendChild( link_node );
    console.log( "- in request_item_manager.display_link(); link added" );
  }

}  // end namespace request_item_manager


console.log( "- josiah_request_item.js END" );
