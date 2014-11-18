console.log( "- easyscan.js START" );


var cell_position_map = { "location": 0, "call_number": 1, "barcode": 2, "availability": 3 }

$(document).ready(
  function() {
    update_item_table();
  }
);

function update_item_table() {
  /* Updates bib-item list to show request-scan button.
   * Called by document.ready()
   */
  rows = $( ".bibItemsEntry" );  // jquery already loaded (whew)
  console.log( "- rows.length, " + rows.length );
  for (var i = 0; i < rows.length; i++) {
    row = rows[i];
    row_dict = extract_row_data( row );
    link_html = build_link_html( row_dict )
    last_cell = row.getElementsByTagName("td")[cell_position_map["availability"]];
    $( last_cell ).after( link_html );
    row.deleteCell( cell_position_map["barcode"] );
  }
  delete_header_cell();
}

function extract_row_data( row ) {
  /* Takes row dom-object; extracts and returns fielded data.
   * Called by update_item_table()
   */
  cells = row.getElementsByTagName("td");
  row_data = {}
  map_keys = Object.keys( cell_position_map );  // yeilds [ "location", "call_number", etc. ] - compatible with older browsers?
  for (var i = 0; i < map_keys.length; i++) {
    key = map_keys[i];
    value = cells[ cell_position_map[key] ].textContent.trim();
    row_data[key] = value;
  }
  console.log( "- row_data, " + JSON.stringify(row_data, null, 4) );
  return row_data;
}

// function extract_row_data( row ) {
//   /* Takes row dom-object; extracts and returns fielded data.
//    * Called by update_item_table()
//    */
//   cells = row.getElementsByTagName("td");
//   var row_data = {
//     "location": cells[cell_position_map["location"]].textContent.trim(),
//     "call_number": cells[cell_position_map["call_number"]].textContent.trim(),
//     "barcode": cells[cell_position_map["barcode"]].textContent.trim(),
//     "availability": cells[cell_position_map["availability"]].textContent.trim()
//   };
//   console.log( "- row_data, " + JSON.stringify(row_data, null, 4) );
//   return row_data;
// }

function build_link_html( row_dict ) {
  /* Takes row dict; returns html link.
   * Called by extract_row_data()
   */
  link = '<a href="http://127.0.0.1/easyscan/request?call_number=THECALLNUMBER&barcode=THEBARCODE">Request Scan</a>';
  link = link.replace( "THECALLNUMBER", row_dict["call_number"] );
  link = link.replace( "THEBARCODE", row_dict["barcode"] );
  console.log( "- link end, " + link );
  return link;
}

function delete_header_cell() {
  /* Deletes barcode header cell
   * Called by update_item_table()
   */
  header_row = $( "tr.bibItemsHeader" )[0];
  header_row.deleteCell( cell_position_map["barcode"] );
  console.log( "- barcode header cell deleted" );
}


console.log( "- easyscan.js END" );

// JSON.stringify(obj, null, 4)
