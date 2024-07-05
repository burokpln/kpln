$(document).ready(function() {
    if (document.getElementById('visualTablePA')) {
        document.getElementById('visualTablePA').addEventListener('click', function() {
            window['tableCustom'].showModal();
        });
    };

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    if (page_url === 'payment-approval') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
    }
    else if (page_url === 'payment-approval-list') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
    }
    else if (page_url === 'payment-pay') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
        document.getElementById('sort-div-13')? document.getElementById('sort-div-13').addEventListener('click', function() {sortTable(13);}):'';
    }
    else if (page_url === 'payment-paid-list') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
        document.getElementById('sort-div-13')? document.getElementById('sort-div-13').addEventListener('click', function() {sortTable(13);}):'';
    }
    else if (page_url === 'payment-paid-list-for-a-period') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
        document.getElementById('sort-div-13')? document.getElementById('sort-div-13').addEventListener('click', function() {sortTable(13);}):'';
        document.getElementById('sort-div-14')? document.getElementById('sort-div-14').addEventListener('click', function() {sortTable(14);}):'';
    }
    else if (page_url === 'payment-list') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
    }
    else if (page_url === 'employees-list') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
        document.getElementById('sort-div-13')? document.getElementById('sort-div-13').addEventListener('click', function() {sortTable(13);}):'';
        //// Не понятно, как сортировать такие столбцы. По этому не сортируем их
        //document.getElementById('sort-div-14')? document.getElementById('sort-div-14').addEventListener('click', function() {sortTable(14);}):'';
        //document.getElementById('sort-div-15')? document.getElementById('sort-div-15').addEventListener('click', function() {sortTable(15);}):'';
        document.getElementById('sort-div-16')? document.getElementById('sort-div-16').addEventListener('click', function() {sortTable(16);}):'';
    }
    else if (page_url === 'contract-main') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
    }
    else if (page_url === 'contract-objects') {
        document.getElementById('sort-div-0')? document.getElementById('sort-div-0').addEventListener('click', function() {sortTable(0);}):'';
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
    }
    else if (page_url === 'contract-list') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
        document.getElementById('sort-div-12')? document.getElementById('sort-div-12').addEventListener('click', function() {sortTable(12);}):'';
        document.getElementById('sort-div-13')? document.getElementById('sort-div-13').addEventListener('click', function() {sortTable(13);}):'';
        document.getElementById('sort-div-14')? document.getElementById('sort-div-14').addEventListener('click', function() {sortTable(14);}):'';
        document.getElementById('sort-div-15')? document.getElementById('sort-div-15').addEventListener('click', function() {sortTable(15);}):'';
        document.getElementById('sort-div-16')? document.getElementById('sort-div-16').addEventListener('click', function() {sortTable(16);}):'';

    }
    else if (page_url === 'contract-acts-list') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
    }
    else if (page_url === 'contract-acts-list') {
        document.getElementById('sort-div-1')? document.getElementById('sort-div-1').addEventListener('click', function() {sortTable(1);}):'';
        document.getElementById('sort-div-2')? document.getElementById('sort-div-2').addEventListener('click', function() {sortTable(2);}):'';
        document.getElementById('sort-div-3')? document.getElementById('sort-div-3').addEventListener('click', function() {sortTable(3);}):'';
        document.getElementById('sort-div-4')? document.getElementById('sort-div-4').addEventListener('click', function() {sortTable(4);}):'';
        document.getElementById('sort-div-5')? document.getElementById('sort-div-5').addEventListener('click', function() {sortTable(5);}):'';
        document.getElementById('sort-div-6')? document.getElementById('sort-div-6').addEventListener('click', function() {sortTable(6);}):'';
        document.getElementById('sort-div-7')? document.getElementById('sort-div-7').addEventListener('click', function() {sortTable(7);}):'';
        document.getElementById('sort-div-8')? document.getElementById('sort-div-8').addEventListener('click', function() {sortTable(8);}):'';
        document.getElementById('sort-div-9')? document.getElementById('sort-div-9').addEventListener('click', function() {sortTable(9);}):'';
        document.getElementById('sort-div-10')? document.getElementById('sort-div-10').addEventListener('click', function() {sortTable(10);}):'';
        document.getElementById('sort-div-11')? document.getElementById('sort-div-11').addEventListener('click', function() {sortTable(11);}):'';
    }
});

function sortTable(column) {
    var table = document.getElementById("payment-table");
    if (!table) {
        table = document.getElementById("employeeTable");
    }
    else if (!table) {
        table = document.getElementById("towTable");
    }
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
    if (page_url === 'payment-paid-list-for-a-period') {
//        document.getElementById('sortCol-1').textContent = i;
        getPaymentPaidDataForAPeriod();
    }
    else {
        filterTable();
    }
}