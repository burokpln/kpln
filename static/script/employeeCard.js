$(document).ready(function() {
    document.getElementById('user_card_crossBtnNAW')? document.getElementById('user_card_crossBtnNAW').addEventListener('click', function() {closeModal();this.closest('section').dataset.user_id='';}):'';
    document.getElementById('change_salary_btn_i')? document.getElementById('change_salary_btn_i').addEventListener('click', function() {getSalary();}):'';
    document.getElementById('fire_employee_i')? document.getElementById('fire_employee_i').addEventListener('click', function() {showSetFireEmployee();}):'';

    document.getElementById('maternity_leave_employee_i')? document.getElementById('maternity_leave_employee_i').addEventListener('click', function() {showSetMaternityLeave();}):'';

    document.getElementById('user_card_last_name')? document.getElementById('user_card_last_name').addEventListener('change', function() {editFNUC_Real_Time();}):'';
    document.getElementById('user_card_first_name')? document.getElementById('user_card_first_name').addEventListener('change', function() {editFNUC_Real_Time();}):'';
    document.getElementById('user_card_surname')? document.getElementById('user_card_surname').addEventListener('change', function() {editFNUC_Real_Time();}):'';
    document.getElementById('id_user_card_edit_full_name')? document.getElementById('id_user_card_edit_full_name').addEventListener('click', function() {editFullNameUserCard();}):'';
    document.getElementById('user_card_date_promotion')? document.getElementById('user_card_date_promotion').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin'); isEditDatePromotion(this)}):'';
    document.getElementById('user_card_date_promotion')? document.getElementById('user_card_date_promotion').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout'); isEditDatePromotion(this)}):'';
    document.getElementById('user_card_date_promotion')? document.getElementById('user_card_date_promotion').addEventListener('change', function() {replaceAllDateForNewEmployee(this);}):'';
    document.getElementById('user_card_b_day')? document.getElementById('user_card_b_day').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('user_card_b_day')? document.getElementById('user_card_b_day').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('user_card_salary_sum')? document.getElementById('user_card_salary_sum').addEventListener('change', function() {document.getElementById('user_card_salary_date').value = '';}):'';
    document.getElementById('user_card_salary_date')? document.getElementById('user_card_salary_date').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('user_card_salary_date')? document.getElementById('user_card_salary_date').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('user_card_salary_date')? document.getElementById('user_card_salary_date').addEventListener('change', function() {replaceAllDateForNewEmployee(this);}):'';
    document.getElementById('user_card_employment_date')? document.getElementById('user_card_employment_date').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('user_card_employment_date')? document.getElementById('user_card_employment_date').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('user_card_employment_date')? document.getElementById('user_card_employment_date').addEventListener('change', function() {replaceAllDateForNewEmployee(this);}):'';
    document.getElementById('user_card_labor_status')? document.getElementById('user_card_labor_status').addEventListener('click', function() {userCardLaborStatus(); userCardLaborData()}):'';
    document.getElementById('user_card_labor_date')? document.getElementById('user_card_labor_date').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('user_card_labor_date')? document.getElementById('user_card_labor_date').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('user_card_labor_date')? document.getElementById('user_card_labor_date').addEventListener('change', function() {changeUserCardLaborData(); replaceAllDateForNewEmployee(this);}):'';
    document.getElementById('user_card_hours')? document.getElementById('user_card_hours').addEventListener('click', function() {userCardHoursData()}):'';
    document.getElementById('user_card_hours_date')? document.getElementById('user_card_hours_date').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('user_card_hours_date')? document.getElementById('user_card_hours_date').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('apply__edit_btn_i')? document.getElementById('apply__edit_btn_i').addEventListener('click', function() {saveEmplChanges();}):'';
    document.getElementById('cancel__edit_btn_i')? document.getElementById('cancel__edit_btn_i').addEventListener('click', function() {closeModal(), this.closest('section').dataset.user_id='';}):'';

    $('#user_card_dept_select').on("select2:open", function() {
        document.getElementById("user_card_date_promotion").style.setProperty('width', '80px','important');
        document.getElementById("user_card_dept_select_label").style.setProperty('min-width', '140px','important');
    //    $('#user_card_dept_select').select2({ width: '80%' });
    });

    $('#user_card_dept_select').on("select2:close", function() {
        document.getElementById("user_card_date_promotion").style.setProperty('width', '105px','important');
        document.getElementById("user_card_dept_select_label").style.setProperty('min-width', '200px','important');
    });

    $('#user_card_dept_select').on("change", function() {
        document.getElementById('user_card_date_promotion').value = "";
            document.getElementById('user_card_date_promotion').dataset.value = '';
    });
    if (document.getElementById('verif_dialog_empl__ok')) {
        document.getElementById('verif_dialog_empl__ok').addEventListener('click', function () {
            setEmployeeCard();
        });
    }
});

function getSalary() {
    let salary_history_table = document.getElementById('salary_history_table');
    let tab_tr0 = salary_history_table.getElementsByTagName('tbody')[0];
    let tab_numRow = salary_history_table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    let description = ['История изменения зарплаты'];

    if (tab_numRow.length) {
        for (var i = 0; i<=tab_numRow.length-1; i++) {
            let cellSalaryDate = tab_numRow[i].getElementsByTagName('td')[0].innerHTML;
            let cellSalarySum = tab_numRow[i].getElementsByTagName('td')[1].innerHTML;
            let cellSalaryDept = tab_numRow[i].getElementsByTagName('td')[2].innerHTML;
            let cellSalaryCreateAt = tab_numRow[i].getElementsByTagName('td')[3].innerHTML;
            let cellCurrentSalary = tab_numRow[i].getElementsByTagName('td')[4].innerHTML;
            let cellSalariesDescription = tab_numRow[i].getElementsByTagName('td')[5].innerHTML;
            cellSalariesDescription = cellSalariesDescription !==''?' - ' + cellSalariesDescription: cellSalariesDescription;

            description.push(cellCurrentSalary + cellSalaryDate + ': ' + cellSalarySum + ' - ' + cellSalaryDept + ' (' + cellSalaryCreateAt+ ')' + cellSalariesDescription)
        }
        return createDialogWindow(status='info', description=description);
    }
    else {
        return createDialogWindow(status='error', description=['Зарплата ещё не назначена']);
    }
}

function showSetFireEmployee() {
    let user_id = document.querySelector("#employee-user__dialog").dataset.user_id;

    if (!user_id) {
        return createDialogWindow(status='error', description=['Сотрудник не найден']);
    }

    return createDialogWindow(status='info',
            description=['Укажите дату увольнения'],
            func=[['click', [setFireEmployeeWithComment, user_id]]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ',
                },
            ],
            text_comment = true,
            loading_windows=false,
            text_comment_type = 'date',
            );
}

function setFireEmployeeWithComment(user_id) {
    var text_comment = document.getElementById('dialog_window_text_comment_input').value;
    if (!text_comment) {
        return document.getElementById('dialog_window_text_comment_input').style.border = "solid #FB3F4A";
    }
    else {
        document.getElementById('dialog_window_text_comment_input').style.border = "1px solid grey";
        text_comment = convertDate(text_comment)
        let curDate = new Date();
        let curDay = curDate.getDate() + 1; //ПЛЮС 1 ДЕНЬ Т.К. В ФАЙЛЕ ДАННЫЕ ОБНОВЛЯЮТСЯ НОЧЬЮ В ПОНЕДЕЛЬНИК, А В НЕДЕЛЬНОМ ПЛАНЕ ПОИСК ПО ВТОРНИКАМ. СОЗДАЕМ ДАТУ ВТОРНИКА
        let curMohth = curDate.getMonth();
        let currentYear = curDate.getFullYear();
        let newDate = new Date(currentYear, curMohth, curDay);

        if (new Date(text_comment).valueOf() < newDate.valueOf()) {
            removeLogInfo();
            return createDialogWindow(status='info',
                description=['Указан прошедший день', 'Сотруднику незамедлительно получит статус "уволен"', 'Подтвердите действие'],
                func=[['click', [setFireEmployee, user_id, text_comment]]],
                buttons=[
                    {
                        id:'flash_cancel_button',
                        innerHTML:'ОТМЕНИТЬ',
                    },
                ],
                );
        }
        removeLogInfo();
        setFireEmployee(user_id=user_id, text_comment=text_comment);
    }
}

function setFireEmployee(user_id=false, text_comment=false) {
    if (text_comment == false) {
        return createDialogWindow(status='error', description=['Ошибка удаления', 'Не определена дата увольнения']);
    }
    else if (user_id == false) {
        return createDialogWindow(status='error', description=['Ошибка удаления', 'Не определен сотрудник']);
    }
    else {
        removeLogInfo();
         //Записываем данные в БД
        fetch('/fire_employee', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'employee_id': user_id,
                'fire_date': text_comment
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    return window.location.href = '/employees-list';
                }
                else {
                    let description = data.description;
                    return createDialogWindow(status='error', description=description);
                }
            })
        return;
    }
}

function AddEmployee(button) {
    var row = button.closest('tr');
    var employeeId = row.dataset.user_id;
    const dialog = document.querySelector("#employee-user__dialog");
    dialog.showModal();
}

function getEmployeeCard(button) {
    var row = button.closest('tr');
    var employeeId = row.dataset.user_id
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    fetch(`/get_card_employee/${employeeId}`)
        .then(response => response.json())
        .then(data => {
            const dialog = document.querySelector("#employee-user__dialog");

            dialog.setAttribute("data-user_id", data.employee['user_id']);

            document.getElementById('user_card_name').value = data.employee['name'];
            document.getElementById('user_card_name').dataset.value = data.employee['name'];
            //Список изменений ФИО
            let user_card_name_label  = document.getElementById('user_card_name_label');
            user_card_name_label.innerText = 'ФИО'
            if (data.unch_list.length) {

                let user_card_hover_history = document.createElement("div");
                user_card_hover_history.className = "user_card_hover_history";
                for (let i of data.unch_list) {
                    let user_card_hover_history_row = document.createElement("div");
                    user_card_hover_history_row.className = "user_card_hover_history_row";

                        let user_card_hover_history_row_name = document.createElement("div");
                        user_card_hover_history_row_name.className = "user_card_hover_history_row_name";
                        user_card_hover_history_row_name.innerText = i['user_card_hover_history_row_name'] + '\u00A0\u00A0';

                        // let user_card_hover_history_row_date = document.createElement("div");
                        // user_card_hover_history_row_date.className = "user_card_hover_history_row_date";
                        // user_card_hover_history_row_date.innerText = '\u00A0' + i['date_promotion_txt'] + '\u00A0\u00A0';

                        let user_card_hover_history_row_created_at = document.createElement("div");
                        user_card_hover_history_row_created_at.className = "user_card_hover_history_row_created_at";
                        user_card_hover_history_row_created_at.innerText = '(' + i['created_at_txt'] + ')';

                        user_card_hover_history_row.appendChild(user_card_hover_history_row_name);
                        // user_card_hover_history_row.appendChild(user_card_hover_history_row_date);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_created_at);

                    user_card_hover_history.appendChild(user_card_hover_history_row);
                }
                user_card_name_label.appendChild(user_card_hover_history);
            }

            document.getElementById('user_card_last_name').value = data.employee['last_name'];
            document.getElementById('user_card_last_name').dataset.value = data.employee['last_name'];

            document.getElementById('user_card_first_name').value = data.employee['first_name'];
            document.getElementById('user_card_first_name').dataset.value = data.employee['first_name'];

            document.getElementById('user_card_surname').value = data.employee['surname'];
            document.getElementById('user_card_surname').dataset.value = data.employee['surname'];

            $('#user_card_contractor_select').val(data.employee['contractor_id']? data.employee['contractor_id'].toString():null).trigger('change');
            document.getElementById('user_card_contractor_select').dataset.value = data.employee['contractor_id']? data.employee['contractor_id'].toString():null;

            document.getElementById('user_card_pers_num').value = data.employee['pers_num'];
            document.getElementById('user_card_pers_num').dataset.value = data.employee['pers_num'];

            $('#user_card_dept_select').val(data.employee['group_id']? data.employee['group_id'].toString():null).trigger('change');
            document.getElementById('user_card_dept_select').dataset.value = data.employee['group_id']? data.employee['group_id'].toString():null;

            document.getElementById('user_card_date_promotion').value = data.employee['date_promotion_txt'];
            document.getElementById('user_card_date_promotion').dataset.value = data.employee['date_promotion_txt'];

            $('#user_card_position_name_select').val(data.employee['position_id']? data.employee['position_id'].toString():null).trigger('change');
            document.getElementById('user_card_position_name_select').dataset.value = data.employee['position_id']? data.employee['position_id'].toString():null;

            document.getElementById('user_card_b_day').value = data.employee['b_day_txt'];
            document.getElementById('user_card_b_day').dataset.value = data.employee['b_day_txt'];

            $('#user_card_education_name_select').val(data.employee['education_id']? data.employee['education_id'].toString():null).trigger('change');
            document.getElementById('user_card_education_name_select').dataset.value = data.employee['education_id']? data.employee['education_id'].toString():null;

            document.getElementById('user_card_salary_sum').value = data.employee['salary_sum_rub'];
            document.getElementById('user_card_salary_sum').dataset.value = data.employee['salary_sum_rub'];

            document.getElementById('user_card_salary_date').value = data.employee['salary_date_txt'];
            document.getElementById('user_card_salary_date').dataset.value = data.employee['salary_date_txt'];

            //Если сотрудник работает (не уволен), отображаем дату приёма
            if (data.employee['pers_num'] !== null && !data.employee['status1']) {
                document.getElementById('user_card_employment_date').value = data.employee['employment_date_txt'];
                document.getElementById('user_card_employment_date').dataset.value = data.employee['employment_date_txt'];
                document.getElementById('user_card_employment_date').disabled = true;
                document.getElementById('user_card_employment_date').readOnly = true;
            }
            else {
                document.getElementById('user_card_employment_date').value = '';
                document.getElementById('user_card_employment_date').dataset.value = '';
                document.getElementById('user_card_employment_date').disabled = false;
                document.getElementById('user_card_employment_date').readOnly = false;
            }

            document.getElementById('user_card_labor_status').checked = data.employee['labor_status'];
            document.getElementById('user_card_labor_status').dataset.value = data.employee['labor_status'];

            document.getElementById('user_card_labor_date').value = data.employee['empl_labor_date_txt'];
            document.getElementById('user_card_labor_date').dataset.value = data.employee['empl_labor_date_txt'];

            document.getElementById('user_card_hours').checked = data.employee['full_day_status'];
            document.getElementById('user_card_hours').dataset.value = data.employee['full_day_status'];

            document.getElementById('user_card_hours_date').value = data.employee['empl_hours_date_txt'];
            document.getElementById('user_card_hours_date').dataset.value = data.employee['empl_hours_date_txt'];

            let salary_history_table = document.getElementById('salary_history_table');

            // Кнопки под аватаркой
            if (data.employee['pers_num'] !== null) {
                document.getElementById('change_salary_btn_i').style.display = "inline-block";
                document.getElementById('fire_employee_i').style.display = "inline-block";
                document.getElementById('maternity_leave_employee_i').style.display = "inline-block";
            }
            else {
                document.getElementById('change_salary_btn_i').style.display = "none";
                document.getElementById('fire_employee_i').style.display = "none";
                document.getElementById('maternity_leave_employee_i').style.display = "none";
            }
            //Если сотрудник уже уволен, кнопки "уволен" и "декрет" нет
            if (data.employee['status3'] === "увол.") {
                document.getElementById('fire_employee_i').style.display = "none";
                document.getElementById('maternity_leave_employee_i').style.display = "none";
            }
            //Если сотрудник в декрете, кнопки "уволен" нет
            if (data.employee['status2']) {
                document.getElementById('maternity_leave_employee_i').innerText = "ИЗ ДЕКРЕТА";
            }
            else {
                document.getElementById('maternity_leave_employee_i').innerText = "В ДЕКРЕТ";
            }

            let tab_tr0 = salary_history_table.getElementsByTagName('tbody')[0];
            let tab_numRow = salary_history_table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
            // Удаляем всё из таблицы зарплат
            for (var i = 1; i<=tab_numRow.length;) {
                salary_history_table.deleteRow(1);
            }

            for (var i = 0; i < data.salaries_list.length; i++) {
                let row = tab_tr0.insertRow(tab_numRow.length);

                let cellSalaryDate = row.insertCell(0);
                cellSalaryDate.innerHTML = data.salaries_list[i]['salary_date'];

                let cellSalarySum = row.insertCell(1);
                cellSalarySum.innerHTML = data.salaries_list[i]['salary_sum_rub'];

                let cellSalaryDept = row.insertCell(2);
                cellSalaryDept.innerHTML = data.salaries_list[i]['dept_short_name'];

                let cellSalaryCreateAt = row.insertCell(3);
                cellSalaryCreateAt.innerHTML = data.salaries_list[i]['created_at'];

                let cellCurrentSalary = row.insertCell(4);
                cellCurrentSalary.innerHTML = data.salaries_list[i]['cur_salary'];

                let cellSalariesDescription = row.insertCell(5);
                cellSalariesDescription.innerHTML = data.salaries_list[i]['salaries_description'];
            }

            //Список изменений отделов
            let user_card_dept_select_label  = document.getElementById('user_card_dept_select_label');
            user_card_dept_select_label.innerText = 'ОТДЕЛ/ГРУППА'
            if (data.dept_promotions.length) {

                let user_card_hover_history = document.createElement("div");
                user_card_hover_history.className = "user_card_hover_history";
                for (let i of data.dept_promotions) {
                    let user_card_hover_history_row = document.createElement("div");
                    user_card_hover_history_row.className = i['cur_dept']? "user_card_hover_history_current_row":"user_card_hover_history_row";

                        let user_card_hover_history_row_name = document.createElement("div");
                        user_card_hover_history_row_name.className = "user_card_hover_history_row_name";
                        user_card_hover_history_row_name.innerText = i['user_card_hover_history_row_name'];

                        let user_card_hover_history_row_date = document.createElement("div");
                        user_card_hover_history_row_date.className = "user_card_hover_history_row_date";
                        user_card_hover_history_row_date.innerText = '\u00A0' + i['date_promotion_txt'] + '\u00A0\u00A0';

                        let user_card_hover_history_row_created_at = document.createElement("div");
                        user_card_hover_history_row_created_at.className = "user_card_hover_history_row_created_at";
                        user_card_hover_history_row_created_at.innerText = '(' + i['created_at_txt'] + ')';

                        user_card_hover_history_row.appendChild(user_card_hover_history_row_name);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_date);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_created_at);

                    user_card_hover_history.appendChild(user_card_hover_history_row);
                }
                user_card_dept_select_label.appendChild(user_card_hover_history);
            }

            //Список приёмов/увольнений
            let user_card_employment_date_label  = document.getElementById('user_card_employment_date_label');
            user_card_employment_date_label.innerText = 'ДАТА ПРИЁМА'
            if (data.haf_list.length) {

                let user_card_hover_history = document.createElement("div");
                user_card_hover_history.className = "user_card_hover_history";
                for (let i of data.haf_list) {
                    let user_card_hover_history_row = document.createElement("div");
                    user_card_hover_history_row.className = i['cur_haf']? "user_card_hover_history_current_row":"user_card_hover_history_row";

                        let user_card_hover_history_row_name = document.createElement("div");
                        user_card_hover_history_row_name.className = "user_card_hover_history_row_name";
                        user_card_hover_history_row_name.innerText = i['user_card_hover_history_row_name'];

                        let user_card_hover_history_row_date = document.createElement("div");
                        user_card_hover_history_row_date.className = "user_card_hover_history_row_date";
                        user_card_hover_history_row_date.innerText = '\u00A0' + i['date_haf_txt'] + '\u00A0\u00A0';

                        let user_card_hover_history_row_created_at = document.createElement("div");
                        user_card_hover_history_row_created_at.className = "user_card_hover_history_row_created_at";
                        user_card_hover_history_row_created_at.innerText = '(' + i['created_at_txt'] + ')';

                        user_card_hover_history_row.appendChild(user_card_hover_history_row_name);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_date);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_created_at);

                    user_card_hover_history.appendChild(user_card_hover_history_row);
                }
                user_card_employment_date_label.appendChild(user_card_hover_history);
            }

            //Список изменения статуса "трудозатраты"
            let user_card_labor_status_label  = document.getElementById('user_card_labor_status_label');
            user_card_labor_status_label.innerText = 'ТРУДОЗАТРАТЫ'
            if (data.labor_status_list.length) {

                let user_card_hover_history = document.createElement("div");
                user_card_hover_history.className = "user_card_hover_history";

                for (let i of data.labor_status_list) {
                    let user_card_hover_history_row = document.createElement("div");
                    user_card_hover_history_row.className = i['cur_labor_status']? "user_card_hover_history_current_row":"user_card_hover_history_row";

                        let user_card_hover_history_row_name = document.createElement("div");
                        user_card_hover_history_row_name.className = "user_card_hover_history_row_name";
                        user_card_hover_history_row_name.innerText = i['user_card_hover_history_row_name'];

                        let user_card_hover_history_row_date = document.createElement("div");
                        user_card_hover_history_row_date.className = "user_card_hover_history_row_date";
                        user_card_hover_history_row_date.innerText = '\u00A0' + i['empl_labor_date_txt'] + '\u00A0\u00A0';

                        let user_card_hover_history_row_created_at = document.createElement("div");
                        user_card_hover_history_row_created_at.className = "user_card_hover_history_row_created_at";
                        user_card_hover_history_row_created_at.innerText = '(' + i['created_at_txt'] + ')';

                        user_card_hover_history_row.appendChild(user_card_hover_history_row_name);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_date);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_created_at);

                    user_card_hover_history.appendChild(user_card_hover_history_row);
                }
                user_card_labor_status_label.appendChild(user_card_hover_history);
                user_card_labor_status_label.title = '';
            }
            else {
                user_card_labor_status_label.title = 'Статус подачи часов сотрудником';
            }

            //Список изменения статуса "почасовая оплата"
            let user_card_hours_label  = document.getElementById('user_card_hours_label');
            user_card_hours_label.innerText = 'ПОЧАСОВАЯ ОПЛАТА'
            if (data.hour_per_day_norm_list.length) {

                let user_card_hover_history = document.createElement("div");
                user_card_hover_history.className = "user_card_hover_history";

                for (let i of data.hour_per_day_norm_list) {
                    let user_card_hover_history_row = document.createElement("div");
                    user_card_hover_history_row.className = i['full_day_status_name']? "user_card_hover_history_current_row":"user_card_hover_history_row";

                        let user_card_hover_history_row_name = document.createElement("div");
                        user_card_hover_history_row_name.className = "user_card_hover_history_row_name";
                        user_card_hover_history_row_name.innerText = i['user_card_hover_history_row_name'];

                        let user_card_hover_history_row_date = document.createElement("div");
                        user_card_hover_history_row_date.className = "user_card_hover_history_row_date";
                        user_card_hover_history_row_date.innerText = '\u00A0' + i['empl_hours_date_txt'] + '\u00A0\u00A0';

                        let user_card_hover_history_row_created_at = document.createElement("div");
                        user_card_hover_history_row_created_at.className = "user_card_hover_history_row_created_at";
                        user_card_hover_history_row_created_at.innerText = '(' + i['created_at_txt'] + ')';

                        user_card_hover_history_row.appendChild(user_card_hover_history_row_name);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_date);
                        user_card_hover_history_row.appendChild(user_card_hover_history_row_created_at);

                    user_card_hover_history.appendChild(user_card_hover_history_row);
                }
                user_card_hours_label.appendChild(user_card_hover_history);
                user_card_hours_label.title = '';
            }
            else {
                user_card_hours_label.title = 'Статус почасовой работы сотрудником';
            }

            //Перекрашиваем правую границу если ранее была открыта карточка и была неудачная попытка сохранения с невалидными данными
            user_card_name_label.style.borderRight = "None";
            document.getElementById('user_card_contractor_label').style.borderRight = "None";
            document.getElementById('user_card_pers_num_label').style.borderRight = "None";
            document.getElementById('user_card_dept_select_label').style.borderRight = "None";
            document.getElementById('user_card_position_name_select_label').style.borderRight = "None";
            document.getElementById('user_card_b_day_label').style.borderRight = "None";
            document.getElementById('user_card_education_name_select_label').style.borderRight = "None";
            document.getElementById('user_card_salary_sum_label').style.borderRight = "None";
            document.getElementById('user_card_employment_date_label').style.borderRight = "None";
            document.getElementById('user_card_labor_status_label').style.borderRight = "None";
            document.getElementById('user_card_hours_label').style.borderRight = "None";

            // Открытие карточки сотрудника
            openModal();
            // Скрытие/отображение строки с кол-вом нормы дня
            userCardLaborStatus();

        })
        .catch(error => {
            sendErrorToServer(['get_card_employee', error.toString()]);
            console.error('Error:', error);
        });
};

var isExecutingSetEmployeeCard = false;
function setEmployeeCard() {
    // Предыдущее выполнение функции не завершено
    if (isExecutingSetEmployeeCard) {
        return
    }
    isExecutingSetEmployeeCard = true;

    const verificationDialog = document.getElementById('verif_dialog_empl');
    verificationDialog.close();

    var user_id = document.getElementById('employee-user__dialog').dataset.user_id;

    var last_name = document.getElementById('user_card_last_name').value;
    var first_name = document.getElementById('user_card_first_name').value;
    var surname = document.getElementById('user_card_surname').value;
    var contractor_id = document.getElementById('user_card_contractor_select').value;
    var pers_num = document.getElementById('user_card_pers_num').value;
    var group_id = document.getElementById('user_card_dept_select').value;
    var group_date_promotion = document.getElementById('user_card_date_promotion').value;
    var position_id = document.getElementById('user_card_position_name_select').value;
    var b_day = document.getElementById('user_card_b_day').value;
    var education_id = document.getElementById('user_card_education_name_select').value;
    var salary_sum = document.getElementById('user_card_salary_sum').value;
    var salary_date = document.getElementById('user_card_salary_date').value;
    var salaries_description = document.getElementById('user_card_salaries_description').value;
    var employment_date = document.getElementById('user_card_employment_date').value;
    var labor_status = document.getElementById('user_card_labor_status').checked;
    var labor_date = document.getElementById('user_card_labor_date').value;
    var full_day_status = labor_status? document.getElementById('user_card_hours').checked:false;
    var full_day_date = labor_status? document.getElementById('user_card_hours_date').value:'';

    var la_name = document.getElementById('user_card_name_label');
    var fi_name = document.getElementById('user_card_name_label');
    var co_name = document.getElementById('user_card_contractor_label');
    var pe_num = document.getElementById('user_card_pers_num_label');
    var gr_name = document.getElementById('user_card_dept_select_label');
    var po_name = document.getElementById('user_card_position_name_select_label');
    var b_d = document.getElementById('user_card_b_day_label');
    var ed_name = document.getElementById('user_card_education_name_select_label');
    var sal_sum = document.getElementById('user_card_salary_sum_label');
    var sal_date = document.getElementById('user_card_salary_sum_label');
    var emp_date = document.getElementById('user_card_employment_date_label');
    var la_status = document.getElementById('user_card_labor_status_label');

    var full_day_status_dataset = labor_status? document.getElementById('user_card_hours').dataset.value:false;

    check_lst = [
        [last_name, la_name],
        [first_name, fi_name],
        [contractor_id, co_name],
        [pers_num, pe_num],
        [group_id, gr_name],
        [group_date_promotion, gr_name],
        [position_id, po_name],
        [b_day, b_d],
        [education_id, ed_name],
        [salary_sum, sal_sum],
        [salary_date, sal_date],
        [employment_date, emp_date]
    ]
    description_lst = ["Фамилия", "Имя", "Компания", "Таб. №", "Группа", "Дата перевода в отдел/группу", "Должность", "День рождения", "Образование", "Текущая зарплата", "Дата зарплаты", "Дата приёма"]

    var description = ['Ошибка', 'Заполнены не все поля:'];

    for (var i=0; i<check_lst.length; i++) {
        if (!check_lst[i][0]) {
            check_lst[i][1].style.borderRight = "solid #FB3F4A";
            description.push('&nbsp;- ' + description_lst[i])
        }
        else {
            check_lst[i][1].style.borderRight = "None";
        }
    }

    //Проверка статуса и даты (трудозатраты, почасовая)
    let labor_fyl_day_status = false // Статус, что если изменили статус галкам, то указаны даты

    if (!labor_date) {
        la_status.style.borderRight = "solid #FB3F4A";
        description.push('&nbsp;- Дата смены статуса трудозатра');
        labor_fyl_day_status = true;
    }
    else {
        la_status.style.borderRight = "None";
        labor_fyl_day_status = false;
    }

    if (full_day_status_dataset === 'true') {
        if (!full_day_date) {
            document.getElementById('user_card_hours_label').style.borderRight = "solid #FB3F4A";
            description.push('&nbsp;- Дата смены статуса почасовой оплаты');
            labor_fyl_day_status = true;
        }
        else {
            document.getElementById('user_card_hours_label').style.borderRight = "None";
            labor_fyl_day_status = labor_fyl_day_status? true:false;
        }
    }

    if (!user_id || !last_name || !first_name || !pers_num || !group_id || !group_date_promotion || !position_id || !b_day || !education_id ||
                                        !salary_sum || !salary_date || !employment_date || labor_fyl_day_status) {
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }

    if (document.getElementById('user_card_pers_num').dataset.value) {
    }

    group_date_promotion = group_date_promotion.split("-").length === 1? convertDate(group_date_promotion):group_date_promotion;
    b_day = b_day.split("-").length === 1? convertDate(b_day):b_day;
    salary_date = salary_date.split("-").length === 1? convertDate(salary_date):salary_date;
    employment_date = employment_date.split("-").length === 1? convertDate(employment_date):employment_date;
    labor_date = labor_date.split("-").length === 1? convertDate(labor_date):labor_date;
    if (full_day_date) {
        full_day_date = full_day_date.split("-").length === 1? convertDate(full_day_date):full_day_date;
    }
    else {
        full_day_date = labor_date;
    }

    description = ['Ошибка'];
    let todayPlusOneYear = new Date(new Date().getTime() + (1000 * 60 * 60 * 24 * 365));
    //Проверка, что дата приёма, смена статуса и пр. даты не меньше 2000 года и не больше года вперед
    if (new Date(salary_date) < new Date('2000-01-01')) {
        sal_date.style.borderRight = "solid #FB3F4A";
        description.push('- Дата зарплаты не может быть меньше 2000 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(salary_date) > todayPlusOneYear) {
        sal_date.style.borderRight = "solid #FB3F4A";
        description.push('- Дата зарплаты не может быть больше текущей даты + 1 год');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(employment_date) < new Date('2000-01-01')) {
        emp_date.style.borderRight = "solid #FB3F4A";
        description.push('- Дата приёма на работу не может быть меньше 2000 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(employment_date) > todayPlusOneYear) {
        emp_date.style.borderRight = "solid #FB3F4A";
        description.push('- Дата приёма на работу не может быть больше текущей даты + 1 год');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(group_date_promotion) < new Date('2000-01-01')) {
        gr_name.style.borderRight = "solid #FB3F4A";
        description.push('- Дата перевода в отдел не может быть меньше 2000 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(group_date_promotion) > todayPlusOneYear) {
        gr_name.style.borderRight = "solid #FB3F4A";
        description.push('- Дата перевода в отдел не может быть больше текущей даты + 1 год');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(labor_date) < new Date('2000-01-01')) {
        la_status.style.borderRight = "solid #FB3F4A";
        description.push('- Дата трудозатрат не может быть меньше 2000 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(labor_date)  > todayPlusOneYear) {
        la_status.style.borderRight = "solid #FB3F4A";
        description.push('- Дата трудозатрат не может быть больше текущей даты + 1 год');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(full_day_date) && full_day_date < new Date('2000-01-01')) {
        document.getElementById('user_card_hours_label').style.borderRight = "solid #FB3F4A";
        description.push('- Дата почасовой оплаты не может быть меньше 2000 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(full_day_date) && full_day_date  > todayPlusOneYear) {
        document.getElementById('user_card_hours_label').style.borderRight = "solid #FB3F4A";
        description.push('- Дата почасовой оплаты не может быть больше текущей даты + 1 год');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    if (new Date(b_day) < new Date('1950-01-01')) {
        b_d.style.borderRight = "solid #FB3F4A";
        description.push('- Дата рождения не может быть меньше 1950 года');
        isExecutingSetEmployeeCard = false;
        return createDialogWindow(status='error', description=description);
    }
    fetch('/save_employee', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'user_id': user_id,
            'last_name': last_name,
            'first_name': first_name,
            'surname': surname,
            'contractor_id': contractor_id,
            'pers_num': pers_num,
            'dept_id': group_id,
            'date_promotion': group_date_promotion,
            'position_id': position_id,
            'b_day': b_day,
            'education_id': education_id,
            'salary_sum': salary_sum,
            'salary_date': salary_date,
            'salaries_description': salaries_description,
            'employment_date': employment_date,
            'full_day_status': full_day_status,
            'empl_hours_date': full_day_date,
            'empl_labor_status': labor_status,
            'empl_labor_date': labor_date,
        })
    })
        .then(response => response.json())
        .then(data => {
            isExecutingSetEmployeeCard = false;
            if (data.status === 'success') {
                window.location.href = '/employees-list';
            } else {
                isExecutingSetEmployeeCard = false;
                return createDialogWindow(status=data.status, description=data.description);
            }
        })
        .catch(error => {
            sendErrorToServer(['save_employee', error.toString()]);
            console.error('Error:', error);
        });
}

function convertDate(empDate, dec=".") {
    var sep = dec=="."?"-":".";
    var dateParts = empDate.split(dec);
    dateParts = `${dateParts[2]}${sep}${dateParts[1]}${sep}${dateParts[0]}`;
    return dateParts;
}

function convertOnfocusDate(empDate, direction=false) {
    if (direction == 'focusin' && empDate.type == 'date') {
        return
    }
    if (!empDate.value) {
        empDate.type = empDate.type == 'text'? 'date':'text';
        return
    }
    if (empDate.type == 'text') {
        tmp_value = convertDate(empDate.value);
        empDate.value = tmp_value;
        empDate.type = 'date';
    }
    else {
        tmp_value = convertDate(empDate.value, "-");
        empDate.type = 'text';
        empDate.value = tmp_value;
    }
}

function isEditDatePromotion(empDate) {
    if (empDate.type == 'text') {
        empDate.style.setProperty('min-width', '85px','important');
        document.getElementById("user_card_dept_select_label").style.setProperty('min-width', '200px','important');
    }
    else {
        empDate.style.setProperty('min-width', '105px','important');
        document.getElementById("user_card_dept_select_label").style.setProperty('min-width', '175px','important');
    }
}

function saveEmplChanges() {
    let verificationDialog = document.getElementById('verif_dialog_empl');
    document.getElementById('verif_dialog_empl_description').innerHTML = `Изменение карточки: ${document.getElementById('user_card_name').value}`;
    verificationDialog.showModal();
}

function userCardLaborStatus() {
    var la_status = document.getElementById('user_card_labor_status');

    var hrs = document.getElementById('user_card_hours');
    var labor_status = la_status.checked;
    if (labor_status) {
        document.getElementById('user_card_hours_div').style.display = 'flex';
    }
    else {
        document.getElementById('user_card_hours_div').style.display = 'none';
        // hrs.value = '';
        // document.getElementById('user_card_hours').checked = false;
    }
}

function changeUserCardLaborData() {
    // ФУНКЦИЯ НЕ НУЖНА - Больше не отчищаем дату почасовой оплаты при смене статуса трудозатрат
    /*В случае если сняли галку "Трудозатраты" и была галка в "Почасовой",
    то почасовая галка снимается в скрипте userCardLaborStatus,
    а значение user_card_hours_date принимаем равным user_card_labor_date*/
    // let user_card_labor_date = document.getElementById('user_card_labor_date').value;
    // let user_card_hours_date = document.getElementById('user_card_hours_date').value;
    //
    // let labor_status = document.getElementById('user_card_labor_status').checked;
    // let full_day_status = document.getElementById('user_card_hours').dataset.value;
    //
    // if (!labor_status && user_card_labor_date) {
    //     document.getElementById('user_card_hours_date').value = convertDate(user_card_labor_date, "-");
    // }
}

function userCardLaborData() {
    //Очищаем даты трудозатрат и почасовой
    document.getElementById('user_card_labor_date').value = '';
    // userCardHoursData();
}

function userCardHoursData() {
    //Очищаем даты трудозатрат и почасовой
    document.getElementById('user_card_hours_date').value = '';
}

function openModal() {
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.remove("hidden");
    overlay.classList.remove("hidden");
};

function closeModal() {
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.add("hidden");
    overlay.classList.add("hidden");
}

function editFullNameUserCard() {
    var user_card_name = document.getElementById('user_card_name');

    var user_card_last_name = document.getElementById('user_card_last_name');
    var user_card_first_name = document.getElementById('user_card_first_name');
    var user_card_surname = document.getElementById('user_card_surname');

    if (user_card_name.hidden) {
        user_card_name.hidden = false;
        user_card_name.disabled  = 1;
        user_card_last_name.hidden = true;
        user_card_first_name.hidden = true;
        user_card_surname.hidden = true;
        document.getElementById('user_card_name_label').style.setProperty('min-width', '200px','important');
    }
    else {
        user_card_name.hidden = true;
        user_card_name.disabled  = false;
        user_card_last_name.hidden = false;
        user_card_first_name.hidden = false;
        user_card_surname.hidden = false;
        document.getElementById('user_card_name_label').style.setProperty('min-width', '105px','important');
    }
}

function editFNUC_Real_Time() {
    var user_card_name = document.getElementById('user_card_name');

    var user_card_last_name = document.getElementById('user_card_last_name');
    var user_card_first_name = document.getElementById('user_card_first_name');
    var user_card_surname = document.getElementById('user_card_surname');

    user_card_name.value = user_card_last_name.value + ' ' + user_card_first_name.value + ' ' + user_card_surname.value;
}

function showSetMaternityLeave() {
    let user_id = document.querySelector("#employee-user__dialog").dataset.user_id;
    let maternityLeave_lastStatus = document.getElementById('maternity_leave_employee_i').innerText;
    let haf_type = '';
    let maternityLeave_title = '';

    if (maternityLeave_lastStatus === "ИЗ ДЕКРЕТА") {
        haf_type = 'hire';
        maternityLeave_title = 'выхода на работу ИЗ декрета'
    }
    else {
        haf_type = 'maternity_leave';
        maternityLeave_title = 'выхода В декрет'
    }

    if (!user_id) {
        return createDialogWindow(status='error', description=['Сотрудник не найден']);
    }

    return createDialogWindow(status='info',
            description=['Укажите дату ' + maternityLeave_title],
            func=[['click', [setMaternityLeaveWithComment, user_id, haf_type]]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ',
                },
            ],
            text_comment = true,
            loading_windows=false,
            text_comment_type = 'date',
            );
}

function setMaternityLeaveWithComment(user_id, haf_type) {
    var text_comment = document.getElementById('dialog_window_text_comment_input').value;
    if (!text_comment) {
        return document.getElementById('dialog_window_text_comment_input').style.border = "solid #FB3F4A";
    }
    else {
        document.getElementById('dialog_window_text_comment_input').style.border = "1px solid grey";
        text_comment = convertDate(text_comment)
        let curDate = new Date();
        let curDay = curDate.getDate() + 1; //ПЛЮС 1 ДЕНЬ Т.К. В ФАЙЛЕ ДАННЫЕ ОБНОВЛЯЮТСЯ НОЧЬЮ В ПОНЕДЕЛЬНИК, А В НЕДЕЛЬНОМ ПЛАНЕ ПОИСК ПО ВТОРНИКАМ. СОЗДАЕМ ДАТУ ВТОРНИКА
        let curMohth = curDate.getMonth();
        let currentYear = curDate.getFullYear();
        let newDate = new Date(currentYear, curMohth, curDay);

        removeLogInfo();
        setMaternityLeave(user_id=user_id, text_comment=text_comment, haf_type=haf_type);
    }
}

function setMaternityLeave(user_id=false, text_comment=false, haf_type=false) {
    if (text_comment == false) {
        return createDialogWindow(status='error', description=['Ошибка удаления', 'Не определена дата увольнения']);
    }
    else if (user_id == false) {
        return createDialogWindow(status='error', description=['Ошибка удаления', 'Не определен сотрудник']);
    }
    else if (haf_type == false) {
        return createDialogWindow(status='error', description=['Ошибка удаления', 'Не определен статус декрета']);
    }
    else {
        removeLogInfo();
         //Записываем данные в БД
        fetch('/maternity_leave', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'employee_id': user_id,
                'ml_date': text_comment,
                'haf_type': haf_type,
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    return window.location.href = '/employees-list';
                }
                else {
                    let description = data.description;
                    return createDialogWindow(status='error', description=description);
                }
            })
        return;
    }
}

function replaceAllDateForNewEmployee(button) {
    let user_card_pers_num = document.getElementById('user_card_pers_num').dataset.value;

    // Если найден табельный номер, значит пользователь не новый, подстановка дат не нужна
    if (user_card_pers_num !== 'null') {
        return false;
    }

    let user_card_date_promotion = document.getElementById('user_card_date_promotion');
    let user_card_date_promotion_value = user_card_date_promotion.value;
    let user_card_salary_date = document.getElementById('user_card_salary_date');
    let user_card_salary_date_value = user_card_salary_date.value;
    let user_card_employment_date = document.getElementById('user_card_employment_date');
    let user_card_employment_date_value = user_card_employment_date.value;
    let user_card_labor_date = document.getElementById('user_card_labor_date');
    let user_card_labor_date_value = user_card_labor_date.value;

    let cur_cell_id = button.id;
    let cur_cell_value = convertDate(button.value, dec="-");

    if (!user_card_date_promotion_value) {
        user_card_date_promotion.value = cur_cell_value;
    }
    if (!user_card_salary_date_value) {
        user_card_salary_date.value = cur_cell_value;
    }
    if (!user_card_employment_date_value) {
        user_card_employment_date.value = cur_cell_value;
    }
    if (!user_card_labor_date_value) {
        user_card_labor_date.value = cur_cell_value;
    }
}