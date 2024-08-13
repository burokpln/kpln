$(document).ready(function() {
    var page_url = document.URL;
    if (document.URL.split('/objects/').length > 1) {
        document.getElementById('edit_btn')? document.getElementById('edit_btn').addEventListener('click', function() {editTow();}):'';
    }
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");

    // При пересохранении договора должны получить комментарий, почему изменили договор
    if (document.URL.split('/contract-list/card/').length > 1 &&
             document.URL.split('/contract-list/card/new/').length <= 1) {
        document.getElementById('save_btn')? document.getElementById('save_btn').addEventListener('click', function() {showSaveContractWithCommentDialogWindow();}):'';
        document.getElementById('cancel_btn')? document.getElementById('cancel_btn').addEventListener('click', function() {cancelTowChanges();}):'';
    }
    else if (document.URL.split('/contract-list/card/new/').length > 1) {
        document.getElementById('save_btn')? document.getElementById('save_btn').addEventListener('click', function() {saveTowChanges();}):'';
        document.getElementById('cancel_btn')? document.getElementById('cancel_btn').addEventListener('click', function() {cancelTowChanges();}):'';
    }
    else {
        document.getElementById('save_btn')? document.getElementById('save_btn').addEventListener('click', function() {saveTowChanges();}):'';
        document.getElementById('cancel_btn')? document.getElementById('cancel_btn').addEventListener('click', function() {cancelTowChanges();}):'';
    }

    document.getElementById('id_div_milestones_getMilestones')? document.getElementById('id_div_milestones_getMilestones').addEventListener('click', function() {getMilestones();}):'';
    document.getElementById('id_div_milestones_getReserves')? document.getElementById('id_div_milestones_getReserves').addEventListener('click', function() {getReserves();}):'';
    document.getElementById('id_div_milestones_getContractsList')? document.getElementById('id_div_milestones_getContractsList').addEventListener('click', function() {getContractsList();}):'';

    document.getElementById('dloadSostavProekta')? document.getElementById('dloadSostavProekta').addEventListener('click', function() {dloadSostavProekta();}):'';
    document.getElementById('columnsSettings')? document.getElementById('columnsSettings').addEventListener('click', function() {columnsSettings();}):'';
    document.getElementById('tablerFocus')? document.getElementById('tablerFocus').addEventListener('click', function() {tablerFocus();}):'';

    let input_tow_name = document.getElementsByClassName('input_tow_name');
    for (let i of input_tow_name) {
        i.addEventListener('change', function() {editDescription(this, 'input_tow_name');});
    }
    let tow_dept = document.getElementsByClassName('tow_dept');
    for (let i of tow_dept) {
        i.addEventListener('change', function() {editDescription(this, 'select_tow_dept');});
    }
    let tow_time_tracking = document.getElementsByClassName('tow_time_tracking');
    for (let i of tow_time_tracking) {
        i.addEventListener('change', function() {editDescription(this, 'checkbox_time_tracking');});
    }
    let button_tow_first_cell = document.getElementsByClassName('button_tow_first_cell');
    for (let i of button_tow_first_cell) {
        i.addEventListener('click', function() {FirstRow();})
    }
    let addTowBefore = document.getElementsByClassName('addTowBefore');
    for (let i of addTowBefore) {
        i.addEventListener('click', function() {addTow(this, 'Before');});
    }
    let addTowAfter = document.getElementsByClassName('addTowAfter');
    for (let i of addTowAfter) {
        i.addEventListener('click', function() {addTow(this, 'After');});
    }
    let towDelTow = document.getElementsByClassName('tow_delTow');
    for (let i of towDelTow) {
        i.addEventListener('click', function() {delTow(this);});
    }
    let shiftTowLeft = document.getElementsByClassName('shiftTowLeft');
    for (let i of shiftTowLeft) {
        i.addEventListener('click', function() {shiftTow(this, 'Left');});
    }
    let shiftTowRight = document.getElementsByClassName('shiftTowRight');
    for (let i of shiftTowRight) {
        i.addEventListener('click', function() {shiftTow(this, 'Right');});
    }
    let shiftTowUp = document.getElementsByClassName('shiftTowUp');
    for (let i of shiftTowUp) {
        i.addEventListener('click', function() {shiftTow(this, 'Up');});
    }
    let shiftTowDown = document.getElementsByClassName('shiftTowDown');
    for (let i of shiftTowDown) {
        i.addEventListener('click', function() {shiftTow(this, 'Down');});
    }
    let addTowNew = document.getElementsByClassName('addTowNew');
    for (let i of addTowNew) {
        i.addEventListener('click', function() {addTow(this, 'New');});
    }
});

let userChanges = {};  //Список изменений tow пользователем
let newRowList = new Set();  //Список новых tow
let deletedRowList = new Set();  //Список удаленных tow
let editDescrRowList = {};  //Список изменений input tow
let highestRow = [];  //Самая верхняя строка с которой "поедет" вся нумерация строк
var proj_url = decodeURI(document.URL.split('/')[4]);  //Название проекта
let reservesChanges = {};  //Список изменений резервов

//Создаём первую tow проекта
function FirstRow() {
    fetch('/get_dept_list/tow')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {

            const tab = document.getElementById("towTable");
            var tab_tr0 = tab.getElementsByTagName('tbody')[0];
            tab.deleteRow(1);
            var row = tab_tr0.insertRow(0);
            let col_i = 0;

            if (document.URL.split('/objects/').length > 1) {
                //**************************************************
                // row

                row.className = "lvl-0";
                row.setAttribute("data-lvl", "0");
                //row.setAttribute("data-del", "1");
                row.setAttribute("data-is_not_edited", '');
                row.id = `${proj_url}_New_${new Date().getTime()}`;
                row.addEventListener('click', function() { mergeTowRow(this);});

                //**************************************************
                // Виды работ
                var tow_name = row.insertCell(0);
                tow_name.className = "tow_name";
                    var div_tow_name = document.createElement('div');
                    div_tow_name.className = "div_tow_name";
                        var input_tow_name = document.createElement('input');
                        input_tow_name.type = "text";
                        input_tow_name.className = "input_tow_name";
                        input_tow_name.placeholder = "Введите название работы";
                        input_tow_name.addEventListener('change', function() {editDescription(this, 'input_tow_name');});
                        //input_tow_name.readOnly = true;
                    div_tow_name.appendChild(input_tow_name);
                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_tow_button";
                    addButtonsForNewRow(div_tow_button, createNewRow=true);
                tow_name.appendChild(div_tow_name);
                tow_name.appendChild(div_tow_button);
                col_i++;
                
                //**************************************************
                // Отдел
                var tow_dept = row.insertCell(col_i);
                tow_dept.className = "tow_dept";
                    var selectDept = document.createElement('select');
                    selectDept.className = "select_tow_dept";
                    //selectDept.disabled  = 1;
                    var option = document.createElement('option');
                    selectDept.appendChild(option);

                    for (j in data.dept_list) {
                        var option = document.createElement('option');
                        option.value = j;
                        option.text = data.dept_list[j];
                        selectDept.appendChild(option);
                    }
                tow_dept.appendChild(selectDept);
                tow_dept.addEventListener('click', function() {editDescription(this, 'select_tow_dept');});
                col_i++;

                //**************************************************
                // Учёт часов
                var tow_time_tracking = row.insertCell(col_i);
                tow_time_tracking.className = "tow_time_tracking";

                var checkbox = document.createElement('input');
                checkbox.type = "checkbox";
                checkbox.className = "checkbox_time_tracking";
                //checkbox.disabled  = 1;
                tow_time_tracking.appendChild(checkbox);
                tow_time_tracking.addEventListener('click', function() {editDescription(this, 'checkbox_time_tracking');});
                col_i++;

                //**************************************************
                // Договорная сумма
                let contract_cost = row.insertCell(col_i);
                contract_cost.className = "contract_cost";
                    let tow_contract_cost = document.createElement('input');
                    tow_contract_cost.type = "text";
                    tow_contract_cost.className = "tow_contract_cost";
                    tow_contract_cost.setAttribute("data-value", null);
                    tow_contract_cost.disabled = true;
                    tow_contract_cost.readOnly = true;
                contract_cost.appendChild(tow_contract_cost);
                col_i++;

                //**************************************************
                // Субподрядная сумма
                let expenditure_contract_cost = row.insertCell(col_i);
                expenditure_contract_cost.className = "expenditure_contract_cost";
                    let tow_expenditure_contract_cost = document.createElement('input');
                    tow_expenditure_contract_cost.type = "text";
                    tow_expenditure_contract_cost.className = "tow_expenditure_contract_cost";
                    tow_expenditure_contract_cost.setAttribute("data-value", null);
                    tow_expenditure_contract_cost.disabled = true;
                    tow_expenditure_contract_cost.readOnly = true;
                expenditure_contract_cost.appendChild(tow_expenditure_contract_cost);
                col_i++;

                //**************************************************
                // Сумма ФОТ
                let fot_cost = row.insertCell(col_i);
                fot_cost.className = "fot_cost";
                    let tow_fot_cost = document.createElement('input');
                    tow_fot_cost.type = "text";
                    tow_fot_cost.className = "tow_fot_cost";
                    tow_fot_cost.setAttribute("data-value", null);
                    tow_fot_cost.disabled = true;
                    tow_fot_cost.readOnly = true;
                fot_cost.appendChild(tow_fot_cost);
                col_i++;

                //**************************************************
                // Распределение
                let cost = row.insertCell(col_i);
                cost.className = "cost";
                    let tow_cost = document.createElement('input');
                    tow_cost.type = "text";
                    tow_cost.classList.add("tow_cost", "calc");
                    tow_cost.setAttribute("data-value", null);
                    setNewRowTowFunc(tow_cost);
                cost.appendChild(tow_cost);
                col_i++;

                //**************************************************
                // ∑ ВЛОЖ.
                let child_cost = row.insertCell(col_i);
                child_cost.className = "child_cost";
                    let tow_child_cost = document.createElement('input');
                    tow_child_cost.type = "text";
                    tow_child_cost.className = "tow_child_cost";
                    tow_child_cost.setAttribute("data-value", 0);
                    tow_child_cost.value = '';
                    tow_child_cost.disabled = true;
                    tow_child_cost.readOnly = true;
                child_cost.appendChild(tow_child_cost);
                col_i++;

                //**************************************************
                // % ДЕТ
                let parent_percent_cost = row.insertCell(col_i);
                parent_percent_cost.className = "parent_percent_cost";
                    let tow_parent_percent_cost = document.createElement('input');
                    tow_parent_percent_cost.type = "text";
                    tow_parent_percent_cost.className = "tow_parent_percent_cost";
                    tow_parent_percent_cost.setAttribute("data-value", 0);
                    tow_parent_percent_cost.value = '';
                    tow_parent_percent_cost.disabled = true;
                    tow_parent_percent_cost.readOnly = true;
                parent_percent_cost.appendChild(tow_parent_percent_cost);

            }
            else {
                //**************************************************
                // row

                row.className = "lvl-0";
                row.setAttribute("data-lvl", "0");
                //row.setAttribute("data-del", "1");
                row.setAttribute("data-tow_cnt", "0");
                row.setAttribute("data-value_type", "");
                row.setAttribute("data-is_not_edited", '');
                row.id = `${proj_url}_New_${new Date().getTime()}`;

                //**************************************************
                // Виды работ
                var tow_name = row.insertCell(0);
                tow_name.className = "tow_name";
                    var div_tow_name = document.createElement('div');
                    div_tow_name.className = "div_tow_name";
                        var input_tow_name = document.createElement('input');
                        input_tow_name.type = "text";
                        input_tow_name.className = "input_tow_name";
                        input_tow_name.placeholder = "Введите название работы";
                        input_tow_name.addEventListener('change', function() {editDescription(this, 'input_tow_name');});
                    div_tow_name.appendChild(input_tow_name);
                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_tow_button";
                    div_tow_button.hidden = true;
                    addButtonsForNewRow(div_tow_button, createNewRow=true);
                tow_name.appendChild(div_tow_name);
                tow_name.appendChild(div_tow_button);
                col_i++;

                //**************************************************
                // Выбор tow
                let cellCheckbox = row.insertCell(col_i);
                cellCheckbox.className = "tow_contract";
                    let checkbox = document.createElement('input');
                    checkbox.type = "checkbox";
                    checkbox.className = "checkbox_time_tracking";
                    checkbox.checked = true;
                cellCheckbox.appendChild(checkbox);
                col_i++;

                //**************************************************
                // Отдел
                let tow_dept = row.insertCell(col_i);
                tow_dept.className = "tow_dept";
                    let selectDept = document.createElement('select');
                    selectDept.className = "select_tow_dept";
                        let option = document.createElement('option');
                        option.value = "";
                    selectDept.appendChild(option);
                        for (let j in data.dept_list) {
                            let option = document.createElement('option');
                            option.value = j;
                            option.text = data.dept_list[j];
                            selectDept.appendChild(option);
                        }
                tow_dept.appendChild(selectDept);
                tow_dept.addEventListener('click', function() {editDescription(this, 'select_tow_dept');});
                col_i++;

                //**************************************************
                // Сумма
                let cost = row.insertCell(col_i);
                cost.className = "cost";
                    let tow_cost = document.createElement('input');
                    tow_cost.type = "text";
                    tow_cost.classList.add("tow_cost", "calc");
                    tow_cost.setAttribute("data-value", null);
                cost.appendChild(tow_cost);
                col_i++;

                //**************************************************
                // % сумма
                let cost_percent = row.insertCell(col_i);
                cost_percent.className = "cost_percent";
                    let tow_cost_percent = document.createElement('input');
                    tow_cost_percent.type = "text";
                    tow_cost_percent.classList.add("tow_cost_percent", "calc");
                    tow_cost_percent.setAttribute("data-value", null);
                cost_percent.appendChild(tow_cost_percent);
                col_i++;

                //**************************************************
                // Сумма ФОТ
                let fot_cost = row.insertCell(col_i);
                fot_cost.className = "fot_cost";
                    let tow_fot_cost = document.createElement('input');
                    tow_fot_cost.type = "text";
                    tow_fot_cost.className = "tow_fot_cost";
                    tow_fot_cost.setAttribute("data-value", null);
                    tow_fot_cost.disabled = true;
                fot_cost.appendChild(tow_fot_cost);
                col_i++;

                //**************************************************
                // Субп. проекта
                let subcontractor_cost = row.insertCell(col_i);
                subcontractor_cost.className = "subcontractor_cost";
                    let tow_subcontractor_cost = document.createElement('input');
                    tow_subcontractor_cost.type = "text";
                    tow_subcontractor_cost.className = "tow_subcontractor_cost";
                    tow_subcontractor_cost.setAttribute("data-value", null);
                    tow_subcontractor_cost.disabled = true;
                subcontractor_cost.appendChild(tow_subcontractor_cost);
                col_i++;

                //**************************************************
                // Начало
                let date_start = row.insertCell(col_i);
                date_start.className = "date_start";
                    let tow_date_start = document.createElement('input');
                    tow_date_start.type = "text";
                    tow_date_start.className = "tow_date_start";
                    tow_date_start.setAttribute("data-value", null);
                    tow_date_start.value = document.getElementById('ctr_card_date_start').value;
                date_start.appendChild(tow_date_start);
                col_i++;

                //**************************************************
                // Окончание
                let date_finish = row.insertCell(col_i);
                date_finish.className = "date_finish";
                    let tow_date_finish = document.createElement('input');
                    tow_date_finish.type = "text";
                    tow_date_finish.className = "tow_date_finish";
                    tow_date_finish.setAttribute("data-value", null);
                    tow_date_finish.value = document.getElementById('ctr_card_date_finish').value;
                date_finish.appendChild(tow_date_finish);
                col_i++;

                //**************************************************
                // ∑ ВЛОЖ.
                let child_cost = row.insertCell(col_i);
                child_cost.className = "child_cost";
                    let tow_child_cost = document.createElement('input');
                    tow_child_cost.type = "text";
                    tow_child_cost.className = "tow_child_cost";
                    tow_child_cost.setAttribute("data-value", 0);
                    tow_child_cost.value = '';
                    tow_child_cost.disabled = true;
                child_cost.appendChild(tow_child_cost);
                col_i++;

                //**************************************************
                // % ДЕТ
                let parent_percent_cost = row.insertCell(col_i);
                parent_percent_cost.className = "parent_percent_cost";
                    let tow_parent_percent_cost = document.createElement('input');
                    tow_parent_percent_cost.type = "text";
                    tow_parent_percent_cost.className = "tow_parent_percent_cost";
                    tow_parent_percent_cost.setAttribute("data-value", 0);
                    tow_parent_percent_cost.value = '';
                    tow_parent_percent_cost.disabled = true;
                parent_percent_cost.appendChild(tow_parent_percent_cost);
                col_i++;

                //**************************************************
                // АВАНС
                let payment_wo_act_cost = row.insertCell(col_i);
                payment_wo_act_cost.className = "payment_wo_act_cost";
                    let tow_payment_wo_act_cost = document.createElement('input');
                    tow_payment_wo_act_cost.type = "text";
                    tow_payment_wo_act_cost.setAttribute("data-value", '');
                    tow_payment_wo_act_cost.value = '';
                    tow_payment_wo_act_cost.disabled = true;
                payment_wo_act_cost.appendChild(tow_payment_wo_act_cost);
                col_i++;

                //**************************************************
                // ПЛАТЕЖ
                let payment_w_act_cost = row.insertCell(col_i);
                payment_w_act_cost.className = "payment_w_act_cost";
                    let tow_payment_w_act_cost = document.createElement('input');
                    tow_payment_w_act_cost.type = "text";
                    tow_payment_w_act_cost.setAttribute("data-value", '');
                    tow_payment_w_act_cost.value = '';
                    tow_payment_w_act_cost.disabled = true;
                payment_w_act_cost.appendChild(tow_payment_w_act_cost);
                col_i++;

                //**************************************************
                // АКТ
                let cell_act_cost = row.insertCell(col_i);
                cell_act_cost.className = "act_cost";
                    let tow_cell_act_cost = document.createElement('input');
                    tow_cell_act_cost.type = "text";
                    tow_cell_act_cost.setAttribute("data-value", '');
                    tow_cell_act_cost.value = '';
                    tow_cell_act_cost.disabled = true;
                cell_act_cost.appendChild(tow_cell_act_cost);
                col_i++;

                //**************************************************
                // А-П
                let cell_remaining_cost = row.insertCell(col_i);
                cell_remaining_cost.className = "remaining_cost";
                    let tow_cell_remaining_cost = document.createElement('input');
                    tow_cell_remaining_cost.type = "text";
                    tow_cell_remaining_cost.setAttribute("data-value", '');
                    tow_cell_remaining_cost.value = '';
                    tow_cell_remaining_cost.disabled = true;
                cell_remaining_cost.appendChild(tow_cell_remaining_cost);
            }

            //Добавляем изменение - Создание новой строки
            UserChangesLog(c_id=row.id, rt='New', u_p_id='', c_row=row); // FirstRow - new row

            var edit_btn = document.getElementById("edit_btn");
            if (!edit_btn.hidden) {
                if (document.URL.split('/objects/').length > 1) {
                    editTow();
                }
                else {
                    isEditContract();
                }
            }
            // Добавляем функции в ячейки
            if (document.URL.split('/contract-list/card/').length > 1) {
                setNewRowContractFunc(row);
            }
            if (document.URL.split('/objects/').length > 1) {
                editTow();
            }

        }
        else if (data.status === 'error') {
            let description = data.description;
            description.unshift('Ошибка');
            return createDialogWindow(status='error2', description=description);
        }
        })
        .catch(error => {
            console.error('Error:', error);
        });
};

//Создание новой строки или копирование структуры строк
function addTow(button, route) {
    if  (!['Before', 'After', 'New'].includes(route)) {
        return createDialogWindow(status='error', description=['Ошибка', 'Направление копирования структуры видов работ задано неверно']);
    }

    var page_url = document.URL.split('/');

    var row = button.closest('tr');
    var className = row.className;
    var cur_lvl = parseInt(className.split('lvl-')[1])
    var newRow = row.cloneNode(true);

    var input_tow_name = newRow.getElementsByClassName("input_tow_name")[0];

    //отображаем кнопку "удалить tow"
    if (row.dataset.is_not_edited) {
        newRow.setAttribute("data-is_not_edited", '');
        var tow_delTow = newRow.querySelector(".tow_delTow");
        tow_delTow.setAttribute("data-is_not_edited", '');
        tow_delTow.hidden = false;
        input_tow_name.className = 'input_tow_name';
    }

    //input_tow_name.readOnly = 1;
    var rowNumber = row.rowIndex;
    var currentRow = button.closest('tr');
    var preRow = row.previousElementSibling;
    var nextRow = row.nextElementSibling;
    var taskRow = row.nextElementSibling;
    var pre_lvl = preRow? parseInt(preRow.className.split('lvl-')[1]):0;
    var p_id = -1;

    if (!taskRow) {
        taskRow = row;
    }
    if (!nextRow) {
        nextRow = row;
    }

    //Добавляем функцию слияний tow если мы в разделе "виды работ"
    if (document.URL.split('/objects/').length > 1) {
        newRow.addEventListener('click', function() { mergeTowRow(this);});
    }

    if (route === 'New') {
        if (cur_lvl+1 > 10) {
            return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности - 10']);
        }

        newRow.className = 'lvl-' + (cur_lvl+1);
        newRow.setAttribute("data-lvl", cur_lvl+1);

        // Очищаем все поля в новой строке
        if (newRow) {
            var textInputs = newRow.querySelectorAll('input[type="text"]');
            textInputs.forEach(function (input) {
                input.value = '';
                //input.readOnly = true;
            });


            var checkbox = newRow.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = document.URL.split('/objects/').length > 1? false:true;
            }

        }
        //Создаём временное id для новой tow
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime()
        if (!row.nextElementSibling) {
            row.parentNode.appendChild(newRow);
        }
        else {
            row.parentNode.insertBefore(newRow, nextRow);
        }

        // Если работаем в договоре, то добавляем даты из карточки договора
        if (document.URL.split('/contract-list/card/').length > 1) {
            newRow.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
            newRow.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
        }

        //Добавляем изменение - Создание новой строки
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=row.id, c_row=newRow); // New - new row
        // Настраиваем кнопки
        addButtonsForNewRow(newRow);

        // Очищаем все поля в новой строке
        clearDataAttributeValue(newRow);

        // Если страница договора, то добавляем функции в ячейки
        if (document.URL.split('/contract-list/card/').length > 1) {
            setNewRowContractFunc(newRow);
            isEditContract();
            return;
        }

        // Добавляем функцию пересчёта детей и родителей в разделе TOW
        setNewRowTowFunc(false, newRow);

        //Включаем режим редактирования, если не был включён
        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow();
        }
        return;
    }

    // Очищаем input всех создаваемых строк
    var textInputs = newRow.querySelectorAll('input[type="text"]');
    textInputs.forEach(function (input) {
        input.value = '';
    });
    var checkbox = newRow.querySelector('input[type="checkbox"]');
    if (checkbox) {
        checkbox.checked = document.URL.split('/objects/').length > 1? false:true;
    }

    // Если работаем в договоре, то добавляем даты из карточки договора
    if (document.URL.split('/contract-list/card/').length > 1) {
        newRow.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
        newRow.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
    }

    // Список создаваемых строк
    var children_list = [];

    //Если копируем структуру вверх
    if (route === 'Before') {
        // Если работаем в договоре, то добавляем даты из карточки договора
        if (document.URL.split('/contract-list/card/').length > 1) {
            newRow.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
            newRow.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
        }

        //Ищем всех детей у копируемой строки
        while (nextRow && !nextRow.classList.contains(className)) {
            var tow_lvl = parseInt(nextRow.className.split('lvl-')[1]);

            //Создаём список детей (те, чей лвл вложенности выше)
            if (tow_lvl > cur_lvl) {
                var child = nextRow.cloneNode(true);

                if (child.dataset.is_not_edited) {
                    child.setAttribute("data-is_not_edited", '');
                    var tow_delTow = child.querySelector(".tow_delTow");
                    tow_delTow.setAttribute("data-is_not_edited", '');
                    tow_delTow.hidden = false;
                    child.getElementsByClassName("input_tow_name")[0].className = 'input_tow_name';
                }

                clearDataAttributeValue(child);

                // Очищаем input всех создаваемых строк
                var textInputs = child.querySelectorAll('input[type="text"]');
                textInputs.forEach(function (input) {
                    input.value = '';
                });
                var checkbox = child.querySelector('input[type="checkbox"]');

                if (checkbox) {
                    checkbox.checked = document.URL.split('/objects/').length > 1? false:true;
                }

                //Добавляем функцию слияний tow если мы в разделе "виды работ"
                if (document.URL.split('/objects/').length > 1) {
                    child.addEventListener('click', function() { mergeTowRow(this);});
                }

                // Если работаем в договоре, то добавляем даты из карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    child.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
                    child.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
                }

                children_list.push(child)
            }
            nextRow = nextRow.nextElementSibling;
        }

        clearDataAttributeValue(newRow);

        //Создаём временное id для новой tow и вставляем tow над текущей строкой
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime();
        row.parentNode.insertBefore(newRow, row);
        //настраиваем кнопки
        addButtonsForNewRow(newRow);
        // Если страница договора, то добавляем функции в ячейки
        if (document.URL.split('/contract-list/card/').length > 1) {
            setNewRowContractFunc(newRow);
        }
        else if (document.URL.split('/objects/').length > 1) {
            // Добавляем функцию пересчёта детей и родителей в разделе TOW
            setNewRowTowFunc(false, newRow);
        }
        //Проходим по списку детей
        for (var i=0; i<children_list.length; i++) {
            tow = children_list[i];
            //Создаём временное id для каждого ребенка
            tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
            var child_lvl = parseInt(tow.className.split('lvl-')[1])
            newRow.parentNode.insertBefore(tow, row);

            //настраиваем кнопки
            addButtonsForNewRow(tow);
            // Если страница договора, то добавляем функции в ячейки
            if (document.URL.split('/contract-list/card/').length > 1) {
                setNewRowContractFunc(tow);
            }
            else if (document.URL.split('/objects/').length > 1) {
                // Добавляем функцию пересчёта детей и родителей в разделе TOW
                setNewRowTowFunc(false, tow);
            }

            //Определяем родителя текущего ребенка
            if (i==0) {
                pre_child_lvl = parseInt(newRow.className.split('lvl-')[1]);
                preChildRow = newRow;
            }
            else {
                pre_child_lvl = parseInt(children_list[i-1].className.split('lvl-')[1]);
                preChildRow = children_list[i-1];
            }
            p_id = findParent(curRow_fP=tow, cur_lvl_fP=child_lvl, pre_lvl_fP=pre_child_lvl, preRow_fP=preChildRow);

            //Записываем все изменения для детей
            UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow); // Before - new child row
            editDescription(button='', type='select_tow_dept', editDescription_row=tow);
            if (page_url[3] == 'objects') {
                editDescription(button='', type='checkbox_time_tracking', editDescription_row=tow);
            }
        }

        //Определяем родителя скопированного родителя
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        //Записываем все изменения для родителя
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=p_id, c_row=newRow); // Before - new row
        editDescription(button='', type='select_tow_dept', editDescription_row=newRow);
        editDescription(button='', type='checkbox_time_tracking', editDescription_row=newRow);

    }
    //Если копируем структуру вниз
    else if (route === 'After') {
        //Определяем уровень вложенности следующей строки
        var tow_lvl = nextRow? parseInt(nextRow.className.split('lvl-')[1]):'';

        // Если работаем в договоре, то добавляем даты из карточки договора
        if (document.URL.split('/contract-list/card/').length > 1) {
            newRow.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
            newRow.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
        }

        //Ищем всех детей у копируемой строки
        while (nextRow && tow_lvl > cur_lvl) {

            tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
            //Создаём список детей (те, чей лвл вложенности выше)
            if (tow_lvl > cur_lvl) {
                var child = nextRow.cloneNode(true)
                if (child.dataset.is_not_edited) {
                    child.setAttribute("data-is_not_edited", '');
                    var tow_delTow = child.querySelector(".tow_delTow");
                    tow_delTow.setAttribute("data-is_not_edited", '');
                    tow_delTow.hidden = false;
                    child.getElementsByClassName("input_tow_name")[0].className = 'input_tow_name';
                }

                clearDataAttributeValue(child);

                // Очищаем input всех создаваемых строк
                var textInputs = child.querySelectorAll('input[type="text"]');
                textInputs.forEach(function (input) {
                    input.value = '';
                });
                var checkbox = child.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.checked = document.URL.split('/objects/').length > 1? false:true;
                }

                //Добавляем функцию слияний tow если мы в разделе "виды работ"
                if (document.URL.split('/objects/').length > 1) {
                    child.addEventListener('click', function() { mergeTowRow(this);});
                }

                // Если работаем в договоре, то добавляем даты из карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    child.querySelector('.tow_date_start').value = document.getElementById('ctr_card_date_start').value;
                    child.querySelector('.tow_date_finish').value = document.getElementById('ctr_card_date_finish').value;
                }

                children_list.push(child)
                nextRow = nextRow.nextElementSibling;
            }
        }

        clearDataAttributeValue(newRow);

        //Создаём временное id для новой tow и вставляем tow над текущей строкой
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime();
        //Если после копируемой структуры есть ещё строка, вставляем скопированное над этой строкой
        if (nextRow) {
            //Если в структуре есть дети
            if (children_list.length){
                if (className == 'lvl-0') {
                    row.parentNode.insertBefore(newRow, nextRow);
                }
                else {
                    taskRow.parentNode.insertBefore(newRow, nextRow);
                }
                //настраиваем кнопки
                addButtonsForNewRow(newRow);
                // Если страница договора, то добавляем функции в ячейки
                if (document.URL.split('/contract-list/card/').length > 1) {
                    setNewRowContractFunc(newRow);
                }
                else if (document.URL.split('/objects/').length > 1) {
                    // Добавляем функцию пересчёта детей и родителей в разделе TOW
                    setNewRowTowFunc(false, newRow);
                }

                //Проходим по списку детей
                for (var i=0; i<children_list.length; i++) {
                    tow = children_list[i];
                    //Создаём временное id для каждого ребенка
                    tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
                    var child_lvl = parseInt(tow.className.split('lvl-')[1])
                    newRow.parentNode.insertBefore(tow, nextRow);

                    //настраиваем кнопки
                    addButtonsForNewRow(tow);
                    // Если страница договора, то добавляем функции в ячейки
                    if (document.URL.split('/contract-list/card/').length > 1) {
                        setNewRowContractFunc(tow);
                    }
                    else if (document.URL.split('/objects/').length > 1) {
                        // Добавляем функцию пересчёта детей и родителей в разделе TOW
                        setNewRowTowFunc(false, tow);
                    }

                    //Определяем родителя текущего ребенка
                    if (i==0) {
                        pre_child_lvl = parseInt(newRow.className.split('lvl-')[1]);
                        preChildRow = newRow;
                    }
                    else {
                        pre_child_lvl = parseInt(children_list[i-1].className.split('lvl-')[1]);
                        preChildRow = children_list[i-1];
                    }
                    p_id = findParent(curRow_fP=tow, cur_lvl_fP=child_lvl, pre_lvl_fP=pre_child_lvl, preRow_fP=preChildRow);

                    //Записываем все изменения для детей
                    UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow); // After - new child row
                    editDescription(button='', type='select_tow_dept', editDescription_row=tow);
                    editDescription(button='', type='checkbox_time_tracking', editDescription_row=tow);
                }
            }
            //В структуре нет детей, просто вставляем копию под текущую строку
            else {
                nextRow.parentNode.insertBefore(newRow, row.nextSibling);
                //настраиваем кнопки
                addButtonsForNewRow(newRow);
                // Если страница договора, то добавляем функции в ячейки
                if (document.URL.split('/contract-list/card/').length > 1) {
                    setNewRowContractFunc(newRow);
                }
                else if (document.URL.split('/objects/').length > 1) {
                    // Добавляем функцию пересчёта детей и родителей в разделе TOW
                    setNewRowTowFunc(false, newRow);
                }
            }
            var newRow_lvl = parseInt(newRow.className.split('lvl-')[1]);

        }
        //После копируемой структуры нет срок (конец таблицы)
        else {
            row.parentNode.appendChild(newRow);
            //настраиваем кнопки
            addButtonsForNewRow(newRow);
            // Если страница договора, то добавляем функции в ячейки
            if (document.URL.split('/contract-list/card/').length > 1) {
                setNewRowContractFunc(newRow);
            }
            else if (document.URL.split('/objects/').length > 1) {
                // Добавляем функцию пересчёта детей и родителей в разделе TOW
                setNewRowTowFunc(false, newRow);
            }

            var newRow_lvl = parseInt(newRow.className.split('lvl-')[1]);

            //Если в структуре есть дети
            if (children_list.length) {
                //Проходим по списку детей
                for (var i=0; i<children_list.length; i++) {
                    tow = children_list[i];
                    //Создаём временное id для каждого ребенка
                    tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
                    var child_lvl = parseInt(tow.className.split('lvl-')[1])
                    row.parentNode.appendChild(tow);

                    //настраиваем кнопки
                    addButtonsForNewRow(tow);
                    // Если страница договора, то добавляем функции в ячейки
                    if (document.URL.split('/contract-list/card/').length > 1) {
                        setNewRowContractFunc(tow);
                    }
                    else if (document.URL.split('/objects/').length > 1) {
                        // Добавляем функцию пересчёта детей и родителей в разделе TOW
                        setNewRowTowFunc(false, tow);
                    }

                    //Определяем родителя текущего ребенка
                    if (i==0) {
                        pre_child_lvl = parseInt(newRow.className.split('lvl-')[1]);
                        preChildRow = newRow;
                    }
                    else {
                        pre_child_lvl = parseInt(children_list[i-1].className.split('lvl-')[1]);
                        preChildRow = children_list[i-1];
                    }
                    p_id = findParent(curRow_fP=tow, cur_lvl_fP=child_lvl, pre_lvl_fP=pre_child_lvl, preRow_fP=preChildRow);

                    //Записываем все изменения для детей
                    UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow); // After - new child row End of table
                    editDescription(button='', type='select_tow_dept', editDescription_row=tow);
                    editDescription(button='', type='checkbox_time_tracking', editDescription_row=tow);
                }
            }
        }
        //Определяем родителя скопированного родителя
        preRow = newRow.previousElementSibling;
        pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=newRow_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        //Записываем все изменения для родителя
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=p_id, c_row=newRow);  // After - new row End of table
        editDescription(button='', type='select_tow_dept', editDescription_row=newRow);
        editDescription(button='', type='checkbox_time_tracking', editDescription_row=newRow);
    }

    if (document.URL.split('/objects/').length > 1) {
        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow();
        }
    }
    else {
        isEditContract();
    }
}

//Удаление структуры
function delTow(button) {
    var row = button.closest('tr');
    var del_no_del_status = 0;

    if (row.dataset.is_not_edited) {
        del_no_del_status = 1;
        return createDialogWindow(status='error', description=['Эту строку удалить нельзя']);
    }

    var rowNumber = row.rowIndex;
    var className = row.className;
    var cur_lvl = parseInt(className.split('lvl-')[1]);

    const tab = document.getElementById("towTable");

    var del_children_list = new Set([row.id]);  //Список удаляемых tow
    var del_row_cnt = 1;  //Счётчик удаляемых tow
    var del_nextRow = row.nextElementSibling;  //Следующая строка

    //Для пересчета нераспределенных средств в карточке договора, создаём список строк для удаления
    //if (document.URL.split('/contract-list/card/').length > 1) {
    //    var del_list_undistributedCost = new Set([row]);
    //}
    var del_list_undistributedCost = new Set([row]);

    //Проверяем, есть ли не удаляемые дети
    while (del_nextRow && true) {
        var del_child_lvl = parseInt(del_nextRow.className.split('lvl-')[1]);

        if (del_child_lvl > cur_lvl) {
            if (del_nextRow.dataset.is_not_edited) {
                createDialogWindow(status='error', description=['Эту строку удалить нельзя, т.к. вложенный элемент нельзя удалить']);
                del_no_del_status = 1;
                return;
            }
            del_row_cnt++;
            del_children_list.add(del_nextRow.id);
            //document.URL.split('/contract-list/card/').length > 1? del_list_undistributedCost.add(del_nextRow):false;
            del_list_undistributedCost.add(del_nextRow);
        }
        else {
            break;
        }
        var del_nextRow = del_nextRow.nextElementSibling;
        if (!del_nextRow) {
            break;
        }
    }

    //Удаляем всё найденное, пересчитываем нераспределенный остаток
    if (!del_no_del_status) {
        //Пересчет нераспределенного остатка
        if (document.URL.split('/contract-list/card/').length > 1) {
            for (let i of del_list_undistributedCost) {
                checkParentOrChildCost(i, percent=false, input_cost=false, subtraction=true);
            }
        }
        else if (document.URL.split('/objects/').length > 1) {
            let del_undistributedCost = 0; //Стоимость всех распределений удаляемых строк
            for (let i of del_list_undistributedCost) {
                del_undistributedCost += parseFloat(i.querySelectorAll(".tow_cost")[0].dataset.value? i.querySelectorAll(".tow_cost")[0].dataset.value:0);
            }
            if (del_undistributedCost) {
                //Последнее значение
                let del_undistributed = document.getElementById('id_div_milestones_contractCost').dataset.contract_cost;
                //Прибавляем удалённые строки
                del_undistributed = parseFloat(del_undistributed) - del_undistributedCost
                document.getElementById('id_div_milestones_contractCost').dataset.contract_cost = del_undistributed;
                //Вызываем функцию визуального пересчета средств
                recalculateContractCost(del_undistributed)
            }
        }
        //Удаление строк
        for (var i=0; i<del_row_cnt; i++) {
            tab.deleteRow(rowNumber);
        }

        if (tab.rows.length > 1) {
            var highestRow_id = tab.getElementsByTagName('tbody')[0].getElementsByTagName("tr")[rowNumber-1];
            if (!highestRow_id) {
                highestRow_id = tab.getElementsByTagName('tbody')[0].getElementsByTagName("tr")[rowNumber-1-del_row_cnt]
                if (!highestRow_id) {
                    highestRow_id = tab.getElementsByTagName('tbody')[0].getElementsByTagName("tr")[rowNumber-2]
                }
            }
            let highestRow_id_id = highestRow_id.id;
            highestRow = [rowNumber, highestRow_id_id];
            if (userChanges[highestRow_id_id]) {
                userChanges[highestRow_id_id]['lvl'] = rowNumber;
            }
            else {
                userChanges[highestRow_id_id] ={lvl: rowNumber};
            }

        }
        else {
            //Т.к. таблица tow опустела, обнуляем значение верхней tow
            highestRow = [];
        }
    }
    else {
        createDialogWindow(status='error', description=['Невозможно удалить желаемую структуру, есть запрещенные для удаления строки']);
    }

    //Обновляем список удаляемых строк
    deletedRowList = deletedRowList.union(del_children_list)

    //Если в таблице не осталось строк, добавляем кнопку "создать строку"
    if (tab.rows.length == 1) {
        var tab_tr0 = tab.getElementsByTagName('tbody')[0];
        var row = tab_tr0.insertRow(0);

        row.className = "div_tow_first_row";

            var td = row.insertCell(0);
            td.className = "div_tow_first_cell";
            td.colSpan = 3;

                var buttonFirstRow = document.createElement("button");
                buttonFirstRow.className = "button_tow_first_cell";
                buttonFirstRow.addEventListener('click', function() {FirstRow();});
                buttonFirstRow.innerHTML = "+ Начать создание состава работ"

            td.appendChild(buttonFirstRow);

        row.appendChild(td);
    }

    if (document.URL.split('/objects/').length > 1) {
        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow();
        }
    }
    else {
        isEditContract();
    }
}

function addButtonsForNewRow(div_tow_button, createNewRow=false) {
    //В зависимости от того, новая ячейка или скопированная, работают разные сценарии
    let newRow = div_tow_button;
    if (createNewRow) {
        let all_button = [
            {class:"tow addTowBefore", onclick:"addTow(this, 'Before')", title:"Скопировать структуру над текущей строкой", src:"/static/img/object/tow/addTow-Before.svg", hidden:0},
            {class:"tow addTowAfter", onclick:"addTow(this, 'After')", title:"Скопировать структуру под структурой текущей строки", src:"/static/img/object/tow/addTow-After.svg", hidden:0},
            {class:"tow_delTow", onclick:"delTow(this)", data_del:"1", title:"Удалить вид работ со всеми вложениями", src:"/static/img/object/tow/delete-tow.svg", hidden:0},
            {class:"tow shiftTowLeft", onclick:"shiftTow(this, 'Left')", title:"Сдвинуть структуру влево", src:"/static/img/object/tow/shiftTow-Left.svg", hidden:0},
            {class:"tow shiftTowRight", onclick:"shiftTow(this, 'Right')", title:"Сдвинуть структуру вправо", src:"/static/img/object/tow/shiftTow-Right.svg", hidden:0},
            {class:"tow shiftTowUp", onclick:"shiftTow(this, 'Up')", title:"Переместить структуру вверх", src:"/static/img/object/tow/shiftTow-Up.svg", hidden:0},
            {class:"tow shiftTowDown", onclick:"shiftTow(this, 'Down')", title:"Переместить структуру вниз", src:"/static/img/object/tow/shiftTow-Down.svg", hidden:0},
            {class:"tow addTowNew", onclick:"addTow(this, 'New')", title:"Добавить дочерний вид работ", src:"/static/img/object/tow/addTow-New.svg", hidden:0},
        ];
        all_button.forEach(button => {
            let buttonElement = document.createElement("button");
            buttonElement.className = button['class'];

            buttonElement.setAttribute("title", button['title']);

            button['data_del']? buttonElement.setAttribute("data-is_not_edited", button['data_del']):'';

            buttonElement.hidden = button['hidden'];

            let imgElement = document.createElement("img");
            imgElement.src = button['src'];

            buttonElement.appendChild(imgElement);
            div_tow_button.appendChild(buttonElement);
        })
    }
    else {
        let input_tow_name = newRow.getElementsByClassName('input_tow_name')[0];
        input_tow_name.addEventListener('change', function() {editDescription(this, 'input_tow_name');})

        let tow_dept = newRow.getElementsByClassName('tow_dept')[0];
        tow_dept.addEventListener('change', function() {editDescription(this, 'select_tow_dept');});

        let tow_time_tracking = newRow.getElementsByClassName('tow_time_tracking')[0];
        tow_time_tracking? tow_time_tracking.addEventListener('change', function() {editDescription(this, 'checkbox_time_tracking');}):'';
    }
    let addTowBefore = newRow.getElementsByClassName('addTowBefore')[0];
    addTowBefore.addEventListener('click', function() {addTow(this, 'Before');});

    let addTowAfter = newRow.getElementsByClassName('addTowAfter')[0];
    addTowAfter.addEventListener('click', function() {addTow(this, 'After');});

    let towDelTow = newRow.getElementsByClassName('tow_delTow')[0];
    towDelTow.addEventListener('click', function() {delTow(this);});

    let shiftTowLeft = newRow.getElementsByClassName('shiftTowLeft')[0];
    shiftTowLeft.addEventListener('click', function() {shiftTow(this, 'Left');});

    let shiftTowRight = newRow.getElementsByClassName('shiftTowRight')[0];
    shiftTowRight.addEventListener('click', function() {shiftTow(this, 'Right');});

    let shiftTowUp = newRow.getElementsByClassName('shiftTowUp')[0];
    shiftTowUp.addEventListener('click', function() {shiftTow(this, 'Up');});

    let shiftTowDown = newRow.getElementsByClassName('shiftTowDown')[0];
    shiftTowDown.addEventListener('click', function() {shiftTow(this, 'Down');});

    let addTowNew = newRow.getElementsByClassName('addTowNew')[0];
    addTowNew.addEventListener('click', function() {addTow(this, 'New');});
}

function setNewRowTowFunc(sNRTF_cell=false, sNRTF_row=false) {
    // Добавляем функцию пересчёта детей и родителей в разделе TOW
    //if (document.URL.split('/objects/').length > 1) {
        //        let tow = newRow.closest('tr');
        if (sNRTF_row) {
            sNRTF_cell = sNRTF_row.querySelector('.tow_cost');
        }

        sNRTF_cell.addEventListener('focusin', function() {convertProjectTowCost(this, 'in');});
        sNRTF_cell.addEventListener('focusout', function() {convertProjectTowCost(this, 'out');});
        sNRTF_cell.addEventListener('change', function() {checkParentOrChildProjectCost(this);});
    //}
}

function mergeTowRow (cell) {
    let row = cell.closest('tr')
    let edit_btn = document.getElementById("edit_btn");

    document.getElementById("mergeTowRowButton")? document.getElementById("mergeTowRowButton").style.display = "none":'';

    // Если включён режим редактирования, то слияние отменяем
    if (edit_btn.hidden) {
        return;
    }
    let tow_list = $('.mergeTowRow');
    // Если выбрана одна строка, проверяем что вторая строка пригодна для слияния пары (Договор + НЕ договор)
    if (tow_list.length == 1  && tow_list[0] != cell) {
        if (tow_list[0].dataset.is_not_edited && cell.dataset.is_not_edited || !tow_list[0].dataset.is_not_edited && !cell.dataset.is_not_edited) {
            return;
        }
    }

    //Проверяем, что выбранный tow не вновь созданный (id - число). Такое не возможно, т.к. в режиме редактирования нельзя сливать tow
    if (!Number.isInteger(parseInt(row.id))) {
        return;
    }

    // Если строка была выбрана раньше - снимаем выделение
    if (row.classList.contains('mergeTowRow')) {
        return row.classList.remove("mergeTowRow");
    }

    // Если выбрано две строки - ничего не делаем
    if ($('.mergeTowRow').length > 1) {
        return;
    }

    // Если страка не была выбрана - выбираем строку
    if (!row.classList.contains('mergeTowRow')) {
        row.classList.add("mergeTowRow");
    }


    // Если выбрано две строки и всё ОК, отображаем "ВОЗМОЖНОСТЬ" слияния двух строк
    if ($('.mergeTowRow').length == 2) {
        document.getElementById("mergeTowRowButton")? document.getElementById("mergeTowRowButton").style.display = "flex":'';
    }
}

function showSaveMergeTowRowDialogWindow() {
    //Проверка, что функция вызвана с листа виды работ объекта договора
    if (document.URL.split('/objects/').length < 2) {
        return false;
    }
    let tow_list = $('.mergeTowRow');
    if (tow_list.length != 2) {
        return createDialogWindow(status='error', description=['Выберите два вида работ и повторите попытку']);
    }
    let contract_tow = false;
    let raw_tow = false;

    if (tow_list[0].dataset.is_not_edited) {
        contract_tow = [tow_list[0].id, tow_list[0].getElementsByClassName("input_tow_name")[0].value];
        raw_tow = [tow_list[1].id, tow_list[1].getElementsByClassName("input_tow_name")[0].value];
    }
    else if (tow_list[1].dataset.is_not_edited) {
        contract_tow = [tow_list[1].id, tow_list[1].getElementsByClassName("input_tow_name")[0].value];
        raw_tow = [tow_list[0].id, tow_list[0].getElementsByClassName("input_tow_name")[0].value];
    }
    else {
        return createDialogWindow(status='error', description=['Ошибка выбора видов работ', 'Обновите страницу и попробуй снова']);
    }
    return createDialogWindow(status='info',
            description=['Подтвердите слияние видов работ',
                        `Вид работ (id: ${raw_tow[0]}) "${raw_tow[1]}"`,
                        "Преобразуется в:",
                        `Вид работ (id: ${contract_tow[0]}) "${contract_tow[1]}"`],
            func=[['click', [SaveMergeTowRow, [contract_tow[0], raw_tow[0]]]]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ',
                },
            ],
            text_comment = false,
            );
}

function SaveMergeTowRow([contract_tow_id=false, raw_tow_id=false]) {
    fetch(`/merge_tow_row/${contract_tow_id}/${raw_tow_id}`, {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": '',
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.url;
            } else {
                return createDialogWindow(status='error', description=['Ошибка', data.description]);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            return createDialogWindow(status='error', description=['Ошибка rev.2', error.toString() + '________________']);
        });
}