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
    document.getElementById('responsibleOrStatusWin')? document.getElementById('responsibleOrStatusWin').addEventListener('click', function() {closeModal();}):'';

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
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_main_task_task_name');});
    }
    //Название главной задачи
    let input_task_name = document.getElementsByClassName('input_task_name');
    for (let i of input_task_name) {
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_name');});
    }
    //Плановые трудозатраты
    let input_task_plan_labor_cost = document.getElementsByClassName('input_task_plan_labor_cost');
    for (let i of input_task_plan_labor_cost) {
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_plan_labor_cost');});
    }

    let th_task_sum_previous_fact = document.getElementsByClassName('th_task_sum_previous_fact');

    if (th_task_sum_previous_fact.length) {
        th_task_sum_previous_fact[0].addEventListener('click', function() {loadOtherPeriod(type='th_task_sum_previous_fact');});
    }
    let th_task_sum_future_fact = document.getElementsByClassName('th_task_sum_future_fact');
    if (th_task_sum_future_fact.length) {
        th_task_sum_future_fact[0].addEventListener('click', function() {loadOtherPeriod(type='th_task_sum_future_fact');});
    }

    // //___________________________________________________________________________________________________________________________________________
    // //week_1_day_1
    // let input_task_week_1_day_1 = document.getElementsByClassName('input_task_week_1_day_1');
    // for (let i of input_task_week_1_day_1) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_1'); recalcWeekSum(this);});
    // }
    // //week_1_day_2
    // let input_task_week_1_day_2 = document.getElementsByClassName('input_task_week_1_day_2');
    // for (let i of input_task_week_1_day_2) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_2'); recalcWeekSum(this);});
    // }
    // //week_1_day_3
    // let input_task_week_1_day_3 = document.getElementsByClassName('input_task_week_1_day_3');
    // for (let i of input_task_week_1_day_3) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_3'); recalcWeekSum(this);});
    // }
    // //week_1_day_4
    // let input_task_week_1_day_4 = document.getElementsByClassName('input_task_week_1_day_4');
    // for (let i of input_task_week_1_day_4) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_4'); recalcWeekSum(this);});
    // }
    // //week_1_day_5
    // let input_task_week_1_day_5 = document.getElementsByClassName('input_task_week_1_day_5');
    // for (let i of input_task_week_1_day_5) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_5'); recalcWeekSum(this);});
    // }
    // //week_1_day_6
    // let input_task_week_1_day_6 = document.getElementsByClassName('input_task_week_1_day_6');
    // for (let i of input_task_week_1_day_6) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_6'); recalcWeekSum(this);});
    // }
    // //week_1_day_7
    // let input_task_week_1_day_7 = document.getElementsByClassName('input_task_week_1_day_7');
    // for (let i of input_task_week_1_day_7) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_1_day_7'); recalcWeekSum(this);});
    // }
    //
    // //___________________________________________________________________________________________________________________________________________
    // //week_2_day_1
    // let input_task_week_2_day_1 = document.getElementsByClassName('input_task_week_2_day_1');
    // for (let i of input_task_week_2_day_1) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_1'); recalcWeekSum(this);});
    // }
    // //week_2_day_2
    // let input_task_week_2_day_2 = document.getElementsByClassName('input_task_week_2_day_2');
    // for (let i of input_task_week_2_day_2) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_2'); recalcWeekSum(this);});
    // }
    // //week_2_day_3
    // let input_task_week_2_day_3 = document.getElementsByClassName('input_task_week_2_day_3');
    // for (let i of input_task_week_2_day_3) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_3'); recalcWeekSum(this);});
    // }
    // //week_2_day_4
    // let input_task_week_2_day_4 = document.getElementsByClassName('input_task_week_2_day_4');
    // for (let i of input_task_week_2_day_4) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_4'); recalcWeekSum(this);});
    // }
    // //week_2_day_5
    // let input_task_week_2_day_5 = document.getElementsByClassName('input_task_week_2_day_5');
    // for (let i of input_task_week_2_day_5) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_5'); recalcWeekSum(this);});
    // }
    // //week_2_day_6
    // let input_task_week_2_day_6 = document.getElementsByClassName('input_task_week_2_day_6');
    // for (let i of input_task_week_2_day_6) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, v_type='input_task_week_2_day_6'); recalcWeekSum(this);});
    // }
    // //week_2_day_7
    // let input_task_week_2_day_7 = document.getElementsByClassName('input_task_week_2_day_7');
    // for (let i of input_task_week_2_day_7) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_2_day_7'); recalcWeekSum(this);});
    // }
    //
    // //___________________________________________________________________________________________________________________________________________
    // //week_3_day_1
    // let input_task_week_3_day_1 = document.getElementsByClassName('input_task_week_3_day_1');
    // for (let i of input_task_week_3_day_1) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_1'); recalcWeekSum(this);});
    // }
    // //week_3_day_2
    // let input_task_week_3_day_2 = document.getElementsByClassName('input_task_week_3_day_2');
    // for (let i of input_task_week_3_day_2) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_2'); recalcWeekSum(this);});
    // }
    // //week_3_day_3
    // let input_task_week_3_day_3 = document.getElementsByClassName('input_task_week_3_day_3');
    // for (let i of input_task_week_3_day_3) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_3'); recalcWeekSum(this);});
    // }
    // //week_3_day_4
    // let input_task_week_3_day_4 = document.getElementsByClassName('input_task_week_3_day_4');
    // for (let i of input_task_week_3_day_4) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_4'); recalcWeekSum(this);});
    // }
    // //week_3_day_5
    // let input_task_week_3_day_5 = document.getElementsByClassName('input_task_week_3_day_5');
    // for (let i of input_task_week_3_day_5) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_5'); recalcWeekSum(this);});
    // }
    // //week_3_day_6
    // let input_task_week_3_day_6 = document.getElementsByClassName('input_task_week_3_day_6');
    // for (let i of input_task_week_3_day_6) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_6'); recalcWeekSum(this);});
    // }
    // //week_3_day_7
    // let input_task_week_3_day_7 = document.getElementsByClassName('input_task_week_3_day_7');
    // for (let i of input_task_week_3_day_7) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_3_day_7'); recalcWeekSum(this);});
    // }
    //
    // //___________________________________________________________________________________________________________________________________________
    // //week_4_day_1
    // let input_task_week_4_day_1 = document.getElementsByClassName('input_task_week_4_day_1');
    // for (let i of input_task_week_4_day_1) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_1'); recalcWeekSum(this);});
    // }
    // //week_4_day_2
    // let input_task_week_4_day_2 = document.getElementsByClassName('input_task_week_4_day_2');
    // for (let i of input_task_week_4_day_2) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_2'); recalcWeekSum(this);});
    // }
    // //week_4_day_3
    // let input_task_week_4_day_3 = document.getElementsByClassName('input_task_week_4_day_3');
    // for (let i of input_task_week_4_day_3) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_3'); recalcWeekSum(this);});
    // }
    // //week_4_day_4
    // let input_task_week_4_day_4 = document.getElementsByClassName('input_task_week_4_day_4');
    // for (let i of input_task_week_4_day_4) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_4'); recalcWeekSum(this);});
    // }
    // //week_4_day_5
    // let input_task_week_4_day_5 = document.getElementsByClassName('input_task_week_4_day_5');
    // for (let i of input_task_week_4_day_5) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_5'); recalcWeekSum(this);});
    // }
    // //week_4_day_6
    // let input_task_week_4_day_6 = document.getElementsByClassName('input_task_week_4_day_6');
    // for (let i of input_task_week_4_day_6) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_6'); recalcWeekSum(this);});
    // }
    // //week_4_day_7
    // let input_task_week_4_day_7 = document.getElementsByClassName('input_task_week_4_day_7');
    // for (let i of input_task_week_4_day_7) {
    //     i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_week_4_day_7'); recalcWeekSum(this);});
    // }

    //comment
    let input_task_responsible_comment = document.getElementsByClassName('input_task_responsible_comment');
    for (let i of input_task_responsible_comment) {
        i.addEventListener('change', function() {editTaskDescription(this, this.value, 'input_task_responsible_comment');});
    }

    let overlay = document.querySelector(".overlay");
    overlay.classList.add("hidden");

    let loading_screen = document.querySelector(".loading_screen");
    loading_screen.classList.add("hidden");

});

const proj_url = decodeURI(document.URL.split('/')[4]);  //Название проекта
let userChanges = {};  //Список изменений tow пользователем
let newRowList = new Set();  //Список новых tow
let deletedRowList = new Set();  //Список удаленных tow
let editDescrRowList = {};  //Список изменений input tow
let highestRow = [];  //Самая верхняя строка с которой "поедет" вся нумерация строк
let reservesChanges = {};  //Список изменений резервов


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
    console.log('включаем creativeModeOn')
    let div_task_button_hidden = $('.div_task_button_hidden');

    if (div_task_button_hidden.length) {
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
        creative_mode_off_btn.hidden = false;
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

function editResponsibleOrStatus(button) {
    var row = button.closest('tr');
    let input_task_name = row.getElementsByClassName('input_task_name')[0].value;
    var taskResponsibleId = row.dataset.task_responsible;
    let newTitle = '';
    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');

    if (button.classList.contains('col-3')) {
        newTitle = `Для задачи "${input_task_name}" назначить ответственного`
        r_or_s_dialod.getElementsByClassName('responsible_or_status_responsible_form__field_wrapper')[0].style.display = "flex";
        r_or_s_dialod.getElementsByClassName('responsible_or_status_status_form__field_wrapper')[0].style.display = "none";
    }
    else if (button.classList.contains('col-4')) {
        let responsible_user = row.getElementsByClassName('td_task_responsible_user')[0].innerText;
        newTitle = `Для задачи "${input_task_name}" отв.(${responsible_user}) назначить ответственного`
        r_or_s_dialod.getElementsByClassName('responsible_or_status_responsible_form__field_wrapper')[0].style.display = "none";
        r_or_s_dialod.getElementsByClassName('responsible_or_status_status_form__field_wrapper')[0].style.display = "flex";
    }

    document.getElementById('responsible_or_status_frame_input').textContent = newTitle;

    //Для кнопки "СОХРАНИТЬ" назначаем выполение функции записи нового значения в ячейку
    let apply__edit_btn = document.getElementById("apply__edit_btn_i");
    let new_apply__edit_btn = apply__edit_btn.cloneNode(true);
    apply__edit_btn.parentNode.replaceChild(new_apply__edit_btn, apply__edit_btn);

    document.getElementById('apply__edit_btn_i').addEventListener('click', function() {applyResponsibleOrStatusChanges(button, row);});

    openModal();
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

            var row = tab_tr0.insertRow(0);
            var col_i = 0;

            //**************************************************
            // main_task

                row.className = "lvl-0 main_task";
                row.setAttribute("data-lvl", "0");
                row.setAttribute("data-tow_cnt", "0");
                row.setAttribute("data-value_type", "");
                row.setAttribute("data-is_not_edited", '');
                row.dataset.task = `_New_${new Date().getTime()}`;
                row.dataset.task_responsible = `_New_${new Date().getTime()}`;

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
                        editTaskDescription(this, this.value, 'input_main_task_task_name');
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
                    input_task_plan_labor_cost.setAttribute("data-value", "None");
                    input_task_plan_labor_cost.disabled = true;
                td_task_plan_labor_cost.appendChild(input_task_plan_labor_cost);
                col_i++;

                //**************************************************
                // Фактические трудозатраты
                var td_task_fact_labor_cost = row.insertCell(col_i);
                td_task_fact_labor_cost.classList.add("td_task_fact_labor_cost", "sticky-cell", "col-6");
                    var input_task_sum_fact = document.createElement('input');
                    input_task_sum_fact.type = "text";
                    input_task_sum_fact.classList.add("input_task_sum_fact", "is_not_edited");
                    input_task_sum_fact.setAttribute("data-value", "None");
                    input_task_sum_fact.disabled = true;
                td_task_fact_labor_cost.appendChild(input_task_sum_fact);
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                    var input_task_sum_forecast = document.createElement('input');
                    input_task_sum_forecast.type = "text";
                    input_task_sum_forecast.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_forecast.setAttribute("data-value", "None");
                    input_task_sum_forecast.disabled = true;
                td_task_forecast_labor_cost.appendChild(input_task_sum_forecast);
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                    var input_task_sum_previous_fact = document.createElement('input');
                    input_task_sum_previous_fact.type = "text";
                    input_task_sum_previous_fact.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_previous_fact.setAttribute("data-value", "None");
                    input_task_sum_previous_fact.disabled = true;
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
                        input_task_week_day.setAttribute("data-value", "None");
                        input_task_week_day.disabled = true;
                    td_task_labor_cost_week_day.appendChild(input_task_week_day);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                    var input_task_sum_future_fact = document.createElement('input');
                    input_task_sum_future_fact.type = "text";
                    input_task_sum_future_fact.classList.add("input_task_sum_future_fact", "is_not_edited");
                    input_task_sum_future_fact.setAttribute("data-value", "None");
                    input_task_sum_future_fact.disabled = true;
                td_task_sum_future_fact.appendChild(input_task_sum_future_fact);
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.placeholder = "...";
                    input_task_responsible_comment.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_responsible_comment');
                    });
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;

                //Добавляем изменение - Создание новой строки
                UserChangesTaskLog(t_id = row.dataset.task, tr_id = row.dataset.task_responsible, rt = 'New', u_p_id = '', c_row = row); // FirstRow - new row

            //********************************************************
            //Строка с задачей
            row = tab_tr0.insertRow(1);
            col_i = 0;

                //**************************************************
                // task

                row.className = "lvl-0 task";
                row.setAttribute("data-lvl", "0");
                row.setAttribute("data-tow_cnt", "0");
                row.setAttribute("data-value_type", "");
                row.setAttribute("data-is_not_edited", '');
                row.dataset.task = `_New_${new Date().getTime()}`;
                row.dataset.task_responsible = `_New_${new Date().getTime()}`;

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
                        editTaskDescription(this, this.value, 'input_task_name');
                    });

                    var div_tow_button = document.createElement('div');
                    div_tow_button.className = "div_task_button_hidden";
                    div_tow_button.hidden = true;
                    addButtonsForNewTask(div_tow_button, createNewRow = true);

                td_task_task_name.appendChild(div_tow_button);
                td_task_task_name.appendChild(input_task_name);
                col_i++;

                //**************************************************
                // Исполнитель
                var td_task_responsible_user = row.insertCell(col_i);
                td_task_responsible_user.classList.add("td_task_responsible_user", "sticky-cell", "col-3");
                td_task_responsible_user.innerText = "...";
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
                    input_task_plan_labor_cost.type = "text";
                    input_task_plan_labor_cost.className = "input_task_plan_labor_cost";
                    input_task_plan_labor_cost.setAttribute("data-value", "None");
                    input_task_plan_labor_cost.placeholder = "...";
                    input_task_plan_labor_cost.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_plan_labor_cost');
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
                    input_task_sum_fact.setAttribute("data-value", "None");
                    input_task_sum_fact.disabled = true;
                td_task_fact_labor_cost.appendChild(input_task_sum_fact);
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                    var input_task_sum_forecast = document.createElement('input');
                    input_task_sum_forecast.type = "text";
                    input_task_sum_forecast.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_forecast.setAttribute("data-value", "None");
                    input_task_sum_forecast.disabled = true;
                td_task_forecast_labor_cost.appendChild(input_task_sum_forecast);
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                    var input_task_sum_previous_fact = document.createElement('input');
                    input_task_sum_previous_fact.type = "text";
                    input_task_sum_previous_fact.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_previous_fact.setAttribute("data-value", "None");
                    input_task_sum_previous_fact.disabled = true;
                td_tow_sum_previous_fact.appendChild(input_task_sum_previous_fact);
                col_i++;

                //**************************************************
                // 4 недели календаря
                for (let i = 0; i < td_task_labor_list_class.length; i++) {
                    var td_task_labor_cost_week_day = row.insertCell(col_i);
                    td_task_labor_cost_week_day.classList.add(td_task_labor_list_class[i][0], td_task_labor_list_class[i][1]);
                    var input_task_week_day = document.createElement('input');
                    input_task_week_day.classList.add(input_task_labor_list_class[i][0], input_task_labor_list_class[i][1]);
                    input_task_week_day.setAttribute("data-value", "None");
                    //Если ячейка не сумма недели, добавляем отслеживание изменения ячейки
                    if (!input_task_labor_list_class[i][0].indexOf("input_task_week_")) {
                        input_task_week_day.type = "number";
                        input_task_week_day.step = "0.01";
                        input_task_week_day.addEventListener('change', function () {
                            editTaskDescription(this, this.value, input_task_labor_list_class[i][0]);
                            recalcWeekSum(this);
                        });
                    }
                    else {
                        input_task_week_day.type = "text";
                        input_task_week_day.disabled = true;
                    }
                    td_task_labor_cost_week_day.appendChild(input_task_week_day);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                    var input_task_sum_future_fact = document.createElement('input');
                    input_task_sum_future_fact.type = "text";
                    input_task_sum_future_fact.classList.add("input_task_sum_future_fact", "is_not_edited");
                    input_task_sum_future_fact.setAttribute("data-value", "None");
                    input_task_sum_future_fact.disabled = true;
                td_task_sum_future_fact.appendChild(input_task_sum_future_fact);
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.addEventListener('change', function () {
                        editTaskDescription(this, this.value, 'input_task_responsible_comment');
                    });
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;


                //Добавляем изменение - Создание новой строки
                UserChangesTaskLog(t_id = row.dataset.task, tr_id = row.dataset.task_responsible, rt = 'New', u_p_id = '', c_row = row); // FirstRow - new row


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
                    var input_task_sum_fact = document.createElement('input');
                    input_task_sum_fact.type = "text";
                    input_task_sum_fact.classList.add("input_task_sum_fact", "is_not_edited");
                    input_task_sum_fact.setAttribute("data-value", "None");
                    input_task_sum_fact.disabled = true;
                td_task_fact_labor_cost.appendChild(input_task_sum_fact);
                col_i++;

                //**************************************************
                // Прогноз
                var td_task_forecast_labor_cost = row.insertCell(col_i);
                td_task_forecast_labor_cost.classList.add("td_task_forecast_labor_cost", "sticky-cell", "col-7");
                    var input_task_sum_forecast = document.createElement('input');
                    input_task_sum_forecast.type = "text";
                    input_task_sum_forecast.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_forecast.setAttribute("data-value", "None");
                    input_task_sum_forecast.disabled = true;
                td_task_forecast_labor_cost.appendChild(input_task_sum_forecast);
                col_i++;

                //**************************************************
                // Предыдущий период
                var td_tow_sum_previous_fact = row.insertCell(col_i);
                td_tow_sum_previous_fact.className = "td_tow_sum_previous_fact";
                    var input_task_sum_previous_fact = document.createElement('input');
                    input_task_sum_previous_fact.type = "text";
                    input_task_sum_previous_fact.classList.add("input_task_sum_forecast", "is_not_edited");
                    input_task_sum_previous_fact.setAttribute("data-value", "None");
                    input_task_sum_previous_fact.disabled = true;
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
                        input_task_week_day.setAttribute("data-value", "None");
                        input_task_week_day.disabled = true;
                    td_task_labor_cost_week_day.appendChild(input_task_week_day);
                    col_i++;
                }

                //**************************************************
                // Следующий период
                var td_task_sum_future_fact = row.insertCell(col_i);
                td_task_sum_future_fact.className = "td_task_sum_future_fact";
                    var input_task_sum_future_fact = document.createElement('input');
                    input_task_sum_future_fact.type = "text";
                    input_task_sum_future_fact.classList.add("input_task_sum_future_fact", "is_not_edited");
                    input_task_sum_future_fact.setAttribute("data-value", "None");
                    input_task_sum_future_fact.disabled = true;
                td_task_sum_future_fact.appendChild(input_task_sum_future_fact);
                col_i++;

                //**************************************************
                // Комментарии
                var td_task_responsible_comment = row.insertCell(col_i);
                td_task_responsible_comment.className = "td_task_responsible_comment";
                    var input_task_responsible_comment = document.createElement('input');
                    input_task_responsible_comment.type = "text";
                    input_task_responsible_comment.classList.add("input_task_responsible_comment", "is_not_edited");
                    input_task_responsible_comment.disabled = true;
                td_task_responsible_comment.appendChild(input_task_responsible_comment);
                col_i++;

                //Добавляем изменение - Создание новой строки
                UserChangesTaskLog(t_id = row.dataset.task, tr_id = row.dataset.task_responsible, rt = 'New', u_p_id = '', c_row = row); // FirstRow - new row





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

function loadOtherPeriod(type='', value='') {
    console.log(type);
}

function recalcWeekSum(button) {
    console.log('recalcWeekSum');
    let cell_class = button.classList[0];
    let cell_value = button.value;

    cell_value = cell_value? parseFloat(cell_value) : 0;
    let cell_dataset_value = button.dataset.value;
    cell_dataset_value = cell_dataset_value!=="None"? parseFloat(cell_dataset_value) : 0;

    let row = button.closest('tr');
    let main_row = null;
    let main_row_sum_week = null;
    let preRow = row.previousElementSibling;
    let preRow_class = null;

    // Ищем главную задачу (том)
    while (!main_row) {
        preRow_class = preRow.className;
        if (preRow_class.includes("main_task")) {
           main_row = preRow;
        }
        preRow = preRow.previousElementSibling;
    }

    //Строка ИТОГО
    let itogo_row = document.getElementsByClassName('last_row')[0];

    let input_task_sum_week = '';

    if (cell_class.includes("week_1")) {
        input_task_sum_week = row.getElementsByClassName('input_task_sum_week_1')[0];
        main_row_sum_week = 'input_task_sum_week_1';
    }
    else if (cell_class.includes("week_2")) {
        input_task_sum_week = row.getElementsByClassName('input_task_sum_week_2')[0];
        main_row_sum_week = 'input_task_sum_week_2';
    }
    else if (cell_class.includes("week_3")) {
        input_task_sum_week = row.getElementsByClassName('input_task_sum_week_3')[0];
        main_row_sum_week = 'input_task_sum_week_3';
    }
    else if (cell_class.includes("week_4")) {
        input_task_sum_week = row.getElementsByClassName('input_task_sum_week_4')[0];
        main_row_sum_week = 'input_task_sum_week_4';
    }

    //ЗАДАЧА. Обновляем значение суммы за неделю и общую факт сумму задачи
    let itsw_dataset_value = input_task_sum_week.dataset.value;

    itsw_dataset_value = itsw_dataset_value!=="None"? parseFloat(itsw_dataset_value) : 0;
    itsw_dataset_value = itsw_dataset_value + cell_value - cell_dataset_value;
    input_task_sum_week.dataset.value = itsw_dataset_value;
    itsw_dataset_value = itsw_dataset_value? '7️⃣ ' + itsw_dataset_value.toFixed(2) : '';
    input_task_sum_week.value = itsw_dataset_value;


    let input_task_sum_fact = row.getElementsByClassName('input_task_sum_fact')[0];
    let itsf_dataset_value = input_task_sum_fact.dataset.value;

    itsf_dataset_value = itsf_dataset_value!=="None"? parseFloat(itsf_dataset_value) : 0;
    itsf_dataset_value = itsf_dataset_value + cell_value - cell_dataset_value;
    input_task_sum_fact.dataset.value = itsf_dataset_value;
    itsf_dataset_value = itsf_dataset_value? '📅 ' + (itsf_dataset_value/8).toFixed(2) : '';
    input_task_sum_fact.value = itsf_dataset_value;

    //ТОМ. Обновляем значение суммы текущего дня
    let main_row_dataset_value = main_row.getElementsByClassName(cell_class)[0].dataset.value;

    main_row_dataset_value = main_row_dataset_value!=="None"? parseFloat(main_row_dataset_value) : 0;
    main_row_dataset_value = main_row_dataset_value + cell_value - cell_dataset_value;
    main_row.getElementsByClassName(cell_class)[0].dataset.value = main_row_dataset_value;

    main_row_dataset_value = main_row_dataset_value? '📅 ' + main_row_dataset_value.toFixed(2) : '';
    main_row.getElementsByClassName(cell_class)[0].value = main_row_dataset_value;

    //ТОМ. Обновляем значение суммы текущей недели
    let mrsw_dataset_value = main_row.getElementsByClassName(main_row_sum_week)[0].dataset.value;

    mrsw_dataset_value = mrsw_dataset_value!=="None"? parseFloat(mrsw_dataset_value) : 0;
    mrsw_dataset_value = mrsw_dataset_value + cell_value - cell_dataset_value;
    main_row.getElementsByClassName(main_row_sum_week)[0].dataset.value = mrsw_dataset_value;

    mrsw_dataset_value = mrsw_dataset_value? '7️⃣ ' + mrsw_dataset_value.toFixed(2) : '';
    main_row.getElementsByClassName(main_row_sum_week)[0].value = mrsw_dataset_value;

    //ТОМ. Обновляем значение общей суммы факт трудозатрат
    let mrsf_dataset_value = main_row.getElementsByClassName('input_task_sum_fact')[0].dataset.value;

    mrsf_dataset_value = mrsf_dataset_value!=="None"? parseFloat(mrsf_dataset_value) : 0;
    mrsf_dataset_value = mrsf_dataset_value + cell_value - cell_dataset_value;
    main_row.getElementsByClassName('input_task_sum_fact')[0].dataset.value = mrsf_dataset_value;

    mrsf_dataset_value = mrsf_dataset_value? '📅 ' + (mrsf_dataset_value/8).toFixed(2) : '';
    main_row.getElementsByClassName('input_task_sum_fact')[0].value = mrsf_dataset_value;

    //ИТОГО. Обновляем значение суммы текущего дня
    let itogo_row_dataset_value = itogo_row.getElementsByClassName(cell_class)[0].dataset.value;

    itogo_row_dataset_value = itogo_row_dataset_value!=="None"? parseFloat(itogo_row_dataset_value) : 0;
    itogo_row_dataset_value = itogo_row_dataset_value + cell_value - cell_dataset_value;
    itogo_row.getElementsByClassName(cell_class)[0].dataset.value = itogo_row_dataset_value;

    itogo_row_dataset_value = itogo_row_dataset_value? '📅 ' + (itogo_row_dataset_value/8).toFixed(2) : '';
    itogo_row.getElementsByClassName(cell_class)[0].value = itogo_row_dataset_value;

    //ИТОГО. Обновляем значение суммы текущей недели тома
    let irsw_dataset_value = itogo_row.getElementsByClassName(main_row_sum_week)[0].dataset.value;

    irsw_dataset_value = irsw_dataset_value!=="None"? parseFloat(irsw_dataset_value) : 0;
    irsw_dataset_value = irsw_dataset_value + cell_value - cell_dataset_value;
    itogo_row.getElementsByClassName(main_row_sum_week)[0].dataset.value = irsw_dataset_value;

    irsw_dataset_value = irsw_dataset_value? '7️⃣ ' + (irsw_dataset_value/8).toFixed(2) : '';
    itogo_row.getElementsByClassName(main_row_sum_week)[0].value = irsw_dataset_value;

    //ТОМ. Обновляем значение общей суммы факт трудозатрат
    let irsf_dataset_value = itogo_row.getElementsByClassName('input_task_sum_fact')[0].dataset.value;

    irsf_dataset_value = irsf_dataset_value!=="None"? parseFloat(irsf_dataset_value) : 0;
    irsf_dataset_value = irsf_dataset_value + cell_value - cell_dataset_value;
    itogo_row.getElementsByClassName('input_task_sum_fact')[0].dataset.value = irsf_dataset_value;

    irsf_dataset_value = irsf_dataset_value? '📅 ' + (irsf_dataset_value/8).toFixed(2) : '';
    itogo_row.getElementsByClassName('input_task_sum_fact')[0].value = irsf_dataset_value;

    // Обновляем данные датасета
    button.dataset.value = button.value;
}

function editTaskDescription(cell, value='', v_type='') {
    isEditTaskTable();
    let row = cell.closest('tr');
    let t_id = row.dataset.task;
    let tr_id = row.dataset.task_responsible;

    if (userChanges[t_id]) {
        if (userChanges[t_id][tr_id]) {
            userChanges[t_id][tr_id][v_type] = value
        }
        else {
            userChanges[t_id][tr_id] = {[v_type]: value}
        }
    }
    else {
        userChanges[t_id] = {[tr_id]: {[v_type]: value}}
    }
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

// t_id - task_id; tr_id - task_responsible_id;
function UserChangesTaskLog(t_id, tr_id, rt, u_p_id, c_row=false, change_lvl=false) {
    // if (u_p_id == c_id) {
    //     return createDialogWindow(status='error', description=[
    //     'Ошибка',
    //     'При последней манипуляции над задачей произошла ошибка.', 'Попробуйте удалить эту задачу или обновите страницу']);
    // }
    // if (!highestRow.length) {
    //     highestRow = [c_row.rowIndex, c_row.id];
    // }
    // else {
    //     if (c_row.rowIndex < highestRow[0]) {
    //         highestRow = [c_row.rowIndex, c_row.id];
    //     }
    // }
    // userChanges[c_id] = {parent_id: u_p_id};
    //
    // if (['Before', 'After', 'New'].includes(rt)) {
    //         newRowList.add(c_id);
    //     }
}

function saveTaskChanges(text_comment=false) {
    console.log(userChanges)
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