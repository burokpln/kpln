function filterTable() {
    var table = document.getElementById("employeeTable");
    for (var i = 1; i<table.rows.length;) {
        table.deleteRow(i);
    }

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    // Если зашли из проекта, то в ссылке находим название проекта
    var obj_name = document.URL.lastIndexOf('/objects')>0? document.URL.substring(document.URL.lastIndexOf('/objects')+9, document.URL.lastIndexOf('/')):'';

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

    console.log('sortCol_id_val', sortCol_id_val)

    fetch('/get-first-contract', {
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
                    'link': obj_name,
                })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];

                if (page_url === 'contracts-main' || page_url === 'contracts-objects' || page_url === 'contracts-list' || page_url === 'contracts-acts-list' || page_url === 'contracts-payments-list') {
                    contractPagination(data.sort_col['col_1'][0]);
                }
            }
            else if (data.status === 'error') {
                if (data.sort_col) {
                    document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                    document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                    document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];
                }

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
        });

}

