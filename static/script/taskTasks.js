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

    tep_info = document.getElementsByClassName("tow_info_screen")[0].dataset.tep_info;
    tep_info = tep_info === 'True';

    edit_btn? edit_btn.addEventListener('click', function() {editTaskTable();}):'';
    save_btn? save_btn.addEventListener('click', function() {saveTaskChanges();}):'';
    cancel_btn? cancel_btn.addEventListener('click', function() {cancelTaskChanges();}):'';
    full_view_btn_show? full_view_btn_show.addEventListener('click', function() {showFullTaskTable();}):'';
    full_view_btn_hide? full_view_btn_hide.addEventListener('click', function() {hideFullTaskTable();}):'';
    full_view_btn_hide? full_view_btn_hide.style.display = "none":'';

    full_view_creative_mode_on_btn? full_view_creative_mode_on_btn.addEventListener('click', function() {creativeModeOn();}):'';
    full_view_creative_mode_off_btn? full_view_creative_mode_off_btn.addEventListener('click', function() {creativeModeOff();}):'';
    creative_mode_on_btn? creative_mode_on_btn.addEventListener('click', function() {creativeModeOn();}):'';
    creative_mode_off_btn? creative_mode_off_btn.addEventListener('click', function() {creativeModeOff();}):'';
    creative_mode_off_btn? creative_mode_off_btn.style.display = "none":'';
    full_view_creative_mode_on_btn? full_view_creative_mode_on_btn.style.display = "none":'';
    full_view_creative_mode_off_btn? full_view_creative_mode_off_btn.style.display = "none":'';

    button_tow_first_cell? button_tow_first_cell.addEventListener('click', function() {FirstTaskRow();}):'';

    document.getElementById('responsible_or_status_crossBtnNAW')? document.getElementById('responsible_or_status_crossBtnNAW').addEventListener('click', function() {closeModal();this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('cancel__edit_btn_i')? document.getElementById('cancel__edit_btn_i').addEventListener('click', function() {closeModal(), this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('responsibleOrStatusWin')? document.getElementById('responsibleOrStatusWin').addEventListener('click', function() {
        closeModal();
        let tow_info_screen = document.querySelector(".tow_info_screen");
        tow_info_screen.classList.add("hidden");
    }):'';

    document.getElementById('info_btn')? document.getElementById('info_btn').addEventListener('click', function() {
        let tow_info_screen = document.querySelector(".tow_info_screen");
        tow_info_screen.className = "tow_info_screen";
        let overlay = document.querySelector(".overlay");
        overlay.className = "overlay";
    }):'';

    //Ответственный
    let td_task_responsible_user = document.getElementsByClassName('td_task_responsible_user');
    for (let i of td_task_responsible_user) {
        if (i.dataset.editing_is_prohibited == 'None') {
            i.addEventListener('click', function () {editResponsibleOrStatus(this);});
        }
    }

    //Статус задачи
    let td_tow_task_statuses = document.getElementsByClassName('td_tow_task_statuses');
    for (let i of td_tow_task_statuses) {
        i.addEventListener('click', function() {editResponsibleOrStatus(this);});
    }

    //Номер задачи
    let input_task_number = document.getElementsByClassName('input_task_number');
    for (let i of input_task_number) {
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_number');});
    }
    //Название главной задачи
    let input_main_task_task_name = document.getElementsByClassName('input_main_task_task_name');
    for (let i of input_main_task_task_name) {
        i.addEventListener('change', function() {editTaskName(this, this.value);});
    }
    //Название задачи
    let input_task_name = document.getElementsByClassName('input_task_name');
    for (let i of input_task_name) {
        i.addEventListener('change', function() {editTaskName(this, this.value);});
    }
    //Плановые трудозатраты
    let input_task_plan_labor_cost = document.getElementsByClassName('input_task_plan_labor_cost');
    for (let i of input_task_plan_labor_cost) {
        i.addEventListener('change', function() {recalcPlanLaborCostWeekSum(this);});
    }

    let th_task_sum_previous_fact = document.getElementsByClassName('th_task_sum_previous_fact');

    if (th_task_sum_previous_fact.length) {
        th_task_sum_previous_fact[0].addEventListener('click', function() {loadOtherPeriod(type='th_task_sum_previous_fact');});
    }
    let th_task_sum_future_fact = document.getElementsByClassName('th_task_sum_future_fact');
    if (th_task_sum_future_fact.length) {
        th_task_sum_future_fact[0].addEventListener('click', function() {loadOtherPeriod(type='th_task_sum_future_fact');});
    }

    //comment
    let input_task_responsible_comment = document.getElementsByClassName('input_task_responsible_comment');
    for (let i of input_task_responsible_comment) {
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_responsible_comment');});
    }

    // let overlay = document.querySelector(".overlay");
    // overlay.classList.add("hidden");

    let loading_screen = document.querySelector(".loading_screen");
    loading_screen.classList.add("hidden");

    let tow_info_screen = document.getElementsByClassName('tow_info_screen');
    for (let i of tow_info_screen) {
        i.addEventListener('click', function() {
            i.classList.add("hidden");
            let overlay = document.querySelector(".overlay");
            overlay.classList.add("hidden");
        });
    }

    let addTowBefore = document.getElementsByClassName('addTowBefore');
    for (let i of addTowBefore) {
        i.addEventListener('click', function() {addTow(this, 'Before');});
    }
    let addTowAfter = document.getElementsByClassName('addTowAfter');
    for (let i of addTowAfter) {
        i.addEventListener('click', function() {addTow(this, 'After');});
    }
    let addTowNew = document.getElementsByClassName('addTowNew');
    for (let i of addTowNew) {
        i.addEventListener('click', function() {addTow(this, 'New');});
    }
    let addResponsibleNew = document.getElementsByClassName('addResponsibleNew');
    for (let i of addResponsibleNew) {
        i.addEventListener('click', function() {addTow(this, 'addResponsibleNew');});
    }
    let shiftTowRight = document.getElementsByClassName('shiftTowRight');
    for (let i of shiftTowRight) {
        i.addEventListener('click', function() {addTow(this, 'Right');});
    }
    let shiftTowUp = document.getElementsByClassName('shiftTowUp');
    for (let i of shiftTowUp) {
        i.addEventListener('click', function() {addTow(this, 'Up');});
    }
    let shiftTowLeft = document.getElementsByClassName('shiftTowLeft');
    for (let i of shiftTowLeft) {
        i.addEventListener('click', function() {addTow(this, 'Left');});
    }
    let shiftTowDown = document.getElementsByClassName('shiftTowDown');
    for (let i of shiftTowDown) {
        i.addEventListener('click', function() {addTow(this, 'Down');});
    }
    let tow_delTow = document.getElementsByClassName('tow_delTow');
    for (let i of tow_delTow) {
        i.addEventListener('click', function() {delTow(this);});
    }
});


const proj_url = decodeURI(document.URL.split('/')[4]);  //Название проекта
var tow_id = document.URL.substring(document.URL.lastIndexOf('/') + 1);  //tow_id
let userChanges = {};  //Список изменений tow пользователем
let newRowObj = {};  //Словарь новых tow
let deletedRowObj = {};  //Словарь удаленных tow
let highestRow = [];  //Самая верхняя строка с которой "поедет" вся нумерация строк
let reservesChanges = {};  //Список изменений резервов
let tep_info = '';

function hideFullTaskTable() {
    // Отобразить таблицу на всю страницу
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
    // Отобразить инфу о проекте + таблица
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


    full_view_btn_hide.hidden = false;
    full_view_creative_mode_on_btn.hidden = false;
    full_view_creative_mode_off_btn.hidden = false;

    document.getElementsByClassName("qqqq")[0].style.maxHeight="calc(100vh - 111px)";
    // document.getElementsByTagName("main")[0].style.paddingTop ="56px";
}

function creativeModeOn() {
    // let div_task_button_hidden = $('.div_task_button_hidden');
    //
    // if (div_task_button_hidden.length) {
    //     div_task_button_hidden.toArray().forEach(function (button) {
    //         button.className = 'div_tow_button';
    //     });
    // }

    let tab = document.getElementById("towTable");
    let tab_tr0 = tab.getElementsByTagName('tbody')[0];

    if (tab_tr0.rows[0].cells[1].classList[0] !== 'empty_table') {
        for (let i = 0, row; row = tab_tr0.rows[i]; i++) {
            if (row.classList[1] === 'last_row') {
                continue;
            }
            if (row.getElementsByClassName("td_task_fact_labor_cost")[0].innerText === '') {
                let div_task_button_hidden = $(row).find(".div_task_button_hidden");
                if (div_task_button_hidden.length) {
                    div_task_button_hidden.toArray().forEach(function (button) {
                        button.className = 'div_tow_button';
                    });
                }
            } else {
                row.getElementsByClassName("col-2")[0].getElementsByClassName("div_task_button_hidden")[0].className = 'div_tow_button'
            }
        }
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
        creative_mode_off_btn.hidden = false;
    }

    isEditTaskTable();
}

function creativeModeOff() {
    let div_tow_button = $('.div_tow_button');

    if (div_tow_button.length) {
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

function editResponsibleOrStatus(button) {
    var row = button.closest('tr');
    var button_value = button.dataset.value;
    let input_task_name = row.getElementsByClassName('input_task_name')[0].value;
    var taskResponsibleId = row.dataset.task_responsible;
    let newTitle = '';
    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');
    let r_dialod = r_or_s_dialod.getElementsByClassName('responsible_or_status_responsible_form__field_wrapper')[0];
    let s_dialod = r_or_s_dialod.getElementsByClassName('responsible_or_status_status_form__field_wrapper')[0];

    let responsible_select = $('#responsible_or_status_responsible_select');

    if (button.classList.contains('col-3')) {
        newTitle = `Для задачи "${input_task_name}" назначить ответственного`;
        let r_dialod = r_or_s_dialod.getElementsByClassName('responsible_or_status_responsible_form__field_wrapper')[0]
        r_dialod.style.display = "flex";
        s_dialod.style.display = "none";
        responsible_select.val(button_value? button_value.toString():null).trigger('change');
    }
    else if (button.classList.contains('col-4')) {
        let responsible_user = row.getElementsByClassName('td_task_responsible_user')[0].innerText;
        newTitle = `Для задачи "${input_task_name}" отв.(${responsible_user}) назначить статус`
        r_dialod.style.display = "none";
        s_dialod.style.display = "flex";
        $('#responsible_or_status_status_select').val(button_value? button_value.toString():null).trigger('change');
    }

    document.getElementById('responsible_or_status_frame_input').textContent = newTitle;

    //Для кнопки "СОХРАНИТЬ" назначаем выполение функции записи нового значения в ячейку
    let apply__edit_btn = document.getElementById("apply__edit_btn_i");
    let new_apply__edit_btn = apply__edit_btn.cloneNode(true);
    apply__edit_btn.parentNode.replaceChild(new_apply__edit_btn, apply__edit_btn);

    document.getElementById('apply__edit_btn_i').addEventListener('click', function() {applyResponsibleOrStatusChanges(button, row);});

    openModal();
    if (responsible_select.data('select2')) {
        if (button.classList.contains('col-3')) {
            responsible_select.select2('open');
        } else if (button.classList.contains('col-4')) {
            $('#responsible_or_status_status_select').select2('open');
        }
    }
}

function openModal() {
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.remove("hidden");
    overlay.classList.remove("hidden");
}

function closeModal() {
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.add("hidden");
    overlay.classList.add("hidden");
}

function applyResponsibleOrStatusChanges(button, row) {
    // нужно передать button из editResponsibleOrStatus,
    // найти нужную ячейку (ФИО или статус) и
    // вставить выбранное значение из выпадающего списка
    let result_val = null;
    let result_text = '';

    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');
    //ФИО
    if (r_or_s_dialod.getElementsByClassName('responsible_or_status_responsible_form__field_wrapper')[0].style.display === "flex") {
        result_val = $('#responsible_or_status_responsible_select').val();
        result_text = $('#responsible_or_status_responsible_select :selected').text();

        row.getElementsByClassName('td_task_responsible_user')[0].dataset.value = result_val;
        row.getElementsByClassName('td_task_responsible_user')[0].innerText = result_text;
    }
    //Статус
    else if (r_or_s_dialod.getElementsByClassName('responsible_or_status_status_form__field_wrapper')[0].style.display === "flex") {
        result_val = $('#responsible_or_status_status_select').val();
        result_text = $('#responsible_or_status_status_select :selected').text();

        row.getElementsByClassName('td_tow_task_statuses')[0].dataset.value = result_val;
        row.getElementsByClassName('td_tow_task_statuses')[0].innerText = result_text;
    }

    editTaskDescription(button, result_val, button.classList[0]);

    closeModal();
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
    }
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

            var row = tab_tr0.insertRow(0);
            var col_i = 0;

            let main_task_parent_id = `_New_1.${new Date().getTime()}`
            let task_id = `_New_2.${new Date().getTime()}`;
            let task_responsible_id = `_New_tr_2.${new Date().getTime()}`

            //**************************************************
            // main_task

                row.className = "lvl-0 main_task";
                row.setAttribute("data-lvl", "0");
                row.setAttribute("data-tow_cnt", "0");
                row.dataset.task = main_task_parent_id;
                row.dataset.task_responsible = `None`;

                //**************************************************
                // Номер задачи
                var td_task_number = row.insertCell(0);
                td_task_number.classList.add("td_task_number", "sticky-cell", "col-1");
                    var input_task_number = document.createElement('input');
                    input_task_number.type = "text";
                    input_task_number.className = "input_task_number";
                    input_task_number.placeholder = "...";
                    input_task_number.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_number');
                    });

                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_task_button_hidden";
                    div_tow_button.hidden = true;
                    addButtonsForNewTask(div_tow_button, false, true);

                td_task_number.appendChild(div_tow_button);
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
                    input_main_task_task_name.addEventListener('change', function () {
                        editTaskName(this, this.value);
                    });

                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_task_button_hidden";
                    div_tow_button.hidden = true;
                    addButtonsForNewTask(div_tow_button, true, true, true);


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
                    input_task_plan_labor_cost.setAttribute("data-value", "None");
                    input_task_plan_labor_cost.disabled = true;
                    input_task_plan_labor_cost.addEventListener('change', function () {
                        recalcPlanLaborCostWeekSum(this);
                    });
                td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                col_i++;

                //**************************************************
                // Фактические трудозатраты
                var td_task_fact_labor_cost = row.insertCell(col_i);
                td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                col_i++;

                //**************************************************
                // 4 недели календаря
                for (let i = 0; i < td_task_labor_list_class.length; i++) {
                    var td_task_labor_cost_week_day = row.insertCell(col_i);
                    td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                        var input_task_week_day = document.createElement('input');
                        input_task_week_day.type = "text";
                        input_task_week_day.classList.add(input_task_labor_list_class[i][0], input_task_labor_list_class[i][1]);
                        input_task_week_day.setAttribute("data-value", "None");
                        input_task_week_day.disabled = true;
                    td_task_labor_cost_week_day.appendChild(input_task_week_day);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.setAttribute("data-value", "None");
                    input_task_responsible_comment.placeholder = "...";
                    input_task_responsible_comment.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_responsible_comment');
                    });
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;

                //Добавляем изменение - Создание новой строки
                UserChangesTaskLog(t_id = main_task_parent_id, tr_id = 'None', rt = 'New', c_row = row, parent_id='None'); // FirstRow - new row

            //********************************************************
            //Строка с задачей
            row = tab_tr0.insertRow(1);
            col_i = 0;

                //**************************************************
                // task

                row.className = "lvl-1 task";
                row.setAttribute("data-lvl", "1");
                row.setAttribute("data-tow_cnt", "0");
                row.dataset.task = task_id;
                row.dataset.task_responsible = task_responsible_id;

                //**************************************************
                // Номер задачи
                var td_task_number = row.insertCell(0);
                td_task_number.classList.add("td_task_number", "sticky-cell", "col-1");
                    var input_task_number = document.createElement('input');
                    input_task_number.type = "text";
                    input_task_number.className = "input_task_number";
                    input_task_number.placeholder = "...";
                    input_task_number.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_number');
                    });

                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_task_button_hidden";
                    div_tow_button.hidden = true;
                    addButtonsForNewTask(div_tow_button, false, true);

                td_task_number.appendChild(div_tow_button);
                td_task_number.appendChild(input_task_number);
                col_i++;

                //**************************************************
                // Название задачи
                var td_task_task_name = row.insertCell(col_i);
                td_task_task_name.classList.add("td_task_task_name", "sticky-cell", "col-2");
                    var input_task_name = document.createElement('input');
                    input_task_name.type = "text";
                    input_task_name.className = "input_task_name";
                    input_task_name.placeholder = "Введите название работы";
                    input_task_name.addEventListener('change', function () {
                        editTaskName(this, this.value);
                    });

                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_task_button_hidden";
                    div_tow_button.hidden = true;
                    addButtonsForNewTask(div_tow_button, true);

                td_task_task_name.appendChild(div_tow_button);
                td_task_task_name.appendChild(input_task_name);
                col_i++;

                //**************************************************
                // Исполнитель
                var td_task_responsible_user = row.insertCell(col_i);
                td_task_responsible_user.classList.add("td_task_responsible_user", "sticky-cell", "col-3");
                td_task_responsible_user.innerText = "...";
                td_task_responsible_user.dataset.editing_is_prohibited = "None";
                td_task_responsible_user.addEventListener('click', function () {
                    editResponsibleOrStatus(this);
                });
                col_i++;

                //**************************************************
                // Статус
                var td_tow_task_statuses = row.insertCell(col_i);
                td_tow_task_statuses.classList.add("td_tow_task_statuses", "sticky-cell", "col-4");
                td_tow_task_statuses.innerText = "...";
                td_tow_task_statuses.addEventListener('click', function () {
                    editResponsibleOrStatus(this);
                });
                col_i++;

                //**************************************************
                // Плановые трудозатраты
                var td_task_plan_labor_cost = row.insertCell(col_i);
                td_task_plan_labor_cost.classList.add("td_task_plan_labor_cost", "sticky-cell", "col-5");
                    var input_task_plan_labor_cost = document.createElement('input');
                    input_task_plan_labor_cost.type = "number";
                    input_task_plan_labor_cost.setAttribute("step", "0.0001");
                    input_task_plan_labor_cost.className = "input_task_plan_labor_cost";
                    input_task_plan_labor_cost.setAttribute("data-value", "None");
                    input_task_plan_labor_cost.placeholder = "...";
                    input_task_plan_labor_cost.disabled = !tep_info;
                    input_task_plan_labor_cost.addEventListener('change', function () {
                        recalcPlanLaborCostWeekSum(this);
                    });
                td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                col_i++;

                //**************************************************
                // Фактические трудозатраты
                var td_task_fact_labor_cost = row.insertCell(col_i);
                td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                col_i++;

                //**************************************************
                // 4 недели календаря
                for (let i = 0; i < td_task_labor_list_class.length; i++) {
                    var td_task_labor_cost_week_day = row.insertCell(col_i);
                    td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.setAttribute("data-value", "None");
                    input_task_responsible_comment.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_responsible_comment');
                    });
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;


                //Добавляем изменение - Создание новой строки
                UserChangesTaskLog(t_id = task_id, tr_id = task_responsible_id, rt = 'New', c_row = row, parent_id=main_task_parent_id); // FirstRow - new row


            //**************************************************
            // last_row
            row = tab_tr0.insertRow(2);
            col_i = 0;


                row.className = "lvl-None last_row";
                row.setAttribute("data-lvl", "None");
                row.setAttribute("data-tow_cnt", "None");
                row.setAttribute("data-value_type", "None");
                row.setAttribute("data-is_not_edited", "None");
                row.dataset.task = 'None';
                row.dataset.task_responsible = 'None';

                //**************************************************
                // Номер задачи
                var td_task_number = row.insertCell(0);
                td_task_number.classList.add("td_task_number", "sticky-cell", "col-1");
                    var input_task_number = document.createElement('input');
                    input_task_number.type = "text";
                    input_task_number.className = "input_task_number";
                    input_task_number.disabled = true;
                td_task_number.appendChild(input_task_number);
                col_i++;

                //**************************************************
                // Название задачи
                var td_main_task_task_name = row.insertCell(col_i);
                td_main_task_task_name.classList.add("td_main_task_task_name", "sticky-cell", "col-2");
                    var input_main_task_task_name = document.createElement('input');
                    input_main_task_task_name.type = "text";
                    input_main_task_task_name.className = "input_main_task_task_name";
                    input_main_task_task_name.value = "ИТОГО";
                    input_main_task_task_name.disabled = true;
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
                    input_task_plan_labor_cost.setAttribute("data-value", "None");
                    input_task_plan_labor_cost.disabled = true;
                td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                col_i++;

                //**************************************************
                // Фактические трудозатраты
                var td_task_fact_labor_cost = row.insertCell(col_i);
                td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                col_i++;

                //**************************************************
                // 4 недели календаря
                for (let i = 0; i < td_task_labor_list_class.length; i++) {
                    var td_task_labor_cost_week_day = row.insertCell(col_i);
                    td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                        var input_task_week_day = document.createElement('input');
                        input_task_week_day.type = "text";
                        input_task_week_day.classList.add(input_task_labor_list_class[i][0], input_task_labor_list_class[i][1]);
                        input_task_week_day.setAttribute("data-value", "None");
                        input_task_week_day.disabled = true;
                    td_task_labor_cost_week_day.appendChild(input_task_week_day);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.setAttribute("data-value", "None");
                    input_task_responsible_comment.disabled = true;
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;

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
            description.unshift('Ошибка');
            return createDialogWindow(status='error2', description=description);
        }
        })
        .catch(error => {
            return createDialogWindow(status='error2', description=['Ошибка', error]);
        });
};

function loadOtherPeriod(type='', value='') {
    console.log(type);
}

function editTaskDescription(cell, value='', v_type='') {
    isEditTaskTable();

    let row = cell.closest('tr');
    let t_id = row.dataset.task;
    let tr_id = row.dataset.task_responsible;

    if (userChanges[t_id]) {
        if (userChanges[t_id][tr_id]) {
            userChanges[t_id][tr_id][v_type] = value;
        }
        else {
            userChanges[t_id][tr_id] = {[v_type]: value};
        }
    }
    else {
        userChanges[t_id] = {[tr_id]: {[v_type]: value}};
    }
}

function editTaskName(cell, value='') {
    //В случае если название поменяли у задачи с соисполнителями, нужно обновить название у всех соисполнителей
    let v_type = cell.className === 'input_task_number'? 'input_task_number': 'input_task_name';

    editTaskDescription(cell, value, v_type);

    let row = cell.closest('tr');

    if (row.cells[1].getAttribute("rowspan")) {
        let rowNumber = row.rowIndex;
        let is_colspan = row.cells[1].getAttribute("rowspan") * 1;
        let tab = document.getElementById("towTable");

        for (let i=1; i<is_colspan; i++) {
            tab.rows[rowNumber + i].cells[1].getElementsByTagName('input')[0].value = value;
            editTaskDescription(tab.rows[rowNumber + i], value, v_type);
        }
    }
}

function addButtonsForNewTask(div_tow_button, createNewTask=false, deleteButton=false, mainTask=false) {
    //В зависимости от того, новая ячейка или скопированная, работают разные сценарии
    let newRow = div_tow_button;

    if (mainTask) {
        //если главная задача и есть кнопка "добавить соисполнителя, удаляем кнопку
        let addResponsibleNew = div_tow_button.getElementsByClassName("addResponsibleNew");
        addResponsibleNew.length? addResponsibleNew[0].remove():false;
    }

    if (createNewTask) {
        let all_button = [
            {class:"tow addTowBefore", onclick:"addTow(this, 'Before')", title:"Скопировать структуру над текущей строкой", src:"/static/img/object/tow/addTow-Before.svg", hidden:0},
            {class:"tow addTowAfter", onclick:"addTow(this, 'After')", title:"Скопировать структуру под структурой текущей строки", src:"/static/img/object/tow/addTow-After.svg", hidden:0},
            {class:"tow shiftTowLeft", onclick:"addTow(this, 'Left')", title:"Сдвинуть структуру влево", src:"/static/img/object/tow/shiftTow-Left.svg", hidden:0},
            {class:"tow shiftTowRight", onclick:"addTow(this, 'Right')", title:"Сдвинуть структуру вправо", src:"/static/img/object/tow/shiftTow-Right.svg", hidden:0},
            {class:"tow shiftTowUp", onclick:"addTow(this, 'Up')", title:"Переместить структуру вверх", src:"/static/img/object/tow/shiftTow-Up.svg", hidden:0},
            {class:"tow shiftTowDown", onclick:"addTow(this, 'Down')", title:"Переместить структуру вниз", src:"/static/img/object/tow/shiftTow-Down.svg", hidden:0},
            {class:"tow addTowNew", onclick:"addTow(this, 'New')", title:"Добавить дочерний вид работ", src:"/static/img/object/tow/addTow-New.svg", hidden:0},
        ];
        if (!mainTask) {
            all_button.push(
                {class:"tow addResponsibleNew", onclick:"addTow(this, 'addResponsibleNew')", title:"Добавить ответственного", src:"/static/img/object/tow/task_add_responsible.svg", hidden:0}
            )
        }

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
    else if (deleteButton) {
        let all_button = [
            {class:"tow_delTow", onclick:"delTow(this)", data_del:"1", title:"Удалить строку со всеми вложениями", src:"/static/img/object/tow/delete-tow.svg", hidden:0},
        ];
        all_button.forEach(button => {
            let buttonElement = document.createElement("button");
            buttonElement.className = button['class'];

            buttonElement.setAttribute("title", button['title']);

            buttonElement.setAttribute("data-is_not_edited", button['data_del']);

            buttonElement.hidden = button['hidden'];

            let imgElement = document.createElement("img");
            imgElement.src = button['src'];

            buttonElement.appendChild(imgElement);
            div_tow_button.appendChild(buttonElement);
        })
    }
    let addTowBefore = newRow.getElementsByClassName('addTowBefore');
    addTowBefore.length? addTowBefore[0].addEventListener('click', function() {addTow(this, 'Before');}):'';

    let addTowAfter = newRow.getElementsByClassName('addTowAfter');
    addTowAfter.length? addTowAfter[0].addEventListener('click', function() {addTow(this, 'After');}):'';

    let towDelTow = newRow.getElementsByClassName('tow_delTow');
    towDelTow.length? towDelTow[0].addEventListener('click', function() {delTow(this);}):'';

    let shiftTowLeft = newRow.getElementsByClassName('shiftTowLeft');
    shiftTowLeft.length? shiftTowLeft[0].addEventListener('click', function() {addTow(this, 'Left');}):'';

    let shiftTowRight = newRow.getElementsByClassName('shiftTowRight');
    shiftTowRight.length? shiftTowRight[0].addEventListener('click', function() {addTow(this, 'Right');}):'';

    let shiftTowUp = newRow.getElementsByClassName('shiftTowUp');
    shiftTowUp.length? shiftTowUp[0].addEventListener('click', function() {addTow(this, 'Up');}):'';

    let shiftTowDown = newRow.getElementsByClassName('shiftTowDown');
    shiftTowDown.length? shiftTowDown[0].addEventListener('click', function() {addTow(this, 'Down');}):'';

    let addTowNew = newRow.getElementsByClassName('addTowNew');
    addTowNew.length? addTowNew[0].addEventListener('click', function() {addTow(this, 'New');}):'';

    let addResponsibleNew = newRow.getElementsByClassName('addResponsibleNew');
    addResponsibleNew.length? addResponsibleNew[0].addEventListener('click', function() {addTow(this, 'addResponsibleNew');}):'';

}

// t_id - task_id; tr_id - task_responsible_id;
function UserChangesTaskLog(t_id, tr_id, rt, c_row=false, parent_id) {
    if (!t_id || !tr_id) {
        return createDialogWindow(status='error', description=[
        'Ошибка',
        'При последней манипуляции над задачей произошла ошибка.', 'Попробуйте удалить эту задачу или обновите страницу']);
    }
    if (!highestRow.length) {
        highestRow = [c_row.rowIndex, c_row.dataset.task, c_row.dataset.task_responsible];
    }
    else {
        if (c_row.rowIndex <= highestRow[0]) {
            highestRow = [c_row.rowIndex, c_row.dataset.task, c_row.dataset.task_responsible];
        }
    }
    editTaskDescription(c_row, parent_id, 'parent_id')
    // userChanges[t_id] = {parent_id: u_p_t_id};

    if (['Before', 'After', 'New'].includes(rt)) {
            calcNewRowObj(t_id, tr_id, 'new')
        }

}

function saveTaskChanges(text_comment=false) {
    try {
        // console.log('userChanges')
        // console.log(userChanges)
        // console.log('newRowObj')
        // console.log(newRowObj)
        // console.log('deletedRowObj')
        // console.log(deletedRowObj)
        // console.log('reservesChanges')
        // console.log(reservesChanges)
        if (!Object.keys(userChanges).length && !Object.keys(newRowObj).length && !Object.keys(deletedRowObj).length && !Object.keys(reservesChanges).length) {
            return createDialogWindow(status = 'info', description = ['Внимание!', 'Изменения не найдены', 'Сохранение не произошло ver-1']);
        }
        for (let k in deletedRowObj) {
            for (let kk in deletedRowObj[k]) {
                let row = [k, kk];

                //удаляем запись из списка изменений и не указаны плановые трудозатраты
                if (userChanges[row[0]] && userChanges[row[0]][row[1]]) {
                    // Проверяем, что если был изменен параметр плановые трудозатраты и значение не пусто, тогда удаляем, иначе не удаляем
                    if (userChanges[row[0]][row[1]].hasOwnProperty('input_task_plan_labor_cost') && userChanges[row[0]][row[1]]['input_task_plan_labor_cost'] === 0) {

                        // Если id не число, то удаляем tr_id
                        if (isNaN(row[1])) {
                            delete userChanges[row[0]][row[1]];
                            //Если ключей не осталось, удаляем
                            if (!Object.keys(userChanges[row[0]]).length) {
                                delete userChanges[row[0]];
                            }
                        } else {
                            userChanges[row[0]][row[1]] = {
                                ['input_task_plan_labor_cost']:
                                    userChanges[row[0]][row[1]]['input_task_plan_labor_cost'],
                                ['is_deleted']:
                                    true,
                            };
                        }
                    } else {
                        delete userChanges[row[0]][row[1]];
                        //Если ключей не осталось, удаляем
                        if (!Object.keys(userChanges[row[0]]).length) {
                            delete userChanges[row[0]];
                        }
                    }
                }
                //убираем из списка вновь созданных строк если строка есть в списке удалённых
                if (newRowObj[row[0]] && newRowObj[row[0]][row[1]]) {
                    delete newRowObj[row[0]][row[1]];
                    //Если ключей не осталось, удаляем
                    if (!Object.keys(newRowObj[row[0]]).length) {
                        delete newRowObj[row[0]];
                    }
                    //Так же убираем и из списка удалённых строк
                    delete deletedRowObj[row[0]][row[1]];
                    //Если ключей не осталось, удаляем
                    if (!Object.keys(deletedRowObj[row[0]]).length) {
                        delete deletedRowObj[row[0]];
                    }
                }
            }
            //КАКОЙ-ТО БАГ ОБНАРУЖИЛ 2024-11-19! Если id не число, удаляем его
            if (isNaN(parseInt(k))) {
                delete deletedRowObj[k];
            }
        }

        if (!Object.keys(userChanges).length && !Object.keys(newRowObj).length && !Object.keys(deletedRowObj).length && !Object.keys(reservesChanges).length) {
            return createDialogWindow(status = 'info', description = ['Внимание!', 'Изменения не найдены', 'Сохранение не произошло ver-2']);
        }
        const tab = document.getElementById("towTable");

        //////////////////////////////////////////////////////////////////////////////////////////////
        // Ищем номер строки
        for (const [k, v] of Object.entries(userChanges)) {
            for (const [kk, vv] of Object.entries(v)) {
                if (!userChanges[k][kk].hasOwnProperty('is_deleted')) {
                    var userChanges_x = tab.querySelector(`tr[data-task="${k}"][data-task_responsible="${kk}"]`);
                    // var userChanges_x = tab.querySelector(`[id='${k}']`);
                    userChanges[k][kk]['lvl'] = userChanges_x.rowIndex;
                }
            }
        }
        // console.log('highestRow.length', highestRow.length, highestRow)
        if (highestRow.length) {
            if (highestRow[2] === null) {
                let tab_tr0 = tab.getElementsByTagName('tbody')[0];
                let c_row = tab_tr0.rows[1];
                highestRow = [c_row.rowIndex, c_row.dataset.task, c_row.dataset.task_responsible];
                var row_highestRow = c_row;
            } else {
                var row_highestRow = tab.querySelector(`tr[data-task="${highestRow[1]}"][data-task_responsible="${highestRow[2]}"]`);
            }

            //Если row_highestRow стал null, значит была удалена строка из highestRow
            if (!row_highestRow) {
                let tab_tr0 = tab.getElementsByTagName('tbody')[0];
                let c_row = tab_tr0.rows[1];
                highestRow = [c_row.rowIndex, c_row.dataset.task, c_row.dataset.task_responsible];
                var row_highestRow = c_row;
            }

            if (userChanges[highestRow[1]]) {
                if (userChanges[highestRow[1]][highestRow[2]]) {
                    userChanges[highestRow[1]][highestRow[2]]['lvl'] = row_highestRow.rowIndex;
                } else {
                    userChanges[highestRow[1]][highestRow[2]] = {['lvl']: row_highestRow.rowIndex}
                }
            } else {
                userChanges[highestRow[1]] = {[highestRow[2]]: {['lvl']: row_highestRow.rowIndex}}
            }

            var newRow_highestRow = row_highestRow.nextElementSibling;
            let t_id = newRow_highestRow.dataset.task;  // task_id
            let tr_id = newRow_highestRow.dataset.task_responsible;  // task_responsible_id
            while (newRow_highestRow && newRow_highestRow.classList[newRow_highestRow.classList.length - 1] !== 'last_row') {
                if (userChanges[t_id]) {
                    if (userChanges[t_id][tr_id]) {
                        userChanges[t_id][tr_id]['lvl'] = newRow_highestRow.rowIndex;
                    } else {
                        userChanges[t_id][tr_id] = {['lvl']: newRow_highestRow.rowIndex};
                    }
                } else {
                    userChanges[t_id] = {[tr_id]: {['lvl']: newRow_highestRow.rowIndex}};
                }

                newRow_highestRow = newRow_highestRow.nextElementSibling;
                t_id = newRow_highestRow.dataset.task;  // task_id
                tr_id = newRow_highestRow.dataset.task_responsible;  // task_responsible_id
            }

        }

        // console.log('  ___ deletedRowObj')
        // console.log(deletedRowObj)
        // console.log('  ___ newRowObj')
        // console.log(newRowObj)
        // console.log('  ___ userChanges')
        // console.log(userChanges)

        if (Object.keys(userChanges).length || Object.keys(newRowObj).length || Object.keys(deletedRowObj).length || Object.keys(reservesChanges).length) {

            //окно заглушка, пока сохраняются данные
            createDialogWindow(status = 'info', description = ['Данные сохраняются...'], func = false, buttons = false, text_comment = false, loading_windows = true);

            fetch(`/save_tasks_changes/${tow_id}`, {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'userChanges': userChanges,
                    'list_newRowList': newRowObj,
                    'list_deletedRowList': deletedRowObj,
                    'reservesChanges': reservesChanges,
                })
            })
                .then(response => response.json())
                .then(data => {
                    removeLogInfo();
                    if (data.status === 'success') {
                        // alert('OK')
                        return location.reload();
                    } else {
                        let description = data.description;
                        description.unshift('Ошибка');
                        return createDialogWindow(status = 'error', description = description);
                    }
                })
            return;


        }
    }
    catch (e) {
        fetch('/error_handler_save_tow_changes', {
                    "headers": {
                        'Content-Type': 'application/json'
                    },
                    "method": "POST",
                    "body": JSON.stringify({
                        'log_url': document.URL,
                        'error_description': e.stack,
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        return location.reload();
                    })
    }
}

function cancelTaskChanges() {
    fetch('/reload_page', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": "",
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = document.URL;
                }
                else {
                    let description = data.description[0];
                    description.unshift('Ошибка');
                    return createDialogWindow(status='error', description=description);
                }
            })

}

//Создание новой строки или копирование структуры строк
function addTow(button, route) {
    if  (!['Before', 'After', 'New', 'addResponsibleNew', 'Left', 'Right', 'Up', 'Down'].includes(route)) {
        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape") {
                location.reload();
                event.preventDefault();
            }
        });
        return createDialogWindow(
            status='error',
            description=[
                'Ошибка 1',
                'Что-то пошло не так при формировании структуры задач',
                'Обновите страницу'
            ],
            func=[['click', [reloadPage]]],
        );
    }

    const tab = document.getElementById("towTable");
    var tab_tr0 = tab.getElementsByTagName('tbody')[0];

    var row = button.closest('tr');
    var className = row.classList[0];
    var class_type = row.classList[row.classList.length-1];
    var cur_lvl = parseInt(className.split('lvl-')[1]);
    let t_id = row.dataset.task;  // task_id
    let tr_id = row.dataset.task_responsible;  // task_responsible_id

    //Проверяем, что строка на объединение Наименования
    let is_colspan = false;
    if (row.getElementsByClassName("col-2")[0]) {
        is_colspan = row.getElementsByClassName("col-2")[0].getAttribute("rowspan") * 1;
    }

    //Если main_task и добавляется соисполнитель - вызываем ошибку, у главной задачи не могут быть исполнители
    if (route === 'addResponsibleNew' && class_type === 'main_task') {
        return createDialogWindow(
            status='error',
            description=[
                'Ошибка',
                'Нельзя добавить исполнителя для базовой задачи',
                'Обновите страницу'
            ],
            func=[['click', [reloadPage]]],
        );
    }

    var newRow = row.cloneNode(true);

    var rowNumber = row.rowIndex;
    var currentRow = button.closest('tr');
    var preRow = row.previousElementSibling;
    var nextRow = row.nextElementSibling;
    var taskRow = row.nextElementSibling;
    var pre_lvl = preRow? parseInt(preRow.classList[0].split('lvl-')[1]):0;
    var p_id = -1;

    if (!taskRow) {
        taskRow = row;
    }
    if (!nextRow) {
        nextRow = row;
    }

    let task_number = newRow.getElementsByClassName("col-1")[0].getElementsByTagName('div')[0];
    let task_name = newRow.getElementsByClassName("col-2")[0].getElementsByTagName('div')[0];
    task_number.className = 'div_tow_button';
    task_name.className = 'div_tow_button';

    //Генерация task_id и task_responsible для новой строки
    let task_id_tmp = `_New_task_${new Date().getTime()}`;
    let task_responsible_id_tmp = class_type === 'main_task'? 'None':`_New_tr_${new Date().getTime()}`;

    //task_id и task_responsible для детей
    let child_t_id = '';  // task_id
    let child_tr_id = '';  // task_responsible_id

    if (route === 'New') {
        class_type === 'main_task'? cur_lvl ++ :cur_lvl;
        // cur_lvl++;
        if (cur_lvl > 3) {
            return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности - 3']);
        }
        task_responsible_id_tmp = `_New_tr_${new Date().getTime()}`;
        newRow.id = proj_url + '_task_' + route + '_' + new Date().getTime();
        newRow.classList = 'lvl-' + cur_lvl + ' task';
        newRow.setAttribute("data-lvl", cur_lvl);
        newRow.setAttribute("data-task", task_id_tmp);
        newRow.setAttribute("data-task_responsible", task_responsible_id_tmp);

        // Очищаем все поля в новой строке
        if (newRow) {
            let textInputs = newRow.querySelectorAll('input[type="text"]');
            textInputs.forEach(function (input) {
                input.value = '';
            });
        }
        if (!row.nextElementSibling) {
            row.parentNode.appendChild(newRow);
        }
        else {
             //Скрываем ячейку названия задачи, если она входит ячейка выше имеет rowspan
            if (is_colspan) {
                let insertIndex = row.rowIndex + is_colspan - 1;
                newRow.getElementsByClassName("col-2")[0].removeAttribute("rowspan");
                row.parentNode.insertBefore(newRow, tab_tr0.rows[insertIndex]);
            }
            else {
                row.parentNode.insertBefore(newRow, nextRow);
            }
        }
        // Если добавляем строку под main_task, то добавляем ячейки и убираем объединение столбцов
        if (class_type === 'main_task') {
            //Удаляем объединение столбцов
                newRow.cells[1].removeAttribute("colspan");
            //Меняем класс ячейки названия задачи
                newRow.cells[1].className = "td_task_task_name sticky-cell col-2";
            //Добавляем кнопку "Добавить соисполнителя"
                let div_tow_button = newRow.cells[1].getElementsByClassName('div_tow_button')[0];
                let addResponsibleNew = document.createElement("button");
                addResponsibleNew.className = "tow addResponsibleNew";
                addResponsibleNew.setAttribute("title", "Добавить ответственного")
                // addResponsibleNew.addEventListener('click', function() {addTow(this, 'addResponsibleNew');});
                    let imgElement = document.createElement("img");
                    imgElement.src = "/static/img/object/tow/task_add_responsible.svg";
                    addResponsibleNew.appendChild(imgElement);
                div_tow_button.appendChild(addResponsibleNew);
            //Меняем класс инпута названия задачи
                newRow.cells[1].getElementsByClassName('input_main_task_task_name')[0].className = "input_task_name";
            //Добавляем 2 ячейки - исполнитель/статус
                let newCellResponsibleUser = newRow.insertCell(2);
                newCellResponsibleUser.className = "td_task_responsible_user sticky-cell col-3";
                newCellResponsibleUser.addEventListener('click', function() {editResponsibleOrStatus(this);});

                let newCellTaskStatuses = newRow.insertCell(3);
                newCellTaskStatuses.className = "td_tow_task_statuses sticky-cell col-4";
                newCellTaskStatuses.addEventListener('click', function() {editResponsibleOrStatus(this);});
            //Меняем тип инпута у плановых трудозатрат и разблокируем input
                newRow.cells[4].getElementsByTagName('input')[0].setAttribute("type", "number");
                newRow.cells[4].getElementsByTagName('input')[0].setAttribute("step", "0.01");
                newRow.cells[4].getElementsByTagName('input')[0].placeholder = "...";
                newRow.cells[4].getElementsByTagName('input')[0].disabled = 0;
            //Разблокируем комментарий
                newRow.getElementsByClassName('input_task_responsible_comment')[0].disabled = 0;
        }

        //Добавляем изменение - Создание новой строки
        if (class_type === 'main_task') {
            UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp, rt=route, c_row=newRow, parent_id=row.dataset.task); // New - new row
        }
        else {
            let preRow = row.previousElementSibling;
            let pre_lvl = parseInt(preRow.classList[0].split('lvl-')[1]);
            let p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);
            UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp, rt=route, c_row=newRow, parent_id=p_id); // New - new row
        }

        // Настраиваем кнопки
        addButtonsForNewTask(task_number);
        addButtonsForNewTask(task_name);

        // Очищаем все поля в новой строке
        clearDataAttributeValue(newRow);

        //Проскроливаем до новой строки
        newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

        return true;
    }
    // Добавить дополнительного исполнителя
    else if (route === 'addResponsibleNew') {
        cur_lvl = class_type === 'main_task'? cur_lvl ++:cur_lvl;
        if (cur_lvl > 3) {
            return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности - 3']);
        }
        newRow.id = proj_url + '_task_' + route + '_' + new Date().getTime();
        newRow.classList = 'lvl-' + cur_lvl + ' task';
        newRow.setAttribute("data-lvl", cur_lvl);
        newRow.setAttribute("data-task_responsible", task_responsible_id_tmp);

        if (!row.nextElementSibling) {
            row.parentNode.appendChild(newRow);
        }
        else {
             //Скрываем ячейку названия задачи
            newRow.getElementsByClassName("td_task_task_name ")[0].hidden = 1;
            if (is_colspan) {
                let insertIndex = row.rowIndex + is_colspan - 1;

                row.getElementsByClassName("col-2")[0].setAttribute("rowspan", is_colspan + 1);
                row.parentNode.insertBefore(newRow, tab_tr0.rows[insertIndex]);
            }
            else {
                row.getElementsByClassName("col-2")[0].setAttribute("rowspan", 2);
                row.parentNode.insertBefore(newRow, nextRow);
            }
        }

        //Добавляем изменение - Создание новой строки
        UserChangesTaskLog(t_id = newRow.dataset.task, tr_id = task_responsible_id_tmp, rt='New', c_row=newRow, parent_id=row.dataset.task); // New - new row

        // Настраиваем кнопки
        addButtonsForNewTask(task_number);
        addButtonsForNewTask(task_name);

        // Очищаем все поля в новой строке кроме названия
        clearDataAttributeValue(newRow, true);

        //Записываем номер и название задачи
        editTaskDescription(newRow.cells[0], newRow.cells[0].getElementsByTagName('input')[0].value, 'input_task_number');
        editTaskDescription(newRow.cells[1], newRow.cells[1].getElementsByTagName('input')[0].value, 'input_task_name');

        //Проскроливаем до новой строки
        newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

        return true;
    }

    // Список создаваемых строк
    let children_list = [];
    let child_cnt = 0;  //Счётчик детей, используем в генераторе id
    let is_child_colspan = 0;  //Счётчик объединённых ячеек у детей. Используем для определения, у каких детей одинаковый task_id
    let child_task_id_tmp = false;  //task_id для детей, если где-то в структуре есть дети с объединенными ячейками
    let child_colspan = is_colspan;  //Статус, что у детей есть объединенные строки (задача с несколькими исполнителями
    let child_lvl = cur_lvl;  //Уровень ребенка
    let plan_labor_cost_value = 0;  //Плановые трудозатраты детей. Нужно для пересчета суммы тома и ИТОГО
    let child_plan_labor_cost_value = 0;  //Плановые трудозатраты детей. Нужно для пересчета суммы тома и ИТОГО

    // Настраиваем кнопки
    addButtonsForNewTask(task_number);
    addButtonsForNewTask(task_name);

    //Определяем уровень вложенности следующей строки
    if (route !== 'Before') {
        var tow_lvl = nextRow ? parseInt(nextRow.classList[0].split('lvl-')[1]) : '';
    }

    if (['Before', 'After'].includes(route)) {
        newRow.id = proj_url + '_task_' + route + '_' + new Date().getTime();
        newRow.classList = 'lvl-' + cur_lvl + ' ' + class_type;
        newRow.setAttribute("data-lvl", cur_lvl);
        newRow.setAttribute("data-task", task_id_tmp);
        newRow.setAttribute("data-task_responsible", task_responsible_id_tmp);

        //Ищем всех детей у копируемой строки
        while (
            (route === 'Before' &&
                (nextRow && !nextRow.classList.contains(className) && !child_colspan || nextRow && nextRow.classList.contains(className) && child_colspan)) ||
            (route === 'After' &&
                nextRow && (tow_lvl > cur_lvl && !child_colspan || tow_lvl === cur_lvl && child_colspan))
            ) {

            child_colspan = child_colspan ? child_colspan - 1 : child_colspan;
            tow_lvl = parseInt(nextRow.classList[0].split('lvl-')[1])

            //Создаём список детей (те, чей лвл вложенности выше)
            if (tow_lvl > cur_lvl && !child_colspan || tow_lvl === cur_lvl && child_colspan) {
                child_cnt++;
                child = nextRow.cloneNode(true);

                //Если дети имеют объединенные ячейки (is_child_colspan), создаем новый task_id
                if (child.getElementsByClassName("col-2")[0].getAttribute("rowspan")) {
                    is_child_colspan = child.getElementsByClassName("col-2")[0].getAttribute("rowspan") * 1;
                    child_task_id_tmp = `_New_task_${child_cnt}_${new Date().getTime()}`;
                    is_child_colspan--;
                } else if (is_child_colspan) {
                    //Если is_child_colspan не ноль, значит текущий ребенок объединен с ребенком выше
                    is_child_colspan--;
                } else {
                    child_task_id_tmp = `_New_task_${child_cnt}_${new Date().getTime()}`;
                }

                clearDataAttributeValue(child, true, true);

                if (child_colspan) {
                    child.setAttribute("data-task", task_id_tmp);
                    child.setAttribute("data-task_responsible", `_New_tr_${child_cnt}_${new Date().getTime()}`);
                } else {
                    child.setAttribute("data-task", child_task_id_tmp);
                    child.setAttribute("data-task_responsible", `_New_tr_${child_cnt}_${new Date().getTime()}`);
                }
                children_list.push(child);

                //Записываем номер и название задачи
                editTaskDescription(child.cells[0], child.cells[0].getElementsByTagName('input')[0].value, 'input_task_number');
                editTaskDescription(child.cells[1], child.cells[1].getElementsByTagName('input')[0].value, 'input_task_name');
                editTaskDescription(child.cells[2], child.cells[2].dataset.value, child.cells[2].classList[0]);
                editTaskDescription(child.cells[3], child.cells[3].dataset.value, child.cells[3].classList[0]);
                // if (class_type !== 'main_task') {

                    //Плановые трудозатраты
                    child_plan_labor_cost_value = child.cells[4].getElementsByTagName('input')[0].dataset.value;
                    editTaskDescription(child.cells[4], child_plan_labor_cost_value, 'input_task_plan_labor_cost');
                    child_plan_labor_cost_value = parseFloat(child_plan_labor_cost_value).toFixed(4) * 1.0;
                    child_plan_labor_cost_value = isNaN(child_plan_labor_cost_value) ? 0 : child_plan_labor_cost_value;
                    plan_labor_cost_value += child_plan_labor_cost_value;
                // }

                if (route === 'After') {
                    nextRow = nextRow.nextElementSibling;
                }
            }
            if (route === 'Before') {
                nextRow = nextRow.nextElementSibling;
            }
        }
    }

    //Плановые трудозатраты. Для пересчета тома и ИТОГО
    child_plan_labor_cost_value = class_type !== 'main_task'? newRow.cells[4].getElementsByTagName('input')[0].dataset.value:newRow.cells[2].getElementsByTagName('input')[0].dataset.value;
    child_plan_labor_cost_value = parseFloat(child_plan_labor_cost_value).toFixed(4) * 1.0;
    child_plan_labor_cost_value = isNaN(child_plan_labor_cost_value) ? 0 : child_plan_labor_cost_value;

    //Если копируем структуру вверх
    if (route === 'Before') {
        clearDataAttributeValue(newRow, true, true);

        row.parentNode.insertBefore(newRow, row);

        //Записываем номер и название задачи
        editTaskDescription(newRow.cells[0], newRow.cells[0].getElementsByTagName('input')[0].value, 'input_task_number');
        editTaskDescription(newRow.cells[1], newRow.cells[1].getElementsByTagName('input')[0].value, 'input_task_name');
        if (class_type !== 'main_task') {
            //Записываем изменения Исполнитель, Статус, Комментарий
            editTaskDescription(newRow.cells[2], newRow.cells[2].dataset.value, newRow.cells[2].classList[0]);
            editTaskDescription(newRow.cells[3], newRow.cells[3].dataset.value, newRow.cells[3].classList[0]);
            editTaskDescription(newRow.cells[4], newRow.cells[4].getElementsByTagName('input')[0].value, 'input_task_plan_labor_cost');
            editTaskDescription(newRow.cells[0], newRow.getElementsByClassName('input_task_responsible_comment')[0].value, 'input_task_responsible_comment');

            //Обновляем статус видимости кнопки "Удалить строку", в случае если нет платновых/фактических задач
            if (newRow.cells[4].getElementsByTagName('input')[0].dataset.value || newRow.cells[5].innerText) {
                task_number.className = 'div_tow_button';
            }

            //Плановые трудозатраты. Для пересчета тома и ИТОГО
            plan_labor_cost_value += child_plan_labor_cost_value;
            replacePlanLaborCostWeekSum(newRow, plan_labor_cost_value);

        }
        else {
            //Добавляем в userChanges информацию о main_task
            editTaskDescription(newRow.cells[0], true, 'main_task');

            //Плановые трудозатраты. Для пересчета ИТОГО
            let last_row = tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0];
            let lr_data_value = parseFloat(last_row.dataset.value).toFixed(4) * 1.0;
            lr_data_value = isNaN(lr_data_value)? 0:lr_data_value;
            lr_data_value = parseFloat(lr_data_value + child_plan_labor_cost_value).toFixed(4) * 1.0;
            let lr_value = lr_data_value;
            lr_value = lr_value ? '📅' + lr_value : '';
            tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].value = lr_value;
            tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].dataset.value = lr_data_value;
        }

        //Проходим по списку детей
        for (var i=0; i<children_list.length; i++) {
            tow = children_list[i];
            //Создаём временное id для каждого ребенка
            tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
            child_lvl = parseInt(tow.classList[0].split('lvl-')[1])
            newRow.parentNode.insertBefore(tow, row);

            // Настраиваем кнопки
            task_number = tow.getElementsByClassName("col-1")[0].getElementsByTagName('div')[0];
            task_name = tow.getElementsByClassName("col-2")[0].getElementsByTagName('div')[0];
            task_number.className = 'div_tow_button';
            task_name.className = 'div_tow_button';
            addButtonsForNewTask(task_number);
            addButtonsForNewTask(task_name);

            //Определяем родителя текущего ребенка
            if (i===0) {
                pre_child_lvl = parseInt(newRow.classList[0].split('lvl-')[1]);
                preChildRow = newRow;
            }
            else {
                pre_child_lvl = parseInt(children_list[i-1].classList[0].split('lvl-')[1]);
                preChildRow = children_list[i-1];
            }
            p_id = findParent(curRow_fP=tow, cur_lvl_fP=child_lvl, pre_lvl_fP=pre_child_lvl, preRow_fP=preChildRow);

            //Записываем все изменения для детей
            child_t_id = tow.dataset.task;  // task_id
            child_tr_id = tow.dataset.task_responsible;  // task_responsible_id
            UserChangesTaskLog(c_id=child_t_id, tr_id=child_tr_id, rt='New', c_row=tow, parent_id=p_id); // Before - new child row
            // //Записываем изменения Исполнитель, Статус, Комментарий
            // editTaskDescription(tow.cells[2], tow.cells[2].dataset.value, tow.cells[2].classList[0]);
            // editTaskDescription(tow.cells[3], tow.cells[3].dataset.value, tow.cells[3].classList[0]);
            // editTaskDescription(tow.cells[0], tow.getElementsByClassName('input_task_responsible_comment')[0].value, 'input_task_responsible_comment');
        }

        //Определяем родителя скопированного родителя
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        //Записываем все изменения для родителя
        UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp, rt=route, c_row=newRow, parent_id=p_id); // Before - new row
        // editTaskDescription(button='', type='select_tow_dept', editDescription_row=newRow);
        // editTaskDescription(button='', type='checkbox_time_tracking', editDescription_row=newRow);

        return true;
    }

    //Если копируем структуру вниз
    else if (route === 'After') {
        clearDataAttributeValue(newRow, true, true);

        //Если после копируемой структуры есть ещё строка, вставляем скопированное над этой строкой
        if (nextRow) {
            //Если в структуре есть дети
            if (children_list.length){
                if (className === 'lvl-0') {
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
                    child_lvl = parseInt(tow.classList[0].split('lvl-')[1])
                    newRow.parentNode.insertBefore(tow, nextRow);

                    // Настраиваем кнопки
                    task_number = tow.getElementsByClassName("col-1")[0].getElementsByTagName('div')[0];
                    task_name = tow.getElementsByClassName("col-2")[0].getElementsByTagName('div')[0];
                    task_number.className = 'div_tow_button';
                    task_name.className = 'div_tow_button';
                    addButtonsForNewTask(task_number);
                    addButtonsForNewTask(task_name);

                    //Определяем родителя текущего ребенка
                    if (i==0) {
                        pre_child_lvl = parseInt(newRow.classList[0].split('lvl-')[1]);
                        preChildRow = newRow;
                    }
                    else {
                        pre_child_lvl = parseInt(children_list[i-1].classList[0].split('lvl-')[1]);
                        preChildRow = children_list[i-1];
                    }
                    p_id = findParent(curRow_fP=tow, cur_lvl_fP=child_lvl, pre_lvl_fP=pre_child_lvl, preRow_fP=preChildRow);

                    //Записываем все изменения для детей
                    child_t_id = tow.dataset.task;  // task_id
                    child_tr_id = tow.dataset.task_responsible;  // task_responsible_id
                    UserChangesTaskLog(c_id=child_t_id, tr_id=child_tr_id, rt='New', c_row=tow, parent_id=p_id); // After - new child row
                    // //Записываем изменения Исполнитель, Статус, Комментарий
                    // editTaskDescription(tow.cells[2], tow.cells[2].dataset.value, tow.cells[2].classList[0]);
                    // editTaskDescription(tow.cells[3], tow.cells[3].dataset.value, tow.cells[3].classList[0]);
                    // editTaskDescription(tow.cells[0], tow.getElementsByClassName('input_task_responsible_comment')[0].value, 'input_task_responsible_comment');
                }
            }
            //В структуре нет детей, просто вставляем копию под текущую строку
            else {
                nextRow.parentNode.insertBefore(newRow, row.nextSibling);
            }
            var newRow_lvl = parseInt(newRow.classList[0].split('lvl-')[1]);
        }
        //После копируемой структуры нет срок (конец таблицы)
        else {
            row.parentNode.appendChild(newRow);

            newRow_lvl = parseInt(newRow.className.split('lvl-')[1]);

            //Если в структуре есть дети
            if (children_list.length) {
                //Проходим по списку детей
                for (var i = 0; i < children_list.length; i++) {
                    tow = children_list[i];
                    //Создаём временное id для каждого ребенка
                    tow.id = proj_url + '_' + newRow.id + '_' + i + '_New_' + new Date().getTime();
                    child_lvl = parseInt(tow.className.split('lvl-')[1])
                    row.parentNode.appendChild(tow);

                    // Настраиваем кнопки
                    task_number = tow.getElementsByClassName("col-1")[0].getElementsByTagName('div')[0];
                    task_name = tow.getElementsByClassName("col-2")[0].getElementsByTagName('div')[0];
                    task_number.className = 'div_tow_button';
                    task_name.className = 'div_tow_button';
                    addButtonsForNewTask(task_number);
                    addButtonsForNewTask(task_name);

                    //Определяем родителя текущего ребенка
                    if (i == 0) {
                        pre_child_lvl = parseInt(newRow.classList[0].split('lvl-')[1]);
                        preChildRow = newRow;
                    } else {
                        pre_child_lvl = parseInt(children_list[i - 1].classList[0].split('lvl-')[1]);
                        preChildRow = children_list[i - 1];
                    }
                    p_id = findParent(curRow_fP = tow, cur_lvl_fP = child_lvl, pre_lvl_fP = pre_child_lvl, preRow_fP = preChildRow);

                    //Записываем все изменения для детей
                    child_t_id = tow.dataset.task;  // task_id
                    child_tr_id = tow.dataset.task_responsible;  // task_responsible_id
                    UserChangesTaskLog(c_id=child_t_id, tr_id=child_tr_id, rt='New', c_row = tow, parent_id=p_id); // After - new child row End of table
                    // //Записываем изменения Исполнитель, Статус, Комментарий
                    // editTaskDescription(tow.cells[2], tow.cells[2].dataset.value, tow.cells[2].classList[0]);
                    // editTaskDescription(tow.cells[3], tow.cells[3].dataset.value, tow.cells[3].classList[0]);
                    // editTaskDescription(tow.cells[0], tow.getElementsByClassName('input_task_responsible_comment')[0].value, 'input_task_responsible_comment');

                }
            }
        }
        //Определяем родителя скопированного родителя
        preRow = newRow.previousElementSibling;
        pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=newRow_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        //Записываем все изменения для родителя
        UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp, rt=route, c_row=newRow, parent_id=p_id);  // After - new row End of table
        // editTaskDescription(button='', type='select_tow_dept', editDescription_row=newRow);

        //Записываем номер и название задачи
        editTaskDescription(newRow.cells[0], newRow.cells[0].getElementsByTagName('input')[0].value, 'input_task_number');
        editTaskDescription(newRow.cells[1], newRow.cells[1].getElementsByTagName('input')[0].value, 'input_task_name');
        if (class_type !== 'main_task') {
            //Записываем изменения Исполнитель, Статус, Комментарий
            editTaskDescription(newRow.cells[2], newRow.cells[2].dataset.value, newRow.cells[2].classList[0]);
            editTaskDescription(newRow.cells[3], newRow.cells[3].dataset.value, newRow.cells[3].classList[0]);
            editTaskDescription(newRow.cells[4], newRow.cells[4].getElementsByTagName('input')[0].value, 'input_task_plan_labor_cost');
            editTaskDescription(newRow.cells[0], newRow.getElementsByClassName('input_task_responsible_comment')[0].value, 'input_task_responsible_comment');

            //Плановые трудозатраты. Для пересчета тома и ИТОГО
            plan_labor_cost_value += child_plan_labor_cost_value;
            replacePlanLaborCostWeekSum(newRow, plan_labor_cost_value)

            //Обновляем статус видимости кнопки "Удалить строку", в случае если нет плановых/фактических задач
            if (newRow.cells[4].getElementsByTagName('input')[0].dataset.value || newRow.cells[5].innerText) {
                task_number.className = 'div_tow_button';
            }
        }
        else {
            //Добавляем в userChanges информацию о main_task
            editTaskDescription(newRow.cells[0], true, 'main_task');
            //Обновляем статус видимости кнопки "Удалить строку", в случае если нет плановых/фактических задач
            if (newRow.cells[2].getElementsByTagName('input')[0].dataset.value || newRow.cells[3].innerText) {
                task_number.className = 'div_tow_button';
            }

            //Плановые трудозатраты. Для пересчета ИТОГО
            let last_row = tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0];
            let lr_data_value = parseFloat(last_row.dataset.value).toFixed(4) * 1.0;
            lr_data_value = isNaN(lr_data_value)? 0:lr_data_value;
            lr_data_value = parseFloat(lr_data_value + child_plan_labor_cost_value).toFixed(4) * 1.0;
            let lr_value = lr_data_value;
            lr_value = lr_value ? '📅' + lr_value : '';
            tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].value = lr_value;
            tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].dataset.value = lr_data_value;
        }

        //Проскроливаем до новой строки
        newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

        return true;
    }

    if  (!['Left', 'Right', 'Up', 'Down'].includes(route)) {
        return false;
    }

    //Ищем всех детей у копируемой строки
    child_colspan = is_colspan
    let check_first_next_row = class_type === 'main_task';  //Для проверки следующей строки, если перемещаем начиная с main_task

    if (nextRow) {
        let nextRow_className = nextRow.classList[0];
        child_lvl = parseInt(nextRow_className.split('lvl-')[1]);
    }

    while (nextRow && (child_lvl > cur_lvl && !child_colspan || child_lvl === cur_lvl && child_colspan || check_first_next_row)) {
        child_colspan = child_colspan ? child_colspan - 1 : child_colspan;
        child_lvl = parseInt(nextRow.classList[0].split('lvl-')[1]);
        check_first_next_row = false;

        //Создаём список детей (те, чей лвл вложенности выше)
        if (child_lvl > cur_lvl && !child_colspan || child_lvl === cur_lvl && child_colspan) {

            if (route === 'Right') {
                nextRow.classList.replace(nextRow.classList[0], 'lvl-' + (child_lvl+1))
            }
            if (route === 'Left') {
                nextRow.classList.replace(nextRow.classList[0], 'lvl-' + (child_lvl-1))
            }

            let child = nextRow;

            children_list.push(child)
            nextRow = nextRow.nextElementSibling;
        }
    }

    //Проверка, на нарушения предельного сдвига вправо/влево
    if (route === 'Right') {
        if (tow_lvl+1 > 3 || child_lvl > 3) {
            return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности']);
        }
    }

    if (route === 'Left') {
        if (tow_lvl < 0) {
            return createDialogWindow(status='error', description=['Ошибка', 'Уровень вложенности не может быть меньше 1']);
        }
        if (is_colspan) {
            return createDialogWindow(status='error', description=['Ошибка', 'Задачу с несколькими исполнителями нельзя переместить влево']);
        }
        //Если есть плановые и фактические трудозатраты
        if (row.className === "lvl-1 task" &&
                (row.cells[4].getElementsByTagName('input')[0].value || row.cells[5].innerText)) {
            return createDialogWindow(status='error', description=['Ошибка', 'Задачу с плановыми/фактическими трудозатратми нельзя преобразовать в ТОМ']);
        }
        //Если перемещаем main_task
        if (cur_lvl === 0) {
            return createDialogWindow(status='error', description=['Ошибка', 'Достигнут максимальный уровень смещения влево']);
        }

    }
    if  (['Left', 'Right'].includes(route)) {
        for (child of children_list) {
            let child_tow_lvl = parseInt(child.classList[0].split('lvl-')[1]);
            if (route === 'Right') {
                if (child_tow_lvl+1 > 3) {
                    return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности']);
                }
            }
            if (route === 'Left') {
                if (child_tow_lvl < 0) {
                    return createDialogWindow(status='error', description=['Ошибка', 'Уровень вложенности не может быть меньше 1']);
                }
            }
        }
    }

    if (route === 'Right') {
        newRow.getElementsByClassName("col-2")[0].removeAttribute("rowspan");
        newRow.classList.replace(newRow.classList[0], 'lvl-' + (cur_lvl));
        newRow.setAttribute("data-lvl", cur_lvl);

        row.classList.replace(row.classList[0], 'lvl-' + (cur_lvl+1));
        row.setAttribute("data-lvl", (cur_lvl+1));

        newRow.id = proj_url + '_' + route + '_' + new Date().getTime();
        newRow.setAttribute("data-task", task_id_tmp);
        newRow.setAttribute("data-task_responsible", task_responsible_id_tmp);

        //Если сдвинули main_task, то превращаем её в task
        if (class_type === 'main_task') {
            //Меняем тип задачи
                row.className = "lvl-1 task";
            //Удаляем объединение столбцов
                row.cells[1].removeAttribute("colspan");
            //Меняем класс ячейки названия задачи
                row.cells[1].className = "td_task_task_name sticky-cell col-2";
            //Добавляем кнопку "Добавить соисполнителя"
                let div_tow_button = row.cells[1].getElementsByClassName('div_tow_button')[0];
                let addResponsibleNew = document.createElement("button");
                addResponsibleNew.className = "tow addResponsibleNew";
                addResponsibleNew.setAttribute("title", "Добавить ответственного");
                addResponsibleNew.addEventListener('click', function() {addTow(this, 'addResponsibleNew');});
                    let imgElement = document.createElement("img");
                    imgElement.src = "/static/img/object/tow/task_add_responsible.svg";
                    addResponsibleNew.appendChild(imgElement);
                div_tow_button.appendChild(addResponsibleNew);
            //Меняем класс инпута названия задачи
                row.cells[1].getElementsByClassName('input_main_task_task_name')[0].className = "input_task_name";
            //Добавляем 2 ячейки - исполнитель/статус
                let newCellResponsibleUser = row.insertCell(2);
                newCellResponsibleUser.className = "td_task_responsible_user sticky-cell col-3";
                newCellResponsibleUser.addEventListener('click', function() {editResponsibleOrStatus(this);});

                let newCellTaskStatuses = row.insertCell(3);
                newCellTaskStatuses.className = "td_tow_task_statuses sticky-cell col-4";
                newCellTaskStatuses.addEventListener('click', function() {editResponsibleOrStatus(this);});
            //Меняем тип инпута у плановых трудозатрат и разблокируем input
                row.cells[4].getElementsByTagName('input')[0].setAttribute("type", "number");
                row.cells[4].getElementsByTagName('input')[0].setAttribute("step", "0.01");
                row.cells[4].getElementsByTagName('input')[0].placeholder = "...";
                row.cells[4].getElementsByTagName('input')[0].disabled = 0;
            //Разблокируем комментарий
                row.getElementsByClassName('input_task_responsible_comment')[0].disabled = 0;
            //Очищаем данные о часах
                clearDataAttributeValue(row, true);

            //Добавляем в userChanges информацию о main_task == false
                editTaskDescription(row.cells[0], false, 'main_task');
        }
        else {
            clearDataAttributeValue(newRow);
        }
        // var textInputs = newRow.querySelectorAll('input[type="text"]');
        // textInputs.forEach(function (input) {
        //     input.value = '';
        // });

        row.parentNode.insertBefore(newRow, row);

        preRow = newRow.previousElementSibling? newRow.previousElementSibling: row;
        pre_lvl = preRow? parseInt(preRow.classList[0].split('lvl-')[1]):cur_lvl;
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp,rt='New', c_row=newRow, parent_id=p_id); // Right - parent-new row
        UserChangesTaskLog(t_id = t_id, tr_id = tr_id, rt=route, c_row=row, parent_id=newRow.dataset.task); // Right - current row

        return true;
    }

    else if (route === 'Up') {
        let tow_values_list = class_type !== 'main_task'? recalcWeekSum(row, preRow, ): false;
        while (preRow) {
            tow_lvl = parseInt(preRow.classList[0].split('lvl-')[1])
            prePreRow = preRow.previousElementSibling;
            if (prePreRow) {
                pre_lvl = parseInt(prePreRow.classList[0].split('lvl-')[1]);
            }
            else if (tow_lvl !== cur_lvl && !prePreRow) {
                return createDialogWindow(status='error', description=['Ошибка', 'Перемещение невозможно', 'В структуре выше нет подходящего по уровню вида работ']);
            }
            //Если перемещаем не main_task и переходим в другую main_task, то пересчитываем сумму часов в строке старой и новой main_task
            if (class_type !== 'main_task' && preRow && preRow.classList[preRow.classList.length-1] === 'main_task') {
                //Если есть дети, пересчитываем
                if (children_list.length){
                    for (children of children_list) {
                        tow_values_list = recalcWeekSum(children, preRow, tow_values_list);
                    }
                }
                if (tow_values_list) {
                    //Глубокое копирование списка значений
                    let deepCopy_tow_values_list = JSON.parse(JSON.stringify(tow_values_list));
                    recalcMainTaskWeekSum(deepCopy_tow_values_list, preRow, 'old');
                }
                let main_task_index = $(tab_tr0).find(".main_task").toArray().indexOf(preRow)
                if (main_task_index > 0) {
                    let new_main_task = $(tab_tr0).find(".main_task").toArray()[main_task_index-1];
                    recalcMainTaskWeekSum(tow_values_list, new_main_task, 'new');
                }
            }

            if (!preRow.cells[1].hidden && (tow_lvl === cur_lvl || (tow_lvl < cur_lvl && pre_lvl === cur_lvl) || pre_lvl+1 === cur_lvl)) {
                row.parentNode.insertBefore(row, preRow);

                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=prePreRow);

                UserChangesTaskLog(t_id=t_id, tr_id=tr_id,rt=route, c_row=row, parent_id=p_id); // Up - current row
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.insertBefore(tow, preRow);
                    }
                }

                //Проскроливаем до новой строки
                if (row.rowIndex > 2) {
                    row.previousElementSibling.previousElementSibling.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                else {
                    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }

                return true;
            }
            preRow = preRow.previousElementSibling;

        }
        return createDialogWindow(status='error', description=['Ошибка', '✨ Перемещение невозможно. Выше только звёзды 🌌']);
    }
    else if (['Down', 'Left'].includes(route)) {
        var extra_row = 1; //Дополнительная строка, для кнопки "вниз" - это плюс один. Иначе нуль

        //Если перемещаем строки вниз и переходим в другую main_task, нужно пересчитать значение недели
        let old_main_task = null;
        let new_main_task = null;
        let tow_values_list = class_type !== 'main_task'? recalcWeekSum(row, nextRow, ): false;

        if (route === 'Left') {
            cur_lvl = cur_lvl-1;
            row.classList.replace(row.classList[0], 'lvl-' + (cur_lvl));
            row.setAttribute("data-lvl", cur_lvl);

            // //Обновляем данные об task_tid и tr_id
            // newRow.setAttribute("data-task", task_id_tmp);
            // newRow.setAttribute("data-task_responsible", task_responsible_id_tmp);
            //
            // //Добавляем информацию о создании новой строки в список новых строк
            // calcNewRowObj(task_id_tmp, ask_responsible_id_tmp, 'new')
            //Если задача становится main_task
            if (cur_lvl===0) {
                row.classList.replace(row.classList[row.classList.length-1], 'main_task');  //переименовываем стиль строки
                row.cells[1].getElementsByClassName('input_task_name')[0].className = "input_main_task_task_name"; //переименовываем стиль input task_name
                row.deleteCell(2); //Удаляем ячейку Исполнитель
                row.deleteCell(2); //Удаляем ячейку Статус
                row.cells[1].setAttribute("colspan", 3); //Объединяем 3 столбца наименования задачи
                row.cells[1].getElementsByClassName('addResponsibleNew')[0].remove();  //Удаляем кнопку "Добавить соисполнителя"
                //очищаем и блокируем input Плановые трудозатраты
                row.cells[2].getElementsByTagName('input')[0].value = '';
                row.cells[2].getElementsByTagName('input')[0].dataset.value = '';
                row.cells[2].getElementsByTagName('input')[0].disabled = true;
                row.cells[2].getElementsByTagName('input')[0].removeAttribute("placeholder");
                //очищаем и блокируем input Комментария
                row.cells[row.cells.length-1].getElementsByTagName('input')[0].value = '';
                row.cells[row.cells.length-1].getElementsByTagName('input')[0].dataset.value = '';
                row.cells[row.cells.length-1].getElementsByTagName('input')[0].disabled = true;
                row.cells[row.cells.length-1].getElementsByTagName('input')[0].removeAttribute("placeholder");

                //Мы должны удалить запись о tr в БД, по этому добавляем запись об удалении строки tr и обнуляем dataset.task_responsible
                if (row.dataset.task_responsible != 'None') {
                    calcNewRowObj(row.dataset.task, row.dataset.task_responsible);
                    row.dataset.task_responsible = 'None';
                    //Добавляем запись о новой строке, если это вновь созданная строка
                    if (row.dataset.task.indexOf('_New') >= 0) {
                        calcNewRowObj(row.dataset.task, row.dataset.task_responsible, 'new');
                    }
                }

                //Добавляем в userChanges информацию о main_task
                editTaskDescription(row.cells[0], true, 'main_task');

                //Меняем тип инпута у плановых трудозатрат
                row.cells[2].getElementsByTagName('input')[0].setAttribute("type", "text");

                // //Добавляем информацию о подзадаче
                // console.log('left_1.rowIndex', newRow.rowIndex, newRow)
                // UserChangesTaskLog(task_id_tmp, task_responsible_id_tmp, 'New', newRow, t_id); // Left - NewRow
            }
            extra_row = 0;
            if (!nextRow || nextRow.classList[nextRow.classList.length-1] === 'last_row') {

                // clearDataAttributeValue(newRow);
                // row.parentNode.insertBefore(newRow, row.nextElementSibling);

                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.classList[0].split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

                UserChangesTaskLog(t_id=row.dataset.task, tr_id=row.dataset.task_responsible, rt=route, c_row=row, parent_id=p_id); // Left - current row

                return;
            }
        }

        while (nextRow) {
            tow_lvl = parseInt(nextRow.classList[0].split('lvl-')[1])
            nextNextRow = nextRow.nextElementSibling;
            if (isNaN(tow_lvl)) {
                return createDialogWindow(status='error', description=['Ошибка', 'Перемещение невозможно v-1', 'В структуре ниже нет подходящей по уровню задачи']);
            }

            if (nextNextRow) {
                var next_lvl = parseInt(nextNextRow.classList[0].split('lvl-')[1])
            }
            else if (!nextNextRow &&  cur_lvl > tow_lvl + extra_row) {
                return createDialogWindow(status='error', description=['Ошибка', 'Перемещение невозможно v-2', 'В структуре ниже нет подходящей по уровню задачи']);
            }
            var row_after = nextRow;

            ver1 = 0;
            ver2 = 0;
            ver3 = 0;
            // Уровень текущей строки (tow) РАВЕН нажатой строки и номер текущей строки не равен нажатой + размер всех детей
            if (tow_lvl == cur_lvl && row.rowIndex + children_list.length + extra_row != nextRow.rowIndex && !nextRow.cells[1].hidden) {
                row_after = nextRow;
                ver1 = 1;
            }
            else if (tow_lvl >= cur_lvl && cur_lvl > next_lvl || isNaN(next_lvl) ) {
                // Уровень текущей строки (tow) БОЛЬШЕ нажатой строки и уровень нажатой строки БОЛЬШЕ следующей
                row_after = nextNextRow;
                ver2 = 1;
            }
            else if (cur_lvl == tow_lvl + 1) {
                // В противном случае, если текущая строка на уровень меньше нажатой строки
                row_after = route == 'Left'? nextRow:nextNextRow;
                ver3 = 1;
            }

            //Запоминаем main_task в которую "зашли"
            if (route === 'Down' && class_type !== 'main_task' && nextRow && nextRow.classList[nextRow.classList.length-1] === 'main_task') {
                new_main_task = nextRow
                //Если изначальная main_task ещё не найдена, находим её
                if (!old_main_task){
                    let main_tasks_list = $(tab_tr0).find(".main_task").toArray(); //Список всех главных задач, нужно для пересчета суммы недели
                    old_main_task = main_tasks_list.indexOf(nextRow) - 1;
                    old_main_task = main_tasks_list[old_main_task];
                }
            }

            if (ver1 || ver2 || ver3) {
                row.parentNode.insertBefore(row, row_after);
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.insertBefore(tow, row_after);
                    }
                }
                // if (route === 'Left') {
                //     //Если нет детей и перемещали влево, добавим пустую подзадачу
                //     clearDataAttributeValue(newRow);
                //     console.log('Left', newRow)
                //
                //     row.parentNode.insertBefore(newRow, row.nextElementSibling);
                // }

                preRow = row.previousElementSibling;
                let preRow_lvl = parseInt(preRow.classList[0].split('lvl-')[1]);

                prePreRow = preRow.previousElementSibling;
                pre_pre_lvl = prePreRow? parseInt(prePreRow.classList[0].split('lvl-')[1]):preRow_lvl;
                prePreRow = prePreRow? prePreRow:preRow;

                p_preRow_id = findParent(curRow_fP=preRow, cur_lvl_fP=preRow_lvl, pre_lvl_fP=pre_pre_lvl,preRow_fP=prePreRow);


                pre_lvl = parseInt(preRow.classList[0].split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

                UserChangesTaskLog(t_id = task_id_tmp, tr_id = task_responsible_id_tmp,rt=route, c_row=row, parent_id=p_id); // ['Down', 'Left'] - current row
                UserChangesTaskLog(t_id = t_id, tr_id = tr_id, rt=route, c_row=preRow, parent_id=p_preRow_id); // ['Down', 'Left'] - previous row

                // if (route === 'Down') {
                //     //Проскроливаем до новой строки
                //     row.scrollIntoView({behavior: 'smooth', block: 'start'});
                // }

                //Если перемещаем не main_task и переходим в другую main_task, то пересчитываем сумму часов в строке старой и новой main_task
                if (route === 'Down' && old_main_task) {
                    //Если есть дети, пересчитываем
                    if (children_list.length){
                        for (children of children_list) {
                            tow_values_list = recalcWeekSum(children, old_main_task, tow_values_list);
                        }
                    }
                    if (tow_values_list) {
                        //Глубокое копирование списка значений
                        let deepCopy_tow_values_list = JSON.parse(JSON.stringify(tow_values_list));
                        recalcMainTaskWeekSum(deepCopy_tow_values_list, old_main_task, 'old');
                    }

                    recalcMainTaskWeekSum(tow_values_list, new_main_task, 'new');

                }

                return;
            }
            else if (!nextNextRow && (tow_lvl === cur_lvl || (tow_lvl >= cur_lvl && pre_lvl === cur_lvl) || cur_lvl === tow_lvl + 1)) {
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.appendChild(tow);
                    }
                    row.parentNode.insertBefore(row, children_list[0]);
                }
                else {
                    row.parentNode.appendChild(row);
                    //Если нет детей и перемещали влево, добавим пустую подзадачу

                    // row.parentNode.appendChild(newRow);
                }
                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.classList[0].split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

                UserChangesTaskLog(t_id = t_id, tr_id = tr_id, rt=route, c_row=row, parent_id=p_id); // ['Down', 'Left'] - current row last row in table

                return;
            }

            nextRow = nextRow.nextElementSibling;
        }
        return createDialogWindow(status='error', description=['Ошибка', '🐋 Перемещение невозможно v-3. Вы в самом низу структуры 🤿']);
    }
}

function clearDataAttributeValue(tow_cdav, taskName=false, responsibleAndStatus=false) {
    //При копировании структуры оставляем названия задач, исполнитель, статус, план
    //При добавлении соисполнителя оставляем название, удаляем исполнителя, статус и план
    //При создании новой строки удаляем названия задач, исполнитель, статус, план
    //Очищаем номер и название задачи
    if (!taskName) {
        tow_cdav.getElementsByClassName("input_task_number")[0].value = '';
        tow_cdav.getElementsByClassName("input_task_number")[0].dataset.value = 0;

        tow_cdav.getElementsByClassName("input_task_name")[0].value = '';
        tow_cdav.getElementsByClassName("input_task_name")[0].dataset.value = 0;
    }
    //Очищаем Ответственного и Статус, План
    if (!responsibleAndStatus) {
        tow_cdav.getElementsByClassName("td_task_responsible_user")[0].innerText = '...';
        tow_cdav.getElementsByClassName("td_task_responsible_user")[0].dataset.value = 0;

        tow_cdav.getElementsByClassName("td_tow_task_statuses")[0].innerText = '...';
        tow_cdav.getElementsByClassName("td_tow_task_statuses")[0].dataset.value = 0;

        tow_cdav.getElementsByClassName("input_task_plan_labor_cost")[0].value = '';
        tow_cdav.getElementsByClassName("input_task_plan_labor_cost")[0].dataset.value = 0;
    }

    //добавляем триггер на изменение название вида работ
    let input_task_number = tow_cdav.getElementsByClassName("input_task_number");
    input_task_number[0].removeEventListener("change", editTaskDescription);
    input_task_number[0].addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_number');})

    //добавляем триггер на изменение название вида работ
    let input_task_name = tow_cdav.getElementsByClassName("input_task_name");
    input_task_name = input_task_name.length > 0 ? input_task_name : tow_cdav.getElementsByClassName("input_main_task_task_name");
    input_task_name[0].removeEventListener("change", editTaskName);
    input_task_name[0].addEventListener('change', function() {editTaskName(this, this.value);})

    //добавляем триггер на изменение плановых трудозатрат
    let input_task_plan_labor_cost = tow_cdav.getElementsByClassName("input_task_plan_labor_cost");
    input_task_plan_labor_cost[0].removeEventListener("change", recalcPlanLaborCostWeekSum);
    input_task_plan_labor_cost[0].addEventListener('change', function() {recalcPlanLaborCostWeekSum(this);})

    //добавляем триггер на изменение комментария
    let input_task_responsible_comment = tow_cdav.getElementsByClassName("input_task_responsible_comment");
    input_task_responsible_comment[0].removeEventListener("change", editTaskDescription);
    input_task_responsible_comment[0].addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_responsible_comment');})

    // Убираем запрет на изменение Ответственного
    let tow_cdav_dataset_responsible = tow_cdav.querySelectorAll("[data-editing_is_prohibited]");
    tow_cdav_dataset_responsible.forEach(function (input) {
        if (input.dataset.value) {
            if (!responsibleAndStatus) {
                input.dataset.value = '';
            }
            input.dataset.editing_is_prohibited = 'None';
        }
    });

    // Очищаем факт ч.дни
    let fact_labor_cost = tow_cdav.getElementsByClassName('td_task_fact_labor_cost');
    if (fact_labor_cost.length) {
        fact_labor_cost[0].innerText = '';
    }

    // Очищаем прогноз
    let forecast_labor_cost = tow_cdav.getElementsByClassName('td_task_forecast_labor_cost');
    if (forecast_labor_cost.length) {
        forecast_labor_cost[0].innerText = '';
    }

    // Очищаем предыдущий и будущий период
    let sum_previous_fact = tow_cdav.getElementsByClassName('td_tow_sum_previous_fact');
    if (sum_previous_fact.length) {
        sum_previous_fact[0].innerText = '';
    }
    let td_task_sum_future_fact = tow_cdav.getElementsByClassName('td_task_sum_future_fact');
    if (td_task_sum_future_fact.length) {
        td_task_sum_future_fact[0].innerText = '';
    }

    // Очищаем ЗНАЧЕНИЯ td_task_labor_cost_sum_week и td_task_labor_cost_week_day
    let td_task_labor_cost_sum_week = tow_cdav.querySelectorAll(".td_task_labor_cost_sum_week");
    td_task_labor_cost_sum_week.forEach(function (input) {
        if (input.innerText) {
            input.innerText = '';
        }
    });
    let td_task_labor_cost_week_day = tow_cdav.querySelectorAll(".td_task_labor_cost_week_day");
    td_task_labor_cost_week_day.forEach(function (input) {
        if (input.innerText) {
            input.innerText = '';
        }
    });

    // Очищаем комментарии
    let textComment = tow_cdav.getElementsByClassName('input_task_responsible_comment');
    if (textComment.length) {
        textComment[0].value = '';
        textComment[0].dataset.value = '';
    }

    // Добавляем функцию для вызова окна "Ответственный и Статус задачи"
    // Ответственный
    let td_task_responsible_user = tow_cdav.getElementsByClassName('td_task_responsible_user');
    for (let i of td_task_responsible_user) {
        if (i.dataset.editing_is_prohibited == 'None') {
            i.addEventListener('click', function () {editResponsibleOrStatus(this);});
        }
    }

    //Статус задачи
    let td_tow_task_statuses = tow_cdav.getElementsByClassName('td_tow_task_statuses');
    for (let i of td_tow_task_statuses) {
        i.addEventListener('click', function() {editResponsibleOrStatus(this);});
    }
}

function findParent(curRow_fP, cur_lvl_fP, pre_lvl_fP, preRow_fP) {
    var p_id = -1;
    if (curRow_fP.classList[0] === 'lvl-0') {
        p_id = 'None';
        return p_id;
    }
    else {
        if (cur_lvl_fP-1 === pre_lvl_fP) {
            p_id = preRow_fP.dataset.task;
        }
        else {
            while (cur_lvl_fP-1 !== pre_lvl_fP && preRow_fP) {
                pre_lvl_fP = parseInt(preRow_fP.classList[0].split('lvl-')[1]);
                if (!preRow_fP.previousElementSibling) {
                    return preRow_fP.dataset.task
                }
                preRow_fP = preRow_fP.previousElementSibling;
            }
            p_id = preRow_fP.nextElementSibling.dataset.task;
        }
    }
    if (p_id === -1) {
    }
    return p_id
}

//Пересчитываем сумму часов для main_tasl
function recalcWeekSum(tow, old_main_task, tow_values_list=[], ) {
    //проверяем, что у task есть плановые/факт часы
    if (!tow.getElementsByClassName('input_task_plan_labor_cost')[0].value && !tow.cells[5].innerText) {
        if (tow_values_list.length) {
            return tow_values_list;
        }
        else {
            let empty_lst = []
            for (let i=4; i<tow.cells.length-2; i++) {
                empty_lst.push('');
            }
            return empty_lst
        }
    }
    //Находим непустые часы в строке
    let tmp_values_list = [];
    //Ищем в ячейках от "План" до "след период"
    for (let i=4; i<tow.cells.length-2; i++) {
        let j = i-4;
        let cell_value = i === 4 ? tow.cells[i].getElementsByTagName('input')[0].value : tow.cells[i].innerText;
        if (cell_value.indexOf('📅') >= 0 || cell_value.indexOf('7️⃣') >= 0) {
            cell_value = cell_value.indexOf('📅') >= 0? cell_value.slice(2):cell_value.slice(3);
        }
        if (cell_value) {
            //Данные в формате HH:MM
            if (i > 7 && i < 41) {
                //Преобразовываем в список [HH, MM]
                cell_value = cell_value.split(':').map(Number)
                //Если есть список часов main_task, пересчитываем часы каждого дня
                if (tow_values_list.length) {
                    //Было пусто, добавляем значения cell_value, иначе пересчитываем
                    if (tow_values_list[j] === '') {
                         tow_values_list[j] = cell_value;
                    }
                    else {
                        tow_values_list[j][1] += cell_value[1];
                        tow_values_list[j][0] += cell_value[0] + Math.floor(tow_values_list[j][1]/60);
                        tow_values_list[j][1] = tow_values_list[j][1] % 60;
                    }
                }
            }
            //Данные - число
            else {
                cell_value = parseFloat(cell_value).toFixed(4) * 1.0;
                //Если есть список часов main_task, пересчитываем часы каждого дня
                if (tow_values_list.length) {
                    //Было пусто, добавляем значения cell_value, иначе пересчитываем
                    if (tow_values_list[j] === '') {
                         tow_values_list[j] = cell_value;
                    }
                    else {

                        tow_values_list[j] += cell_value;
                    }
                }
            }
        }
        if (!tow_values_list.length) {
            tmp_values_list.push(cell_value)
        }

    }
    if (tow_values_list.length) {
        return tow_values_list;
    }
    else {
        return tmp_values_list;
    }
}

function recalcMainTaskWeekSum(values_list, main_task, main_task_type) {
    if (main_task_type === 'old') {
        // отнимаем значения из main_task откуда перемещаем задани
        for (let i=2; i<main_task.cells.length-2; i++) {
            let j = i-2;
            let cell_value = i === 2 ? main_task.cells[i].getElementsByTagName('input')[0].value : main_task.cells[i].innerText;
            if (cell_value.indexOf('📅') >= 0 || cell_value.indexOf('7️⃣') >= 0) {
                cell_value = cell_value.indexOf('📅') >= 0? cell_value.slice(2):cell_value.slice(3);
            }
            //Если есть значения в списке, пересчитываем значение в main_task
            if (values_list[j]) {
                //Если почему-то не было значения в main_task вызываем ошибку и требуем перезагрузить страницу
                if (cell_value === '') {
                    document.addEventListener("keydown", function(event) {
                        if (event.key === "Escape") {
                            location.reload();
                            event.preventDefault();
                        }
                    });
                    return createDialogWindow(
                        status='error',
                        description=[
                            'Ошибка 2',
                            'Что-то пошло не так при формировании структуры задач',
                            'Обновите страницу'
                        ],
                        func=[['click', [reloadPage]]],
                    );
                }
                //Данные в формате HH:MM
                if (i > 5 && i < 39) {
                    //Преобразовываем в список [HH, MM]
                    cell_value = cell_value.split(':').map(Number);
                    values_list[j][1] = cell_value[1] - values_list[j][1];
                    values_list[j][0] = cell_value[0] - Math.floor(values_list[j][1]/60) - values_list[j][0];
                    values_list[j][1] = values_list[j][1] % 60;

                }
                //Данные - число
                else {
                    cell_value = parseFloat(cell_value).toFixed(4) * 1.0;
                    values_list[j] = parseFloat(cell_value - values_list[j]).toFixed(4) * 1.0;
                    values_list[j] = values_list[j]<0? 0:values_list[j];
                }

                if (values_list[j] && values_list[j] !== 0 && JSON.stringify(values_list[j]) !== JSON.stringify([0, 0])) {
                    //Преобразовываем числа в HH:MM
                    if (i>5) {
                        values_list[j][0] = values_list[j][0] < 10? '0'+values_list[j][0]:values_list[j][0];
                        values_list[j][1] = values_list[j][1] === 0? '00':values_list[j][1];

                        values_list[j] = `${values_list[j][0]}:${values_list[j][1]}`;
                    }
                    if ([6, 14, 22, 30].includes(i)) {
                        main_task.cells[i].innerText = '7️⃣' + values_list[j];
                    } else {
                        if (i === 2) {
                            main_task.cells[i].getElementsByTagName('input')[0].value = '📅' + values_list[j];
                            main_task.cells[i].getElementsByTagName('input')[0].dataset.value = values_list[j];
                        }
                        main_task.cells[i].innerText = '📅' + values_list[j];
                    }
                }
                else {
                    if ([6, 14, 22, 30].includes(i)) {
                        main_task.cells[i].innerText = '';
                    } else {
                        if (i === 2) {
                            main_task.cells[i].getElementsByTagName('input')[0].value = '';
                            main_task.cells[i].getElementsByTagName('input')[0].dataset.value = 'None';
                        }
                        main_task.cells[i].innerText = '';
                    }
                }
            }
        }
    }
    else {
        // отнимаем значения из main_task откуда перемещаем задани
        for (let i=2; i<main_task.cells.length-2; i++) {
            let j = i-2;
            let cell_value = i === 2 ? main_task.cells[i].getElementsByTagName('input')[0].value : main_task.cells[i].innerText;
            if (cell_value.indexOf('📅') >= 0 || cell_value.indexOf('7️⃣') >= 0) {
                cell_value = cell_value.indexOf('📅') >= 0? cell_value.slice(2):cell_value.slice(3);
            }
            //Если есть значения в списке, пересчитываем значение в main_task
            if (values_list[j]) {
                //Значения в main_task пусто
                if (cell_value !== '') {
                    //Данные в формате HH:MM
                    if (i > 5 && i < 39) {
                        //Преобразовываем в список [HH, MM]
                        cell_value = cell_value.split(':').map(Number);
                        values_list[j][1] = cell_value[1] + values_list[j][1];
                        values_list[j][0] = cell_value[0] + Math.floor(values_list[j][1] / 60) + values_list[j][0];
                        values_list[j][1] = values_list[j][1] % 60;

                    }
                    //Данные - число
                    else {
                        cell_value = parseFloat(cell_value).toFixed(4) * 1.0;
                        values_list[j] = parseFloat(cell_value + values_list[j]).toFixed(4) * 1.0;
                        values_list[j] = values_list[j] < 0 ? 0 : values_list[j];
                    }
                }

                if (values_list[j]) {
                    //Преобразовываем числа в HH:MM
                    if (i>5) {
                        values_list[j][0] = values_list[j][0] < 10? '0'+values_list[j][0]:values_list[j][0];
                        values_list[j][1] = values_list[j][1] === 0? '00':values_list[j][1];

                        values_list[j] = `${values_list[j][0]}:${values_list[j][1]}`;
                    }
                    if ([6, 14, 22, 30].includes(i)) {
                        main_task.cells[i].innerText = '7️⃣' + values_list[j];
                    } else {
                        if (i === 2) {
                            main_task.cells[i].getElementsByTagName('input')[0].value = '📅' + values_list[j];
                            main_task.cells[i].getElementsByTagName('input')[0].dataset.value = values_list[j];
                        }
                        main_task.cells[i].innerText = '📅' + values_list[j];
                    }
                }
                else {
                    if ([6, 14, 22, 30].includes(i)) {
                        main_task.cells[i].innerText = '';
                    } else {
                        if (i === 2) {
                            main_task.cells[i].getElementsByTagName('input')[0].value = '';
                            main_task.cells[i].getElementsByTagName('input')[0].dataset.value = 'None';
                        }
                        main_task.cells[i].innerText = '';
                    }
                }
            }
        }
    }
}

// function reloadPage() {
//     window.location.href = document.URL;
// }

//Удаление структуры
function delTow(button) {
    let row = button.closest('tr');
    let del_row_plan_labor_cost = row.getElementsByClassName('td_task_plan_labor_cost');
    let del_row_fact_labor_cost = row.getElementsByClassName('td_task_fact_labor_cost');
    let del_no_del_status = 0;

    if (del_row_plan_labor_cost && del_row_fact_labor_cost) {
        if (del_row_plan_labor_cost[0].getElementsByTagName('input')[0].value || del_row_fact_labor_cost[0].innerText) {
            return createDialogWindow(status='error',
                description=[
                    'Ошибка',
                    'Эту строку удалить нельзя',
                    'К задаче привязаны плановые/фактические трудозатраты'
                ]);
            }
        }
    else {
        return createDialogWindow(status='error', description=['Ошибка', 'Ошибка удаления ver-1']);
    }

    let rowNumber = row.rowIndex;
    let className = row.className;
    let cur_lvl = parseInt(className.split('lvl-')[1]);

    let tab = document.getElementById("towTable");

    calcNewRowObj(row.dataset.task, row.dataset.task_responsible)
    let del_row_cnt = 1;  //Счётчик удаляемых tow
    let del_nextRow = row.nextElementSibling;  //Следующая строка
    let is_child_colspan = 0;  //Счётчик объединённых ячеек у детей. Используем для определения, у каких детей одинаковый task_id
    let del_child_plan_labor_cost = del_nextRow.getElementsByClassName('td_task_plan_labor_cost');
    let del_child_fact_labor_cost = del_nextRow.getElementsByClassName('td_task_fact_labor_cost');
    //Если удаляемая строка - строка соисполнителя, удаляем только её. Детей не ищем
    if (row.cells[1].hidden) {
        //ищем первую строку задачи с соисполнителями и меняем количество объединенных строк
        let i = rowNumber;
        while (i) {
            if (!tab.rows[i].cells[1].hidden && tab.rows[i].cells[1].getAttribute("rowspan")) {
                is_child_colspan = tab.rows[i].cells[1].getAttribute("rowspan") * 1;
                //Если было всего 2 соисполнителя, удаляем объединение строк
                if (is_child_colspan === 2) {
                    tab.rows[i].cells[1].removeAttribute("rowspan");
                }
                else {
                    tab.rows[i].cells[1].setAttribute("rowspan", is_child_colspan - 1);
                }
                i = 1;  //Обнуляем счётчик для выхода из цикла
            }
            i--;
        }
    }
    else if (row.cells[1].getAttribute("rowspan")) {
        is_child_colspan = row.cells[1].getAttribute("rowspan") * 1;
        //У следующей строки отображаем скрытую ячейку. Если соисполнителей больше двух, объединяем строки
        tab.rows[rowNumber+1].cells[1].hidden = 0;
        if (is_child_colspan > 2) {
            tab.rows[rowNumber+1].cells[1].setAttribute("rowspan", is_child_colspan - 1);
        }
        else {
            tab.rows[rowNumber+1].cells[1].removeAttribute("rowspan");
        }
    }
    else {
        //Удаляем так же заму task
        calcNewRowObj(row.dataset.task, 'None')
        let del_child_lvl = parseInt(del_nextRow.className.split('lvl-')[1]);
        //Если текущей строки меньше следующей, то проверяем строки на нанличие детей
        if (del_child_lvl > cur_lvl) {
            //Проверяем, есть ли не удаляемые дети
            while (del_nextRow) {
                del_child_lvl = parseInt(del_nextRow.className.split('lvl-')[1]);
                //Проверяем, есть ли объединенные строки
                if (del_nextRow.getElementsByClassName("col-2")[0].getAttribute("rowspan")) {
                    is_child_colspan = del_nextRow.getElementsByClassName("col-2")[0].getAttribute("rowspan") * 1;
                    is_child_colspan--;
                } else if (is_child_colspan) {
                    //Если счётчик объединенных строк не равен нулю, но есть скрытые строки, значит произошла ошибка при генерации строк таблицы
                    if (!del_nextRow.cells[1].hidden) {
                        del_no_del_status = 1;
                        return createDialogWindow(status = 'error', description = ['Ошибка', 'Ошибка удаления ver-3']);
                    }
                    //Если is_child_colspan не ноль, значит текущий ребенок объединен с ребенком выше
                    is_child_colspan--;
                }

                if (del_child_lvl > cur_lvl || is_child_colspan && del_child_lvl === cur_lvl) {
                    //Проверяем, что нет плановых или фактических трудозатрат
                    if (del_child_plan_labor_cost && del_child_fact_labor_cost) {
                        if (del_child_plan_labor_cost[0].getElementsByTagName('input')[0].value || del_child_fact_labor_cost[0].innerText) {
                            del_no_del_status = 1;
                            return createDialogWindow(status = 'error', description = [
                                'Ошибка',
                                'Эту структуру задач нельзя удалить',
                                'К списке задач есть дочерняя задача к которой привязаны плановые/фактические трудозатраты'
                            ]);
                        }
                    } else {
                        del_no_del_status = 1;
                        return createDialogWindow(status = 'error', description = ['Ошибка', 'Ошибка удаления ver-2']);
                    }
                    del_row_cnt++;
                    //Добавляем строку в скисок на удаление
                    calcNewRowObj(del_nextRow.dataset.task, del_nextRow.dataset.task_responsible)
                    // deletedRowObj[del_nextRow.dataset.task] = del_nextRow.dataset.task_responsible;

                } else {
                    break;
                }
                del_nextRow = del_nextRow.nextElementSibling;
                if (!del_nextRow || del_nextRow.classList[del_nextRow.classList.length - 1] === 'last_row') {
                    break;
                }
            }
        }
    }

    //Удаляем всё найденное, пересчитываем нераспределенный остаток
    if (!del_no_del_status) {
        //Удаление строк
        for (let i=0; i<del_row_cnt; i++) {
            tab.deleteRow(rowNumber);
        }
        //Если таблица tow опустела, обнуляем значение верхней tow
        let highestRow_del = [];
        if (tab.rows.length > 2) {
            if (rowNumber === 1) {
                highestRow_del = tab.rows[rowNumber];
            }
            else {
                highestRow_del = tab.rows[rowNumber-1];
            }
            editTaskDescription(highestRow_del, rowNumber, 'lvl')
        }

        //Обновляем список highestRow если, была удалена строка иэ этого списка
        if (highestRow.length && highestRow[0] >= rowNumber) {
            highestRow = [rowNumber, highestRow_del.dataset.task, highestRow_del.dataset.task_responsible]
        }

    }
    else {
        return createDialogWindow(status='error', description=['Ошибка', 'Невозможно удалить желаемую структуру, есть запрещенные для удаления строки']);
    }

    //Если в таблице не осталось строк, добавляем кнопку "создать строку"
    if (tab.rows.length === 2 && tab.rows[1].classList[tab.rows[1].classList.length-1] === 'last_row') {
        tab.deleteRow(1);
    }
    if (tab.rows.length === 1) {
        let tab_tr0 = tab.getElementsByTagName('tbody')[0];
        row = tab_tr0.insertRow(0);

        row.className = "lvl-10";

            var td = row.insertCell(0);
            td.className = "empty_table div_tow_first_cell sticky-cell col-1";
            td.colSpan = 3;

                var buttonFirstRow = document.createElement("button");
                buttonFirstRow.className = "button_tow_first_cell";
                buttonFirstRow.addEventListener('click', function() {FirstTaskRow();});
                buttonFirstRow.innerHTML = "+ Начать создание состава работ"

            td.appendChild(buttonFirstRow);

            var td_empty_table = row.insertCell(1);
            td_empty_table.className = "empty_table";
            td_empty_table.colSpan = 39;


        row.appendChild(td);
        row.appendChild(td_empty_table);
    }
}

//Пересчет и обновление значения плановых трудозатрат
function recalcPlanLaborCostWeekSum(button) {
    const tab = document.getElementById("towTable");

    var row = button.closest('tr');
    let rowNumber = row.rowIndex;

    let plan_labor_cost = row.getElementsByClassName('input_task_plan_labor_cost')[0];
    let plc_value = symbToFloat(button.value, '');
    plc_value = isNaN(plc_value)? 0:plc_value;
    let plc_data_value = parseFloat(plan_labor_cost.dataset.value).toFixed(4) * 1.0;
    plc_data_value = isNaN(plc_data_value)? 0:plc_data_value;

    let main_task_row = null;
    //Находим главную задачу для пересчёта общей суммы
    for (let i=rowNumber; i>0; i--) {
        if (tab.rows[i].classList.contains('main_task')) {
            main_task_row = tab.rows[i].getElementsByClassName('input_task_plan_labor_cost')[0];
            break
        }
    }

    if (!main_task_row) {
        return createDialogWindow(status='error', description=['Ошибка', 'Не удалось пересчитать плановые трудозатраты ver-1']);
    }
    let mt_data_value = parseFloat(main_task_row.dataset.value).toFixed(4) * 1.0;
    mt_data_value = isNaN(mt_data_value)? 0:mt_data_value;

    // Строка ИТОГО
    let last_row = tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0];
    let lr_data_value = parseFloat(last_row.dataset.value).toFixed(4) * 1.0;
    lr_data_value = isNaN(lr_data_value)? 0:lr_data_value;

    //Пересчитываем ТОМ
    mt_data_value = parseFloat(mt_data_value - plc_data_value + plc_value).toFixed(4) * 1.0;
    if (mt_data_value < 0) {
        return createDialogWindow(status='error', description=['Ошибка', 'Не удалось пересчитать плановые трудозатраты ver-2']);
    }
    //Пересчитываем ИТОГО
    lr_data_value = parseFloat(lr_data_value - plc_data_value + plc_value).toFixed(4) * 1.0;
    if (lr_data_value < 0) {
        return createDialogWindow(status='error', description=['Ошибка', 'Не удалось пересчитать плановые трудозатраты ver-3']);
    }

    //Обновляем dataset
    //задача
    plc_data_value = plc_value;
    plc_value = plc_value? plc_value:'';
    row.getElementsByClassName('input_task_plan_labor_cost')[0].value = plc_value;
    row.getElementsByClassName('input_task_plan_labor_cost')[0].dataset.value = plc_data_value;
    //main_task
    let mt_value = mt_data_value;
    mt_value = mt_value? '📅'+mt_value:'';
    main_task_row.value = mt_value;
    main_task_row.dataset.value = mt_data_value;
    //ИТОГО
    let lr_value = lr_data_value;
    lr_value = lr_value? '📅'+lr_value:'';
    tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].value = lr_value;
    tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].dataset.value = lr_data_value;

    //Обновляем лог изменений
    editTaskDescription(button, plc_data_value, 'input_task_plan_labor_cost')
}

//Замена значения плановых трудозатрат
function replacePlanLaborCostWeekSum(row, value) {
    if (!value) {
        return;
    }
    const tab = document.getElementById("towTable");

    let rowNumber = row.rowIndex;

    let main_task_row = null;
    let main_task_cell = null;
    //Находим главную задачу для пересчёта общей суммы

    for (let i=rowNumber; i>0; i--) {
        if (tab.rows[i].classList.contains('main_task')) {
            main_task_row = tab.rows[i];
            main_task_cell = main_task_row.getElementsByClassName('input_task_plan_labor_cost')[0];

            break
        }
    }

    if (!main_task_row) {
        return createDialogWindow(status='error', description=['Ошибка', 'Не удалось пересчитать плановые трудозатраты ver-1']);
    }

        //main_task
        let mt_data_value = parseFloat(main_task_cell.dataset.value).toFixed(4) * 1.0;
        mt_data_value = isNaN(mt_data_value) ? 0 : mt_data_value;
        mt_data_value = parseFloat(mt_data_value + value).toFixed(4) * 1.0;
        let mt_value = mt_data_value;
        mt_value = mt_value ? '📅' + mt_value : '';
        main_task_cell.value = mt_value;
        main_task_cell.dataset.value = mt_data_value;

        // ИТОГО
        let last_row = tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0];
        let lr_data_value = parseFloat(last_row.dataset.value).toFixed(4) * 1.0;
        lr_data_value = isNaN(lr_data_value)? 0:lr_data_value;
        lr_data_value = parseFloat(lr_data_value + value).toFixed(4) * 1.0;
        let lr_value = lr_data_value;
        lr_value = lr_value ? '📅' + lr_value : '';
        tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].value = lr_value;
        tab.rows[tab.rows.length - 1].getElementsByClassName('input_task_plan_labor_cost')[0].dataset.value = lr_data_value;

}

//Конвертируем текст в число и наоборот
function symbToFloat(cost=0, value_type='📅') {
    return parseFloat(cost.replaceAll(' ', '').replaceAll(' ', '').replace(value_type, '').replace(",", "."));
}

function calcNewRowObj(t_id, tr_id, objType='del') {
    objType = objType==='del'? deletedRowObj:newRowObj;
    if (objType[t_id]) {
        objType[t_id][tr_id] = 1;
    }
    else {
        objType[t_id] = {[tr_id]: 1};
    }
}