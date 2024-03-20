function AddEmployee(button) {
    var row = button.closest('tr');
    var employeeId = row.dataset.user_id
    console.log(row);
    console.log(row.dataset);
    console.log(employeeId);
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

            console.log(data.employee)

            dialog.setAttribute("data-user_id", data.employee['user_id']);
            document.getElementById('user_card_name').value = data.employee['name'];
            document.getElementById('user_card_last_name').value = data.employee['last_name'];
            document.getElementById('user_card_first_name').value = data.employee['first_name'];
            document.getElementById('user_card_surname').value = data.employee['surname'];
            $('#user_card_contractor_select').val(data.employee['contractor_id']? data.employee['contractor_id'].toString():null).trigger('change');
            document.getElementById('user_card_pers_num').value = data.employee['pers_num'];
            $('#user_card_dept_select').val(data.employee['group_id']? data.employee['group_id'].toString():null).trigger('change');
            $('#user_card_position_name_select').val(data.employee['position_id']? data.employee['position_id'].toString():null).trigger('change');
            document.getElementById('user_card_b_day').value = data.employee['b_day_txt'];
            $('#user_card_education_name_select').val(data.employee['education_id']? data.employee['education_id'].toString():null).trigger('change');
            document.getElementById('user_card_salary_sum').value = data.employee['salary_sum_rub'];
            document.getElementById('user_card_salary_date').value = data.employee['salary_date_txt'];
            document.getElementById('user_card_employment_date').value = data.employee['employment_date_txt'];
            document.getElementById('user_card_hours').value = data.employee['hours'];
            document.getElementById('user_card_labor_status').checked = data.employee['labor_status'];

            var logDPage = document.getElementById('user_card_salary_log');
            logDPage.innerHTML = ''
            for (var i = 0; i < data.salaries_list.length; i++) {
                const entry = document.createElement("p");
                entry.innerHTML = `
                    -- <span class="logTime"><span class="logTimeBold">${data.salaries_list[i][0]}:</span> ${data.salaries_list[i][1]}</span>
                    ${data.salaries_list[i][3]}.
                    <span class="logCash"><span class="logCashPay">(${data.salaries_list[i][2]})</span> </span>
                `;
                logDPage.appendChild(entry);
            }

            // Открытие карточки сотрудника
            openModal();
            // Скрытие/отображение строки с кол-вом нормы дня
            userCardLaborStatus();

        })
        .catch(error => {
            console.error('Error:', error);
        });
};

function setEmployeeCard() {
    const verificationDialog = document.getElementById('verif_dialog_empl');
    verificationDialog.close();

    var user_id = document.getElementById('employee-user__dialog').dataset.user_id;

    var last_name = document.getElementById('user_card_last_name').value;
    var first_name = document.getElementById('user_card_first_name').value;
    var surname = document.getElementById('user_card_surname').value;
    var contractor_id = document.getElementById('user_card_contractor_select').value;
    var pers_num = document.getElementById('user_card_pers_num').value;
    var group_id = document.getElementById('user_card_dept_select').value;
    var position_id = document.getElementById('user_card_position_name_select').value;
    var b_day = document.getElementById('user_card_b_day').value;
    var education_id = document.getElementById('user_card_education_name_select').value;
    var salary_sum = document.getElementById('user_card_salary_sum').value;
    var salary_date = document.getElementById('user_card_salary_date').value;
    var employment_date = document.getElementById('user_card_employment_date').value;
    var labor_status = document.getElementById('user_card_labor_status').checked;
    var hours = labor_status? 8:document.getElementById('user_card_hours').value;

    var la_name = document.getElementById('user_card_name_label');
    var fi_name = document.getElementById('user_card_name_label');
    var co_name = document.getElementById('user_card_contractor_label');
    var pe_num = document.getElementById('user_card_pers_num_label');
    var gr_name = document.getElementById('user_card_dept_select_label');
    var po_name = document.getElementById('user_card_position_name_select_label');
    var b_d = document.getElementById('user_card_b_day_label');
    var ed_name = document.getElementById('user_card_education_name_select_label');
    var sal_sum = document.getElementById('user_card_salary_sum_label');
    var sal_date = document.getElementById('user_card_salary_date_label');
    var emp_date = document.getElementById('user_card_employment_date_label');
    var la_status = document.getElementById('user_card_labor_status_label');
    var hrs = labor_status? 8:document.getElementById('user_card_hours_label');


    check_lst1 = [la_name, fi_name, co_name, pe_num, gr_name, po_name, b_d, ed_name, sal_sum, sal_date, emp_date, hrs]
    check_lst2 = [last_name, first_name, contractor_id, pers_num, group_id, position_id, b_day, education_id, salary_sum, salary_date, employment_date, hours]
    description_lst = ["Фамилия", "Имя", "Компания", "Таб. №", "Группа", "Должность", "День рождения", "Образование", "Текущая зарплата", "Дата зарплаты", "Дата приёма", "Трудозатраты"]

    var description = [];

    for (var i=0; i<check_lst2.length; i++) {
        if (!check_lst2[i]) {
            check_lst1[i].style.borderRight = "solid #FB3F4A";
            console.log(description_lst[i], check_lst2[i]);
            description.push(description_lst[i])
        }
        else {
            check_lst1[i].style.borderRight = "solid #F3F3F3";
        }
    }
    if (description && !((!labor_status && hours) || (labor_status && !hours))) {
        description.pop()
    }
    if (!user_id || !last_name || !first_name || !pers_num || !group_id || !position_id || !b_day || !education_id || !salary_sum || !salary_date || !employment_date || ((!labor_status && hours) || (labor_status && !hours))) {
        return alert(`Заполнены не все поля: ${description}`)
    }

    b_day = b_day.split("-").length == 1? convertDate(b_day):b_day;
    salary_date = salary_date.split("-").length == 1? convertDate(salary_date):salary_date;
    employment_date = employment_date.split("-").length == 1? convertDate(employment_date):employment_date;

    console.log({'user_id': user_id,
            'last_name': last_name,
            'first_name': first_name,
            'surname': surname,
            'contractor_id': contractor_id,
            'pers_num': pers_num,
            'dept_id': group_id,
            'position_id': position_id,
            'b_day': b_day,
            'education_id': education_id,
            'salary_sum': salary_sum,
            'salary_date': salary_date,
            'employment_date': employment_date,
            'hours': hours,
            'labor_status': labor_status})

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
            'position_id': position_id,
            'b_day': b_day,
            'education_id': education_id,
            'salary_sum': salary_sum,
            'salary_date': salary_date,
            'employment_date': employment_date,
            'hours': hours,
            'labor_status': labor_status
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/${page_url}`;
            } else {
                window.location.href = `/${page_url}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function convertDate(empDate, dec=".") {
    var sep = dec=="."?"-":".";
    console.log(empDate)
    var dateParts = empDate.split(dec);
    dateParts = `${dateParts[2]}${sep}${dateParts[1]}${sep}${dateParts[0]}`;
    return dateParts;
}

function convertOnfocusDate(empDate) {
    if (!empDate.value) {
        empDate.type = empDate.type == 'text'? 'date':'text';
        return
    }
    if (empDate.type == 'text') {
        tmp_value = convertDate(empDate.value)
        empDate.type = 'date';
        empDate.value = tmp_value;
    }
    else {
        tmp_value = convertDate(empDate.value, "-");
        empDate.type = 'text';
        empDate.value = tmp_value;
    }
}

function saveEmplChanges() {
    const verificationDialog = document.getElementById('verif_dialog_empl');
    document.getElementById('verif_dialog_empl_description').innerHTML = `Изменение карточки: ${document.getElementById('user_card_name').value}`
    document.getElementById('verif_dialog_empl__ok').setAttribute("onclick", 'setEmployeeCard()');
    verificationDialog.showModal();
}

function userCardLaborStatus() {
    var la_status = document.getElementById('user_card_labor_status');
    var hrs_div = document.getElementById('user_card_hours_div');
    var hrs = document.getElementById('user_card_hours');
    var labor_status = la_status.checked;
    if (labor_status) {
        document.getElementById('user_card_hours_div').style.display = 'flex';
    }
    else {
        document.getElementById('user_card_hours_div').style.display = 'none';
        hrs.value = '';
    }
}


function openModal() {
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.remove("hidden");
    overlay.classList.remove("hidden");
};


function closeModal() {
    console.log('_______')
    const modal = document.querySelector(".modal");
    const overlay = document.querySelector(".overlay");
    modal.classList.add("hidden");
    overlay.classList.add("hidden");
    console.log('_______')
};

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
    }
    else {
        user_card_name.hidden = true;
        user_card_name.disabled  = false;
        user_card_last_name.hidden = false;
        user_card_first_name.hidden = false;
        user_card_surname.hidden = false;
    }
}

function editFNUC_Real_Time() {
    var user_card_name = document.getElementById('user_card_name');

    var user_card_last_name = document.getElementById('user_card_last_name');
    var user_card_first_name = document.getElementById('user_card_first_name');
    var user_card_surname = document.getElementById('user_card_surname');

    user_card_name.value = user_card_last_name.value + ' ' + user_card_first_name.value + ' ' + user_card_surname.value;
}