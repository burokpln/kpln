//function sortTable2(column, type_col = 'str') {
//    const progressBar = document.querySelector('.progress').style.width;
//    const progressBar2 = document.querySelector('.progress2').style.width;
//    console.log(progressBar, progressBar2)
//    const t2ab = document.getElementById("payment-table").getElementsByTagName('tbody')[0];
//    var tab_numRow = t2ab.getElementsByTagName('tr');
//    console.log(tab_numRow.length)
//
//    // Сортируем через JS
//    if (progressBar == '100%' && progressBar2 == '0%' && tab_numRow.length < 100) {
//        sortTableJS(column, type_col);
//    }
//}
//
//function sortTableJS(column, type_col = 'str') {
//    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
//    table = document.getElementById("payment-table");
//    switching = true;
//    // Set the sorting direction to ascending
//    dir = "asc";
//    rows = table.getElementsByTagName("tr");
//    while (switching) {
//        switching = false;
//        for (i = 1; i < (rows.length - 1); i++) {
//            shouldSwitch = false;
//            x = rows[i].getElementsByTagName("td")[column].dataset.sort;
//            y = rows[i + 1].getElementsByTagName("td")[column].dataset.sort;
//
//            // Тип данных в колонки - строка
//            if (type_col == "str") {
//                if (dir == "asc") {
//                    if (x.toLowerCase() > y.toLowerCase()) {
//                        shouldSwitch = true;
//                        break;
//                    }
//                }
//                else if (dir == "desc") {
//                    if (x.toLowerCase() < y.toLowerCase()) {
//                        shouldSwitch = true;
//                        break;
//                    }
//                }
//            }
//            // Тип данных в колонки - цифра
//            else if (type_col == "num") {
//                if (dir == "asc") {
//                    if (parseFloat(x) > parseFloat(y)) {
//                        shouldSwitch = true;
//                        break;
//                    }
//                }
//                else if (dir == "desc") {
//                    if (parseFloat(x) < parseFloat(y)) {
//                        shouldSwitch = true;
//                        break;
//                    }
//                }
//            }
//        }
//        if (shouldSwitch) {
//            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
//            switching = true;
//            switchcount++;
//        } else {
//            for (i = 1; i < (rows.length - 1); i++) {
//            }
//            if (switchcount == 0 && dir == "asc") {
//                dir = "desc";
//                switching = true;
//            }
//        }
//    }
//
//    // Список колонок с чекбоксом
//    checkbox_col_num = [];
//    for (var i1 = 0; i1 < rows[1].getElementsByTagName("td").length; i1++) {
//        try {
//             if (rows[1].getElementsByTagName("td")[i1].getElementsByTagName("input")[0].getAttribute('type') === 'checkbox') {
//                 checkbox_col_num.push(i1);
//             }
//        }
//        catch {
//        }
//    }
//
//    // у всех чекбоксов меняем значение value и переименовываем название строк
//    if (checkbox_col_num.length) {
//        for (i = 1; i < rows.length; i++) {
//            for (j of checkbox_col_num) {
//                rows[i].getElementsByTagName("td")[j].getElementsByTagName("input")[0].setAttribute("value", i);
//            }
//            rows[i].id = `row-${i-1}`;
//        }
//    }
//    else {
//        for (i = 1; i < rows.length; i++) {
//            rows[i].id = `row-${i-1}`;
//        }
//    }
//
//    // Стрелки в шапке таблицы
//    var col_cnt = rows[0].getElementsByTagName("th").length
//    for (var i = 0; i < col_cnt; i++) {
//        rows[0].getElementsByTagName("th")[i].getElementsByClassName("arrow_sort")[0].innerText = ''
//    }
//    var symbol = dir == "asc"? '▲':'▼'
//    rows[0].getElementsByTagName("th")[column].getElementsByClassName("arrow_sort")[0].innerText = symbol
//
//    tabColorize();
//}

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