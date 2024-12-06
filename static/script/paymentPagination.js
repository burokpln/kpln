$(document).ready(function() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    if (!['payment-approval', 'payment-pay', 'payment-list', 'payment-approval-list', 'payment-paid-list', 'payment-inflow-history-list'].includes(page_url)) {
        var isExecuting = false;
        return;
    }

    const tableR = document.querySelector('.tableR');
    var dialog = document.getElementById("payment-approval__dialog");

    var tableR2 = document.getElementById('payment-table');

    var table_max_length = 175

    if(tableR) {
        if ($(this).innerHeight() > tableR2.offsetHeight) {
            var sortCol_1 = document.getElementById('sortCol-1').textContent;
            if (page_url === 'payment-approval') {
                var isExecuting = false;
                paymentApproval(sortCol_1);
            }
            else if (page_url === 'payment-pay') {
                var isExecuting = false;
                paymentPay(sortCol_1);
            }
            else if (page_url === 'payment-list'|| page_url === 'payment-approval-list' ||page_url === 'payment-paid-list') {
                var isExecuting = false;
                paymentList(sortCol_1);
            }
            else if (page_url === 'payment-inflow-history-list') {
                var isExecuting = false;
                paymentInflowHistory(sortCol_1);
            }
        }
    }

    tableR.addEventListener('scroll', function() {
        var sortCol_1 = document.getElementById('sortCol-1').textContent;
        var scrollPosition = $(this).scrollTop()

        // Скроллим вверх
        if (!scrollPosition && sortCol_1) {
            var tab = document.getElementById("payment-table");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            if (tab_numRow.length >= table_max_length) {
                for (var i = tab_numRow.length; i>table_max_length; i--) {
                    tableR2.deleteRow(i);
                }

                if (page_url === 'payment-approval') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[8].getElementsByTagName('input')[0].value;
                    var payment_due_date = tab_numRow[0].getElementsByTagName('td')[6].dataset.sort;
                    var isExecuting = false;
                    paymentApproval(sortCol_1=sortCol_1, direction='up', sortCol_1_val=payment_due_date, sortCol_id_val=payment_id);
                }
                else if (page_url === 'payment-pay') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[2].dataset.sort;
                    var payment_due_date = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    paymentPay(sortCol_1=sortCol_1, direction='up', sortCol_1_val=payment_due_date, sortCol_id_val=payment_id);
                }
                else if (page_url === 'payment-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[10].dataset.sort;
                    var isExecuting = false;
                    paymentList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=payment_id);
                }
                else if (page_url === 'payment-approval-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    paymentList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=payment_id);
                }
                else if (page_url === 'payment-paid-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    paymentList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=payment_id)
                }
                 else if (page_url === 'payment-inflow-history-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[5].dataset.sort;
                    var isExecuting = false;
                    paymentInflowHistory(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=payment_id)
                }

                tableR.scrollTo({
                    top: 10,
                    behavior: "smooth",
                });
            }
        }

        // Скроллим в самый низ
        if (scrollPosition + $(this).innerHeight() >= $(this)[0].scrollHeight && sortCol_1) {
            document.getElementById('sortCol-1').textContent = '';

            const tab = document.getElementById("payment-table");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            if (page_url === 'payment-approval') {
                var isExecuting = false;
                paymentApproval(sortCol_1);
            }
            else if (page_url === 'payment-pay') {
                var isExecuting = false;
                paymentPay(sortCol_1);
            }
            else if (page_url === 'payment-list' || page_url === 'payment-approval-list' || page_url === 'payment-paid-list') {
                var isExecuting = false;
                paymentList(sortCol_1);
            }
            else if (page_url === 'payment-inflow-history-list') {
                var isExecuting = false;
                paymentInflowHistory(sortCol_1);
            }
            if(tableR) {
                //  возвращает координаты в контексте окна для минимального по размеру прямоугольника tableR
                const rect = tableR.getBoundingClientRect();
            }
            if (tab_numRow.length > table_max_length) {
                for (var i = 1; i<=tab_numRow.length-table_max_length;) {
                    tableR2.deleteRow(1);
                }

            }
            return;
        }
    });
});

function progressBarCalc(direction, numRow, tab_rows, rowCount){
    const progressBar = document.querySelector('.progress');
    const progressBar2 = document.querySelector('.progress2');

    progress_val1 = direction === 'down'? ((numRow / tab_rows)*100).toFixed(2) + '%': ((numRow+rowCount-1)/tab_rows*100).toFixed(2) + '%';

    progress_val2 = direction === 'down'? ((numRow-rowCount)/tab_rows*100).toFixed(2) + '%': ((numRow-1)/tab_rows*100).toFixed(2) + '%';

    progressBar.style.width = progress_val1;
    progressBar2.style.width = progress_val2;
}

function prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val){
    //Значение параметров сортировки
    sortCol_1_val = !sortCol_1_val? document.getElementById('sortCol-1_val').textContent: sortCol_1_val;
    sortCol_id_val = !sortCol_id_val? document.getElementById('sortCol-id_val').textContent: sortCol_id_val;

    if (direction === 'up') {
        sortCol_1 = sortCol_1.split('#')[0] + '#' + (sortCol_1.split('#')[1]=='1'? 0: 1);
    }

    var filter_input = document.querySelectorAll('[id*="filter-input-"]');
    var filterValsList = []; // Значения фильтров

    for (var i=0; i<filter_input.length; i++) {
        if (filter_input[i].value) {
            filterValsList.push([i, filter_input[i].value]);
        }
    }

    return([sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList]);
}

var limit = 25
var isExecuting = false;

function paymentApproval(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return
    }
    isExecuting = true;

    [sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList] = prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val);

    // Получили пустые данные - загрузили всю таблицу - ничего не делаем
    if (!sortCol_1) {
        isExecuting = false;
        return
    }
    else {
        fetch('/get-paymentApproval-pagination', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'limit': limit,
                'sort_col_1': sortCol_1,
                'sort_col_1_val': sortCol_1_val,
                'sort_col_id_val': sortCol_id_val,
                'filterValsList': filterValsList,
            })
        })
            .then(response => response.json())
            .then(data => {
                isExecuting = false;
                if (data.status === 'success') {
                    if (!data.payment) {
                        if (direction === 'up') {
                            if (data.sort_col['col_1'][0]) {
                                data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            }
                        }
                        else {
                            data.sort_col['col_1'][0]? document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]: 0;
                            data.sort_col['col_1'][1]? document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]: 0;
                            data.sort_col['col_id']? document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']: 0;
                        }
                        return;
                    }
                    if (direction === 'up') {
                        if (data.sort_col['col_1'][0]) {
                            data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        }
                    }
                    else {
                        document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                        document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']
                    }

                    const tab = document.getElementById("payment-table");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');


                    // Определяем номер строки
                    let numRow;
                    if (direction === 'down') {
                        try {
                            numRow = parseInt(tab_numRow[tab_numRow.length-1].getElementsByTagName('td')[0].getElementsByTagName('input')[0].value);
                        }
                        catch {
                            numRow = 0;
                        }
                    }
                    else {
                        numRow = tab_numRow[0].id;
                        numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];

                    var rowCount = 0;
                    for (let pmt of data.payment) {

                        direction === 'down'? numRow++: numRow-- ;

                        let numRow1 = numRow;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        let table2 = document.getElementById("payment-table");
                        rowCount = table2.rows.length;

                        let row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // Флажок выбора
                        let cellCheckbox = row.insertCell(0);
                        cellCheckbox.className = "th_select_i";
                        cellCheckbox.setAttribute("data-sort", "0");
                        data.setting_users.hasOwnProperty('0') ? cellCheckbox.hidden = true: 0;
                        let checkbox = document.createElement('input');
                        checkbox.type = "checkbox";
                        checkbox.id = `selectedRows-${numRow}`;
                        checkbox.name = "selectedRows";
                        checkbox.value = numRow;
                        checkbox.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); paymentApprovalNoSelect(numRow1); refreshSortValChb(numRow1);});
                        cellCheckbox.appendChild(checkbox);

                        //**************************************************
                        // Описание
                        let cellDescription = row.insertCell(1);
                        cellDescription.className = "th_description_i";
                        cellDescription.setAttribute("data-sort", `${pmt['descr_part1']}: ${pmt['payment_description']}`);
                        data.setting_users.hasOwnProperty('1') ? cellDescription.hidden = true: 0;
                        cellDescription.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        cellDescription.title = `${pmt['descr_part1']}\n${pmt['payment_description']}`;
                        let spanBold = document.createElement('span');
                        spanBold.className = "paymentFormBold";
                        spanBold.innerHTML = pmt['descr_part1'] + ":<br>";
                        let textNode = document.createTextNode(pmt['payment_description_short']);
                        cellDescription.appendChild(spanBold);
                        cellDescription.appendChild(textNode);

                        //**************************************************
                        // Общая сумма
                        let cellPaymentSum = row.insertCell(2);
                        cellPaymentSum.className = "th_main_sum_i";
                        cellPaymentSum.setAttribute("data-sort", pmt['payment_sum']);
                        data.setting_users.hasOwnProperty('2') ? cellPaymentSum.hidden = true: 0;
                        cellPaymentSum.innerHTML = pmt['payment_sum_rub'];

                        //**************************************************
                        // Остаток к оплате
                        let cellSumRemain = row.insertCell(3);
                        cellSumRemain.className = "th_sum_remain_i";
                        cellSumRemain.setAttribute("data-sort", pmt['approval_sum']);
                        data.setting_users.hasOwnProperty('3') ? cellSumRemain.hidden = true: 0;
                        let inputApprovalSum = document.createElement('input');
                        inputApprovalSum.id = `approvalSum-${numRow}`;
                        inputApprovalSum.name = "approval_sum";
                        inputApprovalSum.value = pmt['approval_sum'];
                        inputApprovalSum.hidden = true;
                        inputApprovalSum.readOnly = true;
                        cellSumRemain.innerHTML = pmt['approval_sum_rub'];
                        cellSumRemain.appendChild(inputApprovalSum);

                        //**************************************************
                        // Согласованная сумма
                        let cellSumAgreed = row.insertCell(4);
                        cellSumAgreed.className = "th_sum_agreed_i";
                        cellSumAgreed.setAttribute("data-sort", pmt['amount']);
                        data.setting_users.hasOwnProperty('4') ? cellSumAgreed.hidden = true: 0;
                        let inputAmount = document.createElement('input');
                        inputAmount.id = `amount-${numRow}`;
                        inputAmount.name = "amount";
                        inputAmount.value = pmt['amount_rub'];
                        inputAmount.setAttribute("data-amount", 0);
                        inputAmount.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); saveData(numRow1, data.page); refreshSortValAmount(numRow1);});
                        cellSumAgreed.appendChild(inputAmount);
                        if (data.user_role_id == '6') {
                            cellSumAgreed.hidden = true;
                        }

                        //**************************************************
                        // Ответственный
                        let cellResponsible = row.insertCell(5);
                        cellResponsible.className = "th_responsible_i";
                        cellResponsible.setAttribute("data-sort", `${pmt['last_name']} ${pmt['first_name']}`);
                        data.setting_users.hasOwnProperty('5') ? cellResponsible.hidden = true: 0;
                        cellResponsible.innerHTML = `${pmt['last_name']} ${pmt['first_name'][0]}.`;

                        //**************************************************
                        // Срок оплаты
                        let cellPayDate = row.insertCell(6);
                        cellPayDate.className = "th_pay_date_i";
                        cellPayDate.setAttribute("data-sort", pmt['payment_due_date']);
                        data.setting_users.hasOwnProperty('6') ? cellPayDate.hidden = true: 0;
                        cellPayDate.innerHTML = pmt['payment_due_date_txt'];

                        //**************************************************
                        // Статус
                        let cellStatus = row.insertCell(7);
                        cellStatus.className = "th_status_i";
                        cellStatus.id = `status-${numRow}`;
                        cellStatus.setAttribute("data-sort", pmt['status_id']);
                        data.setting_users.hasOwnProperty('7') ? cellStatus.hidden = true: 0;
                        let selectStatus = document.createElement('select');
                        selectStatus.id = `status_id-${numRow}`;
                        selectStatus.name = "status_id";
                        selectStatus.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); saveData(numRow1, data.page);});
                        for (let j = 0; j < data.approval_statuses.length; j++) {
                            let option = document.createElement('option');
                            option.text = data.approval_statuses[j].payment_agreed_status_name;
                            selectStatus.appendChild(option);
                        }
                        selectStatus[0].selected = true;
                        for (i = 0; i < selectStatus.length; i++) {
                            if (selectStatus[i].value === pmt['status_name'].toString()) {
                                selectStatus[i].selected = true;
                            }
                        }
                        cellStatus.appendChild(selectStatus);

                        //**************************************************
                        // Дата создания
                        let cellDateCreate = row.insertCell(8);
                        cellDateCreate.className = "th_date_create_i";
                        cellDateCreate.setAttribute("data-sort", pmt['payment_at']);
                        data.setting_users.hasOwnProperty('8') ? cellDateCreate.hidden = true: 0;
                        let inputPaymentNumber = document.createElement('input');
                        inputPaymentNumber.id = `paymentNumber-${numRow}`;
                        inputPaymentNumber.name = "payment_number";
                        inputPaymentNumber.value = pmt['payment_id'];
                        inputPaymentNumber.hidden = true;
                        inputPaymentNumber.readOnly = true;
                        cellDateCreate.innerHTML = pmt['payment_at_txt'];
                        cellDateCreate.appendChild(inputPaymentNumber);

                        //**************************************************
                        // До полной оплаты
                        let cellSavePay = row.insertCell(9);
                        cellSavePay.className = "th_save_pay_i";
                        cellSavePay.setAttribute("data-sort", pmt['payment_full_agreed_status'] ? "1" : "0");
                        data.setting_users.hasOwnProperty('9') ? cellSavePay.hidden = true: 0;
                        let checkboxPaymentFullStatus = document.createElement('input');
                        checkboxPaymentFullStatus.type = "checkbox";
                        checkboxPaymentFullStatus.id = `paymentFullStatus-${numRow}`;
                        checkboxPaymentFullStatus.name = "payment_full_agreed_status";
                        checkboxPaymentFullStatus.value = numRow;
                        if (pmt['payment_full_agreed_status']) {
                            checkboxPaymentFullStatus.checked = true;
                        }
                        checkboxPaymentFullStatus.addEventListener("change", function() {saveData(numRow1, data.page); tabColorize(numRow1); refreshSortValChb(numRow1);});
                        cellSavePay.appendChild(checkboxPaymentFullStatus);

                        tabColorize(numRow);

                    }
                    // Прогресс бар
                    progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/payment-approval';
                }
        })
        .catch(error => {
        sendErrorToServer(['get-paymentApproval-pagination', error.toString()]);
        console.error('Error:', error);
    });
    }
};

function paymentPay(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return
    }
    isExecuting = true;

    [sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList] = prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val)

    // Получили пустые данные - загрузили всю таблицу - ничего не делаем
    if (!sortCol_1) {
        isExecuting = false;
        return;
    }
    else {
        fetch('/get-paymentPay-pagination', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'limit': limit,
                'sort_col_1': sortCol_1,
                'sort_col_1_val': sortCol_1_val,
                'sort_col_id_val': sortCol_id_val,
                'filterValsList': filterValsList
            })
        })
            .then(response => response.json())
            .then(data => {
                isExecuting = false;
                if (data.status === 'success') {
                    if (!data.payment) {
                        if (direction === 'up') {
                            if (data.sort_col['col_1'][0]) {
                                data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            }
                        }
                        else {
                            data.sort_col['col_1'][0]? document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]: 0;
                            data.sort_col['col_1'][1]? document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]: 0;
                            data.sort_col['col_id']? document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']: 0;
                        }
                        return;
                    }
                    if (direction === 'up') {
                        if (data.sort_col['col_1'][0]) {
                            data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        }
                    }
                    else {
                        document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                        document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']
                    }

                    const tab = document.getElementById("payment-table");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            numRow = parseInt(tab_numRow[tab_numRow.length-1].getElementsByTagName('td')[0].getElementsByTagName('input')[0].value)
                        }
                        catch {
                            numRow = 0
                        }
                    }
                    else {
                        numRow = tab_numRow[0].id;
                        numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
                    var rowCount = 0;

                    for (let pmt of data.payment) {

                        direction === 'down'? numRow++: numRow-- ;

                        let numRow1 = numRow;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        let table2 = document.getElementById("payment-table");
                        rowCount = table2.rows.length;
                        let lastRow = table2.rows[rowCount - 1];

                        let row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // Флажок выбора
                        let cellCheckbox = row.insertCell(0);
                        cellCheckbox.className = "th_select_i";
                        cellCheckbox.setAttribute("data-sort", "0");
                        data.setting_users.hasOwnProperty('0') ? cellCheckbox.hidden = true: 0;
                        let checkbox = document.createElement('input');
                        checkbox.type = "checkbox";
                        checkbox.id = `selectedRows-${numRow}`;
                        checkbox.name = "selectedRows";
                        checkbox.value = numRow;
                        checkbox.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); paymentApprovalNoSelect(numRow1); refreshSortValChb(numRow1);});
                        cellCheckbox.appendChild(checkbox);

                        //**************************************************
                        // Статья затрат
                        let cellCostItemName = row.insertCell(1);
                        cellCostItemName.className = "th_category_i";
                        cellCostItemName.id = `category-${numRow}`;
                        cellCostItemName.setAttribute("data-sort", pmt['cost_item_name']);
                        cellCostItemName.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('1') ? cellCostItemName.hidden = true: 0;
                        cellCostItemName.innerHTML = pmt['cost_item_name'];
                        let input = document.createElement('input');
                        input.id = `paymentNumber-${numRow}`;
                        input.name = 'payment_number';
                        input.value = pmt['payment_id'];
                        input.hidden = true;
                        input.readOnly = true;
                        cellCostItemName.appendChild(input);

                        //**************************************************
                        // Номер платежа
                        let cellPayNumber = row.insertCell(2);
                        cellPayNumber.className = "th_payment_number_i"
                        cellPayNumber.setAttribute("data-sort", pmt['payment_id']);
                        cellPayNumber.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('2') ? cellPayNumber.hidden = true: 0;
                        cellPayNumber.innerHTML = pmt['payment_number'];

                        //**************************************************
                        // Наименование платежа
                        let cellPayName = row.insertCell(3);
                        cellPayName.className = "th_name_i"
                        cellPayName.setAttribute("data-sort", pmt['basis_of_payment']);
                        cellPayName.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        cellPayName.title = `${pmt['basis_of_payment']}`;
                        data.setting_users.hasOwnProperty('3') ? cellPayName.hidden = true: 0;
                        cellPayName.innerHTML = pmt['basis_of_payment'];

                        //**************************************************
                        // Описание
                        let cellDescription = row.insertCell(4);
                        cellDescription.className = "th_description_i";
                        cellDescription.setAttribute("data-sort", `${pmt['contractor_name']}: ${pmt['payment_description']}`);
                        cellDescription.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        cellDescription.title = `${pmt['payment_description']}`;
                        data.setting_users.hasOwnProperty('4') ? cellDescription.hidden = true: 0;
                        let spanBold = document.createElement('span');
                        spanBold.className = "paymentFormBold";
                        spanBold.innerHTML = pmt['contractor_name'] + ": ";
                        let textNode = document.createTextNode(pmt['payment_description']);
                        let inputDescription = document.createElement('input');
                        inputDescription.name = 'contractor_id';
                        inputDescription.value = pmt['contractor_id'];
                        inputDescription.hidden = true;
                        inputDescription.readOnly = true;
                        cellDescription.appendChild(inputDescription);

                        cellDescription.appendChild(spanBold);
                        cellDescription.appendChild(textNode);

                        //**************************************************
                        // Объект
                        let cellObject = row.insertCell(5);
                        cellObject.className = "th_object_i"
                        cellObject.setAttribute("data-sort", pmt['object_name']);
                        cellObject.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('5') ? cellObject.hidden = true: 0;
                        cellObject.innerHTML = pmt['object_name'];

                        //**************************************************
                        // Ответственный
                        let cellResponsible = row.insertCell(6);
                        cellResponsible.className = "th_responsible_i"
                        cellResponsible.setAttribute("data-sort", `${pmt['last_name']} ${pmt['first_name']}`);
                        cellResponsible.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('6') ? cellResponsible.hidden = true: 0;
                        cellResponsible.innerHTML = `${pmt['last_name']} ${pmt['first_name'][0]}`;

                        //**************************************************
                        // Контрагент
                        let cellContractor = row.insertCell(7);
                        cellContractor.className = "th_contractor_i"
                        cellContractor.setAttribute("data-sort", pmt['partner']);
                        cellContractor.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('7') ? cellContractor.hidden = true: 0;
                        cellContractor.innerHTML = pmt['partner'];

                        //**************************************************
                        // Общая сумма
                        let cellSumPay = row.insertCell(8);
                        cellSumPay.className = "th_main_sum_i"
                        cellSumPay.setAttribute("data-sort", pmt['payment_sum']);
                        cellSumPay.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('8') ? cellSumPay.hidden = true: 0;
                        cellSumPay.innerHTML = pmt['payment_sum_rub'];

                        //**************************************************
                        // Оплаченная сумма
                        let cellSumPaid = row.insertCell(9);
                        cellSumPaid.className = "th_paid_sum_i"
                        cellSumPaid.setAttribute("data-sort", pmt['paid_sum']);
                        cellSumPaid.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('9') ? cellSumPaid.hidden = true: 0;
                        cellSumPaid.innerHTML = pmt['paid_sum_rub'];

                        //**************************************************
                        // Согласованная сумма
                        let cellSumAgreed = row.insertCell(10);
                        cellSumAgreed.className = "th_sum_remain_i";
                        cellSumAgreed.setAttribute("data-sort", pmt['approval_sum']);
                        cellSumAgreed.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('10') ? cellSumAgreed.hidden = true: 0;
                        let inputSumAgreed = document.createElement('input');
                        inputSumAgreed.id = `approvalSum-${numRow}`;
                        inputSumAgreed.name = 'approval_sum';
                        inputSumAgreed.value = pmt['approval_sum'];
                        inputSumAgreed.hidden = true;
                        inputSumAgreed.readOnly = true;
                        cellSumAgreed.innerHTML = pmt['approval_sum_rub'];
                        cellSumAgreed.appendChild(inputSumAgreed);

                        //**************************************************
                        // Сумма к оплате
                        let cellSumCurrent = row.insertCell(11);
                        cellSumCurrent.className = "th_sum_agreed";
                        cellSumCurrent.setAttribute("data-sort", pmt['amount']);
                        data.setting_users.hasOwnProperty('11') ? cellSumCurrent.hidden = true: 0;
                        let inputAmount = document.createElement('input');
                        inputAmount.id = `amount-${numRow}`;
                        inputAmount.name = "amount";
                        inputAmount.value = pmt['amount_rub'];
                        inputAmount.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); saveData(numRow1, data.page);});
                        cellSumCurrent.appendChild(inputAmount);

                        //**************************************************
                        // Срок оплаты
                        let cellPayDate = row.insertCell(12);
                        cellPayDate.className = "th_date_create_i";
                        cellPayDate.setAttribute("data-sort", pmt['payment_due_date']);
                        cellPayDate.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        data.setting_users.hasOwnProperty('12') ? cellPayDate.hidden = true: 0;
                        cellPayDate.innerHTML = pmt['payment_due_date_txt'];

                        //**************************************************
                        // Дата создания
                        let cellDateCreate = row.insertCell(13);
                        cellDateCreate.className = "th_date_create_i";
                        cellDateCreate.setAttribute("data-sort", pmt['payment_at']);
                        data.setting_users.hasOwnProperty('13') ? cellDateCreate.hidden = true: 0;
                        cellDateCreate.innerHTML = pmt['payment_at_txt'];

                        //**************************************************
                        // До полной оплаты
                        let cellSavePay = row.insertCell(14);
                        cellSavePay.className = "th_save_pay_i";
                        cellSavePay.setAttribute("data-sort", pmt['payment_full_agreed_status'] ? "1" : "0");
                        data.setting_users.hasOwnProperty('14') ? cellSavePay.hidden = true: 0;
                        let checkboxPaymentFullStatus = document.createElement('input');
                        checkboxPaymentFullStatus.type = "checkbox";
                        checkboxPaymentFullStatus.id = `paymentFullStatus-${numRow}`;
                        checkboxPaymentFullStatus.name = "payment_full_agreed_status";
                        checkboxPaymentFullStatus.value = numRow;
                        if (pmt['payment_full_agreed_status']) {
                            checkboxPaymentFullStatus.checked = true;
                        }
                        checkboxPaymentFullStatus.addEventListener("change", function() {saveData(numRow1, data.page); tabColorize(numRow1); refreshSortValChb(numRow1);});
                        cellSavePay.appendChild(checkboxPaymentFullStatus);

                    }

                    // Прогресс бар
                    progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/payment-pay';
                }
        })
        .catch(error => {
        sendErrorToServer(['get-paymentPay-pagination', error.toString()]);
        console.error('Error:', error);
    });
    }
}

function paymentList(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return
    }
    isExecuting = true;

    [sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList] = prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val)

    var fetchFunc = ''; // Название вызываемой функции в fetch
    var col_shift = 0; // Сдвиг колонок
    var col_shift2 = 0; // Сдвиг колонок
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    if (page_url == 'payment-list') {
        fetchFunc = '/get-paymentList-pagination';
    }
    else if (page_url == 'payment-approval-list') {
        fetchFunc = '/get-paymentApprovalList-pagination';
        col_shift = 1;
    }
    else if (page_url == 'payment-paid-list') {
        fetchFunc = '/get-paymentPaidList-pagination';
        col_shift = 1;
        col_shift2 = 1;
    }

    // Получили пустые данные - загрузили всю таблицу - ничего не делаем
    if (!sortCol_1) {
        isExecuting = false;
        return;
    }
    else {

        fetch(fetchFunc, {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'limit': limit,
                'sort_col_1': sortCol_1,
                'sort_col_1_val': sortCol_1_val,
                'sort_col_id_val': sortCol_id_val,
                'filterValsList': filterValsList,
            })
        })
            .then(response => response.json())
            .then(data => {
                isExecuting = false;
                if (data.status === 'success') {
                    if (!data.payment) {
                        if (direction === 'up') {
                            if (data.sort_col['col_1'][0]) {
                                data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            }
                        }
                        else {
                            data.sort_col['col_1'][0]? document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]: 0;
                            data.sort_col['col_1'][1]? document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]: 0;
                            data.sort_col['col_id']? document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']: 0;
                        }
                        return;
                    }
                    if (direction === 'up') {
                        if (data.sort_col['col_1'][0]) {
                            data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        }
                    }
                    else {
                        document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                        document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']
                    }

                    const tab = document.getElementById("payment-table");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            if (page_url == 'payment-list') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'payment-approval-list') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'payment-paid-list') {
                                numRow = parseInt(tab_numRow[tab_numRow.length-1].getElementsByTagName('td')[0].innerHTML)
                            }
                        }
                        catch {
                            numRow = 0
                        }
                    }
                    else {
                        if (page_url == 'payment-list' || page_url == 'payment-approval-list' || page_url == 'payment-paid-list') {
                            numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
                    var rowCount = 0;

                    for (let pmt of data.payment) {

                        direction === 'down'? numRow++: numRow-- ;

                        let numRow1 = numRow;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        let table2 = document.getElementById("payment-table");
                        rowCount = table2.rows.length;

                        let row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;
                        let i = 0
                        //**************************************************
                        // Номер строки
                        if (page_url == 'payment-paid-list') {
                            let cellNumber = row.insertCell(0);
                            cellNumber.className = "th_nnumber_i";
                            cellNumber.setAttribute("data-sort", numRow);
                            data.setting_users.hasOwnProperty('0') ? cellNumber.hidden = true: 0;
                            cellNumber.innerHTML = numRow;
                        }

                        //**************************************************
                        // Номер платежа
                        i = 0+col_shift2
                        let cellPayNumber = row.insertCell(i);
                        cellPayNumber.className = "th_payment_number"
                        cellPayNumber.setAttribute("data-sort", pmt['payment_id']);
                        data.setting_users.hasOwnProperty(i) ? cellPayNumber.hidden = true: 0;
                        if (page_url == 'payment-approval-list') {
                            cellPayNumber.addEventListener("click", function() {getPaymentCard(pmt['payment_id']);});
                        }
                        cellPayNumber.innerHTML = pmt['payment_number'];

                        //**************************************************
                        // Статья затрат
                        i = 1+col_shift2
                        let cellCostItemName = row.insertCell(i);
                        cellCostItemName.className = "th_category_i"
                        cellCostItemName.setAttribute("data-sort", pmt['cost_item_name']);
                        data.setting_users.hasOwnProperty(i) ? cellCostItemName.hidden = true: 0;
                        cellCostItemName.innerHTML = pmt['cost_item_name'];

                        //**************************************************
                        // Наименование платежа
                        i = 2+col_shift2
                        let cellPayName = row.insertCell(i);
                        cellPayName.className = "th_name_i"
                        cellPayName.setAttribute("data-sort", pmt['basis_of_payment']);
                        cellPayName.title = `${pmt['basis_of_payment']}`;
                        data.setting_users.hasOwnProperty(i) ? cellPayName.hidden = true: 0;
                        cellPayName.innerHTML = pmt['basis_of_payment_short'];

                        //**************************************************
                        // Описание
                        i = 3+col_shift2
                        let cellDescription = row.insertCell(i);
                        cellDescription.className = "th_description_i";
                        cellDescription.setAttribute("data-sort", `${pmt['contractor_name']}: ${pmt['payment_description_short']}`);
                        cellDescription.title = `${pmt['payment_description']}`;
                        data.setting_users.hasOwnProperty(i) ? cellDescription.hidden = true: 0;
                        let spanBold = document.createElement('span');
                        spanBold.className = "paymentFormBold";
                        spanBold.innerHTML = pmt['contractor_name'] + ": ";
                        let textNode = document.createTextNode(pmt['payment_description_short']);
                        cellDescription.appendChild(spanBold);
                        cellDescription.appendChild(textNode);

                        //**************************************************
                        // Объект
                        i = 4+col_shift2
                        let cellObject = row.insertCell(i);
                        cellObject.className = "th_object_i"
                        cellObject.setAttribute("data-sort", pmt['object_name']);
                        data.setting_users.hasOwnProperty(i) ? cellObject.hidden = true: 0;
                        cellObject.innerHTML = pmt['object_name'];

                        //**************************************************
                        // Ответственный
                        i = 5+col_shift2
                        let cellResponsible = row.insertCell(i);
                        cellResponsible.className = "th_responsible_i"
                        cellResponsible.setAttribute("data-sort", `${pmt['last_name']} ${pmt['first_name']}`);
                        data.setting_users.hasOwnProperty(i) ? cellResponsible.hidden = true: 0;
                        cellResponsible.innerHTML = `${pmt['last_name']} ${pmt['first_name'][0]}`;

                        //**************************************************
                        // Контрагент
                        i = 6+col_shift2
                        let cellContractor = row.insertCell(i);
                        cellContractor.className = "th_contractor_i"
                        cellContractor.setAttribute("data-sort", pmt['partner']);
                        data.setting_users.hasOwnProperty(i) ? cellContractor.hidden = true: 0;
                        cellContractor.innerHTML = pmt['partner'];

                        //**************************************************
                        // Общая сумма
                        i = 7+col_shift2
                        let cellSumPay = row.insertCell(i);
                        cellSumPay.className = "th_main_sum_i"
                        cellSumPay.setAttribute("data-sort", pmt['payment_sum']);
                        data.setting_users.hasOwnProperty(i) ? cellSumPay.hidden = true: 0;
                        cellSumPay.innerHTML = pmt['payment_sum_rub'];

                        //**************************************************
                        // Согласованная сумма
                        if (page_url == 'payment-approval-list' || page_url == 'payment-paid-list') {
                            i = 7+col_shift+col_shift2
                            let cellSumRemain = row.insertCell(i);
                            cellSumRemain.className = "th_sum_remain_i"
                            cellSumRemain.setAttribute("data-sort", pmt['approval_sum']);
                            data.setting_users.hasOwnProperty(i) ? cellSumRemain.hidden = true: 0;
                            cellSumRemain.innerHTML = pmt['approval_sum_rub'];
                        }

                        //**************************************************
                        // Оплаченная сумма
                        i = 8+col_shift+col_shift2
                        let cellSumPaid = row.insertCell(i);
                        cellSumPaid.className = "th_sum_remain_i"
                        cellSumPaid.setAttribute("data-sort", pmt['paid_sum']);
                        data.setting_users.hasOwnProperty(i) ? cellSumPaid.hidden = true: 0;
                        cellSumPaid.innerHTML = pmt['paid_sum_rub'];

                        //**************************************************
                        // Срок оплаты
                        i = 9+col_shift+col_shift2
                        let cellDueDate = row.insertCell(i);
                        cellDueDate.className = "th_pay_date_i"
                        cellDueDate.setAttribute("data-sort", pmt['payment_due_date']);
                        data.setting_users.hasOwnProperty(i) ? cellDueDate.hidden = true: 0;
                        cellDueDate.innerHTML = pmt['payment_due_date_txt'];

                        //**************************************************
                        // Дата создания
                        i = 10+col_shift+col_shift2
                        let cellAT = row.insertCell(i);
                        cellAT.className = "th_date_create_i"
                        cellAT.setAttribute("data-sort", pmt['payment_at']);
                        data.setting_users.hasOwnProperty(i) ? cellAT.hidden = true: 0;
                        cellAT.innerHTML = pmt['payment_at_txt'];

                        //**************************************************
                        // Дата согласования
                        if (page_url === 'payment-approval-list') {
                            i = 11+col_shift+col_shift2
                            let cellSumRemain = row.insertCell(i);
                            cellSumRemain.className = "th_date_create_i"
                            cellSumRemain.setAttribute("data-sort", pmt['created_at']);
                            data.setting_users.hasOwnProperty(i) ? cellSumRemain.hidden = true: 0;
                            cellSumRemain.innerHTML = pmt['created_at_txt'];
                        }

                        //**************************************************
                        // Статус последней оплаты
                        if (page_url == 'payment-paid-list') {
                            i = 11+col_shift+col_shift2
                            let cellLastPaymentStatus = row.insertCell(i);
                            cellLastPaymentStatus.className = "th_object_i";
                            cellLastPaymentStatus.setAttribute("data-sort", pmt['status_name']);
                            data.setting_users.hasOwnProperty(i) ? cellLastPaymentStatus.hidden = true: 0;
                            cellLastPaymentStatus.innerHTML = pmt['status_name'];
                        }

                    }
                    // Прогресс бар
                    progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = `/${page_url}`;
                }
        })
        .catch(error => {
        sendErrorToServer([fetchFunc, error.toString()]);
        console.error('Error:', error);
    });
    }
};

function paymentPaidPeriod(data) {
    var payment = data.payment;
    var sortCol_1 = data.sortCol_1;
    var sortCol_1_val = data.sortCol_1_val;
    var sortCol_id_val = data.sortCol_id_val;
    var setting_users = data.setting_users;
    var tab_rows = data.tab_rows;
    var direction = data.direction;
    var description = data.description;

    document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
    document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
    document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']


    const tab = document.getElementById("payment-table");
    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    var numRow = 0

    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
    var rowCount = 0;

    if (payment) {
        for (let pmt of payment) {
            numRow++;

            let numRow1 = numRow;

            // Вставляем ниже новую ячейку, копируя предыдущую
            let table2 = document.getElementById("payment-table");
            rowCount = table2.rows.length;
            let lastRow = table2.rows[rowCount - 1];

            let row = tab_tr0.insertRow(tab_numRow.length);

            //////////////////////////////////////////
            // Меняем данные в ячейке
            //////////////////////////////////////////
            // id
            row.id = `row-${numRow}`;
            let i = 0
            //**************************************************
            // Номер строки
            let cellNumber = row.insertCell(0);
            cellNumber.className = "th_nnumber_i";
            cellNumber.setAttribute("data-sort", numRow);
            data.setting_users.hasOwnProperty('0') ? cellNumber.hidden = true: 0;
            cellNumber.innerHTML = numRow;

            //**************************************************
            // Номер платежа
            let cellPayNumber = row.insertCell(1);
            cellPayNumber.className = "th_payment_number"
            cellPayNumber.setAttribute("data-sort", pmt['payment_id']);
            data.setting_users.hasOwnProperty('1') ? cellPayNumber.hidden = true: 0;
            cellPayNumber.innerHTML = pmt['payment_number'];

            //**************************************************
            // Статья затрат
            let cellCostItemName = row.insertCell(2);
            cellCostItemName.className = "th_category_i"
            cellCostItemName.setAttribute("data-sort", pmt['cost_item_name']);
            data.setting_users.hasOwnProperty('2') ? cellCostItemName.hidden = true: 0;
            cellCostItemName.innerHTML = pmt['cost_item_name'];

            //**************************************************
            // Наименование платежа
            let cellPayName = row.insertCell(3);
            cellPayName.className = "th_name_i"
            cellPayName.setAttribute("data-sort", pmt['basis_of_payment']);
            cellPayName.title = `${pmt['basis_of_payment']}`;
            data.setting_users.hasOwnProperty('3') ? cellPayName.hidden = true: 0;
            cellPayName.innerHTML = pmt['basis_of_payment_short'];

            //**************************************************
            // Описание
            let cellDescription = row.insertCell(4);
            cellDescription.className = "th_description_i";
            cellDescription.setAttribute("data-sort", `${pmt['contractor_name']}: ${pmt['payment_description_short']}`);
            cellDescription.title = `${pmt['payment_description']}`;
            data.setting_users.hasOwnProperty('4') ? cellDescription.hidden = true: 0;
            let spanBold = document.createElement('span');
            spanBold.className = "paymentFormBold";
            spanBold.innerHTML = pmt['contractor_name'] + ": ";
            let textNode = document.createTextNode(pmt['payment_description_short']);
            cellDescription.appendChild(spanBold);
            cellDescription.appendChild(textNode);

            //**************************************************
            // Объект
            let cellObject = row.insertCell(5);
            cellObject.className = "th_object_i"
            cellObject.setAttribute("data-sort", pmt['object_name']);
            data.setting_users.hasOwnProperty('5') ? cellObject.hidden = true: 0;
            cellObject.innerHTML = pmt['object_name'];

            //**************************************************
            // Ответственный
            let cellResponsible = row.insertCell(6);
            cellResponsible.className = "th_responsible_i"
            cellResponsible.setAttribute("data-sort", `${pmt['last_name']} ${pmt['first_name']}`);
            data.setting_users.hasOwnProperty('6') ? cellResponsible.hidden = true: 0;
            cellResponsible.innerHTML = `${pmt['last_name']} ${pmt['first_name'][0]}`;

            //**************************************************
            // Контрагент
            let cellContractor = row.insertCell(7);
            cellContractor.className = "th_contractor_i"
            cellContractor.setAttribute("data-sort", pmt['partner']);
            data.setting_users.hasOwnProperty('7') ? cellContractor.hidden = true: 0;
            cellContractor.innerHTML = pmt['partner'];

            //**************************************************
            // Общая сумма
            let cellSumPay = row.insertCell(8);
            cellSumPay.className = "th_main_sum_i"
            cellSumPay.setAttribute("data-sort", pmt['payment_sum']);
            data.setting_users.hasOwnProperty('8') ? cellSumPay.hidden = true: 0;
            cellSumPay.innerHTML = pmt['payment_sum_rub'];

            //**************************************************
            // Оплаченная сумма
            let cellSumPaid = row.insertCell(9);
            cellSumPaid.className = "th_sum_remain_i"
            cellSumPaid.setAttribute("data-sort", pmt['paid_sum']);
            data.setting_users.hasOwnProperty('9') ? cellSumPaid.hidden = true: 0;
            cellSumPaid.innerHTML = pmt['paid_sum_rub'];

            //**************************************************
            // Срок оплаты
            let cellDueDate = row.insertCell(10);
            cellDueDate.className = "th_pay_date_i"
            cellDueDate.setAttribute("data-sort", pmt['payment_due_date']);
            data.setting_users.hasOwnProperty('10') ? cellDueDate.hidden = true: 0;
            cellDueDate.innerHTML = pmt['payment_due_date_txt'];

            //**************************************************
            // Дата создания
            let cellAT = row.insertCell(11);
            cellAT.className = "th_date_create_i"
            cellAT.setAttribute("data-sort", pmt['payment_at']);
            data.setting_users.hasOwnProperty('11') ? cellAT.hidden = true: 0;
            cellAT.innerHTML = pmt['payment_at_txt'];

            //**************************************************
            // Дата оплаты
            let paidAT = row.insertCell(12);
            paidAT.className = "th_date_create_i"
            paidAT.setAttribute("data-sort", pmt['paid_at']);
            data.setting_users.hasOwnProperty('12') ? paidAT.hidden = true: 0;
            paidAT.innerHTML = pmt['paid_at_txt'];

            //**************************************************
            // Статус последней оплаты
            let cellLastPaymentStatus = row.insertCell(13);
            cellLastPaymentStatus.className = "th_object_i";
            cellLastPaymentStatus.setAttribute("data-sort", pmt['status_name']);
            data.setting_users.hasOwnProperty('13') ? cellLastPaymentStatus.hidden = true: 0;
            cellLastPaymentStatus.innerHTML = pmt['status_name'];

        }
        // Общая сумма и кол-во платежей
        document.getElementById("card_summary_paid_value").innerText = payment[0]['card_summary_paid_value'];
        document.getElementById("card__cost_id_cnt").innerText = 'Кол-во платежей: ' + tab_rows;
    }
    else {
        tab_rows = 0;
        // Общая сумма и кол-во платежей
        document.getElementById("card_summary_paid_value").innerText = '-';
        document.getElementById("card__cost_id_cnt").innerText = 'Кол-во платежей: -';

        var row = tab_tr0.insertRow(0);
        var emptyTable = row.insertCell(0);
        emptyTable.className = "empty_table";
        emptyTable.innerHTML = 'Данные не найдены';
        emptyTable.style.textAlign = "center";
        emptyTable.style.fontStyle = "italic";

        emptyTable.colSpan = tab.getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th').length;

    }
    // Прогресс бар
    const progressBar = document.querySelector('.progress');
    const progressBar2 = document.querySelector('.progress2');
    progressBar.style.width = '100%';
    progressBar2.style.width = '0%';

    return createDialogWindow(status='success', description=description);


}

function paymentInflowHistory(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return
    }
    isExecuting = true;

    [sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList] = prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val)

    // Получили пустые данные - загрузили всю таблицу - ничего не делаем
    if (!sortCol_1) {
        isExecuting = false;
        return;
    }
    else {
        fetch('/get-inflowHistory-pagination', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'limit': limit,
                'sort_col_1': sortCol_1,
                'sort_col_1_val': sortCol_1_val,
                'sort_col_id_val': sortCol_id_val,
                'filterValsList': filterValsList
            })
        })
            .then(response => response.json())
            .then(data => {
                isExecuting = false;
                if (data.status === 'success') {
                    if (!data.payment) {
                        if (direction === 'up') {
                            if (data.sort_col['col_1'][0]) {
                                data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            }
                        }
                        else {
                            data.sort_col['col_1'][0]? document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]: 0;
                            data.sort_col['col_1'][1]? document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]: 0;
                            data.sort_col['col_id']? document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']: 0;
                        }
                        return;
                    }
                    if (direction === 'up') {
                        if (data.sort_col['col_1'][0]) {
                            data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        }
                    }
                    else {
                        document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                        document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']
                    }

                    const tab = document.getElementById("payment-table");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    let numRow;
                    if (direction === 'down') {
                        try {
                            numRow = tab_numRow[tab_numRow.length-1].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                        catch {
                            numRow = 0
                        }
                    }
                    else {
                        numRow = tab_numRow[0].id;
                        numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
                    var rowCount = 0;

                    for (let pmt of data.payment) {
                        direction === 'down'? numRow++: numRow-- ;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        let table2 = document.getElementById("payment-table");
                        rowCount = table2.rows.length;

                        let row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // id
                        let cellNumber = row.insertCell(0);
                        cellNumber.className = "th_nnumber_i";
                        cellNumber.setAttribute("data-sort", numRow);
                        data.setting_users.hasOwnProperty('0') ? cellNumber.hidden = true: 0;
                        cellNumber.innerHTML = pmt['inflow_id'];

                        //**************************************************
                        // Компания
                        let cellContractor = row.insertCell(1);
                        cellContractor.className = "th_contractor_i"
                        cellContractor.setAttribute("data-sort", pmt['contractor_name']);
                        data.setting_users.hasOwnProperty('1') ? cellPayNumber.hidden = true: 0;
                        cellContractor.innerHTML = pmt['contractor_name'];

                        //**************************************************
                        // Описание
                        let cellDescription = row.insertCell(2);
                        cellDescription.className = "th_description_i"
                        cellDescription.setAttribute("data-sort", pmt['inflow_description']);
                        data.setting_users.hasOwnProperty('2') ? cellCostItemName.hidden = true: 0;
                        cellDescription.innerHTML = pmt['inflow_description'];

                        //**************************************************
                        // Тип поступления
                        let cellInflowType = row.insertCell(3);
                        cellInflowType.className = "th_category_i"
                        cellInflowType.setAttribute("data-sort", pmt['inflow_type_name']);
                        data.setting_users.hasOwnProperty('3') ? cellPayName.hidden = true: 0;
                        cellInflowType.innerHTML = pmt['inflow_type_name'];

                        //**************************************************
                        // Сумма
                        let cellSumPay = row.insertCell(4);
                        cellSumPay.className = "th_main_sum_i";
                        cellSumPay.setAttribute("data-sort", pmt['inflow_sum']);
                        data.setting_users.hasOwnProperty('4') ? cellDescription.hidden = true: 0;
                        cellSumPay.innerHTML = pmt['inflow_sum_rub'];

                        //**************************************************
                        // Дата создания
                        let cellDateCreate = row.insertCell(5);
                        cellDateCreate.className = "th_date_create_i"
                        cellDateCreate.setAttribute("data-sort", pmt['inflow_at']);
                        data.setting_users.hasOwnProperty('5') ? cellObject.hidden = true: 0;
                        cellDateCreate.innerHTML = pmt['inflow_at_txt'];
                    }

                    // Прогресс бар
                    progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/';
                }
        })
        .catch(error => {
        sendErrorToServer(['get-inflowHistory-pagination', error.toString()]);
        console.error('Error:', error);
    });
    }
}
