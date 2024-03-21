$(document).ready(function() {

    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    const tableR = document.querySelector('.tableEmp');

    var tableR2 = document.getElementById('employeeTable');

    var table_max_length = 175

    if(tableR) {
        if ($(this).innerHeight() > tableR2.offsetHeight) {
            var sortCol_1 = document.getElementById('sortCol-1').textContent;
            if (page_url === 'contracts-main') {
                var isExecuting = false;
                contractMain(sortCol_1);
            }
            else if (page_url === 'contracts-objects') {
                var isExecuting = false;
                //contractObj(sortCol_1);
            }
            else if (page_url === 'contracts-list' || page_url === 'contracts-acts-list' || page_url === 'contracts-payments-list') {
                var isExecuting = false;
                //contractList(sortCol_1);
            }
        }
    }

    tableR.addEventListener('scroll', function() {
        var sortCol_1 = document.getElementById('sortCol-1').textContent;
        var scrollPosition = $(this).scrollTop()

        // Скроллим вверх
        if (!scrollPosition && sortCol_1) {
            var tab = document.getElementById("employeeTable");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            if (tab_numRow.length >= table_max_length) {
                for (var i = tab_numRow.length; i>table_max_length; i--) {
                    table.deleteRow(i);
                }

                if (page_url === 'contracts-main') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[1].getElementsByTagName('input')[0].value;
                    var payment_due_date = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var isExecuting = false;
                    contractMain(sortCol_1=sortCol_1, direction='up', sortCol_1_val=payment_due_date, sortCol_id_val=payment_id);
                }
                else if (page_url === 'contracts-objects') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[2].dataset.sort;
                    var payment_due_date = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    //contractObj(sortCol_1=sortCol_1, direction='up', sortCol_1_val=payment_due_date, sortCol_id_val=payment_id);
                }
                else if (page_url === 'contracts-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var create_at = tab_numRow[0].getElementsByTagName('td')[10].dataset.sort;
                    var isExecuting = false;
                    //contractList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=create_at, sortCol_id_val=payment_id);
                }
                else if (page_url === 'contracts-acts-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var create_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    //contractList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=create_at, sortCol_id_val=payment_id);
                }
                else if (page_url === 'contracts-payments-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var create_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    //contractList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=create_at, sortCol_id_val=payment_id)
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

            const tab = document.getElementById("employeeTable");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            if (page_url === 'contracts-main') {
                var isExecuting = false;
                contractMain(sortCol_1);
            }
            else if (page_url === 'contracts-objects') {
                var isExecuting = false;
                contractObj(sortCol_1);
            }
            else if (page_url === 'contracts-list' || page_url === 'contracts-acts-list' || page_url === 'contracts-payments-list') {
                var isExecuting = false;
                contractList(sortCol_1);
            }
            if(tableR) {
                //  возвращает координаты в контексте окна для минимального по размеру прямоугольника tableR
                const rect = tableR.getBoundingClientRect();
            }
            if (tab_numRow.length > table_max_length) {
                for (var i = 1; i<=tab_numRow.length-table_max_length;) {
                    table.deleteRow(1);
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

function contractMain(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
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

        fetch('/get-contractMain-pagination', {
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
                    
                    if (!data.contract) {
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

                    const tab = document.getElementById("employeeTable");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            var numRow = tab_numRow[tab_numRow.length-1].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                            }
                        catch {
                            numRow = 0;
                        }
                    }
                    else {
                        var numRow = tab_numRow[0].id;
                        numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];

                    for (ctr of data.contract) {

                        direction === 'down'? numRow++: numRow-- ;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        var table2 = document.getElementById("employeeTable");
                        var rowCount = table2.rows.length;

                        var row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // ID ОБЪЕКТА
                        var objID = row.insertCell(0);
                        objID.className = "th_description_i";
                        objID.innerHTML = ctr['object_id'];

                        //**************************************************
                        // НАЗВАНИЕ ОБЪЕКТА
                        var objName = row.insertCell(1);
                        objName.className = "th_description_i";
                        objName.innerHTML = ctr['object_name'];

                        // Прогресс бар
                        console.log(direction, numRow, data.tab_rows, rowCount)
                        progressBarCalc(direction, numRow, data.tab_rows, rowCount);

                    }
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/contracts-main';
                }
        })
        .catch(error => {
        console.error('Error:', error);
    });
    }
};

function contractObj(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
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

        fetch('/get-contractObj-pagination', {
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
                    if (!data.contract) {
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

                    const tab = document.getElementById("employeeTable");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            var numRow = parseInt(tab_numRow[tab_numRow.length-1].getElementsByTagName('td')[0].getElementsByTagName('input')[0].value)
                        }
                        catch {
                            var numRow = 0
                        }
                    }
                    else {
                            var numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];

                    for (ctr of data.contract) {

                        direction === 'down'? numRow++: numRow-- ;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        var table2 = document.getElementById("employeeTable");
                        var rowCount = table2.rows.length;
                        var lastRow = table2.rows[rowCount - 1];

                        var row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // Флажок выбора
                        var cellCheckbox = row.insertCell(0);
                        cellCheckbox.className = "th_select_i";
                        cellCheckbox.setAttribute("data-sort", "0");
                        data.setting_users.hasOwnProperty('0') ? cellCheckbox.hidden = true: 0;
                        var checkbox = document.createElement('input');
                        checkbox.type = "checkbox";
                        checkbox.id = `selectedRows-${numRow}`;
                        checkbox.name = "selectedRows";
                        checkbox.value = numRow;
                        checkbox.setAttribute("onchange", `contractMainRecalcCards(${numRow}), contractMainNoSelect(${numRow}), refreshSortValChb(${numRow})`)
                        cellCheckbox.appendChild(checkbox);

                        //**************************************************
                        // Статья затрат
                        var cellCostItemName = row.insertCell(1);
                        cellCostItemName.className = "th_category_i";
                        cellCostItemName.id = `category-${numRow}`;
                        cellCostItemName.setAttribute("data-sort", ctr['cost_item_name']);
                        cellCostItemName.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('1') ? cellCostItemName.hidden = true: 0;
                        cellCostItemName.innerHTML = ctr['cost_item_name'];
                        var input = document.createElement('input');
                        input.id = `paymentNumber-${numRow}`;
                        input.name = 'payment_number';
                        input.value = ctr['payment_id'];
                        input.hidden = true;
                        input.readOnly = true;
                        cellCostItemName.appendChild(input);

                        //**************************************************
                        // Номер платежа
                        var cellPayNumber = row.insertCell(2);
                        cellPayNumber.className = "th_payment_number_i"
                        cellPayNumber.setAttribute("data-sort", ctr['payment_id']);
                        cellPayNumber.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('2') ? cellPayNumber.hidden = true: 0;
                        cellPayNumber.innerHTML = ctr['payment_number'];

                        //**************************************************
                        // Наименование платежа
                        var cellPayName = row.insertCell(3);
                        cellPayName.className = "th_name_i"
                        cellPayName.setAttribute("data-sort", ctr['basis_of_payment']);
                        cellPayName.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        cellPayName.title = `${ctr['basis_of_payment']}`;
                        data.setting_users.hasOwnProperty('3') ? cellPayName.hidden = true: 0;
                        cellPayName.innerHTML = ctr['basis_of_payment'];

                        //**************************************************
                        // Описание
                        var cellPayName = row.insertCell(4);
                        cellPayName.className = "th_description_i";
                        cellPayName.setAttribute("data-sort", `${ctr['contractor_name']}: ${ctr['payment_description']}`);
                        cellPayName.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        cellPayName.title = `${ctr['payment_description']}`;
                        data.setting_users.hasOwnProperty('4') ? cellPayName.hidden = true: 0;
                        var spanBold = document.createElement('span');
                        spanBold.className = "paymentFormBold";
                        spanBold.innerHTML = ctr['contractor_name'] + ": ";
                        var textNode = document.createTextNode(ctr['payment_description']);
                        var input = document.createElement('input');
                        input.name = 'contractor_id';
                        input.value = ctr['contractor_id'];
                        input.hidden = true;
                        input.readOnly = true;
                        cellPayName.appendChild(input);

                        cellPayName.appendChild(spanBold);
                        cellPayName.appendChild(textNode);

                        //**************************************************
                        // Объект
                        var cellObject = row.insertCell(5);
                        cellObject.className = "th_object_i"
                        cellObject.setAttribute("data-sort", ctr['object_name']);
                        cellObject.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('5') ? cellObject.hidden = true: 0;
                        cellObject.innerHTML = ctr['object_name'];

                        //**************************************************
                        // Ответственный
                        var cellResponsible = row.insertCell(6);
                        cellResponsible.className = "th_responsible_i"
                        cellResponsible.setAttribute("data-sort", `${ctr['last_name']} ${ctr['first_name']}`);
                        cellResponsible.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('6') ? cellResponsible.hidden = true: 0;
                        cellResponsible.innerHTML = `${ctr['last_name']} ${ctr['first_name'][0]}`;

                        //**************************************************
                        // Контрагент
                        var cellContractor = row.insertCell(7);
                        cellContractor.className = "th_contractor_i"
                        cellContractor.setAttribute("data-sort", ctr['partner']);
                        cellContractor.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('7') ? cellContractor.hidden = true: 0;
                        cellContractor.innerHTML = ctr['partner'];

                        //**************************************************
                        // Общая сумма
                        var cellSumPay = row.insertCell(8);
                        cellSumPay.className = "th_main_sum_i"
                        cellSumPay.setAttribute("data-sort", ctr['payment_sum']);
                        cellSumPay.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('8') ? cellSumPay.hidden = true: 0;
                        cellSumPay.innerHTML = ctr['payment_sum_rub'];

                        //**************************************************
                        // Оплаченная сумма
                        var cellSumPaid = row.insertCell(9);
                        cellSumPaid.className = "th_paid_sum_i"
                        cellSumPaid.setAttribute("data-sort", ctr['paid_sum']);
                        cellSumPaid.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('9') ? cellSumPaid.hidden = true: 0;
                        cellSumPaid.innerHTML = ctr['paid_sum_rub'];

                        //**************************************************
                        // Согласованная сумма
                        var cellSumAgreed = row.insertCell(10);
                        cellSumAgreed.className = "th_sum_remain_i";
                        cellSumAgreed.setAttribute("data-sort", ctr['approval_sum']);
                        cellSumAgreed.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('10') ? cellSumAgreed.hidden = true: 0;
                        var input = document.createElement('input');
                        input.id = `approvalSum-${numRow}`;
                        input.name = 'approval_sum';
                        input.value = ctr['approval_sum'];
                        input.hidden = true;
                        input.readOnly = true;
                        cellSumAgreed.innerHTML = ctr['approval_sum_rub'];
                        cellSumAgreed.appendChild(input);

                        //**************************************************
                        // Сумма к оплате
                        var cellSumCurrent = row.insertCell(11);
                        cellSumCurrent.className = "th_sum_agreed";
                        cellSumCurrent.setAttribute("data-sort", ctr['amount']);
                        data.setting_users.hasOwnProperty('11') ? cellSumCurrent.hidden = true: 0;
                        var inputAmount = document.createElement('input');
                        inputAmount.id = `amount-${numRow}`;
                        inputAmount.name = "amount";
                        inputAmount.value = ctr['amount_rub'];
                        inputAmount.setAttribute("onchange", `contractMainRecalcCards(${numRow}), saveData(${numRow}, '${data.page}')`)
                        cellSumCurrent.appendChild(inputAmount);

                        //**************************************************
                        // Срок оплаты
                        var cellPayDate = row.insertCell(12);
                        cellPayDate.className = "th_date_create_i";
                        cellPayDate.setAttribute("data-sort", ctr['payment_due_date']);
                        cellPayDate.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        data.setting_users.hasOwnProperty('12') ? cellPayDate.hidden = true: 0;
                        cellPayDate.innerHTML = ctr['payment_due_date_txt'];

                        //**************************************************
                        // Дата создания
                        var cellDateCreate = row.insertCell(13);
                        cellDateCreate.className = "th_date_create_i";
                        cellDateCreate.setAttribute("data-sort", ctr['payment_at']);
                        data.setting_users.hasOwnProperty('13') ? cellDateCreate.hidden = true: 0;
                        cellDateCreate.innerHTML = ctr['payment_at_txt'];

                        //**************************************************
                        // До полной оплаты
                        var cellSavePay = row.insertCell(14);
                        cellSavePay.className = "th_save_pay_i";
                        cellSavePay.setAttribute("data-sort", ctr['payment_full_agreed_status'] ? "1" : "0");
                        data.setting_users.hasOwnProperty('14') ? cellSavePay.hidden = true: 0;
                        var checkboxPaymentFullStatus = document.createElement('input');
                        checkboxPaymentFullStatus.type = "checkbox";
                        checkboxPaymentFullStatus.id = `paymentFullStatus-${numRow}`;
                        checkboxPaymentFullStatus.name = "payment_full_agreed_status";
                        checkboxPaymentFullStatus.value = numRow;
                        if (ctr['payment_full_agreed_status']) {
                            checkboxPaymentFullStatus.checked = true;
                        }
                        checkboxPaymentFullStatus.setAttribute("onchange", `saveData(${numRow}, '${data.page}'), tabColorize(${numRow}), refreshSortValChb(${numRow})`);
                        cellSavePay.appendChild(checkboxPaymentFullStatus);

                        // Прогресс бар
                        progressBarCalc(direction, numRow, data.tab_rows, rowCount);

                    }
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/contracts-objects';
                }
        })
        .catch(error => {
        console.error('Error:', error);
    });
    }
}

function contractList(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
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

    if (page_url == 'contracts-list') {
        fetchFunc = '/get-contractList-pagination';
    }
    else if (page_url == 'contracts-acts-list') {
        fetchFunc = '/get-contractMainList-pagination';
        col_shift = 1;
    }
    else if (page_url == 'contracts-payments-list') {
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
                    if (!data.contract) {
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

                    const tab = document.getElementById("employeeTable");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            if (page_url == 'contracts-list') {
                                var numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contracts-acts-list') {
                                var numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contracts-payments-list') {
                                var numRow = parseInt(tab_numRow[tab_numRow.length-1].getElementsByTagName('td')[0].innerHTML)
                            }
                        }
                        catch {
                            var numRow = 0
                        }
                    }
                    else {
                        if (page_url == 'contracts-list' || page_url == 'contracts-acts-list' || page_url == 'contracts-payments-list') {
                            var numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0]

                    for (ctr of data.contract) {

                        direction === 'down'? numRow++: numRow-- ;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        var table2 = document.getElementById("employeeTable");
                        var rowCount = table2.rows.length;

                        var row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;

                        //**************************************************
                        // Номер строки
                        if (page_url == 'contracts-payments-list') {
                            var cellNumber = row.insertCell(0);
                            cellNumber.className = "th_nnumber_i";
                            cellNumber.setAttribute("data-sort", numRow);
                            data.setting_users.hasOwnProperty('0') ? cellNumber.hidden = true: 0;
                            cellNumber.innerHTML = numRow;
                        }

                        //**************************************************
                        // Номер платежа
                        var i = 0+col_shift2
                        var cellPayNumber = row.insertCell(i);
                        cellPayNumber.className = "th_payment_number"
                        cellPayNumber.setAttribute("data-sort", ctr['payment_id']);
                        data.setting_users.hasOwnProperty(i) ? cellPayNumber.hidden = true: 0;
                        if (page_url == 'contracts-acts-list') {
                            cellPayNumber.setAttribute("onclick", `getPaymentCard(${ctr['payment_id']})`);
                        }
                        cellPayNumber.innerHTML = ctr['payment_number'];

                        //**************************************************
                        // Статья затрат
                        var i = 1+col_shift2
                        var cellCostItemName = row.insertCell(i);
                        cellCostItemName.className = "th_category_i"
                        cellCostItemName.setAttribute("data-sort", ctr['cost_item_name']);
                        data.setting_users.hasOwnProperty(i) ? cellCostItemName.hidden = true: 0;
                        cellCostItemName.innerHTML = ctr['cost_item_name'];

                        //**************************************************
                        // Наименование платежа
                        var i = 2+col_shift2
                        var cellCostItemName = row.insertCell(i);
                        cellCostItemName.className = "th_name_i"
                        cellCostItemName.setAttribute("data-sort", ctr['basis_of_payment']);
                        cellCostItemName.title = `${ctr['basis_of_payment']}`;
                        data.setting_users.hasOwnProperty(i) ? cellCostItemName.hidden = true: 0;
                        cellCostItemName.innerHTML = ctr['basis_of_payment_short'];

                        //**************************************************
                        // Описание
                        var i = 3+col_shift2
                        var cellPayName = row.insertCell(i);
                        cellPayName.className = "th_description_i";
                        cellPayName.setAttribute("data-sort", `${ctr['contractor_name']}: ${ctr['payment_description_short']}`);
                        cellPayName.title = `${ctr['payment_description']}`;
                        data.setting_users.hasOwnProperty(i) ? cellPayName.hidden = true: 0;
                        var spanBold = document.createElement('span');
                        spanBold.className = "paymentFormBold";
                        spanBold.innerHTML = ctr['contractor_name'] + ": ";
                        var textNode = document.createTextNode(ctr['payment_description_short']);
                        cellPayName.appendChild(spanBold);
                        cellPayName.appendChild(textNode);

                        //**************************************************
                        // Объект
                        var i = 4+col_shift2
                        var cellObject = row.insertCell(i);
                        cellObject.className = "th_object_i"
                        cellObject.setAttribute("data-sort", ctr['object_name']);
                        data.setting_users.hasOwnProperty(i) ? cellObject.hidden = true: 0;
                        cellObject.innerHTML = ctr['object_name'];

                        //**************************************************
                        // Ответственный
                        var i = 5+col_shift2
                        var cellResponsible = row.insertCell(i);
                        cellResponsible.className = "th_responsible_i"
                        cellResponsible.setAttribute("data-sort", `${ctr['last_name']} ${ctr['first_name']}`);
                        data.setting_users.hasOwnProperty(i) ? cellResponsible.hidden = true: 0;
                        cellResponsible.innerHTML = `${ctr['last_name']} ${ctr['first_name'][0]}`;

                        //**************************************************
                        // Контрагент
                        var i = 6+col_shift2
                        var cellContractor = row.insertCell(i);
                        cellContractor.className = "th_contractor_i"
                        cellContractor.setAttribute("data-sort", ctr['partner']);
                        data.setting_users.hasOwnProperty(i) ? cellContractor.hidden = true: 0;
                        cellContractor.innerHTML = ctr['partner'];

                        //**************************************************
                        // Общая сумма
                        var i = 7+col_shift2
                        var cellSumPay = row.insertCell(i);
                        cellSumPay.className = "th_main_sum_i"
                        cellSumPay.setAttribute("data-sort", ctr['payment_sum']);
                        data.setting_users.hasOwnProperty(i) ? cellSumPay.hidden = true: 0;
                        cellSumPay.innerHTML = ctr['payment_sum_rub'];

                        //**************************************************
                        // Согласованная сумма
                        if (page_url == 'contracts-acts-list' || page_url == 'contracts-payments-list') {
                            var i = 7+col_shift+col_shift2
                            var cellSumRemain = row.insertCell(i);
                            cellSumRemain.className = "th_sum_remain_i"
                            cellSumRemain.setAttribute("data-sort", ctr['approval_sum']);
                            data.setting_users.hasOwnProperty(i) ? cellSumRemain.hidden = true: 0;
                            cellSumRemain.innerHTML = ctr['approval_sum_rub'];
                        }

                        //**************************************************
                        // Оплаченная сумма
                        var i = 8+col_shift+col_shift2
                        var cellSumPaid = row.insertCell(i);
                        cellSumPaid.className = "th_sum_remain_i"
                        cellSumPaid.setAttribute("data-sort", ctr['paid_sum']);
                        data.setting_users.hasOwnProperty(i) ? cellSumPaid.hidden = true: 0;
                        cellSumPaid.innerHTML = ctr['paid_sum_rub'];

                        //**************************************************
                        // Срок оплаты
                        var i = 9+col_shift+col_shift2
                        var cellDueDate = row.insertCell(i);
                        cellDueDate.className = "th_pay_date_i"
                        cellDueDate.setAttribute("data-sort", ctr['payment_due_date']);
                        data.setting_users.hasOwnProperty(i) ? cellDueDate.hidden = true: 0;
                        cellDueDate.innerHTML = ctr['payment_due_date_txt'];

                        //**************************************************
                        // Дата создания
                        var i = 10+col_shift+col_shift2
                        var cellAT = row.insertCell(i);
                        cellAT.className = "th_date_create_i"
                        cellAT.setAttribute("data-sort", ctr['payment_at']);
                        data.setting_users.hasOwnProperty(i) ? cellAT.hidden = true: 0;
                        cellAT.innerHTML = ctr['payment_at_txt'];

                        //**************************************************
                        // Дата согласования
                        if (page_url === 'contracts-acts-list') {
                            var i = 11+col_shift+col_shift2
                            var cellSumRemain = row.insertCell(i);
                            cellSumRemain.className = "th_date_create_i"
                            cellSumRemain.setAttribute("data-sort", ctr['create_at']);
                            data.setting_users.hasOwnProperty(i) ? cellSumRemain.hidden = true: 0;
                            cellSumRemain.innerHTML = ctr['create_at_txt'];
                        }

                        //**************************************************
                        // Статус последней оплаты
                        if (page_url == 'contracts-payments-list') {
                            var i = 11+col_shift+col_shift2
                            var cellLastPaymentStatus = row.insertCell(i);
                            cellLastPaymentStatus.className = "th_object_i";
                            cellLastPaymentStatus.setAttribute("data-sort", ctr['status_name']);
                            data.setting_users.hasOwnProperty(i) ? cellLastPaymentStatus.hidden = true: 0;
                            cellLastPaymentStatus.innerHTML = ctr['status_name'];
                        }

                        // Прогресс бар
                        progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                    }
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
        console.error('Error:', error);
    });
    }
};
