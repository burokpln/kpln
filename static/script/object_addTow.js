$(document).ready(function() {
    var edit_btn = document.getElementById("edit_btn");
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");

    edit_btn.setAttribute("onclick", "editTow()");
    save_btn.setAttribute("onclick", "saveTowChanges()");
    cancel_btn.setAttribute("onclick", "cancelTowChanges()");
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

            //Список кнопок
            var all_button = [
                //{class:"tow", onclick:"editDescription(this)", title:"Редактировать название", src:"/static/img/object/tow/icon-edit-pen.svg", hidden:0},
                //{class:"tow", onclick:"saveDescription(this)", title:"Сохранить изменение", src:"/static/img/object/tow/icon-ok.svg", hidden:1},
                //{class:"tow", onclick:"undoEditDescr(this)", title:"Отменить изменение", src:"/static/img/object/tow/icon-ok.svg", hidden:1},
                {class:"tow", onclick:"addTow(this, 'Before')", title:"Скопировать структуру над текущей строкой", src:"/static/img/object/tow/addTow-Before.svg", hidden:0},
                {class:"tow", onclick:"addTow(this, 'After')", title:"Скопировать структуру под структурой текущей строки", src:"/static/img/object/tow/addTow-After.svg", hidden:0},
                {class:"tow_delTow", onclick:"delTow(this)", data_del:"1", title:"Удалить вид работ со всеми вложениями", src:"/static/img/object/tow/delete-tow.svg", hidden:0},
                {class:"tow", onclick:"shiftTow(this, 'Left')", title:"Сдвинуть структуру влево", src:"/static/img/object/tow/shiftTow-Left.svg", hidden:0},
                {class:"tow", onclick:"shiftTow(this, 'Right')", title:"Сдвинуть структуру вправо", src:"/static/img/object/tow/shiftTow-Right.svg", hidden:0},
                {class:"tow", onclick:"shiftTow(this, 'Up')", title:"Переместить структуру вверх", src:"/static/img/object/tow/shiftTow-Up.svg", hidden:0},
                {class:"tow", onclick:"shiftTow(this, 'Down')", title:"Переместить структуру вниз", src:"/static/img/object/tow/shiftTow-Down.svg", hidden:0},
                {class:"tow", onclick:"addTow(this, 'New')", title:"Добавить дочерний вид работ", src:"/static/img/object/tow/addTow-New.svg", hidden:0},
            ];

            const tab = document.getElementById("towTable");
            var tab_tr0 = tab.getElementsByTagName('tbody')[0];
            tab.deleteRow(1);
            var row = tab_tr0.insertRow(0);

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
                    input_tow_name.setAttribute("onclick", "editDescription(this, 'input_tow_name')")
                    //input_tow_name.readOnly = true;
                div_tow_name.appendChild(input_tow_name);
                var div_tow_button = document.createElement('div');
                div_tow_button.className = "div_tow_button";
                    all_button.forEach(button => {
                        // Create the <button> element
                        var buttonElement = document.createElement("button");
                        buttonElement.className = button['class'];

                        buttonElement.setAttribute("onclick", button['onclick']);
                        buttonElement.setAttribute("title", button['title']);

                        if (button['data_del']) {
                            buttonElement.setAttribute("data-del", button['data_del']);
                        }

                        buttonElement.hidden = button['hidden'];

                        // Create the <img> element
                        var imgElement = document.createElement("img");
                        imgElement.src = button['src'];

                        // Append the <img> element inside the <button> element
                        buttonElement.appendChild(imgElement);

                        // Append the <button> element to the parent element
                        div_tow_button.appendChild(buttonElement);
                    })

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
            tow_dept.setAttribute("onclick", "editDescription(this, 'select_tow_dept')")

            //**************************************************
            // Учёт часов
            var tow_time_tracking = row.insertCell(2);
            tow_time_tracking.className = "tow_time_tracking";

            var checkbox = document.createElement('input');
            checkbox.type = "checkbox";
            checkbox.className = "checkbox_time_tracking";
            //checkbox.disabled  = 1;
            tow_time_tracking.appendChild(checkbox);
            tow_time_tracking.setAttribute("onclick", "editDescription(this, 'checkbox_time_tracking')")

            //Добавляем изменение - Создание новой строки
            UserChangesLog(c_id=row.id, rt='New', u_p_id='', c_row=row);

        }
        else if (data.status === 'error') {
            alert(data.description)
        }
        })
        .catch(error => {
            console.error('Error:', error);
        });
};

//Создание новой строки или копирование структуры строк
function addTow(button, route) {
    if  (!['Before', 'After', 'New'].includes(route)) {
        alert('Направление копирования структуры видов работ задано неверно');
        return
    }
    var row = button.closest('tr');
    var className = row.className;
    var cur_lvl = parseInt(className.split('lvl-')[1])
    var newRow = row.cloneNode(true);

    //отображаем кнопку "удалить tow"
    if (row.dataset.del == "0") {
        newRow.setAttribute("data-del", "1");
        var tow_delTow = newRow.querySelector(".tow_delTow");
        tow_delTow.setAttribute("data-del", "1");
    }

    var input_tow_name = newRow.getElementsByClassName("input_tow_name")[0];
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

    // Удалить переменную, как всё будет готово
    var rowIndex = Array.from(currentRow.parentNode.children).indexOf(currentRow);

    if (route === 'New') {
        if (cur_lvl+1 > 10) {
            alert(`Превышена максимальная глубина вложенности - ${nextRow}`);
            return
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
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=row.id, c_row=newRow);

        //Включаем режим редактирования, если не был включён
        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow()
        }
        return;
    }

    // Очищаем input всех создаваемых строк
    var textInputs = newRow.querySelectorAll('input[type="text"]');
    textInputs.forEach(function (input) {
        input.value = '';
        //input.readOnly = 1;
    });
    //    // Очищаем checkbox всех создаваемых строк
    //    var checkbox = newRow.querySelector('input[type="checkbox"]');
    //    if (checkbox) {
    //        checkbox.checked = false;
    //        //checkbox.disabled  = 1;
    //    }
    //var select_tr = newRow.querySelectorAll('select');
    //select_tr.forEach(slc => {
        //slc.disabled = 1;
    //});


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
                if (row.dataset.del == "0") {
                    child.setAttribute("data-del", "1");
                    var tow_delTow = newRow.querySelector(".tow_delTow");
                    tow_delTow.setAttribute("data-del", "1");
                }

                // Очищаем input всех создаваемых строк
                var textInputs = child.querySelectorAll('input[type="text"]');
                textInputs.forEach(function (input) {
                    input.value = '';
                    //input.readOnly = 1;
                });
                //                // Очищаем checkbox всех создаваемых строк
                //                var checkbox = child.querySelector('input[type="checkbox"]');
                //                if (checkbox) {
                //                    checkbox.checked = false;
                //                    //checkbox.disabled  = 1;
                //                }
                children_list.push(child)
            }
            nextRow = nextRow.nextElementSibling;
        }

        //Создаём временное id для новой tow и вставляем tow над текущей строкой
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime();
        row.parentNode.insertBefore(newRow, row);
            //Проходим по списку детей
            for (var i=0; i<children_list.length; i++) {
                tow = children_list[i];
                //Создаём временное id для каждого ребенка
                tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
                var child_lvl = parseInt(tow.className.split('lvl-')[1])
                newRow.parentNode.insertBefore(tow, row);

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
                UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow);
                editDescription(button='', type='select_tow_dept', editDescription_row=tow);
                editDescription(button='', type='checkbox_time_tracking', editDescription_row=tow);
            }

        //Определяем родителя скопированного родителя
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        //Записываем все изменения для родителя
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=p_id, c_row=newRow);
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
                if (row.dataset.del == "0") {
                    child.setAttribute("data-del", "1");
                    var tow_delTow = newRow.querySelector(".tow_delTow");
                    tow_delTow.setAttribute("data-del", "1");
                }

                // Очищаем input всех создаваемых строк
                var textInputs = child.querySelectorAll('input[type="text"]');
                textInputs.forEach(function (input) {
                    input.value = '';
                    //input.readOnly = 1;
                });
                //                // Очищаем checkbox всех создаваемых строк
                //                var checkbox = child.querySelector('input[type="checkbox"]');
                //                if (checkbox) {
                //                    checkbox.checked = false;
                //                    //checkbox.disabled  = 1;
                //                }
                children_list.push(child)
                nextRow = nextRow.nextElementSibling;
            }
        }

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
                //Проходим по списку детей
                for (var i=0; i<children_list.length; i++) {
                    tow = children_list[i];
                    //Создаём временное id для каждого ребенка
                    tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
                    var child_lvl = parseInt(tow.className.split('lvl-')[1])
                    newRow.parentNode.insertBefore(tow, nextRow);

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
                    UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow);
                    editDescription(button='', type='select_tow_dept', editDescription_row=tow);
                    editDescription(button='', type='checkbox_time_tracking', editDescription_row=tow);
                }
            }
            //В структуре нет детей, просто вставляем копию под текущую строку
            else {
                nextRow.parentNode.insertBefore(newRow, row.nextSibling);
            }
            var newRow_lvl = parseInt(newRow.className.split('lvl-')[1]);

        }
        //После копируемой структуры нет срок (конец таблицы)
        else {
            row.parentNode.appendChild(newRow);
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
                    UserChangesLog(c_id=tow.id, rt='New', u_p_id=p_id, c_row=tow);
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
        UserChangesLog(c_id=newRow.id, rt=route, u_p_id=p_id, c_row=newRow);
        editDescription(button='', type='select_tow_dept', editDescription_row=newRow);
        editDescription(button='', type='checkbox_time_tracking', editDescription_row=newRow);
    }

    var edit_btn = document.getElementById("edit_btn");
    if (!edit_btn.hidden) {
        editTow()
    }
}

//Удаление структуры
function delTow(button) {
    var row = button.closest('tr');
    var del_no_del_status = 0;

    if (row.dataset.del == "0") {
        alert('Эту строку удалить нельзя');
        del_no_del_status = 1;
        return;
    }

    var rowNumber = row.rowIndex;
    var className = row.className;
    var cur_lvl = parseInt(className.split('lvl-')[1]);

    const tab = document.getElementById("towTable");

    var del_children_list = new Set([row.id]);  //Список удаляемых tow
    var del_row_cnt = 1;  //Счётчик удаляемых tow
    var del_nextRow = row.nextElementSibling;  //Следующая строка

    //Проверяем, есть ли не удаляемые дети
    while (del_nextRow || true) {
        var del_child_lvl = parseInt(del_nextRow.className.split('lvl-')[1]);

        if (del_child_lvl > cur_lvl) {
            if (del_nextRow.dataset.del == '0') {
                alert('Эту строку удалить нельзя, т.к. вложенный элемент нельзя удалить');
                del_no_del_status = 1;
                return;
            }
            del_row_cnt++;
            del_children_list.add(del_nextRow.id);
        }
        else {
            break;
        }
        var del_nextRow = del_nextRow.nextElementSibling;
        if (!del_nextRow) {
            break;
        }
    }

    //Если нет запрета на удаление строк, то удаляем всё найденное
    if (!del_no_del_status) {
        for (var i=0; i<del_row_cnt; i++) {
            tab.deleteRow(rowNumber);
        }
        var highestRow_id = tab.getElementsByTagName('tbody')[0].getElementsByTagName("tr")[rowNumber-1];
        highestRow = [rowNumber, highestRow_id.id];
        userChanges[highestRow_id.id] = {lvl: rowNumber};
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
                buttonFirstRow.setAttribute("onclick", "FirstRow()");
                buttonFirstRow.innerHTML = "+ Начать создание состава работ"

            td.appendChild(buttonFirstRow);

        row.appendChild(td);
    }

    var edit_btn = document.getElementById("edit_btn");
    if (!edit_btn.hidden) {
        editTow()
    }

}
