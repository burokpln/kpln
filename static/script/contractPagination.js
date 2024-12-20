$(document).ready(function() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    const tableR = document.querySelector('.tableEmp');

    var tableR2 = document.getElementById('employeeTable');

    var table_max_length = 175

    if(tableR) {
        if ($(this).innerHeight() > tableR2.offsetHeight) {
            var sortCol_1 = document.getElementById('sortCol-1').textContent;
            if (['contract-main', 'contract-objects', 'contract-list', 'contract-acts-list', 'contract-payments-list'].includes(page_url)) {
                var isExecuting = false;
                contractPagination(sortCol_1);
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
                for (tab_numRow.length; i>table_max_length; i--) {
                    tableR2.deleteRow(i);
                }

                if (page_url === 'contract-main') {
                    var object_id = tab_numRow[0].getElementsByTagName('td')[0].innerHTML;
                    var object_name = tab_numRow[0].getElementsByTagName('td')[1].innerHTML;
                    var isExecuting = false;
                    contractPagination(sortCol_1=sortCol_1, direction='up', sortCol_1_val=object_name, sortCol_id_val=object_id);
                }
                else if (page_url === 'contract-objects') {
                    var object_id = tab_numRow[0].getElementsByTagName('td')[0].innerHTML;
                    var object_name = tab_numRow[0].getElementsByTagName('td')[1].innerHTML;
                    var isExecuting = false;
                    contractPagination(sortCol_1=sortCol_1, direction='up', sortCol_1_val=object_name, sortCol_id_val=object_id);
                }
                else if (page_url === 'contract-list') {
                    var contract_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[11].dataset.sort;
                    var isExecuting = false;
                    contractPagination(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=contract_id);
                }
                else if (page_url === 'contract-acts-list') {
                    var act_id = tab_numRow[0].getElementsByTagName('td')[0].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    contractPagination(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=act_id);
                }
                else if (page_url === 'contract-payments-list') {
                    var payment_id = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var created_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    contractPagination(sortCol_1=sortCol_1, direction='up', sortCol_1_val=created_at, sortCol_id_val=payment_id)
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

            if (page_url === 'contract-main') {
                var isExecuting = false;
                contractPagination(sortCol_1);
            }
            else if (page_url === 'contract-objects') {
                var isExecuting = false;
                contractPagination(sortCol_1);
            }
            else if (page_url === 'contract-list' || page_url === 'contract-acts-list' || page_url === 'contract-payments-list') {
                var isExecuting = false;
                contractPagination(sortCol_1);
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

function contractPagination(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
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

    // Если зашли из проекта, то в ссылке находим название проекта
    var obj_name = document.URL.lastIndexOf('/objects')>0? decodeURIComponent(document.URL.substring(document.URL.lastIndexOf('/objects')+9, document.URL.lastIndexOf('/'))):'';

    if (page_url == 'contract-main') {
        fetchFunc = '/get-contractMain-pagination';
    }
    else if (page_url == 'contract-objects') {
        fetchFunc = '/get-contractObj-pagination';
    }
    else if (page_url == 'contract-list') {
        fetchFunc = '/get-contractList-pagination';
    }
    else if (page_url == 'contract-acts-list') {
        fetchFunc = '/get-actList-pagination';
        col_shift = 1;
    }
    else if (page_url == 'contract-payments-list') {
        fetchFunc = '/get-contractPayList-pagination';
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
                'link': obj_name,
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
                    let numRow;
                    if (direction === 'down') {
                        try {
                            if (page_url == 'contract-main') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contract-objects') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contract-list') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contract-acts-list') {
                                numRow = tab_numRow[tab_numRow.length-1].id;
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                            else if (page_url == 'contract-payments-list') {
                                numRow = parseInt(numRow.split('row-')[1]);
                            }
                        }
                        catch {
                            numRow = 0
                        }
                    }
                    else {
                        if (page_url == 'contract-main') {
                            numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                        else if (page_url == 'contract-objects') {
                            numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                        else if (page_url == 'contract-list' || page_url == 'contract-acts-list' || page_url == 'contract-payments-list') {
                            numRow = tab_numRow[0].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0]
                    
                    for (let ctr of data.contract) {
                        direction === 'down'? numRow++: numRow-- ;
                        let numRow1 = numRow;

                        let objID = null;
                        let objName = null;
                        let i = null;
                        let cellCheckbox = null;
                        let checkbox = null;
                        let cellObject = null;
                        let cellType = null;
                        let cellContactNumber = null;
                        let cellDateStart = null;
                        let cellDateFinish = null;
                        let cellSubContactNumber = null;
                        let cellSubDateStart = null;
                        let cellSubDateFinish = null;
                        let cellContractor = null;
                        let cellPartner = null;
                        let cellDescription = null;
                        let cellStatus = null;
                        let cellAllow = null;
                        let cellVAT = null;
                        let cellCost = null;
                        let cellCreateAt = null;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        let table2 = document.getElementById("employeeTable");
                        let rowCount = table2.rows.length;

                        let row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;
                        if (page_url == 'contract-main') {
                            //**************************************************
                            // ID ОБЪЕКТА
                            objID = row.insertCell(0);
                            objID.className = "th_description_i";
                            objID.innerHTML = ctr['object_id'];

                            //**************************************************
                            // НАЗВАНИЕ ОБЪЕКТА
                            objName = row.insertCell(1);
                            objName.className = "th_description_i";
                            objName.innerHTML = ctr['object_name'];
                        }
                        else if (page_url == 'contract-objects') {
                            //**************************************************
                            // ID ОБЪЕКТА
                            objID = row.insertCell(0);
                            objID.className = "th_description_i";
                            objID.innerHTML = ctr['object_id'];

                            //**************************************************
                            // НАЗВАНИЕ ОБЪЕКТА
                            objName = row.insertCell(1);
                            objName.className = "th_description_i";
                            objName.innerHTML = ctr['object_name'];
                        }
                        else if (page_url == 'contract-list') {
                            //**************************************************
                            // Флажок выбора
                            i = 0
                            cellCheckbox = row.insertCell(i);
                            cellCheckbox.className = "th_select_i";
                            cellCheckbox.setAttribute("data-sort", ctr['contract_id']);
                            cellCheckbox.hidden = data.setting_users.hasOwnProperty('0')? true:0;
                            checkbox = document.createElement('input');
                            checkbox.type = "checkbox";
                            checkbox.id = `selectedRows-${numRow}`;
                            checkbox.name = "selectedRows";
                            checkbox.value = numRow;
                            checkbox.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); paymentApprovalNoSelect(numRow1); refreshSortValChb(numRow1);});
                            cellCheckbox.appendChild(checkbox);
    
                            //**************************************************
                            // Объект
                            i = 1
                            cellObject = row.insertCell(i);
                            cellObject.className = "th_description_i";
                            cellObject.setAttribute("data-sort", ctr['object_name']);
                            cellObject.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellObject.innerHTML = ctr['object_name'];
                            cellObject.addEventListener("click", function() {getContractCard(this);});
                            if (data.link) {
                                cellObject.hidden = true;
                            }
    
                            //**************************************************
                            // Тип договора
                            i = 2
                            cellType = row.insertCell(i);
                            cellType.className = "th_description_i"
                            cellType.setAttribute("data-sort", ctr['type_name']);
                            cellType.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellType.innerHTML = ctr['type_name'];
    
                            //**************************************************
                            // Номер договора
                            i = 3
                            cellContactNumber = row.insertCell(i);
                            cellContactNumber.className = "th_description_i";
                            cellContactNumber.setAttribute("data-sort", ctr['contract_number']);
                            cellContactNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellContactNumber.innerHTML = ctr['contract_number'];

                            //**************************************************
                            // Дата последнего статуса договора
                            i = 4
                            cellContractStatusDate = row.insertCell(i);
                            cellContractStatusDate.className = "th_description_i";
                            cellContractStatusDate.setAttribute("data-sort", ctr['contract_status_date']);
                            cellContractStatusDate.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellContractStatusDate.innerHTML = ctr['contract_status_date_txt'];

                            //**************************************************
                            // Дата старта договора
                            i = 5
                            cellDateStart = row.insertCell(i);
                            cellDateStart.className = "th_description_i";
                            cellDateStart.setAttribute("data-sort", ctr['date_start']);
                            cellDateStart.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellDateStart.innerHTML = ctr['date_start_txt'];
    
                            //**************************************************
                            // Дата окончания договора
                            i = 6
                            cellDateFinish = row.insertCell(i);
                            cellDateFinish.className = "th_description_i";
                            cellDateFinish.setAttribute("data-sort", ctr['date_finish']);
                            cellDateFinish.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellDateFinish.innerHTML = ctr['date_finish_txt'];
    
                            //**************************************************
                            // Номер дополнительного соглашения
                            i = 7
                            cellSubContactNumber = row.insertCell(i);
                            cellSubContactNumber.className = "th_description_i";
                            cellSubContactNumber.setAttribute("data-sort", ctr['subcontract_number']);
                            cellSubContactNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellSubContactNumber.innerHTML = ctr['subcontract_number'];
    
                            //**************************************************
                            // Дата старта дополнительного соглашения
                            i = 8
                            cellSubDateStart = row.insertCell(i);
                            cellSubDateStart.className = "th_description_i";
                            cellSubDateStart.setAttribute("data-sort", ctr['subdate_start']);
                            cellSubDateStart.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellSubDateStart.innerHTML = ctr['subdate_start_txt'];
    
                            //**************************************************
                            // Дата окончания дополнительного соглашения
                            i = 9
                            cellSubDateFinish = row.insertCell(i);
                            cellSubDateFinish.className = "th_description_i";
                            cellSubDateFinish.setAttribute("data-sort", ctr['subdate_finish']);
                            cellSubDateFinish.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellSubDateFinish.innerHTML = ctr['subdate_finish_txt'];
    
                            //**************************************************
                            // Заказчик
                            i = 10
                            cellPartner = row.insertCell(i);
                            cellPartner.className = "th_description_i";
                            cellPartner.setAttribute("data-sort", ctr['partner_name']);
                            cellPartner.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellPartner.innerHTML = ctr['partner_name'];
    
                            //**************************************************
                            // Подрядчик
                            i = 11
                            cellContractor = row.insertCell(i);
                            cellContractor.className = "th_description_i";
                            cellContractor.setAttribute("data-sort", ctr['contractor_name']);
                            cellContractor.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellContractor.innerHTML = ctr['contractor_name'];
    
                            //**************************************************
                            // Краткое описание, примечание
                            i = 12
                            cellDescription = row.insertCell(i);
                            cellDescription.className = "th_description_i";
                            cellDescription.setAttribute("data-sort", ctr['contract_description']);
                            cellDescription.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellDescription.innerHTML = ctr['contract_description'];
    
                            //**************************************************
                            // Статус
                            i = 13
                            cellStatus = row.insertCell(i);
                            cellStatus.className = "th_description_i";
                            cellStatus.setAttribute("data-sort", ctr['status_name']);
                            cellStatus.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellStatus.innerHTML = ctr['status_name'];
    
                            //**************************************************
                            // Учитывается / НЕ учитывается
                            i = 14
                            cellAllow = row.insertCell(i);
                            cellAllow.className = "th_select_i";
                            cellAllow.setAttribute("data-sort", ctr['allow']);
                            cellAllow.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxAllow = document.createElement('input');
                            checkboxAllow.type = "checkbox";
                            checkboxAllow.name = "contract_allow";
                            checkboxAllow.value = numRow;
                            checkboxAllow.checked = ctr['allow']? true:0;
                            checkboxAllow.disabled  = 1;
                            cellAllow.appendChild(checkboxAllow);
    
                            //**************************************************
                            // НДС
                            i = 15
                            cellVAT = row.insertCell(i);
                            cellVAT.className = "th_select_i";
                            cellVAT.setAttribute("data-sort", ctr['vat']);
                            cellVAT.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxVAT = document.createElement('input');
                            checkboxVAT.type = "checkbox";
                            checkboxVAT.name = "contract_vat";
                            checkboxVAT.value = numRow;
                            checkboxVAT.checked = ctr['vat']? true:0;
                            checkboxVAT.disabled  = 1;
                            cellVAT.appendChild(checkboxVAT);
    
                            //**************************************************
                            // Общая сумма
                            i = 16
                            cellCost = row.insertCell(i);
                            cellCost.className = "th_description_i";
                            cellCost.setAttribute("data-sort", ctr['contract_cost']);
                            cellCost.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCost.innerHTML = ctr['contract_cost_rub'];
    
                            //**************************************************
                            // Дата создания
                            i = 17
                            cellCreateAt = row.insertCell(i);
                            cellCreateAt.className = "th_description_i";
                            cellCreateAt.setAttribute("data-sort", ctr['created_at']);
                            cellCreateAt.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCreateAt.innerHTML = ctr['created_at_txt'];
    
                            // Прогресс бар
                            progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                        }
                        else if (page_url == 'contract-acts-list') {
                            //**************************************************
                            // Флажок выбора
                            cellCheckbox = row.insertCell(0);
                            cellCheckbox.className = "th_select_i";
                            cellCheckbox.setAttribute("data-sort", ctr['act_id']);
                            cellCheckbox.hidden = data.setting_users.hasOwnProperty('0')? true:0;
                            checkbox = document.createElement('input');
                            checkbox.type = "checkbox";
                            checkbox.id = `selectedRows-${numRow}`;
                            checkbox.name = "selectedRows";
                            checkbox.value = numRow;
                            checkbox.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); paymentApprovalNoSelect(numRow1); refreshSortValChb(numRow1);});
                            cellCheckbox.appendChild(checkbox);
    
                            //**************************************************
                            // Объект
                            i = 1
                            cellObject = row.insertCell(i);
                            cellObject.className = "th_description_i";
                            cellObject.setAttribute("data-sort", ctr['object_name']);
                            cellObject.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellObject.innerHTML = ctr['object_name'];
                            cellObject.addEventListener("click", function() {getActCard(this);});
                            if (data.link) {
                                cellObject.hidden = true;
                            }
    
                            //**************************************************
                            // Тип акта
                            i = 2
                            cellType = row.insertCell(i);
                            cellType.className = "th_description_i"
                            cellType.setAttribute("data-sort", ctr['type_name']);
                            cellType.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellType.innerHTML = ctr['type_name'];
    
                            //**************************************************
                            // Номер договора
                            i = 3
                            cellContactNumber = row.insertCell(i);
                            cellContactNumber.className = "th_description_i";
                            cellContactNumber.setAttribute("data-sort", ctr['contract_number']);
                            cellContactNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellContactNumber.innerHTML = ctr['contract_number'];
    
                            //**************************************************
                            // Номер акта
                            i = 4
                            var cellActNumber = row.insertCell(i);
                            cellActNumber.className = "th_description_i";
                            cellActNumber.setAttribute("data-sort", ctr['act_number']);
                            cellActNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellActNumber.innerHTML = ctr['act_number'];
    
                            //**************************************************
                            // Дата акта
                            i = 5
                            var cellActDate = row.insertCell(i);
                            cellActDate.className = "th_description_i";
                            cellActDate.setAttribute("data-sort", ctr['act_date']);
                            cellActDate.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellActDate.innerHTML = ctr['act_date_txt'];
    
                            //**************************************************
                            // Статус подписания акта
                            i = 6
                            var cellActStatus = row.insertCell(i);
                            cellActStatus.className = "th_description_i";
                            cellActStatus.setAttribute("data-sort", ctr['status_name']);
                            cellActStatus.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellActStatus.innerHTML = ctr['status_name'];
    
                            //**************************************************
                            // НДС основного договора
                            i = 7
                            cellVAT = row.insertCell(i);
                            cellVAT.className = "th_select_i";
                            cellVAT.setAttribute("data-sort", ctr['vat']);
                            cellVAT.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxVAT = document.createElement('input');
                            checkboxVAT.type = "checkbox";
                            checkboxVAT.name = "contract_vat";
                            checkboxVAT.value = numRow;
                            checkboxVAT.checked = ctr['vat']? true:0;
                            checkboxVAT.disabled  = 1;
                            cellVAT.appendChild(checkboxVAT);

                            //**************************************************
                            // Сумма Без НДС
                            i = 8
                            cellCost = row.insertCell(i);
                            cellCost.className = "th_description_i";
                            cellCost.setAttribute("data-sort", ctr['act_cost']);
                            cellCost.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCost.innerHTML = ctr['act_cost_rub'];
    
                            //**************************************************
                            // Количество видов работ в акте
                            i = 9
                            var cellCountTow = row.insertCell(i);
                            cellCountTow.className = "th_description_i";
                            cellCountTow.setAttribute("data-sort", ctr['count_tow']);
                            cellCountTow.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCountTow.innerHTML = ctr['count_tow'];
    
                            //**************************************************
                            // Назначение - Учитывается / НЕ учитывается
                            i = 10
                            cellAllow = row.insertCell(i);
                            cellAllow.className = "th_select_i";
                            cellAllow.setAttribute("data-sort", ctr['allow']);
                            cellAllow.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxAllow = document.createElement('input');
                            checkboxAllow.type = "checkbox";
                            checkboxAllow.name = "contract_allow";
                            checkboxAllow.value = numRow;
                            checkboxAllow.checked = ctr['allow']? true:0;
                            checkboxAllow.disabled  = 1;
                            cellAllow.appendChild(checkboxAllow);
    
                            //**************************************************
                            // Дата создания
                            i = 11
                            cellCreateAt = row.insertCell(i);
                            cellCreateAt.className = "th_description_i";
                            cellCreateAt.setAttribute("data-sort", ctr['created_at']);
                            cellCreateAt.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCreateAt.innerHTML = ctr['created_at_txt'];
    
                            // Прогресс бар
                            progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                        }
                        else if (page_url == 'contract-payments-list') {
                            //**************************************************
                            // Флажок выбора
                            cellCheckbox = row.insertCell(0);
                            cellCheckbox.className = "th_select_i";
                            cellCheckbox.setAttribute("data-sort", ctr['payment_id']);
                            cellCheckbox.hidden = data.setting_users.hasOwnProperty('0')? true:0;
                            checkbox = document.createElement('input');
                            checkbox.type = "checkbox";
                            checkbox.id = `selectedRows-${numRow}`;
                            checkbox.name = "selectedRows";
                            checkbox.value = numRow;
                            checkbox.addEventListener("change", function() {paymentApprovalRecalcCards(numRow1); paymentApprovalNoSelect(numRow1); refreshSortValChb(numRow1);});
                            cellCheckbox.appendChild(checkbox);

                            //**************************************************
                            // Объект
                            i = 1
                            cellObject = row.insertCell(i);
                            cellObject.className = "th_description_i";
                            cellObject.setAttribute("data-sort", ctr['object_name']);
                            cellObject.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellObject.innerHTML = ctr['object_name'];
                            cellObject.addEventListener("click", function() {getContractsPaymentCard(this);});
                            if (data.link) {
                                cellObject.hidden = true;
                            }

                            //**************************************************
                            // Тип платежа
                            i = 2
                            cellType = row.insertCell(i);
                            cellType.className = "th_description_i"
                            cellType.setAttribute("data-sort", ctr['type_name']);
                            cellType.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellType.innerHTML = ctr['type_name'];

                            //**************************************************
                            // Номер договора
                            i = 3
                            cellContactNumber = row.insertCell(i);
                            cellContactNumber.className = "th_description_i";
                            cellContactNumber.setAttribute("data-sort", ctr['contract_number']);
                            cellContactNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellContactNumber.innerHTML = ctr['contract_number'];

                            //**************************************************
                            // Вид платежа
                            i = 4
                            var cellPayType = row.insertCell(i);
                            cellPayType.className = "th_description_i";
                            cellPayType.setAttribute("data-sort", ctr['payment_type_name']);
                            cellPayType.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellPayType.innerHTML = ctr['payment_type_name'];

                            //**************************************************
                            // Номер акта
                            i = 5
                            var cellActNumber = row.insertCell(i);
                            cellActNumber.className = "th_description_i";
                            cellActNumber.setAttribute("data-sort", ctr['act_number']);
                            cellActNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellActNumber.innerHTML = ctr['act_number'];

                            //**************************************************
                            // Номер платежа
                            i = 6
                            var cellPaymentNumber = row.insertCell(i);
                            cellPaymentNumber.className = "th_description_i";
                            cellPaymentNumber.setAttribute("data-sort", ctr['payment_number']);
                            cellPaymentNumber.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellPaymentNumber.innerHTML = ctr['payment_number'];

                            //**************************************************
                            // Дата платежа
                            i = 7
                            var cellPayDate = row.insertCell(i);
                            cellPayDate.className = "th_description_i";
                            cellPayDate.setAttribute("data-sort", ctr['payment_date']);
                            cellPayDate.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellPayDate.innerHTML = ctr['payment_date_txt'];

                            //**************************************************
                            // НДС основного договора
                            i = 8
                            cellVAT = row.insertCell(i);
                            cellVAT.className = "th_select_i";
                            cellVAT.setAttribute("data-sort", ctr['vat']);
                            cellVAT.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxVAT = document.createElement('input');
                            checkboxVAT.type = "checkbox";
                            checkboxVAT.name = "contract_vat";
                            checkboxVAT.value = numRow;
                            checkboxVAT.checked = ctr['vat']? true:0;
                            checkboxVAT.disabled  = 1;
                            cellVAT.appendChild(checkboxVAT);

                            //**************************************************
                            // Сумма Без НДС
                            i = 9
                            cellCost = row.insertCell(i);
                            cellCost.className = "th_description_i";
                            cellCost.setAttribute("data-sort", ctr['payment_cost']);
                            cellCost.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCost.innerHTML = ctr['payment_cost_without_vat_rub'];

                            //**************************************************
                            // Назначение - Учитывается / НЕ учитывается
                            i = 10
                            cellAllow = row.insertCell(i);
                            cellAllow.className = "th_select_i";
                            cellAllow.setAttribute("data-sort", ctr['allow']);
                            cellAllow.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            checkboxAllow = document.createElement('input');
                            checkboxAllow.type = "checkbox";
                            checkboxAllow.name = "contract_allow";
                            checkboxAllow.value = numRow;
                            checkboxAllow.checked = ctr['allow']? true:0;
                            checkboxAllow.disabled  = 1;
                            cellAllow.appendChild(checkboxAllow);

                            //**************************************************
                            // Дата создания
                            i = 11
                            cellCreateAt = row.insertCell(i);
                            cellCreateAt.className = "th_description_i";
                            cellCreateAt.setAttribute("data-sort", ctr['created_at']);
                            cellCreateAt.hidden = data.setting_users.hasOwnProperty(i)? true:0;
                            cellCreateAt.innerHTML = ctr['created_at_txt'];

                            // Прогресс бар
                            progressBarCalc(direction, numRow, data.tab_rows, rowCount);
                        }
                    }
                    return
                }
                else if (data.status === 'error') {
                    const tab = document.getElementById("employeeTable");
                    var tab_tr = tab.getElementsByTagName('tbody')[0];

                    if (tab_tr.getElementsByClassName("empty_table")[0]) {
                        return;
                    }

                    var row = tab_tr.insertRow(0);
                    var emptyTable = row.insertCell(0);
                    emptyTable.className = "empty_table";
                    emptyTable.innerHTML = 'Данные не найдены';
                    emptyTable.style.textAlign = "center";
                    emptyTable.style.fontStyle = "italic";

                    emptyTable.colSpan = tab.getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th').length;

                    return createDialogWindow(status='error', description=['Ошибка',data.description]);
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
