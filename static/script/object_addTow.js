$(document).ready(function() {
    var page_url = document.URL;
    if (document.URL.split('/objects/').length > 1) {
        var edit_btn = document.getElementById("edit_btn");
        edit_btn.addEventListener('click', function() {editTow();});

    }
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");

    if (document.URL.split('/contract-acts-list').length > 1) {
        save_btn.addEventListener('click', function() {saveAct();});
        cancel_btn.addEventListener('click', function() {cancelTowChanges();});
    }
    else {
        save_btn.addEventListener('click', function() {saveTowChanges();});
        cancel_btn.addEventListener('click', function() {cancelTowChanges();});
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

            if (document.URL.split('/objects/').length > 1) {
                //**************************************************
                // row

                row.className = "lvl-0";
                row.setAttribute("data-lvl", "0");
                row.setAttribute("data-del", "1");
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
                        //input_tow_name.readOnly = true;
                    div_tow_name.appendChild(input_tow_name);
                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_tow_button";
                    addButtonsForNewRow(div_tow_button, createNewRow=true);
                tow_name.appendChild(div_tow_name);
                tow_name.appendChild(div_tow_button);

                //**************************************************
                // Отдел
                var tow_dept = row.insertCell(1);
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

                //**************************************************
                // Учёт часов
                var tow_time_tracking = row.insertCell(2);
                tow_time_tracking.className = "tow_time_tracking";

                var checkbox = document.createElement('input');
                checkbox.type = "checkbox";
                checkbox.className = "checkbox_time_tracking";
                //checkbox.disabled  = 1;
                tow_time_tracking.appendChild(checkbox);
                tow_time_tracking.addEventListener('click', function() {editDescription(this, 'checkbox_time_tracking');});
            }
            else {
                //**************************************************
                // row

                row.className = "lvl-0";
                row.setAttribute("data-lvl", "0");
                row.setAttribute("data-del", "1");
                row.setAttribute("data-tow_cnt", "0");
                row.setAttribute("data-value_type", "");
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

                //**************************************************
                // Выбор tow
                let cellCheckbox = row.insertCell(1);
                cellCheckbox.className = "tow_contract";
                    let checkbox = document.createElement('input');
                    checkbox.type = "checkbox";
                    checkbox.className = "checkbox_time_tracking";
                cellCheckbox.appendChild(checkbox);

                //**************************************************
                // Отдел
                let tow_dept = row.insertCell(2);
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

                //**************************************************
                // Сумма
                let cost = row.insertCell(3);
                cost.className = "cost";
                    let tow_cost = document.createElement('input');
                    tow_cost.type = "text";
                    tow_cost.classList.add("tow_cost", "calc");
                    tow_cost.setAttribute("data-value", null);
                cost.appendChild(tow_cost);

                //**************************************************
                // % сумма
                let cost_percent = row.insertCell(4);
                cost_percent.className = "cost_percent";
                    let tow_cost_percent = document.createElement('input');
                    tow_cost_percent.type = "text";
                    tow_cost_percent.classList.add("tow_cost_percent", "calc");
                    tow_cost_percent.setAttribute("data-value", null);
                cost_percent.appendChild(tow_cost_percent);

                //**************************************************
                // Сумма ФОТ
                let fot_cost = row.insertCell(5);
                fot_cost.className = "fot_cost";
                    let tow_fot_cost = document.createElement('input');
                    tow_fot_cost.type = "text";
                    tow_fot_cost.className = "tow_fot_cost";
                    tow_fot_cost.setAttribute("data-value", null);
                    tow_fot_cost.disabled = true;
                fot_cost.appendChild(tow_fot_cost);

                //**************************************************
                // Субп. проекта
                let subcontractor_cost = row.insertCell(6);
                subcontractor_cost.className = "subcontractor_cost";
                    let tow_subcontractor_cost = document.createElement('input');
                    tow_subcontractor_cost.type = "text";
                    tow_subcontractor_cost.className = "tow_subcontractor_cost";
                    tow_subcontractor_cost.setAttribute("data-value", null);
                    tow_subcontractor_cost.disabled = true;
                subcontractor_cost.appendChild(tow_subcontractor_cost);

                //**************************************************
                // Начало
                let date_start = row.insertCell(7);
                date_start.className = "date_start";
                    let tow_date_start = document.createElement('input');
                    tow_date_start.type = "text";
                    tow_date_start.className = "tow_date_start";
                    tow_date_start.setAttribute("data-value", null);
                date_start.appendChild(tow_date_start);

                //**************************************************
                // Окончание
                let date_finish = row.insertCell(8);
                date_finish.className = "date_finish";
                    let tow_date_finish = document.createElement('input');
                    tow_date_finish.type = "text";
                    tow_date_finish.className = "tow_date_finish";
                    tow_date_finish.setAttribute("data-value", null);
                date_finish.appendChild(tow_date_finish);

//                // Добавляем функции в ячейки
//                setNewRowContractFunc(row);
//                addButtonsForNewRow(row);

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
            // Если страница договора, то добавляем функции в ячейки
            if (document.URL.split('/contract-list/card/').length > 1) {
                setNewRowContractFunc(row);
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

    if (route === 'New') {
        if (cur_lvl+1 > 10) {
            return createDialogWindow(status='error', description=['Ошибка', `Превышена максимальная глубина вложенности - ${nextRow}`]);
        }

        newRow.className = 'lvl-' + (cur_lvl+1);

        // Очищаем все поля в новой строке
        if (newRow) {
            var textInputs = newRow.querySelectorAll('input[type="text"]');
            textInputs.forEach(function (input) {
                input.value = '';
                //input.readOnly = true;
            });

            var checkbox = newRow.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = false;
                //checkbox.disabled  = 1;
            }

            //var select_tr = newRow.querySelectorAll('select');
            //select_tr.forEach(slc => {
            //    slc.disabled = 1;
            //});
        }
        //Создаём временное id для новой tow
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime()
        if (!row.nextElementSibling) {
            row.parentNode.appendChild(newRow);
        }
        else {
            row.parentNode.insertBefore(newRow, nextRow);
        }

        //Добавляем изменение - Создание новой строки
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=row.id, c_row=newRow); // New - new row
        // Настраиваем кнопки
        addButtonsForNewRow(newRow);
        // Если страница договора, то добавляем функции в ячейки
        if (document.URL.split('/contract-list/card/').length > 1) {
            setNewRowContractFunc(newRow);
            clearDataAttributeValue(newRow);
            isEditContract();
            return;
        }

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
        checkbox.checked = false;
    }


    // Список создаваемых строк
    var children_list = [];

    //Если копируем структуру вверх
    if (route === 'Before') {
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
                    checkbox.checked = false;
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
                    checkbox.checked = false;
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
    if (document.URL.split('/contract-list/card/').length > 1) {
        var del_list_undistributedCost = new Set([row]);
    }

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
            document.URL.split('/contract-list/card/').length > 1? del_list_undistributedCost.add(del_nextRow):false;
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
                undistributedCost(i, percent=false, input_cost=false, subtraction=true);
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

//            buttonElement.addEventListener('click', function() {button['onclick'];});
            buttonElement.setAttribute("title", button['title']);

            button['data_del']? buttonElement.setAttribute("data-del", button['data_del']):'';

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
//    }
}