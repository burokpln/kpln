$(document).ready(function() {
    var page_url = document.URL;

    var save_btn = document.getElementById("save_btn");
    var annul_btn = document.getElementById("annul_btn");
    var cancel_btn = document.getElementById("cancel_btn");
    var unapproved_tasks_btn = document.getElementById("show_unapproved_tasks_btn");

    save_btn? save_btn.addEventListener('click', function() {saveTaskChanges();}):'';
    annul_btn? annul_btn.addEventListener('click', function() {saveTaskChanges(false);}):'';
    cancel_btn? cancel_btn.addEventListener('click', function() {cancelTaskChanges();}):'';
    unapproved_tasks_btn? unapproved_tasks_btn.addEventListener('click', function() {showUnapprovedTasks(this);}):'';

    document.getElementById('responsible_or_status_crossBtnNAW')? document.getElementById('responsible_or_status_crossBtnNAW').addEventListener('click', function() {closeModal();this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('cancel__edit_btn_i')? document.getElementById('cancel__edit_btn_i').addEventListener('click', function() {closeModal(), this.closest('section').dataset.task_responsible_id='';}):'';
    document.getElementById('responsibleOrStatusWin')? document.getElementById('responsibleOrStatusWin').addEventListener('click', function() {closeModal();}):'';

    let filter_input_2 = document.getElementById('filter-input-2');
    if (filter_input_2) {
        filter_input_2.addEventListener('click', function() {showFilterSelect2(this);});
    }
    let filter_input_5 = document.getElementById('filter-input-5');
    if (filter_input_5) {
        filter_input_5.addEventListener('click', function() {showFilterSelect2(this);});
    }
    $('#select-filter-input-2').on("select2:close", function() {
        showFilterSelect2(this);
    });
    $('#select-filter-input-2').on("select2:open", function() {
        showFilterSelect2(this, true);
    });
    $('#select-filter-input-5').on("select2:close", function() {
        showFilterSelect2(this);
    });
    $('#select-filter-input-5').on("select2:open", function() {
        showFilterSelect2(this, true);
    });

    // Фильтрация
    let filter_input_1 = document.getElementById('filter-input-1');
    if (filter_input_1) {
        filter_input_1.addEventListener('input', function() {filterMyTasksTable(this);});
    }
    $('#select-filter-input-2').on("change.select2", function() {
        filterMyTasksTable(this);
    });
    let filter_input_3 = document.getElementById('filter-input-3');
    if (filter_input_3) {
        filter_input_3.addEventListener('input', function() {filterMyTasksTable(this);});
    }
    let filter_input_4 = document.getElementById('filter-input-4');
    if (filter_input_4) {
        filter_input_4.addEventListener('input', function() {filterMyTasksTable(this);});
    }
    $('#select-filter-input-5').on("change.select2", function() {
        filterMyTasksTable(this);
    });
    let filter_input_6 = document.getElementById('filter-input-6');
    if (filter_input_6) {
        filter_input_6.addEventListener('input', function() {filterMyTasksTable(this);});
    }

    let filter_input_11 = document.getElementById('filter-input-11');
    if (filter_input_11) {
        filter_input_11.addEventListener('input', function() {filterMyTasksTable(this, 'towTable2');});
    }
    let filter_input_12 = document.getElementById('filter-input-12');
    if (filter_input_12) {
        filter_input_12.addEventListener('input', function() {filterMyTasksTable(this, 'towTable2');});
    }
    let filter_input_13 = document.getElementById('filter-input-13');
    if (filter_input_13) {
        filter_input_13.addEventListener('input', function() {filterMyTasksTable(this, 'towTable2');});
    }

    //Неотправленные, несогласованные, частично заполненные
    let unsent_hours_list_div = $(".unsent_hours_list_div .wrong_hours_date_div");
    if (unsent_hours_list_div.length) {
        unsent_hours_list_div.toArray().forEach(function (button) {
            button.addEventListener('click', function () {showUnhotrUsers(this);});
        });
    }

    //Выбор/снятие выбора у всех флажков
    let th_tow_select = document.getElementsByClassName('th_tow_select');
    if (th_tow_select) {
        th_tow_select[0].addEventListener('click', function() {selectAllUnsentHotr();});
    }

    // Флажок выбора часов из таблицы
    let input_task_select = $(".input_task_select");
    if (input_task_select.length) {
        input_task_select.toArray().forEach(function (button) {
            button.addEventListener('click', function () {unsentHotrSelect(this);});
        });
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

    //Список объектов
    getAllProjects()
    //Список статусов
    getAllStatuses()

    // Скрываем календарь
    document.querySelector('.calendar-container .arrow-right').addEventListener('click', function() {hideCalendar();});

    // Отображаем календарь
    document.querySelector('.right-panel').addEventListener('click', (event) => {
        const calendarContainer = document.querySelector('.calendar-container');

        // Check if the calendar-container is hidden
        if (calendarContainer.style.display === 'none') {
            const isArrowRight = event.target.closest('.arrow-right');

            // Only trigger if not clicking on ".calendar-container .arrow-right"
            if (!isArrowRight) {
                hideCalendar(false);
            }
        }
    });

    // Перелистывание календаря
    document.querySelector('.calendar-month .arrow-left').addEventListener('click', function() {changeMonth(this, 'change', this.dataset.date);});
    document.querySelector('.calendar-month .arrow-right').addEventListener('click', function() {changeMonth(this, 'change', this.dataset.date);});

    //Выбор даты из input date
    let month_year = document.getElementsByClassName('month-year');
    if (month_year) {
        month_year[0].addEventListener('click', function() {changeMonth(this, 'click', this.value);});
        // month_year[0].addEventListener('change', function() {changeMonth(this, 'change', this.value);});
        month_year[0].addEventListener('focusout', function() {changeMonth(this, 'focusout', this.value);});
    }
    let month_year_date = document.getElementsByClassName('month-year-date');
    if (month_year_date) {
        month_year_date[0].addEventListener('change', function() {changeMonth(this, 'change', this.value);});
    }

    //Выбор дня из календаря (кружочка)
    let circle = document.getElementsByClassName('circle');
    for (let i of circle) {
        i.addEventListener('click', function() {changeMonth(this, 'change', this.dataset.date);});
    }

    //Нажатие на кнопку "Неотправленные даты"
    let unapproved_hours_date = document.getElementsByClassName('unapproved_hours_date');
    for (let i of unapproved_hours_date) {
        i.addEventListener('click', function() {changeMonth(this, 'change', this.dataset.date);});
    }
    let unapproved_hours_date_hide = document.getElementsByClassName('unapproved_hours_date_hide');
    for (let i of unapproved_hours_date_hide) {
        i.addEventListener('click', function() {changeMonth(this, 'change', this.dataset.date);});
    }
    let unapproved_hours_list_div = $(".unapproved_hours_list_div .wrong_hours_date_div");
    if (unapproved_hours_list_div.length) {
        unapproved_hours_list_div.toArray().forEach(function (button) {
            button.addEventListener('click', function () {changeMonth(this, 'change', this.dataset.date);});
        });
    }
    let unapproved_hours_list_div_hide = $(".unapproved_hours_list_div_hide .wrong_hours_date_div");
    if (unapproved_hours_list_div_hide.length) {
        unapproved_hours_list_div_hide.toArray().forEach(function (button) {
            button.addEventListener('click', function () {changeMonth(this, 'change', this.dataset.date);});
        });
    }
    let not_full_sent_list_div = $(".not_full_sent_list_div .wrong_hours_date_div");
    if (not_full_sent_list_div.length) {
        not_full_sent_list_div.toArray().forEach(function (button) {
            button.addEventListener('click', function () {changeMonth(this, 'change', this.dataset.date);});
        });
    }



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


function hideCalendar(doHide=true) {
    //Функция скрытия/отображения календаря в верхней части страницы check_hours
    //Проверяем скрыт или отображён календарь
    let calendar_container = document.getElementsByClassName('calendar-container');
    if (!calendar_container) {
        return 0;
    }
    let hidden_calendar = document.getElementsByClassName('hidden-calendar');
    let unapproved_hours_list_div = document.getElementsByClassName('unapproved_hours_list_div');
    let left_panel = document.getElementsByClassName('left-panel');
    let right_panel = document.getElementsByClassName('right-panel');

    if (doHide) {
        //Скрываем календарь
        if (calendar_container) {
            calendar_container[0].style.display = "none"
        }
        //Отображаем заглушку календаря
        if (hidden_calendar) {
            hidden_calendar[0].style.display = "flex"
        }
        //Отображаем список НЕ ПРОВЕРЕНО
        if (unapproved_hours_list_div) {
            unapproved_hours_list_div[0].style.display = "flex"
        }
        //Меняем ширину меню со списками дат
        if (left_panel) {
            left_panel[0].classList.add("full_width");
        }
        if (right_panel) {
            right_panel[0].classList.add("hidden-panel");
        }
    }
    else if (!doHide) {
        //Отображаем календарь
        if (calendar_container) {
            calendar_container[0].style.display = "flex"
        }
        //Скрываем заглушку календаря
        if (hidden_calendar) {
            hidden_calendar[0].style.display = "none"
        }
        //Скрываем список НЕ ПРОВЕРЕНО
        if (unapproved_hours_list_div) {
            unapproved_hours_list_div[0].style.display = "none"
        }
        //Меняем ширину меню со списками дат
        if (left_panel) {
            left_panel[0].classList.remove("full_width");
        }
        if (right_panel) {
            right_panel[0].classList.remove("hidden-panel");
        }
    }
}

function changeMonth(button, eventType, value) {
    //Функция перелистывания месяца в календаре на странице check_hours

    //Если кликаем на месяц год или вышли из выбора даты в input date, то никаких изменений с календарём не производим
    if (eventType === 'click') {
        let month_year_date = document.getElementsByClassName('month-year-date');
        if (month_year_date) {
            month_year_date[0].style.display = "flex";
            month_year_date[0].focus(); // Set focus to the date input
        }
        let month_year_title = document.getElementsByClassName('month-year-title');
        if (month_year_title) {
            month_year_title[0].style.display = "none";
        }
        return true;
    }
    else if (eventType === 'focusout') {
        let month_year_date = document.getElementsByClassName('month-year-date');
        if (month_year_date) {
            month_year_date[0].style.display = "none";
        }
        let month_year_title = document.getElementsByClassName('month-year-title');
        if (month_year_title) {
            month_year_title[0].style.display = "flex";
        }
        return true;
    }

    //Если отредактировали дату, сменили месяц или день - обращаемся на сервер за новой информацией
    if (eventType !== 'change') {
        return true;
    }

    window.location.href = value? `/check_hours/${value}`:`/check_hours`;

}

function getAllProjects() {
    let pr = document.getElementById("select-filter-input-2");
    if (pr) {
        pr_list = {};
        for (let i = 0; i < pr.length; i++) {
            pr_list[pr.options[i].value] = pr.options[i].text;
        }
    }
}

function getAllStatuses(){
    let st = document.getElementById("select-filter-input-5");
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
    if (button.id === 'filter-input-2'){
        let input_2 = $('#select-filter-input-2');
        hideFilterInput(2, 0, 2);
        if (input_2.data('select2')) {
            input_2.select2('open');
        }
    }

    else if (button.id === 'filter-input-5'){
        let input_5 = $('#select-filter-input-5');
        hideFilterInput(5, 0, 2);
        if (input_5.data('select2')) {
            input_5.select2('open');
        }
    }

    else if (button.id === 'select-filter-input-2'){
        if (statusIsOpened) {
            hideFilterInput(2, 0, 2);
        }
        else {
            hideFilterInput(2, 2, 0);
        }

    }
    else if (button.id === 'select-filter-input-5'){
        if (statusIsOpened) {
            hideFilterInput(5, 0, 2);
        }
        else {
            hideFilterInput(5, 2, 0);
        }
    }

}

function filterMyTasksTable(button, tableId='towTable', fromShowUnapprovedTasksBtn=false) {
    //Функция скрывающая строки при фильтрации. Ищет совпадения, скрывает если совпадений не было найдено
    if (tableId === 'towTable') {
        if (button.id === 'select-filter-input-2') {
            let idList = $("#select-filter-input-2").val();
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

            document.getElementById("filter-input-2").value = selectedList;
            document.getElementById("filter-input-2").title = titleSelectedList;
        }
        else if (button.id === 'select-filter-input-5') {
            let idList = $("#select-filter-input-5").val();
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

            document.getElementById("filter-input-5").value = selectedList;
            document.getElementById("filter-input-5").title = titleSelectedList;
        }
        //Проверка на показать/скрыть непроверенное. Если на странице есть такая кнопка,
        // нужно фильтровать в зависимости от того, нажата или нет кнопка "Непроверенное" - кнопка только для рукотдела

        let unapproved_tasks_btn = document.getElementById("show_unapproved_tasks_btn");
        let show_unapproved_tasks = false;
        if (unapproved_tasks_btn) {
            let button_status = unapproved_tasks_btn.innerText;
            show_unapproved_tasks = button_status !== 'ПОКАЗАТЬ НЕПРОВЕРЕННОЕ';
        }
        else {
            show_unapproved_tasks = true;
        }

        // Список значений статусов
        let filter_input_1 = $("#filter-input-1").val().toLowerCase();
        let filter_input_2 = $("#select-filter-input-2").val();
        let filter_input_3 = $("#filter-input-3").val().toLowerCase();
        let filter_input_4 = $("#filter-input-4").val().toLowerCase();
        let filter_input_5 = $("#select-filter-input-5").val();
        let filter_input_6 = $("#filter-input-6").val().toLowerCase();

        let row_cnt = 0; //Счётчик не скрытых задач

        let tab = document.getElementById("towTable");

        if (tab.classList.contains('hideTable')) {
            tab = document.getElementById("towTable");
        }

        let tab_tr0 = tab.getElementsByTagName('tbody')[0];

        for (let i = 0, row; row = tab_tr0.rows[i]; i++) {
            //Сверяем статус строки "показать непроверенное"
            let row_status_filter = show_unapproved_tasks? 1:row.classList.contains('unapproved_hotr_list_hide')? 0:1;

            //Статус фильтрации для каждого столбца
            let status_filter_1 = !filter_input_1 ? 1 : 0;
            let status_filter_2 = !filter_input_2 ? 1 : 0;
            let status_filter_3 = !filter_input_3 ? 1 : 0;
            let status_filter_4 = !filter_input_4 ? 1 : 0;
            let status_filter_5 = !filter_input_5 ? 1 : 0;
            let status_filter_6 = !filter_input_6 ? 1 : 0;


            //Значения ячеек
            let val_1 = row.cells[1].dataset.value.toLowerCase();
            let val_2 = row.cells[2].dataset.value;
            let val_3 = row.cells[3].dataset.value.toLowerCase();
            let val_4 = row.cells[4].title.toLowerCase();
            let val_5 = row.cells[5].dataset.cur_value;
            let val_6 = row.cells[6].getElementsByTagName('input')[0].dataset.value.toLowerCase();

            //Ищем совпадения в ячейках
            if (!status_filter_1 && val_1.indexOf(filter_input_1) >= 0) {
                status_filter_1 = 1;
            }
            if (!status_filter_2 && filter_input_2.includes(val_2)) {
                status_filter_2 = 1;
            }
            if (!status_filter_3 && val_3.indexOf(filter_input_3) >= 0) {
                status_filter_3 = 1;
            }
            if (!status_filter_4 && val_4.indexOf(filter_input_4) >= 0) {
                status_filter_4 = 1;
            }
            if (!status_filter_5 && filter_input_5.includes(val_5)) {
                status_filter_5 = 1;
            }
            if (!status_filter_6 && val_6.indexOf(filter_input_6) >= 0) {
                status_filter_6 = 1;
            }

            if (row_status_filter && status_filter_1 && status_filter_2 && status_filter_3 && status_filter_4 && status_filter_5 && status_filter_6) {
                row.hidden = 0;
                row_cnt++;
            } else {
                row.hidden = 1;
                //Помимо скрытия строки снимаем флажок с чекбокса выбора строки
                let checkbox = row.getElementsByClassName("input_task_select");
                if (checkbox && checkbox[0].checked) {
                    checkbox[0].checked = 0;
                    unsentHotrSelect(checkbox[0]);
                }
            }
        }

        if (!row_cnt && !fromShowUnapprovedTasksBtn) {
            return createDialogWindow(status = 'info', description = ['Внимание!', 'Совпадений не найдено', 'Попробуйте изменить фильтр']);
        }
    }

    else if (tableId === 'towTable2') {
        // Список значений статусов
        let filter_input_11 = $("#filter-input-11").val().toLowerCase();
        let filter_input_12 = $("#filter-input-12").val().toLowerCase();
        let filter_input_13 = $("#filter-input-13").val().toLowerCase();

        let row_cnt = 0; //Счётчик не скрытых задач

        let tab = document.getElementById("towTable2");

        if (tab.classList.contains('hideTable')) {
            tab = document.getElementById("towTable2");
        }

        let tab_tr0 = tab.getElementsByTagName('tbody')[0];

        for (let i = 0, row; row = tab_tr0.rows[i]; i++) {
            //Статус фильтрации для каждого столбца
            let status_filter_11 = !filter_input_11 ? 1 : 0;
            let status_filter_12 = !filter_input_12 ? 1 : 0;
            let status_filter_13 = !filter_input_13 ? 1 : 0;

            //Значения ячеек
            let val_11 = row.cells[0].innerText.toLowerCase();
            let val_12 = row.cells[1].innerText.toLowerCase();
            let val_13 = row.cells[2].innerText.toLowerCase();

            //Ищем совпадения в ячейках
            if (!status_filter_11 && val_11.indexOf(filter_input_11) >= 0) {
                status_filter_11 = 1;
            }
            if (!status_filter_12 && val_12.indexOf(filter_input_12) >= 0) {
                status_filter_12 = 1;
            }
            if (!status_filter_13 && val_13.indexOf(filter_input_13) >= 0) {
                status_filter_13 = 1;
            }

            if (status_filter_11 && status_filter_12 && status_filter_13) {
                row.hidden = 0;
                row_cnt++;
            } else {
                row.hidden = 1;
            }
        }

        if (!row_cnt && !fromShowUnapprovedTasksBtn) {
            return createDialogWindow(status = 'info', description = ['Внимание!', 'Совпадений не найдено', 'Попробуйте изменить фильтр']);
        }
    }
}

function editTaskInformation(cell, value='', v_type='') {
    isEditTaskTable();
    let row = cell.closest('tr');
    let t_id = row.dataset.task;
    let tr_id = row.dataset.task_responsible;
    let user_id = row.dataset.user_id;
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
        if (userChanges[t_id][tr_id][user_id][v_type]) {
            delete userChanges[t_id][tr_id][user_id][v_type];
            //Если ключей не осталось, удаляем
            if (!Object.keys(userChanges[t_id][tr_id][user_id]).length) {
                delete userChanges[t_id][tr_id][user_id];
            }
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
            if (userChanges[t_id][tr_id][user_id]) {
                userChanges[t_id][tr_id][user_id][v_type] = value;
            }
            else {
                userChanges[t_id][tr_id][user_id] = {[v_type]: value};
            }
        }
        else {
            userChanges[t_id][tr_id] = {[user_id]: {[v_type]: value}};
        }
    }
    else {
        userChanges[t_id] = {[tr_id]: {[user_id]: {[v_type]: value}}};
    }
}

function showUnhotrUsers(button){
    // Отображаем/скрываем таблицу сотрудников не отправивших часы за указанную дату
    let unapproved_tasks_btn = document.getElementById("show_unapproved_tasks_btn");
    //Проверяем отобразить или скрыть таблицу
    if (button.classList.contains('selected')) {
        button.classList.remove("selected");
        document.getElementById('towTable').className = 'tow';
        document.getElementById('towTable2').className = 'tow hideTable';
        document.getElementsByClassName('unsent_h1')[0].style.display = "flex";
        document.getElementsByClassName('un_hotr_users_h1')[0].style.display = "none";
        document.getElementsByClassName('un_hotr_users_h1')[0].style.display = "none";
        unapproved_tasks_btn? unapproved_tasks_btn.disabled = 0:1;
        return;
    }

    //Если была нажата кнопка другого дня нужно убрать выделение, по этому проходим по всем кнопкам и удаляем класс выделение (selected)
    let wrong_hours_date_div = $(".wrong_hours_date_div");
    if (wrong_hours_date_div.length) {
        wrong_hours_date_div.toArray().forEach(function (button) {
            button.classList.remove("selected");
        });
    }

    button.classList.add("selected");
    let un_hotr_users = button.getElementsByClassName('div_un_hotr_users')[0].getElementsByTagName('tr');
    let h1_title = `Список сотрудников не отправивших часы: ${button.dataset.date} - ${button.dataset.weekday}`;
    document.getElementsByClassName('unsent_h1')[0].style.display = "none";
    document.getElementsByClassName('un_hotr_users_h1')[0].style.display = "flex";
    document.getElementsByClassName('un_hotr_users_h1')[0].innerText = h1_title;

    document.getElementById('towTable').className = 'tow hideTable';
    document.getElementById('towTable2').className = 'tow';
    unapproved_tasks_btn? unapproved_tasks_btn.disabled = 1:1;

    const tab = document.getElementById("towTable2");
    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
    tab_tr0.innerHTML = '';
    for (let i of un_hotr_users) {


        let row = tab_tr0.insertRow(0);

        //**************************************************
        // id
        let cellUserId = row.insertCell(0);
        cellUserId.className = "th_responsible_i";
        cellUserId.innerHTML = i.getElementsByTagName('td')[0].innerHTML;

        //**************************************************
        // ФИО сотрудника
        let cellFIO = row.insertCell(1);
        cellFIO.className = "th_responsible_i";
        cellFIO.innerHTML = i.getElementsByTagName('td')[1].innerHTML;

        //**************************************************
        // Не заполнено
        let cellFullDayUnsent = row.insertCell(2);
        cellFullDayUnsent.className = "th_responsible_i";
        cellFullDayUnsent.innerHTML = i.getElementsByTagName('td')[2].innerHTML;
    }
}

function saveTaskChanges(isSave=true) {

    let current_day = $(".current-day");
    if (current_day.length) {
        current_day = current_day[0].dataset.date;
    }
    else {
        current_day = document.URL.split('check_hours/')
        if (current_day.length === 1) {
            return createDialogWindow(status='error', description=[
                'Ошибка',
                'Не удалось определить день за который отправляются часы',
                'Обновите страницу и попробуйте снова'
            ]);
        }
        current_day = current_day[1]
    }

    let is_head_of_dept = document.getElementById("task-my_tasks_page");
    is_head_of_dept = is_head_of_dept.dataset.is_head_of_dept;

    //Проверяем, что строка выделена. Если нет параметра 'input_task_select' - удаляем запись о строке
    userChangesTask = inputTaskSelectNotInList(userChangesTask);
    userChangesWork = inputTaskSelectNotInList(userChangesWork);

    //Добавляем значение согласуемых часов строки
    userChangesTask = getHousrForUserChanges(userChangesTask);
    userChangesWork = getHousrForUserChanges(userChangesWork, false);

    fetch("/save_check_hours", {
        headers: {
            "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({
            userChangesTask: userChangesTask,
            userChangesWork: userChangesWork,
            currentDay: current_day,
            isSave: isSave,
            is_head_of_dept: is_head_of_dept,
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
    let userName = row.getElementsByClassName('td_task_responsible_user')[0].innerText;
    let newTitle = '';
    let r_or_s_dialod = document.getElementById('responsible_or_status__dialog');

    newTitle = `Для задачи "${td_task_task_name}" назначить статус. Ответственный: ${userName}`
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

function isEditTaskTable() {
    var save_btn = document.getElementById("save_btn");
    var annul_btn = document.getElementById("annul_btn");

    if (save_btn.disabled) {
        editTaskTable();
    }
}

function editTaskTable() {
    let save_btn = document.getElementById("save_btn");
    let cancel_btn = document.getElementById("cancel_btn");
    let annul_btn = document.getElementById("annul_btn");
    if (save_btn.disabled) {
        save_btn.disabled = 0;
        cancel_btn.disabled = 0;
        annul_btn.disabled = 0;
    }
    else {
        save_btn.disabled = 1;
        cancel_btn.disabled = 1;
        annul_btn.disabled = 1;
    }
}

function selectAllUnsentHotr(){
    //Выбор всех строк в таблице
    let selectStatus = 1;
    let th_tow_select = document.getElementsByClassName('th_tow_select')[0];
    if (th_tow_select.classList.contains('full_select')) {
        selectStatus = 0;
    }
    else if (th_tow_select.classList.contains('part_of_select')) {
        selectStatus = 0;
    }

    let input_task_select = $(".input_task_select");
    if (input_task_select.length) {
        input_task_select.toArray().forEach(function (button) {
            //Если происходит выбор флажков, проверяем, что строка не срыта
            if (selectStatus) {
                let row = button.closest('tr');
                if (!row.hidden) {
                    button.checked = selectStatus;
                    unsentHotrSelect(button);
                }
            }
            else if (button.checked != selectStatus) {
                button.checked = selectStatus;
                unsentHotrSelect(button);
            }
        });
    }

    if (!Object.keys(userChangesTask).length && !Object.keys(userChangesWork).length) {
        editTaskTable();
    }
}

function unsentHotrSelect(button){
    editTaskInformation(button, button.checked?'true':'false', button.classList[0]);

    //Чекбоксы
    let checkboxes = document.querySelectorAll('.input_task_select');
    checkboxes = document.querySelectorAll('tr:not([hidden="hidden"]) .input_task_select')
    //Статус, что всё выделено
    let allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
    //Статус, что везде снят выбор
    let allUnChecked = Array.from(checkboxes).every(checkbox => !checkbox.checked);

    //В шапке ячейка ВЫБОР для разукращивания
    let th_tow_select = document.getElementsByClassName('th_tow_select')[0];

    if (allChecked) {
      th_tow_select.classList.add("full_select");
      th_tow_select.classList.remove("part_of_select");
    }
    else if (allUnChecked) {
      th_tow_select.classList.remove("full_select");
      th_tow_select.classList.remove("part_of_select");
    }
    else {
      th_tow_select.classList.remove("full_select");
      th_tow_select.classList.add("part_of_select");
    }
}

function showUnapprovedTasks(button) {
    // Отображаем/скрываем несогласованные часы для рукотдела

    //Если отображен список сотрудников-должников, то кнопку не используем
    if (document.getElementById("towTable").classList.contains('hideTable')) {
         return;
    }
    else {
        //Если отображена таблицы с заглушкой, что данных нет, удаляем заглушку
        let rowsToRemove = document.querySelectorAll('tr.lvl-10');
        rowsToRemove.forEach(row => {
            row.remove();
        });

        //Кол-во доступного для проверки в календаре
        let label_hotr = document.querySelectorAll('.day-label_unsent_hotr');
        let label_hotr_hide = document.querySelectorAll('.day-label_unsent_hotr_hide');



        //Проверяем скрыт или отображён календарь
        let hidden_panel = document.getElementsByClassName('hidden-panel');
        let display_unapproved_hours_list = hidden_panel.length? "flex":"none";
        let display_unapproved_hours_list_reverse = "none";
        let display_unapproved_hours_date = hidden_panel.length? "none":"flex";
        let display_unapproved_hours_date_reverse = "none";

        //Список неотправленных дат
        let unapproved_hours_list_div = document.querySelectorAll('.unapproved_hours_list_div');
        let unapproved_hours_list_div_hide = document.querySelectorAll('.unapproved_hours_list_div_hide');
        unapproved_hours_list_div.forEach(hotr => {
            hotr.classList.remove('unapproved_hours_list_div');
            hotr.classList.add('unapproved_hours_list_div_hide');
            hotr.style.display = display_unapproved_hours_list_reverse;
        });
        unapproved_hours_list_div_hide.forEach(hotr => {
            hotr.classList.remove('unapproved_hours_list_div_hide');
            hotr.classList.add('unapproved_hours_list_div');
            hotr.style.display = display_unapproved_hours_list;
        });

        //Список неотправленных дат из календаря
        let unapproved_hours_date = document.querySelectorAll('.unapproved_hours_date');
        let unapproved_hours_date_hide = document.querySelectorAll('.unapproved_hours_date_hide');
        unapproved_hours_date.forEach(hotr => {
            hotr.classList.remove('unapproved_hours_date');
            hotr.classList.add('unapproved_hours_date_hide');
            hotr.style.display = display_unapproved_hours_date_reverse;
        });
        unapproved_hours_date_hide.forEach(hotr => {
            hotr.classList.remove('unapproved_hours_date_hide');
            hotr.classList.add('unapproved_hours_date');
            hotr.style.display = display_unapproved_hours_date;
        });

        let button_status = button.innerText;

        if(button_status === 'ПОКАЗАТЬ НЕПРОВЕРЕННОЕ') {
            button.innerText = 'СКРЫТЬ НЕПРОВЕРЕННОЕ';
            button.classList.add("object_main_btn_pressed");

            label_hotr.forEach(hotr => {
                hotr.style.display = "none";
            });
            label_hotr_hide.forEach(hotr => {
                hotr.style.display = "flex";
            });

            //Кружки в календаре
            let orange_circles = document.querySelectorAll('.unsent_day_hotr_hide');
            orange_circles.forEach(circle => {
                circle.classList.remove('unsent_day_hotr_hide');
                circle.classList.add('unsent_day_hotr_show');
            });
        }
        else {
            button.innerText = 'ПОКАЗАТЬ НЕПРОВЕРЕННОЕ';
            button.classList.remove("object_main_btn_pressed");

            label_hotr.forEach(hotr => {
                hotr.style.display = "flex";
            });
            label_hotr_hide.forEach(hotr => {
                hotr.style.display = "none";
            });

            //Кружки в календаре
            let orange_circles = document.querySelectorAll('.unsent_day_hotr_show');
            orange_circles.forEach(circle => {
                circle.classList.remove('unsent_day_hotr_show');
                circle.classList.add('unsent_day_hotr_hide');
            });
        }
    }
    return filterMyTasksTable(false, 'towTable', true);
}

function inputTaskSelectNotInList(userChanges) {
    // Функция проверяет список изменения (userChangesTask/userChangesWork), что строка выделена
    // Если нет параметра 'input_task_select' - удаляем запись о строке
    for (let t_id in userChanges) {
        for (let tr_id in userChanges[t_id]) {
            for (let user_id in userChanges[t_id][tr_id]) {
                if (!Object.keys(userChanges[t_id][tr_id][user_id]).includes('input_task_select')) {
                    delete userChanges[t_id][tr_id][user_id];
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
            }
        }
    }
    return userChanges;
}

function getHousrForUserChanges(userChanges, isTask=true) {
    // Для каждой согласуемой строки добавляем часы, чтобы проверить валидность данных
    let row_type = isTask? 'task':'org_work';
    for (let t_id in userChanges) {
        for (let tr_id in userChanges[t_id]) {
            for (let user_id in userChanges[t_id][tr_id]) {
                let hotr_value = `tr[data-row_type="${row_type}"][data-task="${t_id}"][data-task_responsible="${tr_id}"][data-user_id="${user_id}"] .td_task_work_day`;

                hotr_value = document.querySelector(hotr_value).dataset.value;
                console.log(hotr_value);
                userChanges[t_id][tr_id][user_id]['hotr_value'] = hotr_value;
            }
        }
    }
    return userChanges;
}