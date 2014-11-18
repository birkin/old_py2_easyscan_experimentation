console.log( "- easyscan.js START" );


// jquery already loaded (whew)
rows = $( ".bibItemsEntry" );
console.log( "- rows.length, " + rows.length );

for (var i = 0; i < rows.length; i++) {
  row = rows[i];
  row_dict = extract_row_data( row );
  console.log( "- row_dict, " + JSON.stringify(row_dict, null, 4) );
}

function extract_row_data( row ) {
  cells = row.getElementsByTagName("td");
  var row_data = {
    "location": cells[0].textContent.trim(),
    "call_number": cells[1].textContent.trim(),
    "barcode": cells[2].textContent.trim(),
    "availability": cells[3].textContent.trim()
  };
  return row_data;
}

console.log( "- easyscan.js END" );

// JSON.stringify(obj, null, 4)



// row = rows[0];
// cells = row.getElementsByTagName("td");
// console.log( "- cells.length, " + cells.length );

// cell1 = cells[0]
// // console.log( "- cell, " + JSON.stringify(cell, null, 4) );  // circular error
// console.log( "- cell1 textContent, " + cell1.textContent );

// cell2 = cells[1]
// console.log( "- cell2 textContent, " + cell2.textContent );

// cell3 = cells[2]
// console.log( "- cell3 textContent, " + cell3.textContent );
