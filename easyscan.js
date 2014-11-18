console.log( "- easyscan.js START" );


// jquery already loaded (whew)
rows = $( ".bibItemsEntry" );
console.log( "- rows.length, " + rows.length );

for (var i = 0; i < rows.length; i++) {
  row = rows[i];
  row_dict = extract_row_data( row );
  link_html = build_link_html( row_dict )
  last_cell = row.getElementsByTagName("td")[3];
  // $( last_cell ).after( "<td>HELLO</td>" );
  $( last_cell ).after( link_html );
}

function extract_row_data( row ) {
  cells = row.getElementsByTagName("td");
  var row_data = {
    "location": cells[0].textContent.trim(),
    "call_number": cells[1].textContent.trim(),
    "barcode": cells[2].textContent.trim(),
    "availability": cells[3].textContent.trim()
  };
  console.log( "- row_data, " + JSON.stringify(row_data, null, 4) );
  return row_data;
}

function build_link_html( row_dict ) {
  // link = '<a href="http://google.com">LINK</a>';
  link = '<a href="http://127.0.0.1/easyscan/request?call_number=THECALLNUMBER&barcode=THEBARCODE">Request Scan</a>';
  link = link.replace( "THECALLNUMBER", row_dict["call_number"] );
  link = link.replace( "THEBARCODE", row_dict["barcode"] );
  console.log( "- link end, " + link );
  return link;
}

console.log( "- easyscan.js END" );

// JSON.stringify(obj, null, 4)
