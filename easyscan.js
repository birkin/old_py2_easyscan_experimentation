console.log( "- easyscan.js START" );


// jquery already loaded (whew)
rows = $( ".bibItemsEntry" );
console.log( "- rows.length, " + rows.length );

row = rows[0];
cells = row.getElementsByTagName("td");
console.log( "- cells.length, " + cells.length );

cell1 = cells[0]
// console.log( "- cell, " + JSON.stringify(cell, null, 4) );  // circular error
console.log( "- cell1 textContent, " + cell1.textContent );

cell2 = cells[1]
console.log( "- cell2 textContent, " + cell2.textContent );

cell3 = cells[2]
console.log( "- cell3 textContent, " + cell3.textContent );


console.log( "- easyscan.js END" );

// JSON.stringify(obj)
