$(document).ready(function() {
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
    document.getElementById('filter-input-13')? document.getElementById('filter-input-13').addEventListener('change', function() {filterTable();}):'';
    document.getElementById('filter-input-14')? document.getElementById('filter-input-14').addEventListener('change', function() {filterTable();}):'';
    document.getElementById('filter-input-16')? document.getElementById('filter-input-16').addEventListener('change', function() {filterTable();}):'';

    document.getElementById('employeeCardWin')? document.getElementById('employeeCardWin').addEventListener('click', function() {closeModal();}):'';

    var downloadButton = document.getElementById('employeeCardWin');
    downloadButton.style.textDecoration = 'none';

    document.getElementById('verif_dialog_empl_crossBtnNAW')? document.getElementById('verif_dialog_empl_crossBtnNAW').addEventListener('click', function() {this.closest('dialog').close();}):'';
    document.getElementById('verif_dialog_empl__cancel')? document.getElementById('verif_dialog_empl__cancel').addEventListener('click', function() {this.closest('dialog').close();}):'';
});

function filterTable() {
    var table = document.getElementById("employeeTable");
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
    console.log(filterValsList)

    fetch('/get-first-employee', {
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

                employeeList(data.sort_col['col_1'][0]);
            }
            else if (data.status === 'error') {
                if (!data.employee) {
                    alert(data.description)
                    window.location.href = '/employees-list';
                }
                else {
                    document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                    document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                    document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];

                    const tab = document.getElementById("employeeTable");
                    var tab_tr = tab.getElementsByTagName('tbody')[0];
                    var row = tab_tr.insertRow(0);
                    var emptyTable = row.insertCell(0);
                    emptyTable.className = "empty_table";
                    emptyTable.innerHTML = 'Данные не найдены';
                    emptyTable.style.textAlign = "center";
                    emptyTable.style.fontStyle = "italic";

                    emptyTable.colSpan = tab.getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th').length;
                }
            }
        });

}

