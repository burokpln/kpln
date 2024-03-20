function sortTable(column, type_col = 'str') {
    var table = document.getElementById("payment-table");
    row_0 = table.getElementsByTagName("tr")[0];

    var col_cnt = row_0.getElementsByTagName("th").length
    for (var i = 0; i < col_cnt; i++) {
        i == column? 1:row_0.getElementsByTagName("th")[i].getElementsByClassName("arrow_sort")[0].innerText = '';
    }

    dir = {'▲': ['▼', 1], '▼': ['▲', 0]};

    var old_dir = row_0.getElementsByTagName("th")[column].getElementsByClassName("arrow_sort")[0].innerText;

    if (!old_dir) {
        old_dir = '▼';
        document.getElementById('sortCol-1').textContent = `${column}#1`
        var sortCol_1 = `${column}#1`
        row_0.getElementsByTagName("th")[column].getElementsByClassName("arrow_sort")[0].innerText = old_dir;
    }
    else if (dir[old_dir]) {
        row_0.getElementsByTagName("th")[column].getElementsByClassName("arrow_sort")[0].innerText = dir[old_dir][0];
        var sortCol_1 = `${column}#${dir[old_dir][1]}`
        document.getElementById('sortCol-1').textContent = `${column}#${dir[old_dir][1]}`
    }
    document.getElementById('sortCol-1_val').textContent = '';
    document.getElementById('sortCol-id_val').textContent = '';
    filterTable();

}