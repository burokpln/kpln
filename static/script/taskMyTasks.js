$(document).ready(function() {
    var page_url = document.URL;
    var my_tasks_other_period = document.getElementById("my_tasks_other_period");
    var show_completed_tasks_btn = document.getElementById("show_completed_tasks_btn");
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");

    my_tasks_other_period? my_tasks_other_period.addEventListener('change', function() {getOtherPeriod(my_tasks_other_period);}):'';
    show_completed_tasks_btn? show_completed_tasks_btn.addEventListener('click', function() {showCompletedTasks(this);}):'';
    save_btn? save_btn.addEventListener('click', function() {saveTaskChanges();}):'';
    cancel_btn? cancel_btn.addEventListener('click', function() {cancelTaskChanges();}):'';

    document.getElementById('responsible_or_status_crossBtnNAW')? document.getElementById('responsible_or_status_crossBtnNAW').addEventListener('click', function() {closeModal();this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('cancel__edit_btn_i')? document.getElementById('cancel__edit_btn_i').addEventListener('click', function() {closeModal(), this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('responsibleOrStatusWin')? document.getElementById('responsibleOrStatusWin').addEventListener('click', function() {closeModal();}):'';

    // Окно с аннулированными платежами
    document.getElementById('user_card_crossBtnNAW')? document.getElementById('user_card_crossBtnNAW').addEventListener('click', function() {closeModal2();}):'';
    document.getElementById('annul_hours_listWin')? document.getElementById('annul_hours_listWin').addEventListener('click', function() {closeModal2();}):'';



    let filter_input_1 = document.getElementById('filter-input-1');
    if (filter_input_1) {
        filter_input_1.addEventListener('click', function() {showFilterSelect2(this);});
    }
    let filter_input_4 = document.getElementById('filter-input-4');
    if (filter_input_4) {
        filter_input_4.addEventListener('click', function() {showFilterSelect2(this);});
    }
    $('#select-filter-input-1').on("select2:close", function() {
        showFilterSelect2(this);
    });
    $('#select-filter-input-1').on("select2:open", function() {
        showFilterSelect2(this, true);
    });
    $('#select-filter-input-4').on("select2:close", function() {
        showFilterSelect2(this);
    });
    $('#select-filter-input-4').on("select2:open", function() {
        showFilterSelect2(this, true);
    });

    // Фильтрация
    $('#select-filter-input-1').on("change.select2", function() {
        filterMyTasksTable(this);
    });
    let filter_input_2 = document.getElementById('filter-input-2');
    if (filter_input_2) {
        filter_input_2.addEventListener('input', function() {filterMyTasksTable(this);});
    }
    let filter_input_3 = document.getElementById('filter-input-3');
    if (filter_input_3) {
        filter_input_3.addEventListener('input', function() {filterMyTasksTable(this);});
    }
    $('#select-filter-input-4').on("change.select2", function() {
        filterMyTasksTable(this);
    });
    let filter_input_5 = document.getElementById('filter-input-5');
    if (filter_input_5) {
        filter_input_5.addEventListener('input', function() {filterMyTasksTable(this);});
    }

    //Неотправленные, несогласованные, частично заполненные
    let wrong_hours_date_div = document.getElementsByClassName('wrong_hours_date_div');
    for (let i of wrong_hours_date_div) {
        i.addEventListener('click', function () {getOtherPeriod(this);});
    }

    //Статус задачи
    let td_tow_task_statuses = document.getElementsByClassName('td_tow_task_statuses');
    for (let i of td_tow_task_statuses) {
        if (i.closest('tr').dataset.row_type === 'task')
        i.addEventListener('click', function() {editResponsibleOrStatus(this);});
    }

    //comment
    let input_task_responsible_comment = document.getElementsByClassName('input_task_responsible_comment');
    for (let i of input_task_responsible_comment) {
        i.addEventListener('change', function() {editTaskInformation(this, this.value, 'input_task_responsible_comment');});
    }

    //day_1
    let input_task_week_1_day_1 = document.getElementsByClassName('input_task_week_1_day_1');
    for (let i of input_task_week_1_day_1) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_2
    let input_task_week_1_day_2 = document.getElementsByClassName('input_task_week_1_day_2');
    for (let i of input_task_week_1_day_2) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_3
    let input_task_week_1_day_3 = document.getElementsByClassName('input_task_week_1_day_3');
    for (let i of input_task_week_1_day_3) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_4
    let input_task_week_1_day_4 = document.getElementsByClassName('input_task_week_1_day_4');
    for (let i of input_task_week_1_day_4) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_5
    let input_task_week_1_day_5 = document.getElementsByClassName('input_task_week_1_day_5');
    for (let i of input_task_week_1_day_5) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_6
    let input_task_week_1_day_6 = document.getElementsByClassName('input_task_week_1_day_6');
    for (let i of input_task_week_1_day_6) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //day_7
    let input_task_week_1_day_7 = document.getElementsByClassName('input_task_week_1_day_7');
    for (let i of input_task_week_1_day_7) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {recalcHourPerDay(this)});
    }
    //Список объектов
    getAllProjects()
    //Список статусов
    getAllStatuses()
});

let userChangesTask = {};  //Список часов по задачам
let userChangesWork = {};  //Список часов по оргработам
let newRowList = new Set();  //Список новых tow
let deletedRowList = new Set();  //Список удаленных tow
let editDescrRowList = {};  //Список изменений input tow
let highestRow = [];  //Самая верхняя строка с которой "поедет" вся нумерация строк
let reservesChanges = {};  //Список изменений резервов

let pr_list = {}; //Список проектов
let status_list = {};  //Список статусов


function getAllProjects() {
    let pr = document.getElementById("select-filter-input-1");
    if (pr) {
        pr_list = {};
        for (let i = 0; i < pr.length; i++) {
            pr_list[pr.options[i].value] = pr.options[i].text;
        }
    }
}

function getAllStatuses(){
    let st = document.getElementById("select-filter-input-4");
    if (st) {
        status_list = {};
        for (let i = 0; i < st.length; i++) {
            status_list[st.options[i].value] = st.options[i].text;
        }
    }
}

function hideFilterInput(inputN=1, inputStatus=1, divStatus=0) {
    //Определяем видимость поля input и select2 в шапке таблица, когда фильтруем столбец с выпадающий список

    //Списки статусов видимости
    let displayStatus_1 = 'block';
    let displayStatus_2 = 'inline-block';
    let displayStatus_3 = 'none';

    //Определяем статус видимости
    inputStatus = inputStatus? displayStatus_2:displayStatus_3;
    divStatus = divStatus? displayStatus_1:displayStatus_3;

    //Задаём статус видимости
    document.getElementById(`filter-input-${inputN}`).style.setProperty('display', inputStatus,'important');
    document.getElementById(`div-filter-input-${inputN}`).style.setProperty('display', divStatus,'important');
}

function showFilterSelect2(button, statusIsOpened=false){
    //Функция отображает select2 выпадающий список в шапке таблице при клике на input и наоборот, скрывает select2 и отображает input при закрытии select2
    if (button.id === 'filter-input-1'){
        let input_1 = $('#select-filter-input-1');
        hideFilterInput(1, 0, 1);
        if (input_1.data('select2')) {
            input_1.select2('open');
        }
    }

    else if (button.id === 'filter-input-4'){
        let input_4 = $('#select-filter-input-4');
        hideFilterInput(4, 0, 1);
        if (input_4.data('select2')) {
            input_4.select2('open');
        }
    }

    else if (button.id === 'select-filter-input-1'){
        if (statusIsOpened) {
            hideFilterInput(1, 0, 1);
        }
        else {
            hideFilterInput(1, 1, 0);
        }

    }
    else if (button.id === 'select-filter-input-4'){
        if (statusIsOpened) {
            hideFilterInput(4, 0, 1);
        }
        else {
            hideFilterInput(4, 1, 0);
        }
    }

}

function filterMyTasksTable(button) {
    // Статус отображения завершенных задач
    let completed_hide = document.getElementById("show_completed_tasks_btn");
    completed_hide = completed_hide.innerText !== 'ПОКАЗАТЬ ЗАВЕРШЕННОЕ'? 'tr_task_status_closed':'tr_task_status_not_closed';

    if (button.id === 'select-filter-input-1'){
        let idList = $("#select-filter-input-1").val();
        let selectedList = '';
        let titleSelectedList = '';
        if (idList) {
            let firstVal = pr_list[idList[0]];
            selectedList = firstVal;
            if (idList.length > 1) {
                titleSelectedList = firstVal;
                selectedList = `... ${idList.length} пр.`;
                for (let i = 1; i < idList.length; i++) {
                    titleSelectedList += `\n${pr_list[idList[i]]}`;
                }
            }
        }

        document.getElementById("filter-input-1").value = selectedList;
        document.getElementById("filter-input-1").title = titleSelectedList;
    }
    else if (button.id === 'select-filter-input-4'){
        let idList = $("#select-filter-input-4").val();
        let selectedList = '';
        let titleSelectedList = '';
        if (idList) {
            let firstVal = status_list[idList[0]];
            selectedList = firstVal;
            if (idList.length > 1) {
                titleSelectedList = firstVal;
                selectedList = `... ${idList.length} ст.`;
                for (let i = 1; i < idList.length; i++) {
                    titleSelectedList += `\n${status_list[idList[i]]}`;
                }
            }
        }

        document.getElementById("filter-input-4").value = selectedList;
        document.getElementById("filter-input-4").title = titleSelectedList;
    }

    // Список значений статусов
    let filter_input_1 = $("#select-filter-input-1").val();
    let filter_input_2 = $("#filter-input-2").val().toLowerCase();
    let filter_input_3 = $("#filter-input-3").val().toLowerCase();
    let filter_input_4 = $("#select-filter-input-4").val();
    let filter_input_5 = $("#filter-input-5").val().toLowerCase();


        console.log('filter_input_1', filter_input_1, '__')
        console.log('filter_input_2', filter_input_2, '__')
        console.log('filter_input_3', filter_input_3, '__')
        console.log('filter_input_4', filter_input_4, '__')
        console.log('filter_input_5', filter_input_5, '__')

    let row_cnt = 0; //Счётчик не скрытых задач

    let tab = document.getElementById("towTable");
    let tab_tr0 = tab.getElementsByTagName('tbody')[0];

    for (let i = 0, row; row = tab_tr0.rows[i]; i++) {
        //Статус фильтрации для каждого столбца
        let status_filter_1 = !filter_input_1? 1:0;
        let status_filter_2 = !filter_input_2? 1:0;
        let status_filter_3 = !filter_input_3? 1:0;
        let status_filter_4 = !filter_input_4? 1:0;
        let status_filter_5 = !filter_input_5? 1:0;

        //Статус закрытой задачи
        let status_filter_0 = 0;
        if (completed_hide === row.classList[0]) {
            status_filter_0 = 1
        }

        //Значения ячеек
        let val_1 = row.cells[1].dataset.value;
        let val_2 = row.cells[2].dataset.value.toLowerCase();
        let val_3 = row.cells[3].title.toLowerCase();
        let val_4 = row.cells[4].dataset.cur_value;
        let val_5 = row.cells[5].getElementsByTagName('input')[0].dataset.value.toLowerCase();

        //Ищем совпадения в ячейках
        if (!status_filter_1 && filter_input_1.includes(val_1)) {
            status_filter_1 = 1;
        }
        if (!status_filter_2 && val_2.indexOf(filter_input_2) >= 0) {
            status_filter_2 = 1;
        }
        if (!status_filter_3 && val_3.indexOf(filter_input_3) >= 0) {
            status_filter_3 = 1;
        }
        if (!status_filter_4 && filter_input_4.includes(val_4)) {
            status_filter_4 = 1;
        }
        if (!status_filter_5 && val_5.indexOf(filter_input_5) >= 0) {
            status_filter_5 = 1;
        }

        if (status_filter_0 && status_filter_1 && status_filter_2 && status_filter_3 && status_filter_4 && status_filter_5) {
            row.hidden = 0;
            row_cnt++;
        }
        else {
            row.hidden = 1;
        }
    }

    if (!row_cnt) {
        return createDialogWindow(status = 'info', description = ['Внимание!', 'Совпадений не найдено', 'Попробуйте изменить фильтр']);
    }
}

function editTaskInformation(cell, value='', v_type='') {
    isEditTaskTable();
    let row = cell.closest('tr');
    let t_id = row.dataset.task;
    let tr_id = row.dataset.task_responsible;
    let d_value = cell.dataset.value;
    let row_type = row.dataset.row_type;
    let userChanges= false;
    if (row_type === 'task') {
        userChanges = userChangesTask;
    }
    else if (row_type === 'org_work') {
        userChanges = userChangesWork;
    }

    let empty_value = ['', 'None']

    //Если значение стало изначальным, как при загрузке страницы, то удаляем это изменение
    if (d_value === value || empty_value.includes(value) && empty_value.includes(d_value)) {
        // Если изменений не было, то или ничего не делаем или удаляем из userChanges ранее указанное значение
        if (userChanges[t_id][tr_id][v_type]) {
            delete userChanges[t_id][tr_id][v_type];
            //Если ключей не осталось, удаляем
            if (!Object.keys(userChanges[t_id][tr_id]).length) {
                delete userChanges[t_id][tr_id];
            }
            //Если ключей не осталось, удаляем
            if (!Object.keys(userChanges[t_id]).length) {
                delete userChanges[t_id];
            }
            //Если ключей не осталось, удаляем
            if (!Object.keys(userChanges).length) {
                userChanges = {};
            }
        }
        return;
    }

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

function getOtherPeriod(button){
    //Подготовка в загрузке другого периода часов
    //Находим дату подгружаемого периода
    //Если запрашиваемый период != ранее подгруженному периоду, продолжаем
    let other_period_date = ''
    if (button.id === 'my_tasks_other_period') {
        other_period_date = button.value;
        let cur_period_date = button.dataset.week;
        if (other_period_date === cur_period_date) {
            return createDialogWindow(status='error', description=['Ничего не произошло', 'Выбранный период уже подгружен']);
        }
    }
    else {
        other_period_date = button.dataset.date;
        other_period = new Date(other_period_date);
        let day_0 = document.getElementById('my_tasks_other_period').dataset.day_0;
        let day_6 = document.getElementById('my_tasks_other_period').dataset.day_6;
        day_0 = new Date(day_0);
        day_6 = new Date(day_6);
        if (other_period >= day_0 && day_6 >= other_period) {
            return createDialogWindow(status='error', description=['Ничего не произошло', 'Выбранный период уже подгружен']);
        }
    }
    if (!other_period_date) {
        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape") {
                location.reload();
                event.preventDefault();
            }
        });
        return createDialogWindow(status='error',
            description=['Не уждалось определить дату периода', 'Обновите страницу и попробуйте ещё раз'],
            func=[['click', [reloadPage]]],
            );
    }

    //Запращиваем подтверждение на подгрузку операции, в случае, если userChanges не пуст
    if (Object.keys(userChangesTask).length || Object.keys(userChangesWork).length) {
        return createDialogWindow(status='info',
                description=['Есть несохранённые данные', 'Добавленные/удалённые/изменённые часы не сохранятся', 'Подтвердите смену периода'],
                func=[['click', [loadOtherPeriod, other_period_date]]],
                buttons=[
                    {
                        id:'flash_cancel_button',
                        innerHTML:'ОТМЕНИТЬ',
                    },
                ],
                );
    }
    //Подгружаем указанную неделю, если userChanges пуст
    loadOtherPeriod(other_period_date)
}

// function reloadPage() {
//     window.location.href = document.URL;
// }

function loadOtherPeriod(other_period_date) {
    //Загружаем данные на страницу
    fetch(`/get_my_tasks_other_period/${other_period_date}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const tab = document.getElementById("towTable");
                var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                //Обновляем шапку календаря
                headTable  = tab.getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th');
                for (let i=6; i<headTable.length; i++) {
                    headTable[i].className = data.calendar_cur_week[i-6].class;
                    let title_date = `${new Date(data.calendar_cur_week[i-6].work_day).getFullYear()}-${String(new Date(data.calendar_cur_week[i-6].work_day).getMonth() + 1).padStart(2, '0')}-${String(new Date(data.calendar_cur_week[i-6].work_day).getDate()).padStart(2, '0')}`
                    headTable[i].setAttribute("title", title_date + ' - ' + data.calendar_cur_week[i-6].day_week);
                    headTable[i].getElementsByTagName('div')[0].innerText = data.calendar_cur_week[i-6].work_day_txt;
                    headTable[i].getElementsByTagName('div')[1].innerText = data.calendar_cur_week[i-6].hours_per_day_txt + ' ч.';
                    headTable[i].getElementsByTagName('div')[1].dataset.value = data.calendar_cur_week[i-6].hours_per_day;
                    headTable[i].getElementsByTagName('div')[1].dataset.hpdn_status = data.calendar_cur_week[i-6].hpdn_status;
                }

                //Обновляем часы задач по новому периоду
                for (let i=0; i<tab_numRow.length; i++) {
                    let t_r_id = tab_numRow[i].dataset.task_responsible;
                    //Если были найдены часы за указанный период, то обновляем, иначе удаляем

                    let labor_cost_week_day = tab_numRow[i].getElementsByClassName('td_task_labor_cost_week_day');
                    //Проходим по всем дням календаря
                    for (let ii=0; ii<labor_cost_week_day.length; ii++) {
                        labor_cost_week_day[ii].className = `td_task_labor_cost_week_day td_tow_week_1_day_${ii+1} ${data.calendar_cur_week[ii].class}`;

                        let labor_cost_week_day_input = labor_cost_week_day[ii].getElementsByTagName('input')[0];
                        labor_cost_week_day_input.className = `input_task_week_1_day_${ii+1} ${data.calendar_cur_week[ii].td_class}`;

                        let dataset_value = 'None';
                        let input_value = '';
                        if (data.tasks[t_r_id]) {
                            dataset_value = data.tasks[t_r_id][`input_task_week_1_day_${ii+1}`];
                            input_value = data.tasks[t_r_id][`input_task_week_1_day_${ii+1}_txt`];
                            dataset_value = dataset_value? dataset_value:'None';
                        }
                        labor_cost_week_day_input.dataset.value = dataset_value;
                        labor_cost_week_day_input.dataset.cur_value = dataset_value;
                        labor_cost_week_day_input.value = input_value;
                    }
                }

                //обновляем информацию о периоде подгруженной недели
                let my_tasks_other_period = document.getElementById("my_tasks_other_period");
                my_tasks_other_period.value = data.current_period[0];
                my_tasks_other_period.dataset.week = data.current_period[0];
                my_tasks_other_period.dataset.day_0 = data.current_period[1];
                my_tasks_other_period.dataset.day_6 = data.current_period[2];

                //Удаляем сохраненные в памяти ранее внесенные часы (комментарии и статусы не удаляем)
                if (Object.keys(userChangesTask).length) {
                    for (const [k, v] of Object.entries(userChangesTask)) {

                        if (Object.keys(v).length) {
                            for (const [kk, vv] of Object.entries(v)) {

                                if (Object.keys(vv).length) {
                                    for (const [kkk, vvv] of Object.entries(vv)) {


                                        if (kkk.indexOf('input_task_week_1_day_') === 0) {
                                            delete userChangesTask[k][kk][kkk];

                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesTask[k][kk]).length) {
                                                delete userChangesTask[k][kk];
                                            }
                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesTask[k]).length) {
                                                delete userChangesTask[k];
                                            }
                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesTask).length) {
                                                userChangesTask = {};
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if (Object.keys(userChangesWork).length) {
                    for (const [k, v] of Object.entries(userChangesWork)) {

                        if (Object.keys(v).length) {
                            for (const [kk, vv] of Object.entries(v)) {

                                if (Object.keys(vv).length) {
                                    for (const [kkk, vvv] of Object.entries(vv)) {


                                        if (kkk.indexOf('input_task_week_1_day_') === 0) {
                                            delete userChangesWork[k][kk][kkk];

                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesWork[k][kk]).length) {
                                                delete userChangesWork[k][kk];
                                            }
                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesWork[k]).length) {
                                                delete userChangesWork[k];
                                            }
                                            //Если ключей не осталось, удаляем
                                            if (!Object.keys(userChangesWork).length) {
                                                userChangesWork = {};
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                return createDialogWindow(status='success', description=['Данные обновлены']);
                }
            else {
                let description = data.description;
                return createDialogWindow(status='error', description=description);
            }
        })
}

function saveTaskChanges() {

    let th_task_work_day_date = $(".th_task_work_day_date");
    let calendar_cur_week = [];

    if (th_task_work_day_date.length) {
            th_task_work_day_date.toArray().forEach(function (button) {
                calendar_cur_week.push(button.innerText)
            });
        }

    fetch("/save_my_tasks", {
        headers: {
            "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({
            userChangesTask: userChangesTask,
            userChangesWork: userChangesWork,
            calendar_cur_week: calendar_cur_week,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = document.URL;
            }
        else {
            let description = data.description;
            return createDialogWindow(status='error', description=description);
        }
    })
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

function editResponsibleOrStatus(button) {
    var row = button.closest('tr');
    var button_value = button.dataset.cur_value;
    let td_task_task_name = row.getElementsByClassName('td_task_task_name')[0].innerText;
    var taskResponsibleId = row.dataset.task_responsible;
    let newTitle = '';
    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');

    newTitle = `Для задачи "${td_task_task_name}" назначить статус`
    r_or_s_dialod.getElementsByClassName('responsible_or_status_status_form__field_wrapper')[0].style.display = "flex";
    $('#responsible_or_status_status_select').val(button_value? button_value.toString():null).trigger('change');

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

function closeModal2() {
    const modal2 = document.querySelector(".modal2");
    const overlay = document.querySelector(".overlay");
    modal2.classList.add("hidden");
    overlay.classList.add("hidden");
}

function applyResponsibleOrStatusChanges(button, row) {
    // нужно передать button из editResponsibleOrStatus,
    // найти нужную ячейку (ФИО или статус) и
    // вставить выбранное значение из выпадающего списка
    let result_val = null;
    let result_text = '';

    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');

    //Статус
    result_val = $('#responsible_or_status_status_select').val();
    result_text = $('#responsible_or_status_status_select :selected').text();

    row.getElementsByClassName('td_tow_task_statuses')[0].dataset.cur_value = result_val;
    row.getElementsByClassName('td_tow_task_statuses')[0].innerText = result_text;


    editTaskInformation(button, result_val, button.classList[0]);

    closeModal();
}

function recalcHourPerDay(button) {
    //Пересчёт общего кол-ва часов за сутки при изменении данных в ячейке часов
    let week_day = button.classList[0][button.classList[0].length - 1]*1;
    let previous_value = button.dataset.cur_value;
    previous_value = previous_value==='None'? 0:previous_value;
    let cur_value = button.value;
    cur_value = cur_value? convertTime(cur_value, ':') * 1.0 : 0;

    //Данные из шапки таблицы
    let headTable  = document.getElementById("towTable").getElementsByTagName('thead')[0].getElementsByTagName('tr')[0].getElementsByTagName('th');
    let headCell = headTable[5+week_day].getElementsByTagName('div')[1];
    let headCellCurValue = headCell.dataset.value * 1.0;
    let hpdn_status = headCell.dataset.hpdn_status;  //Статус почасовой оплаты. В случае true не проверяем на переполнения 8 часов

    let difference_value = (headCellCurValue + cur_value - previous_value).toFixed(3) * 1.00;

    //Проверяем переполнение 8 часов если в этот день нет статуса почасовой оплаты
    if (hpdn_status === 'False' && difference_value > 8) {
        let remainder_value = 8 - headCellCurValue - previous_value;
        button.value = previous_value? convertTime(previous_value):'';
        return createDialogWindow(
            status='error',
            description=[
                'Ошибка',
                'Нельзя внести часы, т.к. произойдёт превышение подачи 8 часов в сутки',
                `Вы можете указать до ${convertTime(remainder_value)} ч.`,
                `Вы указали до ${convertTime(cur_value)} ч.`,
            ]
        );
    }
    //Указываем на факт превышения 8 часов, если так вышло и есть статус почасовой оплаты
    else if (hpdn_status === 'True' && difference_value > 8) {
        let remainder_value = 8 - headCellCurValue - previous_value;
         createDialogWindow(
            status='info',
            description=[
                'Обратите внимание',
                `Произошло превышение подачи 8 часов в сутки (${convertTime(difference_value)} ч.)`,
                `Вы указали ${convertTime(cur_value)} ч.`,
            ]
        );
    }
    //При превышении 24 часов указываем на ошибку и возвращаем прошлое значение
    if (difference_value > 24) {
        let remainder_value = 24 - headCellCurValue - previous_value;
        button.value = previous_value? convertTime(previous_value):'';
        return createDialogWindow(
            status='error',
            description=[
                'Ошибка',
                'В сутки нельзя внести более 24 часов',
                `Вы можете указать до ${convertTime(remainder_value)} ч.`,
                `Вы указали ${convertTime(cur_value)} ч.`,
            ]
        );
    }

    //Обновляем данные в шапке
    headCell.innerText = `${convertTime(difference_value.toString())} ч.`;
    headCell.dataset.value = difference_value;

    //Обновляем данные в ячейке
    button.dataset.cur_value = cur_value;

    editTaskInformation(button, cur_value, button.classList[0]);
}

function convertOnfocusDate(empDate, direction=false) {
    if (direction == 'focusin' && empDate.type != 'text') {
        return
    }
    if (!empDate.value) {
        empDate.type = empDate.type == 'text'? 'time':'text';
        return
    }
    if (empDate.type == 'text') {
        // tmp_value = convertTime(empDate.value);
        // empDate.value = tmp_value;
        empDate.type = 'time';
    }
    else {
        // tmp_value = convertTime(empDate.value, ":");
        // empDate.value = tmp_value;
        empDate.type = 'text';
    }
}

function convertTime(empDate, dec=".") {
    //Переводим float в HH:MM и наоборок
    if (dec=== ":") {
        const [hours, minutes] = empDate.split(':').map(Number);
        return parseFloat((hours + minutes / 60).toFixed(3));
    }
    const hours = Math.floor(empDate);
    const minutes = Math.round((empDate - hours) * 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function convertDate(empDate, dec=".") {
    var sep = dec=="."?"-":".";
    var dateParts = empDate.split(dec);
    dateParts = `${dateParts[2]}${sep}${dateParts[1]}${sep}${dateParts[0]}`;
    return dateParts;
}

function isEditTaskTable() {
    var save_btn = document.getElementById("save_btn");

    if (save_btn.disabled) {
        editTaskTable();
    }
}

function editTaskTable() {
    let save_btn = document.getElementById("save_btn");
    let cancel_btn = document.getElementById("cancel_btn");
    if (save_btn.disabled) {
        save_btn.disabled = 0;
        cancel_btn.disabled = 0;
    }
    else {
        save_btn.disabled = 1;
        cancel_btn.disabled = 1;
    }
}

function showCompletedTasks(button) {
    let button_status = button.innerText;
    let tr_task_status_closed = $('.tr_task_status_closed');
    let input_task_number_not_closed = $('.input_task_number_not_closed');
    let input_task_number = $('.input_task_number');

    if (button_status === 'ПОКАЗАТЬ ЗАВЕРШЕННОЕ') {
        button.innerText = 'СКРЫТЬ ЗАВЕРШЕННОЕ';
        if (tr_task_status_closed.length) {
            tr_task_status_closed.toArray().forEach(function (button) {
                button.hidden = 0;
            });
        }
        if (input_task_number.length) {
            input_task_number.toArray().forEach(function (button) {
                button.hidden = 0;
            });
        }
        if (input_task_number_not_closed.length) {
            input_task_number_not_closed.toArray().forEach(function (button) {
                button.hidden = 1;
            });
        }
    }
    else {
        button.innerText = 'ПОКАЗАТЬ ЗАВЕРШЕННОЕ';
        if (tr_task_status_closed.length) {
            tr_task_status_closed.toArray().forEach(function (button) {
                button.hidden = 1;
            });
        }
        if (input_task_number.length) {
            input_task_number.toArray().forEach(function (button) {
                button.hidden = 1;
            });
        }
        if (input_task_number_not_closed.length) {
            input_task_number_not_closed.toArray().forEach(function (button) {
                button.hidden = 0;
            });
        }
    }
    return true;
}