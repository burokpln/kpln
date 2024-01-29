function filterTable() {
    var table = document.getElementById("payment-table");
    for (var i = 1; i<table.rows.length;) {
        table.deleteRow(i);
    }

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    var sortCol_1 = document.getElementById('sortCol-1').textContent;
    var sortCol_1_val = document.getElementById('sortCol-1_val').textContent;
    var sortCol_id_val = document.getElementById('sortCol-id_val').textContent;

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
                document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']

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
        });

}

