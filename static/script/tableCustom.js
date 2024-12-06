$(document).ready(function() {
    document.getElementById('closeBtnTC')? document.getElementById('closeBtnTC').addEventListener('click', function() {tableCustomSave();}):'';
});

const crossButtonTC = document.querySelector("#crossBtnTC");
const dialogTC = document.querySelector("#tableCustom");


crossButtonTC.addEventListener("click", closeDialogTC);
function closeDialogTC() {
    dialogTC.close();
}

var col_lst = [];
var hide_status_lst = [];

var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

if (page_url !== 'new-payment') {

    table = document.getElementById("payment-table");
    cols = table.getElementsByTagName("tr")[0].getElementsByTagName("th");
    table_hidden_col = table.dataset.hidden_col;
    if (table_hidden_col) {
        table_hidden_col = table_hidden_col.slice(1, table_hidden_col.length-1).split(',');
    }

    for (var i = 0; i < cols.length; i++) {
        var jj = cols[i].getElementsByTagName("div")[0].innerHTML.split('&nbsp;')[0];
        col_lst.push(jj)
        if (table_hidden_col && table_hidden_col.includes(i.toString())) {
            hide_status_lst.push(false)
        }
        else {
            hide_status_lst.push(cols[i].getAttribute('hidden') == null ? true : false);
        }
    }


    var table_columns_list = document.getElementById('columns_list');

    if (col_lst.length) {
        for (var i = 0; i < col_lst.length; i++) {

            let newRow = document.createElement("tr");

            let newCell_1 = document.createElement("td");
            newCell_1.className = "ttdname"
            newCell_1.innerHTML = col_lst[i][0].toUpperCase() + col_lst[i].substring(1).toLowerCase();

            let newCell_2 = document.createElement("td");
            newCell_2.className = "ttdcbox";
            var newCell_2_input = document.createElement("input");
            newCell_2_input.type = "checkbox";
            newCell_2_input.checked = hide_status_lst[i];
            newCell_2.appendChild(newCell_2_input)

            newRow.appendChild(newCell_1);
            newRow.appendChild(newCell_2);
            table_columns_list.appendChild(newRow);
            if (table_hidden_col && table_hidden_col.includes(i.toString())) {
                newRow.setAttribute("hidden", "hidden");
            }
        }
    }
    else {
        table_columns_list.textContent = 0;
    }
}


function tableCustomSave() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    var table_custom2 = document.getElementById("columns_list").getElementsByTagName("tr");

    // Список скрываемых колонок
    hide_col_lst = [];
    show_col_lst = [];

    if (page_url === 'new-payment') {
        for (var i = 0; i < table_custom2.length; i++) {
            row = table_custom2[i].getElementsByTagName("td");
            if (!row[1].getElementsByTagName("input")[0].checked) {
                hide_col_lst.push(row[0].id);
            }
            else {
                show_col_lst.push(row[0].id);
            }
        }
    }

    else if (page_url !== 'new-payment') {
        for (var i = 0; i < table_custom2.length; i++) {
            row = table_custom2[i].getElementsByTagName("td");
            if (!row[1].getElementsByTagName("input")[0].checked) {
                hide_col_lst.push(i);
            }
            else {
                show_col_lst.push(i);
            }
        }

        // Список скрытых ранее столбцов
        table2 = document.getElementById("payment-table");
        rows2 = table2.getElementsByTagName("tr")[0].getElementsByTagName("th");
        show_col_lst2 = [];

        for (var i = 0; i < rows2.length; i++) {
            if (rows2[i].getAttribute("hidden") !== null) {
                for (var s of show_col_lst) {
                    i == s ? show_col_lst2.push(i) : 1;
                }
            }
        }

        if (hide_col_lst.length) {
            for (var i of hide_col_lst) {
                $(`#payment-table th:nth-child(${i + 1})`).attr("hidden", true);
                $(`#payment-table td:nth-child(${i + 1})`).attr("hidden", true);
            }
        }

        show_col_lst = show_col_lst2
        if (show_col_lst.length) {
            for (var i of show_col_lst) {
                $(`#payment-table th:nth-child(${i + 1})`).removeAttr('hidden');
                $(`#payment-table td:nth-child(${i + 1})`).removeAttr('hidden');
            }
        }
    }
    var msg = page_url === 'new-payment' ? "Изменения сохранены. Обновите страницу" : "Изменения сохранены"

    if (hide_col_lst.length || show_col_lst.length) {

        var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

        fetch('/save_tab_settings', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'page_url': page_url,
                'hide_list': hide_col_lst
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    closeDialogTC();
                    alert(msg)

                    //                        document.querySelector("#tableCustom").close();
                }
                else if (data.status === 'error') {
                    alert(data.description);

                }
                else {
                    window.location.href = `/${page_url}`;
                }
            })
            .catch(error => {
                sendErrorToServer(['save_tab_settings', error.toString()]);
                console.error('Error:', error);
            });
    }
}
