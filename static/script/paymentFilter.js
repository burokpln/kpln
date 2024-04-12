$(document).ready(function() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    if (['payment-approval', 'payment-pay', 'payment-approval-list', 'payment-paid-list', 'payment-list'].includes(page_url)) {
        document.addEventListener('DOMContentLoaded', function() {
            var paymentForm = document.getElementById('paymentForm');
            paymentForm.style.alignSelf = 'flex-start';
        });

    }
    if (page_url === 'payment-approval') {
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-6')? document.getElementById('filter-input-6').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-7')? document.getElementById('filter-input-7').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-8')? document.getElementById('filter-input-8').addEventListener('change', function() {filterTable();}):'';

        var totalSelectInfo = document.getElementById('totalSelectInfo');
        totalSelectInfo.style.display = 'none';
    }
    else if (page_url === 'payment-approval-list') {
        document.getElementById('filter-input-0')? document.getElementById('filter-input-0').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-6')? document.getElementById('filter-input-6').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-7')? document.getElementById('filter-input-7').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-8')? document.getElementById('filter-input-8').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-9')? document.getElementById('filter-input-9').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-10')? document.getElementById('filter-input-10').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-11')? document.getElementById('filter-input-11').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-12')? document.getElementById('filter-input-12').addEventListener('change', function() {filterTable();}):'';
    }
    else if (page_url === 'payment-pay') {
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-6')? document.getElementById('filter-input-6').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-7')? document.getElementById('filter-input-7').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-8')? document.getElementById('filter-input-8').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-9')? document.getElementById('filter-input-9').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-10')? document.getElementById('filter-input-10').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-11')? document.getElementById('filter-input-11').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-13')? document.getElementById('filter-input-13').addEventListener('change', function() {filterTable();}):'';
    }
    else if (page_url === 'payment-paid-list') {
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-6')? document.getElementById('filter-input-6').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-7')? document.getElementById('filter-input-7').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-8')? document.getElementById('filter-input-8').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-9')? document.getElementById('filter-input-9').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-10')? document.getElementById('filter-input-10').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-11')? document.getElementById('filter-input-11').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-12')? document.getElementById('filter-input-12').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-13')? document.getElementById('filter-input-13').addEventListener('change', function() {filterTable();}):'';

    }
    else if (page_url === 'payment-list') {
        document.getElementById('filter-input-0')? document.getElementById('filter-input-0').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-6')? document.getElementById('filter-input-6').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-7')? document.getElementById('filter-input-7').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-8')? document.getElementById('filter-input-8').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-9')? document.getElementById('filter-input-9').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-10')? document.getElementById('filter-input-10').addEventListener('change', function() {filterTable();}):'';

        var downloadButton = document.getElementById('a_downloadButton');
        downloadButton.style.textDecoration = 'none';
    }
});

function filterTable() {
    var table = document.getElementById("payment-table");
    for (var i = 1; i<table.rows.length;) {
        table.deleteRow(i);
    }

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    var sortCol_1 = document.getElementById('sortCol-1').textContent;
    var sortCol_1_val = document.getElementById('sortCol-1_val').textContent;
    var sortCol_id_val = document.getElementById('sortCol-id_val').textContent;

    document.getElementById('sortCol-1').textContent = '';
    document.getElementById('sortCol-1_val').textContent = '';
    document.getElementById('sortCol-id_val').textContent = '';

    var filter_input = document.querySelectorAll('[id*="filter-input-"]');
    var filterValsList = []; // Значения фильтров

    for (var i=0; i<filter_input.length; i++) {
        if (filter_input[i].value) {
            filterValsList.push([i, filter_input[i].value]);
        }
    }

    fetch('/get-first-pay', {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'limit': 1,
                    'sort_col_1': sortCol_1,
                    'sort_col_1_val': sortCol_1_val,
                    'sort_col_id_val': sortCol_id_val,
                    'filterValsList': filterValsList,
                    'page_url': page_url,
                })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];

                if (page_url === 'payment-approval') {
                    paymentApproval(data.sort_col['col_1'][0]);
                }
                else if (
                        page_url === 'payment-approval-list' ||
                        page_url === 'payment-paid-list' ||
                        page_url === 'payment-list') {
                    paymentList(data.sort_col['col_1'][0]);
                }
                else if (
                        page_url === 'payment-pay') {
                    paymentPay(data.sort_col['col_1'][0]);
                }
            }
            else if (data.status === 'error') {

                document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];

                const tab = document.getElementById("payment-table");
                var tab_tr = tab.getElementsByTagName('tbody')[0];
                var row = tab_tr.insertRow(0);
                var emptyTable = row.insertCell(0);
                emptyTable.className = "empty_table";
                emptyTable.innerHTML = 'Данные не найдены';
                emptyTable.style.textAlign = "center";
                emptyTable.style.fontStyle = "italic";

                emptyTable.colSpan = tab.getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th').length;
            }
        });

}

