$(document).ready(function() {
    var page_url = document.URL;
    var edit_btn = document.getElementById("edit_btn");
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");
    var full_view_btn_show = document.getElementById("full_view_btn_show");
    var full_view_btn_hide = document.getElementById("full_view_btn_hide");
    var full_view_creative_mode_on_btn = document.getElementById("full_view_creative_mode_on_btn");
    var full_view_creative_mode_off_btn = document.getElementById("full_view_creative_mode_off_btn");
    var creative_mode_on_btn = document.getElementById("creative_mode_on_btn");
    var creative_mode_off_btn = document.getElementById("creative_mode_off_btn");
    var proj_info_layout = document.getElementById('proj-info_layout');
    var button_tow_first_cell = document.getElementsByClassName("button_tow_first_cell")[0];

    edit_btn? edit_btn.addEventListener('click', function() {editTaskTable();}):'';
    full_view_btn_show? full_view_btn_show.addEventListener('click', function() {showFullTaskTable();}):'';
    full_view_btn_hide? full_view_btn_hide.addEventListener('click', function() {hideFullTaskTable();}):'';
    full_view_btn_hide.style.display = "none";

    full_view_creative_mode_on_btn? full_view_creative_mode_on_btn.addEventListener('click', function() {creativeModeOn();}):'';
    full_view_creative_mode_off_btn? full_view_creative_mode_off_btn.addEventListener('click', function() {creativeModeOff();}):'';
    creative_mode_on_btn? creative_mode_on_btn.addEventListener('click', function() {creativeModeOn();}):'';
    creative_mode_off_btn? creative_mode_off_btn.addEventListener('click', function() {creativeModeOff();}):'';
    creative_mode_off_btn.style.display = "none";
    full_view_creative_mode_on_btn.style.display = "none";
    full_view_creative_mode_off_btn.style.display = "none";

    button_tow_first_cell? button_tow_first_cell.addEventListener('click', function() {FirstTaskRow();}):'';
});

const proj_url = decodeURI(document.URL.split('/')[4]);  //Название проекта
let userChanges = {};  //Список изменений tow пользователем
let newRowList = new Set();  //Список новых tow
let deletedRowList = new Set();  //Список удаленных tow
let editDescrRowList = {};  //Список изменений input tow
let highestRow = [];  //Самая верхняя строка с которой "поедет" вся нумерация строк
let reservesChanges = {};  //Список изменений резервов

function hideFullTaskTable() {
    const full_view_btn_show = document.getElementById("full_view_btn_show");
    const full_view_btn_hide = document.getElementById("full_view_btn_hide");
    const proj_info_layout = document.getElementById('proj-info_layout');

    const full_view_creative_mode_on_btn = document.getElementById("full_view_creative_mode_on_btn");
    const full_view_creative_mode_off_btn = document.getElementById("full_view_creative_mode_off_btn");
    const creative_mode_on_btn = document.getElementById("creative_mode_on_btn");
    const creative_mode_off_btn = document.getElementById("creative_mode_off_btn");

    full_view_btn_hide.style.display = "none";
    full_view_btn_show.style.display = "inline-block";
    proj_info_layout.style.display = "block";

    const full_view_creative_mode_on_btn_style_display = full_view_creative_mode_on_btn.style.display;
    const full_view_creative_mode_off_btn_style_display = full_view_creative_mode_off_btn.style.display;
    creative_mode_on_btn.style.display = full_view_creative_mode_on_btn_style_display;
    creative_mode_off_btn.style.display = full_view_creative_mode_off_btn_style_display;
    full_view_creative_mode_on_btn.style.display = "none";
    full_view_creative_mode_off_btn.style.display = "none";

    document.getElementsByClassName("qqqq")[0].style.maxHeight="calc(100vh - 141px)";
    // document.getElementsByTagName("main")[0].style.paddingTop ="100px";
}

function showFullTaskTable() {
    const full_view_btn_show = document.getElementById("full_view_btn_show");
    const full_view_btn_hide = document.getElementById("full_view_btn_hide");
    const proj_info_layout = document.getElementById('proj-info_layout');

    const full_view_creative_mode_on_btn = document.getElementById("full_view_creative_mode_on_btn");
    const full_view_creative_mode_off_btn = document.getElementById("full_view_creative_mode_off_btn");
    const creative_mode_on_btn = document.getElementById("creative_mode_on_btn");
    const creative_mode_off_btn = document.getElementById("creative_mode_off_btn");

    full_view_btn_hide.style.display = "inline-block";
    full_view_btn_show.style.display = "none";
    proj_info_layout.style.display = "none";

    const creative_mode_on_btn_style_display = creative_mode_on_btn.style.display;
    const creative_mode_off_btn_style_display = creative_mode_off_btn.style.display;
    full_view_creative_mode_on_btn.style.display = creative_mode_on_btn_style_display;
    full_view_creative_mode_off_btn.style.display = creative_mode_off_btn_style_display;
    creative_mode_on_btn.style.display = "none";
    creative_mode_off_btn.style.display = "none";

    document.getElementsByClassName("qqqq")[0].style.maxHeight="calc(100vh - 111px)";
    // document.getElementsByTagName("main")[0].style.paddingTop ="56px";
}

function creativeModeOn() {
    console.log('включаем creativeModeOn')
    let div_task_button_hidden = $('.div_task_button_hidden');

    if (div_task_button_hidden.length) {
        console.log(div_task_button_hidden[0].classList)
        div_task_button_hidden.toArray().forEach(function (button) {
            button.className = 'div_tow_button';
        });
    }

    const full_view_btn_show = document.getElementById("full_view_btn_show").style.display;
    const full_view_btn_hide = document.getElementById("full_view_btn_hide").style.display;

    var full_view_creative_mode_on_btn = document.getElementById("full_view_creative_mode_on_btn");
    var full_view_creative_mode_off_btn = document.getElementById("full_view_creative_mode_off_btn");
    var creative_mode_on_btn = document.getElementById("creative_mode_on_btn");
    var creative_mode_off_btn = document.getElementById("creative_mode_off_btn");
    if (full_view_btn_show === "none") {
        full_view_creative_mode_on_btn.style.display = "none";
        full_view_creative_mode_off_btn.style.display = "inline-block";
    }
    else if (full_view_btn_hide === "none") {
        creative_mode_on_btn.style.display = "none";
        creative_mode_off_btn.style.display = "inline-block";
    }

    isEditTaskTable();
}

function creativeModeOff() {
    console.log('   _ отключаем creativeModeOff')
    let div_tow_button = $('.div_tow_button');

    if (div_tow_button.length) {
        console.log(div_tow_button[0].classList)
        div_tow_button.toArray().forEach(function (button) {
            button.className = 'div_task_button_hidden';
        });
    }

    const full_view_btn_show = document.getElementById("full_view_btn_show").style.display;
    const full_view_btn_hide = document.getElementById("full_view_btn_hide").style.display;

    var full_view_creative_mode_on_btn = document.getElementById("full_view_creative_mode_on_btn");
    var full_view_creative_mode_off_btn = document.getElementById("full_view_creative_mode_off_btn");
    var creative_mode_on_btn = document.getElementById("creative_mode_on_btn");
    var creative_mode_off_btn = document.getElementById("creative_mode_off_btn");

    if (full_view_btn_show === "none") {
        full_view_creative_mode_on_btn.style.display = "inline-block";
        full_view_creative_mode_off_btn.style.display = "none";
    }
    else if (full_view_btn_hide === "none") {
        creative_mode_on_btn.style.display = "inline-block";
        creative_mode_off_btn.style.display = "none";
    }
}

function isEditTaskTable() {
    var edit_btn = document.getElementById("edit_btn");
    if (!edit_btn.hidden) {
        editTaskTable();
    }
}

function editTaskTable() {
    var edit_btn = document.getElementById("edit_btn");
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");
    if (edit_btn.hidden) {
        edit_btn.hidden = 0;
        save_btn.hidden = true;
        cancel_btn.hidden = true;
    }
    else {
        edit_btn.hidden = true;
        save_btn.hidden = 0;
        cancel_btn.hidden = 0;

        if (document.URL.split('/contract-list/card/').length > 1) {
            let input_tow_name = document.getElementsByClassName('input_tow_name');
            for (let i of input_tow_name) {
                i.disabled  = false;
            }
            let tow_dept = document.querySelectorAll(".select_tow_dept");
            for (let i of tow_dept) {
                i.disabled  = false;
            }
            if (document.URL.split('/contract-list/card/new/').length > 1) {
                contract_id = 'new';
            }
        }
        else if (document.URL.split('/contract-acts-list').length > 1) {
            // Разрешаем редактирования для некоторых полей в карточке акта
            var ctr_card_act_number = document.getElementById("ctr_card_act_number");
            ctr_card_act_number.disabled = false;
            var ctr_card_date_start = document.getElementById("ctr_card_date_start");
            ctr_card_date_start.disabled = false;
            var ctr_card_status_name = document.getElementById("ctr_card_status_name");
            ctr_card_status_name.disabled = false;
            var ctr_card_act_cost = document.getElementById("ctr_card_act_cost");
            ctr_card_act_cost.disabled = false;
        }
        else if (document.URL.split('/contract-payments-list').length > 1) {
            // Разрешаем редактирования для некоторых полей в карточке платежей
            document.getElementById("ctr_card_payment_number").disabled = false;
            document.getElementById("ctr_card_date_start").disabled = false;
            document.getElementById("ctr_card_payment_cost").disabled = false;
        }
    }

//    const tab = document.getElementById("towTable");
//    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
}

function taskSelectSearch2MouseOver(taskRow, cell) {
    console.log('mouseover', taskRow.getElementsByClassName(cell)[0]);
    $(taskRow.getElementsByClassName(cell)[0]).prop("disabled", false);
}

function taskSelectSearch2MouseOut(taskRow, cell) {
    console.log('mouseout', taskRow.getElementsByClassName(cell)[0]);
    $(taskRow.getElementsByClassName(cell)[0]).prop("disabled", true);
}

//Создаём первую задачу
function FirstTaskRow() {
    var tow_id = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    fetch(`/get_employees_list/employees_and_task_statuses/${tow_id}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {

            //Список данных для создания ячеек 4-х недели
            var td_task_labor_list_class = [
                ["td_task_labor_cost_sum_week", "td_task_labor_cost_sum_week_1"],
                ["td_task_labor_cost_week_day_1_day", "td_tow_week_1_day_1"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_2"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_3"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_4"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_5"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_6"],
                ["td_task_labor_cost_week_day", "td_tow_week_1_day_7"],
                ["td_task_labor_cost_sum_week", "td_task_labor_cost_sum_week_2"],
                ["td_task_labor_cost_week_day_1_day", "td_tow_week_2_day_1"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_2"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_3"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_4"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_5"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_6"],
                ["td_task_labor_cost_week_day", "td_tow_week_2_day_7"],
                ["td_task_labor_cost_sum_week", "td_task_labor_cost_sum_week_3"],
                ["td_task_labor_cost_week_day_1_day", "td_tow_week_3_day_1"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_2"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_3"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_4"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_5"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_6"],
                ["td_task_labor_cost_week_day", "td_tow_week_3_day_7"],
                ["td_task_labor_cost_sum_week", "td_task_labor_cost_sum_week_4"],
                ["td_task_labor_cost_week_day_1_day", "td_tow_week_4_day_1"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_2"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_3"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_4"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_5"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_6"],
                ["td_task_labor_cost_week_day", "td_tow_week_4_day_7"],
            ]

            var input_task_labor_list_class = [
                ["input_task_sum_week_1", "is_not_edited"],
                ["input_task_week_1_day_1", "is_not_edited"],
                ["input_task_week_1_day_2", "is_not_edited"],
                ["input_task_week_1_day_3", "is_not_edited"],
                ["input_task_week_1_day_4", "is_not_edited"],
                ["input_task_week_1_day_5", "is_not_edited"],
                ["input_task_week_1_day_6", "is_not_edited"],
                ["input_task_week_1_day_7", "is_not_edited"],
                ["input_task_sum_week_2", "is_not_edited"],
                ["input_task_week_2_day_1", "is_not_edited"],
                ["input_task_week_2_day_2", "is_not_edited"],
                ["input_task_week_2_day_3", "is_not_edited"],
                ["input_task_week_2_day_4", "is_not_edited"],
                ["input_task_week_2_day_5", "is_not_edited"],
                ["input_task_week_2_day_6", "is_not_edited"],
                ["input_task_week_2_day_7", "is_not_edited"],
                ["input_task_sum_week_3", "is_not_edited"],
                ["input_task_week_3_day_1", "is_not_edited"],
                ["input_task_week_3_day_2", "is_not_edited"],
                ["input_task_week_3_day_3", "is_not_edited"],
                ["input_task_week_3_day_4", "is_not_edited"],
                ["input_task_week_3_day_5", "is_not_edited"],
                ["input_task_week_3_day_6", "is_not_edited"],
                ["input_task_week_3_day_7", "is_not_edited"],
                ["input_task_sum_week_4", "is_not_edited"],
                ["input_task_week_4_day_1", "is_not_edited"],
                ["input_task_week_4_day_2", "is_not_edited"],
                ["input_task_week_4_day_3", "is_not_edited"],
                ["input_task_week_4_day_4", "is_not_edited"],
                ["input_task_week_4_day_5", "is_not_edited"],
                ["input_task_week_4_day_6", "is_not_edited"],
                ["input_task_week_4_day_7", "is_not_edited"],
            ]

            const tab = document.getElementById("towTable");
            var tab_tr0 = tab.getElementsByTagName('tbody')[0];
            tab.deleteRow(1);
                    for (var jj =0; jj< 30; jj++) {
            var row = tab_tr0.insertRow(0);
            var col_i = 0;

            //**************************************************
            // main_task

                        row.className = "lvl-0 main_task";
                        row.setAttribute("data-lvl", "0");
                        row.setAttribute("data-tow_cnt", "0");
                        row.setAttribute("data-value_type", "");
                        row.setAttribute("data-is_not_edited", '');
                        row.id = `_New_${new Date().getTime()}`;

                        //**************************************************
                        // Номер задачи
                        var td_task_number = row.insertCell(0);
                        td_task_number.classList.add("td_task_number", "sticky-cell", "col-1");
                        var input_task_number = document.createElement('input');
                        input_task_number.type = "text";
                        input_task_number.className = "input_task_number";
                        input_task_number.value = col_i * 10 + jj
                        input_task_number.addEventListener('change', function () {
                            editTaskDescription(this, 'input_task_number');
                        });
                        td_task_number.appendChild(input_task_number);
                        col_i++;

                        //**************************************************
                        // Название задачи
                        var td_main_task_task_name = row.insertCell(col_i);
                        td_main_task_task_name.classList.add("td_main_task_task_name", "sticky-cell", "col-2");
                        var input_main_task_task_name = document.createElement('input');
                        input_main_task_task_name.type = "text";
                        input_main_task_task_name.className = "input_main_task_task_name";
                        input_main_task_task_name.placeholder = "Введите название работы";
                        input_main_task_task_name.value = (col_i * 10 + jj) + '   input_main_task_task_name.placeholder'
                        input_main_task_task_name.addEventListener('click', function () {
                            editTaskDescription(this, 'input_main_task_task_name');
                        });

                        var div_tow_button = document.createElement('div');
                        div_tow_button.className = "div_task_button_hidden";
                        div_tow_button.hidden = true;
                        addButtonsForNewTask(div_tow_button, createNewRow = true);


                        td_main_task_task_name.appendChild(div_tow_button);
                        td_main_task_task_name.appendChild(input_main_task_task_name);
                        td_main_task_task_name.colSpan = 3;
                        col_i++;

                        //**************************************************
                        // Плановые трудозатраты
                        var td_task_plan_labor_cost = row.insertCell(col_i);
                        td_task_plan_labor_cost.classList.add("td_task_plan_labor_cost", "sticky-cell", "col-5");
                        var input_task_plan_labor_cost = document.createElement('input');
                        input_task_plan_labor_cost.type = "text";
                        input_task_plan_labor_cost.className = "input_task_plan_labor_cost";
                        input_task_plan_labor_cost.value = col_i * 10;
                        input_task_plan_labor_cost.disabled = true;
                        input_task_plan_labor_cost.addEventListener('click', function () {
                            editTaskDescription(this, 'input_task_plan_labor_cost');
                        });
                        td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                        col_i++;

                        //**************************************************
                        // Фактические трудозатраты
                        var td_task_fact_labor_cost = row.insertCell(col_i);
                        td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                        var input_task_sum_fact = document.createElement('input');
                        input_task_sum_fact.type = "text";
                        input_task_sum_fact.classList.add("input_task_sum_fact", "is_not_edited");
                        input_task_sum_fact.setAttribute("data-value", null);
                        input_task_sum_fact.readOnly = true;
                        input_task_sum_fact.disabled = true;

                        input_task_sum_fact.value = col_i * 10
                        td_task_fact_labor_cost.appendChild(input_task_sum_fact);
                        col_i++;

                        //**************************************************
                        // Прогноз
                        var td_task_forecast_labor_cost = row.insertCell(col_i);
                        td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                        var input_task_sum_forecast = document.createElement('input');
                        input_task_sum_forecast.type = "text";
                        input_task_sum_forecast.classList.add("input_task_sum_forecast", "is_not_edited");
                        input_task_sum_forecast.setAttribute("data-value", null);
                        input_task_sum_forecast.readOnly = true;
                        input_task_sum_forecast.disabled = true;

                        input_task_sum_forecast.value = col_i * 10
                        td_task_forecast_labor_cost.appendChild(input_task_sum_forecast);
                        col_i++;

                        //**************************************************
                        // Предыдущий период
                        var td_tow_sum_previous_fact = row.insertCell(col_i);
                        td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                        var input_task_sum_previous_fact = document.createElement('input');
                        input_task_sum_previous_fact.type = "text";
                        input_task_sum_previous_fact.classList.add("input_task_sum_forecast", "is_not_edited");
                        input_task_sum_previous_fact.setAttribute("data-value", null);
                        input_task_sum_previous_fact.readOnly = true;
                        input_task_sum_previous_fact.disabled = true;
                        input_task_sum_previous_fact.value = col_i * 10
                        td_tow_sum_previous_fact.appendChild(input_task_sum_previous_fact);
                        col_i++;

                        //**************************************************
                        // 4 недели календаря
                        for (let i = 0; i < td_task_labor_list_class.length; i++) {
                            var td_task_labor_cost_week_day = row.insertCell(col_i);
                            td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                            var input_task_week_day = document.createElement('input');
                            input_task_week_day.type = "text";
                            input_task_week_day.classList.add(input_task_labor_list_class[i][0], input_task_labor_list_class[i][1]);
                            input_task_week_day.setAttribute("data-value", null);
                            input_task_week_day.readOnly = true;
                            input_task_week_day.disabled = true;

                            input_task_week_day.value = col_i * 10
                            //Если ячейка не сумма недели, добавляем отслеживание изменения ячейки
                            if (!input_task_labor_list_class[i][0].indexOf("input_task_week_")) {
                                input_task_week_day.addEventListener('click', function () {
                                    editTaskDescription(this, input_task_labor_list_class[i][0]);
                                });
                            }
                            td_task_labor_cost_week_day.appendChild(input_task_week_day);
                            col_i++;
                        }

                        //**************************************************
                        // Следующий период
                        var td_tow_sum_future_fact = row.insertCell(col_i);
                        td_tow_sum_future_fact.className = "td_tow_sum_future_fact";
                        var input_task_sum_future_fact = document.createElement('input');
                        input_task_sum_future_fact.type = "text";
                        input_task_sum_future_fact.classList.add("input_task_sum_future_fact", "is_not_edited");
                        input_task_sum_future_fact.setAttribute("data-value", null);
                        input_task_sum_future_fact.readOnly = true;
                        input_task_sum_future_fact.disabled = true;
                        input_task_sum_future_fact.value = col_i * 10
                        td_tow_sum_future_fact.appendChild(input_task_sum_future_fact);
                        col_i++;

                        //**************************************************
                        // Комментарии
                        var td_task_responsible_comment = row.insertCell(col_i);
                        td_task_responsible_comment.className = "td_task_responsible_comment";
                        var input_task_responsible_comment = document.createElement('input');
                        input_task_responsible_comment.type = "text";
                        input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                        input_task_responsible_comment.setAttribute("data-value", null);
                        input_task_responsible_comment.value = col_i * 10
                        input_task_responsible_comment.addEventListener('click', function () {
                            editTaskDescription(this, 'input_task_responsible_comment');
                        });
                        td_task_responsible_comment.appendChild(input_task_responsible_comment);
                        col_i++;


                        //Добавляем изменение - Создание новой строки
                        UserChangesTaskLog(c_id = row.id, rt = 'New', u_p_id = '', c_row = row); // FirstRow - new row

            //********************************************************
            //Строка с задачей
            var row = tab_tr0.insertRow(1);
            var col_i = 0;

                        //**************************************************
                        // main_task

                        row.className = "lvl-0 task";
                        row.setAttribute("data-lvl", "0");
                        row.setAttribute("data-tow_cnt", "0");
                        row.setAttribute("data-value_type", "");
                        row.setAttribute("data-is_not_edited", '');
                        row.id = `_New_${new Date().getTime()}`;

                        //**************************************************
                        // Номер задачи
                        var td_task_number = row.insertCell(0);
                        td_task_number.classList.add("td_task_number", "sticky-cell", "col-1");
                        var input_task_number = document.createElement('input');
                        input_task_number.type = "text";
                        input_task_number.className = "input_task_number";
                        input_task_number.value = col_i
                        input_task_number.addEventListener('change', function () {
                            editTaskDescription(this, 'input_task_number');
                        });
                        td_task_number.appendChild(input_task_number);
                        col_i++;

                        //**************************************************
                        // Название задачи
                        var td_task_task_name = row.insertCell(col_i);
                        td_task_task_name.classList.add("td_task_task_name", "sticky-cell", "col-2");
                        var input_task_task_name = document.createElement('input');
                        input_task_task_name.type = "text";
                        input_task_task_name.className = "input_task_task_name";
                        input_task_task_name.placeholder = "Введите название работы";
                        input_task_task_name.value = col_i + "   var input_task_task_name = document.createElement('input');"
                        input_task_task_name.addEventListener('click', function () {
                            editTaskDescription(this, 'input_task_task_name');
                        });

                        var div_tow_button = document.createElement('div');
                        div_tow_button.className = "div_task_button_hidden";
                        div_tow_button.hidden = true;
                        addButtonsForNewTask(div_tow_button, createNewRow = true);

                        td_task_task_name.appendChild(div_tow_button);
                        td_task_task_name.appendChild(input_task_task_name);
                        col_i++;

                        //**************************************************
                        // Исполнитель
                        var td_task_responsible_user = row.insertCell(col_i);
                        td_task_responsible_user.classList.add("td_task_responsible_user", "sticky-cell", "col-3");
                            var task_responsible_user = document.createElement('select');
                            task_responsible_user.classList.add("selectSearch2", "task_responsible_user");
                                var option = document.createElement('option');
                            task_responsible_user.appendChild(option);

                            for (j in data.employees_list) {
                                var option = document.createElement('option');
                                option.value = data.employees_list[j]['user_id'];
                                option.text = data.employees_list[j]['short_full_name'];
                                if (data.employees_list[j]['user_id'] == col_i-1) {
                                    option.setAttribute('selected', 'selected');
                                }
                                task_responsible_user.appendChild(option);
                            }

                        td_task_responsible_user.appendChild(task_responsible_user);
                        col_i++;

                        $(task_responsible_user).select2();
                        $(task_responsible_user).on('select2:select', function(e) {editTaskDescription(this, 'task_responsible_user');});

                        // td_task_responsible_user.addEventListener('click', function () {
                        //     taskSelectSearch2MouseOver(this, 'task_responsible_user');
                        // });
                        //td_task_responsible_user.getElementsByClassName("task_responsible_user")[0]
                        // td_task_responsible_user.addEventListener('mouseout', function () {
                        //     taskSelectSearch2MouseOut(this, 'task_responsible_user');
                        // });

                        // $(document).on("mouseenter", ".task_responsible_user .select2-container", function(e) {
                        //     taskSelectSearch2MouseOver(task_responsible_user);
                        // });
                        //
                        // $(document).on("mouseleave", ".task_responsible_user .select2-container", function(e) {
                        //     taskSelectSearch2MouseOut(this, 'task_responsible_user');
                        // });

                        //**************************************************
                        // Статус
                        var td_tow_task_statuses = row.insertCell(col_i);
                        td_tow_task_statuses.classList.add("td_tow_task_statuses", "sticky-cell", "col-4");
                            var task_task_statuses = document.createElement('select');
                            task_task_statuses.classList.add("selectSearch2", "task_task_statuses");
                                var option = document.createElement('option');
                            task_task_statuses.appendChild(option);

                            for (j in data.task_statuses) {
                                var option = document.createElement('option');
                                option.value = data.task_statuses[j]['task_status_id'];
                                option.text = data.task_statuses[j]['task_status_name'];
                                if (data.task_statuses[j]['task_status_id'] == col_i-1) {
                                    option.setAttribute('selected', 'selected');
                                }
                                task_task_statuses.appendChild(option);
                            }

                        td_tow_task_statuses.appendChild(task_task_statuses);
                        col_i++;

                        $(task_task_statuses).select2();
                        $(task_task_statuses).on('select2:select', function(e) {editTaskDescription(this, 'task_task_statuses');});




                        // $(document).on("mouseenter", ".task_task_statuses .select2-container", function(e) {
                        //     taskSelectSearch2MouseOver(task_task_statuses);
                        // });
                        //
                        // $(document).on("mouseleave", ".task_task_statuses .select2-container", function(e) {
                        //     taskSelectSearch2MouseOut(task_task_statuses);
                        // });

            // let ss2_tru = $('.task_responsible_user');
            // let ss2_tts = $('.task_task_statuses');
            //
            // ss2_tru.toArray().forEach(function (tru) {
            //     $(tru).prop("disabled", true);
            //     tru.addEventListener("mouseover", function() {taskSelectSearch2MouseOver(this);});
            //     tru.addEventListener("mouseout", function() {taskSelectSearch2MouseOut(this);});
            //
            // });
            //
            // ss2_tts.toArray().forEach(function (tts) {
            //     $(tts).prop("disabled", true);
            //     tts.addEventListener("mouseover", function() {taskSelectSearch2MouseOver(this);});
            //     tts.addEventListener("mouseout", function() {taskSelectSearch2MouseOut(this);});
            // });



                        //**************************************************
                        // Плановые трудозатраты
                        var td_task_plan_labor_cost = row.insertCell(col_i);
                        td_task_plan_labor_cost.classList.add("td_task_plan_labor_cost", "sticky-cell", "col-5");
                        var input_task_plan_labor_cost = document.createElement('input');
                        input_task_plan_labor_cost.type = "text";
                        input_task_plan_labor_cost.className = "input_task_plan_labor_cost";
                        input_task_plan_labor_cost.placeholder = "...";
                        input_task_plan_labor_cost.value = col_i
                        input_task_plan_labor_cost.addEventListener('click', function () {
                            editTaskDescription(this, 'input_task_plan_labor_cost');
                        });
                        td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                        col_i++;

                        //**************************************************
                        // Фактические трудозатраты
                        var td_task_fact_labor_cost = row.insertCell(col_i);
                        td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                        var input_task_sum_fact = document.createElement('input');
                        input_task_sum_fact.type = "text";
                        input_task_sum_fact.classList.add("input_task_sum_fact", "is_not_edited");
                        input_task_sum_fact.setAttribute("data-value", null);
                        input_task_sum_fact.readOnly = true;
                        input_task_sum_fact.disabled = true;

                        input_task_sum_fact.value = col_i
                        td_task_fact_labor_cost.appendChild(input_task_sum_fact);
                        col_i++;

                        //**************************************************
                        // Прогноз
                        var td_task_forecast_labor_cost = row.insertCell(col_i);
                        td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                        var input_task_sum_forecast = document.createElement('input');
                        input_task_sum_forecast.type = "text";
                        input_task_sum_forecast.classList.add("input_task_sum_forecast", "is_not_edited");
                        input_task_sum_forecast.setAttribute("data-value", null);
                        input_task_sum_forecast.readOnly = true;
                        input_task_sum_forecast.disabled = true;

                        input_task_sum_forecast.value = col_i
                        td_task_forecast_labor_cost.appendChild(input_task_sum_forecast);
                        col_i++;

                        //**************************************************
                        // Предыдущий период
                        var td_tow_sum_previous_fact = row.insertCell(col_i);
                        td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                        var input_task_sum_previous_fact = document.createElement('input');
                        input_task_sum_previous_fact.type = "text";
                        input_task_sum_previous_fact.classList.add("input_task_sum_forecast", "is_not_edited");
                        input_task_sum_previous_fact.setAttribute("data-value", null);
                        input_task_sum_previous_fact.readOnly = true;
                        input_task_sum_previous_fact.disabled = true;
                        input_task_sum_previous_fact.value = col_i
                        td_tow_sum_previous_fact.appendChild(input_task_sum_previous_fact);
                        col_i++;

                        //**************************************************
                        // 4 недели календаря
                        for (let i = 0; i < td_task_labor_list_class.length; i++) {
                            var td_task_labor_cost_week_day = row.insertCell(col_i);
                            td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                            var input_task_week_day = document.createElement('input');
                            input_task_week_day.type = "text";
                            input_task_week_day.classList.add(input_task_labor_list_class[i][0], input_task_labor_list_class[i][1]);
                            input_task_week_day.setAttribute("data-value", null);

                            input_task_week_day.value = col_i
                            //Если ячейка не сумма недели, добавляем отслеживание изменения ячейки
                            if (!input_task_labor_list_class[i][0].indexOf("input_task_week_")) {
                                input_task_week_day.addEventListener('click', function () {
                                    editTaskDescription(this, input_task_labor_list_class[i][0]);
                                });
                            }
                            else {
                                input_task_week_day.readOnly = true;
                                input_task_week_day.disabled = true;
                            }
                            td_task_labor_cost_week_day.appendChild(input_task_week_day);
                            col_i++;
                        }

                        //**************************************************
                        // Следующий период
                        var td_tow_sum_future_fact = row.insertCell(col_i);
                        td_tow_sum_future_fact.className = "td_tow_sum_future_fact";
                        var input_task_sum_future_fact = document.createElement('input');
                        input_task_sum_future_fact.type = "text";
                        input_task_sum_future_fact.classList.add("input_task_sum_future_fact", "is_not_edited");
                        input_task_sum_future_fact.setAttribute("data-value", null);
                        input_task_sum_future_fact.readOnly = true;
                        input_task_sum_future_fact.disabled = true;
                        input_task_sum_future_fact.value = col_i
                        td_tow_sum_future_fact.appendChild(input_task_sum_future_fact);
                        col_i++;

                        //**************************************************
                        // Комментарии
                        var td_task_responsible_comment = row.insertCell(col_i);
                        td_task_responsible_comment.className = "td_task_responsible_comment";
                        var input_task_responsible_comment = document.createElement('input');
                        input_task_responsible_comment.type = "text";
                        input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                        input_task_responsible_comment.setAttribute("data-value", null);
                        input_task_responsible_comment.readOnly = true;
                        input_task_responsible_comment.value = col_i
                        input_task_responsible_comment.addEventListener('click', function () {
                            editTaskDescription(this, 'input_task_responsible_comment');
                        });
                        td_task_responsible_comment.appendChild(input_task_responsible_comment);
                        col_i++;


                        //Добавляем изменение - Создание новой строки
                        UserChangesTaskLog(c_id = row.id, rt = 'New', u_p_id = '', c_row = row); // FirstRow - new row
                    }

            // let ss2_tru = $('.task_responsible_user');
            // let ss2_tts = $('.task_task_statuses');
            //
            // ss2_tru.toArray().forEach(function (tru) {
            //     $(tru).prop("disabled", true);
            //     // tru.addEventListener("mouseover", function() {taskSelectSearch2MouseOver(this);});
            //     // tru.addEventListener("mouseout", function() {taskSelectSearch2MouseOut(this);});
            //
            // });
            //
            // ss2_tts.toArray().forEach(function (tts) {
            //     $(tts).prop("disabled", true);
            //     // tts.addEventListener("mouseover", function() {taskSelectSearch2MouseOver(this);});
            //     // tts.addEventListener("mouseout", function() {taskSelectSearch2MouseOut(this);});
            // });
            creativeModeOn();

            var edit_btn = document.getElementById("edit_btn");
            if (!edit_btn.hidden) {
                if (document.URL.split('/tasks/').length > 1) {
                    isEditTaskTable();
                }
            }

        }
        else if (data.status === 'error') {
            let description = data.description;
            console.log(description);
            description.unshift('Ошибка');
            return createDialogWindow(status='error2', description=description);
        }
        })
        .catch(error => {
            console.error('Error:', error);
        });
};

function editTaskDescription(cell, type='') {
    console.log(cell);
}

function addButtonsForNewTask(div_tow_button, createNewTask=false) {
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
}

function UserChangesTaskLog(c_id, rt, u_p_id, c_row=false, change_lvl=false) {
        if (u_p_id == c_id) {
            return createDialogWindow(status='error', description=[
            'Ошибка',
            'При последней манипуляции над задачей произошла ошибка.', 'Попробуйте удалить эту задачу или обновите страницу']);
        }
        if (!highestRow.length) {
            highestRow = [c_row.rowIndex, c_row.id];
        }
        else {
            if (c_row.rowIndex < highestRow[0]) {
                highestRow = [c_row.rowIndex, c_row.id];
            }
        }
        userChanges[c_id] = {parent_id: u_p_id};

        if (['Before', 'After', 'New'].includes(rt)) {
            newRowList.add(c_id);
        }
}