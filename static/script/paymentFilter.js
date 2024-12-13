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

        document.getElementById('dataForAPeriod')? document.getElementById('dataForAPeriod').addEventListener('click', function() {goToPagePaidDataForAPeriod();}):'';

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
    else if (page_url === 'payment-paid-list-for-a-period') {
        document.getElementById('refresh_data_for_a_period')? document.getElementById('refresh_data_for_a_period').addEventListener('click', function() {getPaymentPaidDataForAPeriod();}):'';
        document.getElementById('button_get_for_a_last_1_day')? document.getElementById('button_get_for_a_last_1_day').addEventListener('click', function() {twoDatesToGetPaidDataForAPeriod(this);}):'';
        document.getElementById('button_get_for_a_last_7_days')? document.getElementById('button_get_for_a_last_7_days').addEventListener('click', function() {twoDatesToGetPaidDataForAPeriod(this);}):'';
        document.getElementById('button_get_for_a_last_30_days')? document.getElementById('button_get_for_a_last_30_days').addEventListener('click', function() {twoDatesToGetPaidDataForAPeriod(this);}):'';
        document.getElementById('button_get_for_a_period')? document.getElementById('button_get_for_a_period').addEventListener('click', function() {twoDatesToGetPaidDataForAPeriod(this);}):'';

        let period_first_date_input = document.getElementById('period_first_date_input');
        if (period_first_date_input) {
            period_first_date_input.addEventListener('focusin', function() {convertOnFocusDateDataForAPeriod(this, 'focusin');});
            period_first_date_input.addEventListener('focusout', function() {convertOnFocusDateDataForAPeriod(this, 'focusout');});
        }
        let period_second_date_input = document.getElementById('period_second_date_input');
        if (period_second_date_input) {
            period_second_date_input.addEventListener('focusin', function() {convertOnFocusDateDataForAPeriod(this, 'focusin');});
            period_second_date_input.addEventListener('focusout', function() {convertOnFocusDateDataForAPeriod(this, 'focusout');});
        }
        var isExecutingDataForAPeriod = false;

    }
    else if (page_url === 'payment-inflow-history-list') {
        document.getElementById('filter-input-0')? document.getElementById('filter-input-0').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-1')? document.getElementById('filter-input-1').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-2')? document.getElementById('filter-input-2').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-3')? document.getElementById('filter-input-3').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-4')? document.getElementById('filter-input-4').addEventListener('change', function() {filterTable();}):'';
        document.getElementById('filter-input-5')? document.getElementById('filter-input-5').addEventListener('change', function() {filterTable();}):'';

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
                else if (
                        page_url === 'payment-inflow-history-list') {
                    paymentInflowHistory(data.sort_col['col_1'][0]);
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

function goToPagePaidDataForAPeriod() {
    window.location.href = '/payment-paid-list-for-a-period';
}

function convertDateDataForAPeriod(empDate, dec=".") {
    var sep = dec=="."?"-":".";
    var dateParts = empDate.split(dec);
    dateParts = `${dateParts[2]}${sep}${dateParts[1]}${sep}${dateParts[0]}`;
    return dateParts;
}

function convertOnFocusDateDataForAPeriod(empDate, focusStatus='') {
    if (!empDate.value) {
        empDate.type = focusStatus == 'focusin'? 'date':'text';
    }
    else if (empDate.type == 'text' && focusStatus == 'focusin') {
        tmp_value = convertDateDataForAPeriod(empDate.value);
        empDate.value = tmp_value;
        empDate.type = 'date';
    }
    else if (empDate.type == 'date' && focusStatus == 'focusout') {
        tmp_value = convertDateDataForAPeriod(empDate.value, "-");
        empDate.type = 'text';
        empDate.value = tmp_value;
    }
}
var isExecutingDataForAPeriod = false;
function twoDatesToGetPaidDataForAPeriod(btn) {
    // Кнопка 1 день
    if (btn.id == 'button_get_for_a_last_1_day') {
        let fDay = new Date(new Date(new Date().setHours(0, 0, 0, 0)));
        let sDay = fDay;

        document.getElementById('filterDateFirst_val').innerText = fDay;
        document.getElementById('filterDateSecond_val').innerText = sDay;
    }
    // Кнопка 7 дней
    else if (btn.id == 'button_get_for_a_last_7_days') {
        let fDay = new Date(new Date().setHours(0, 0, 0, 0));
        let sDay = new Date(new Date(new Date().setHours(0, 0, 0, 0)).setDate(fDay.getDate() - 6));
        fDay = new Date(fDay);

        document.getElementById('filterDateFirst_val').innerText = fDay;
        document.getElementById('filterDateSecond_val').innerText = sDay;
    }
    // Кнопка 30 дней
    else if (btn.id == 'button_get_for_a_last_30_days') {
        let fDay = new Date(new Date().setHours(0, 0, 0, 0));
        let sDay = new Date(new Date(new Date().setHours(0, 0, 0, 0)).setDate(fDay.getDate() - 29));
        fDay = new Date(fDay);

        document.getElementById('filterDateFirst_val').innerText = fDay;
        document.getElementById('filterDateSecond_val').innerText = sDay;
    }
    // Кнопка период
    else if (btn.id == 'button_get_for_a_period') {
        let fDay = document.getElementById('period_first_date_input').value;
        let sDay = document.getElementById('period_second_date_input').value;

        // Не указаны обе даты
        if (!fDay && !sDay) {
            return createDialogWindow(status='error', description=['Ошибка получения дат периода', 'Укажите хотя бы одну из двух дат']);
        }
        // Не указана одна из двух дат
        else if (!fDay) {
            document.getElementById('period_first_date_input').value = sDay;
            sDay = sDay.split(".");
            sDay = new Date(sDay[2], +sDay[1] - 1, sDay[0]);
            fDay = sDay;
        }
        // Не указана одна из двух дат
        else if (!sDay) {
            document.getElementById('period_second_date_input').value = fDay;
            fDay = fDay.split(".");
            fDay = new Date(fDay[2], +fDay[1] - 1, fDay[0]);
            sDay = fDay;
        }
        // Обе даты указаны
        else {
            fDay = fDay.split(".");
            sDay = sDay.split(".");
            fDay = new Date(fDay[2], +fDay[1] - 1, fDay[0]);
            sDay = new Date(sDay[2], +sDay[1] - 1, sDay[0]);
        }

        // Первая дата меньше второй даты
        if (fDay.valueOf() > sDay.valueOf()) {
            let tmp = fDay;
            fDay = sDay;
            sDay = tmp;
            let tmp_fDay = ('0' + fDay.getDate()).slice(-2) + '.' + ('0' + (fDay.getMonth() + 1)).slice(-2) + '.' + fDay.getFullYear();
            let tmp_sDay = ('0' + sDay.getDate()).slice(-2) + '.' + ('0' + (sDay.getMonth() + 1)).slice(-2) + '.' + sDay.getFullYear();

            document.getElementById('period_first_date_input').value = tmp_fDay;
            document.getElementById('period_second_date_input').value = tmp_sDay;
        }

        document.getElementById('filterDateFirst_val').innerText = new Date(fDay);
        document.getElementById('filterDateSecond_val').innerText = new Date(sDay);
    }
    // Функция вызвана не пойми откуда
    else {
        return createDialogWindow(status='error', description=['Ошибка выгрузки оплаченных платежей за период', 'Некорректный вызов функции']);
    }
    // Запрос данных с сервера
    getPaymentPaidDataForAPeriod();
}

function getPaymentPaidDataForAPeriod() {
    // Предыдущее выполнение функции не завершено
    if (isExecutingDataForAPeriod) {
        return createDialogWindow(status='error', description=['Предыдущая выгрузка данных ещё не завершена', 'Повторная выгрузка отменена', 'Вы можете обновить страницу и попробовать снова']);
    }
    isExecutingDataForAPeriod = true;

    var table = document.getElementById("payment-table");
    for (var i = 1; i<table.rows.length;) {
        table.deleteRow(i);
    }

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    var sortCol_1 = document.getElementById('sortCol-1').textContent;
    var sortCol_1_val = document.getElementById('sortCol-1_val').textContent;
    var sortCol_id_val = document.getElementById('sortCol-id_val').textContent;

    let fDay = document.getElementById('filterDateFirst_val').innerText;
    let sDay = document.getElementById('filterDateSecond_val').innerText;
    if (!fDay || !sDay) {
        isExecutingDataForAPeriod = false;
        return createDialogWindow(status='error', description=['Ошибка выгрузки оплаченных платежей', 'Не указана дата, обновите страницу']);
    }

    // Кнопка "Обновить данные" становится доступна
    document.getElementById('refresh_data_for_a_period').disabled = false;

    fDay = new Date(fDay);
    sDay = new Date(sDay);

    let dateFirst = fDay.getFullYear() + '-' +  ('0' + (fDay.getMonth() + 1)).slice(-2) + '-' + ('0' + fDay.getDate()).slice(-2);
    let dateSecond = sDay.getFullYear() + '-' +  ('0' + (sDay.getMonth() + 1)).slice(-2) + '-' + ('0' + sDay.getDate()).slice(-2);

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

    fetch('/get-payment_paid_data-for-a-period', {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'sort_col_1': sortCol_1,
                    'sort_col_1_val': sortCol_1_val,
                    'sort_col_id_val': sortCol_id_val,
                    'filterValsList': filterValsList,
                    'dateFirst': dateFirst,
                    'dateSecond': dateSecond,
                    'page_url': page_url,
                })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0];
                document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1];
                document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id'];
                if (page_url === 'payment-paid-list-for-a-period') {
                    paymentPaidPeriod(data);
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
            isExecutingDataForAPeriod = false;
        });

}