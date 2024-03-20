$(document).ready(function() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    const tableR = document.querySelector('.tableEmp');

    var tableR2 = document.getElementById('employeeTable');

    var table_max_length = 175

    if(tableR) {
        if ($(this).innerHeight() > tableR2.offsetHeight) {
            var sortCol_1 = document.getElementById('sortCol-1').textContent;

            var isExecuting = false;
            employeeList(sortCol_1);

        }
    }

    tableR.addEventListener('scroll', function() {
        var sortCol_1 = document.getElementById('sortCol-1').textContent;
        var scrollPosition = $(this).scrollTop()

        // Скроллим вверх
        if (!scrollPosition && sortCol_1) {
            var tab = document.getElementById("employeeTable");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            if (tab_numRow.length >= table_max_length) {
                for (var i = tab_numRow.length; i>table_max_length; i--) {
                    table.deleteRow(i);
                }

                    var user_id = tab_numRow[0].getElementsByTagName('td')[1].dataset.sort;
                    var create_at = tab_numRow[0].getElementsByTagName('td')[12].dataset.sort;
                    var isExecuting = false;
                    employeeList(sortCol_1=sortCol_1, direction='up', sortCol_1_val=create_at, sortCol_id_val=payment_id)

                tableR.scrollTo({
                    top: 10,
                    behavior: "smooth",
                });
            }
        }

        // Скроллим в самый низ
        if (scrollPosition + $(this).innerHeight() >= $(this)[0].scrollHeight && sortCol_1) {
            document.getElementById('sortCol-1').textContent = '';

            const tab = document.getElementById("employeeTable");
            var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            var isExecuting = false;
            employeeList(sortCol_1);
            
            if(tableR) {
                //  возвращает координаты в контексте окна для минимального по размеру прямоугольника tableR
                const rect = tableR.getBoundingClientRect();
            }
            if (tab_numRow.length > table_max_length) {
                for (var i = 1; i<=tab_numRow.length-table_max_length;) {
                    table.deleteRow(1);
                }
            }
            return;
        }
    });
});

function progressBarCalc(direction, numRow, tab_rows, rowCount){
    const progressBar = document.querySelector('.progress');
    const progressBar2 = document.querySelector('.progress2');

    progress_val1 = direction === 'down'? ((numRow / tab_rows)*100).toFixed(2) + '%': ((numRow+rowCount-1)/tab_rows*100).toFixed(2) + '%';

    progress_val2 = direction === 'down'? ((numRow-rowCount)/tab_rows*100).toFixed(2) + '%': ((numRow-1)/tab_rows*100).toFixed(2) + '%';

    progressBar.style.width = progress_val1;
    progressBar2.style.width = progress_val2;
}

function prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val){
    //Значение параметров сортировки
    sortCol_1_val = !sortCol_1_val? document.getElementById('sortCol-1_val').textContent: sortCol_1_val;
    sortCol_id_val = !sortCol_id_val? document.getElementById('sortCol-id_val').textContent: sortCol_id_val;

    if (direction === 'up') {
        sortCol_1 = sortCol_1.split('#')[0] + '#' + (sortCol_1.split('#')[1]=='1'? 0: 1);
    }

    var filter_input = document.querySelectorAll('[id*="filter-input-"]');
    var filterValsList = []; // Значения фильтров

    for (var i=0; i<filter_input.length; i++) {
        if (filter_input[i].value) {
            filterValsList.push([i, filter_input[i].value]);
        }
    }

    return([sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList]);
}

var limit = 25
var isExecuting = false;

function employeeList(sortCol_1, direction='down', sortCol_1_val=false, sortCol_id_val=false) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return
    }
    isExecuting = true;

    [sortCol_1, sortCol_1_val, sortCol_id_val, filterValsList] = prepareDataFetch(direction, sortCol_1, sortCol_1_val, sortCol_id_val);

    // Получили пустые данные - загрузили всю таблицу - ничего не делаем
    if (!sortCol_1) {
        isExecuting = false;
        return
    }
    else {

        fetch('/get-employee-pagination', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'limit': limit,
                'sort_col_1': sortCol_1,
                'sort_col_1_val': sortCol_1_val,
                'sort_col_id_val': sortCol_id_val,
                'filterValsList': filterValsList,
            })
        })
            .then(response => response.json())
            .then(data => {
                isExecuting = false;
                if (data.status === 'success') {
                    if (!data.employee) {
                        if (direction === 'up') {
                            if (data.sort_col['col_1'][0]) {
                                data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            }
                        }
                        else {
                            data.sort_col['col_1'][0]? document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]: 0;
                            data.sort_col['col_1'][1]? document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]: 0;
                            data.sort_col['col_id']? document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']: 0;
                        }
                        return;
                    }
                    if (direction === 'up') {
                        if (data.sort_col['col_1'][0]) {
                            data.sort_col['col_1'][0] = data.sort_col['col_1'][0].split('#')[0] + '#' + (data.sort_col['col_1'][0].split('#')[1]=='1'? 0: 1);
                            document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        }
                    }
                    else {
                        document.getElementById('sortCol-1').textContent = data.sort_col['col_1'][0]
                        document.getElementById('sortCol-1_val').textContent = data.sort_col['col_1'][1]
                        document.getElementById('sortCol-id_val').textContent = data.sort_col['col_id']
                    }

                    const tab = document.getElementById("employeeTable");
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                    // Определяем номер строки
                    if (direction === 'down') {
                        try {
                            var numRow = tab_numRow[tab_numRow.length-1].id;
                            numRow = parseInt(numRow.split('row-')[1]);
                        }
                        catch {
                            numRow = 0;
                        }

                    }
                    else {
                        var numRow = tab_numRow[0].id;
                        numRow = parseInt(numRow.split('row-')[1]);
                    }

                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];

                    for (emp of data.employee) {

                        direction === 'down'? numRow++: numRow-- ;

                        // Вставляем ниже новую ячейку, копируя предыдущую
                        var table2 = document.getElementById("employeeTable");
                        var rowCount = table2.rows.length;

                        var row = direction === 'down'? tab_tr0.insertRow(tab_numRow.length): tab_tr0.insertRow(0);

                        //////////////////////////////////////////
                        // Меняем данные в ячейке
                        //////////////////////////////////////////
                        // id
                        row.id = `row-${numRow}`;
                        row.className = "employee_tab_row";
                        row.setAttribute("data-user_id", emp['user_id']);

                        //**************************************************
                        // Если сотрудник не создан
                        if (!emp['pers_num']) {

                            var contractor_name = row.insertCell(0);
                            contractor_name.className = "th_description_i";
                            contractor_name.innerHTML = 'id_' + emp['user_id'];

                            var pers_num = row.insertCell(1);
                            pers_num.className = "th_description_i";
                            pers_num.innerHTML = "-";

                            var empl_name = row.insertCell(2);
                            empl_name.className = "th_description_i";
                            empl_name.innerHTML = emp['name'];

                                var add_empl = row.insertCell(3);
                                add_empl.className = "th_description_i";
                                add_empl.colSpan = 14;

                                    var buttonAddEmpl = document.createElement("button");
                                    buttonAddEmpl.className = "button_add_employee";
                                    buttonAddEmpl.setAttribute("onclick", "getEmployeeCard(this)");
                                    buttonAddEmpl.innerHTML = "+ Создать сотрудника"

                                add_empl.appendChild(buttonAddEmpl);

                        }
                        else {
                            //**************************************************
                            // КОМПАНИЯ
                            var contractor_name = row.insertCell(0);
                            contractor_name.className = "th_description_i";
                            contractor_name.innerHTML = emp['contractor_name'];
                            //**************************************************
                            // ТАБ №
                            var pers_num = row.insertCell(1);
                            pers_num.className = "th_description_i";
                            pers_num.innerHTML = emp['pers_num'];
                            //**************************************************
                            // ФИО СОТРУДНИКА
                            var empl_name = row.insertCell(2);
                            empl_name.className = "th_description_i";
                            empl_name.innerHTML = emp['name'];
                            empl_name.setAttribute("onclick", 'getEmployeeCard(this)');
                            //**************************************************
                            // ОТДЕЛ
                            var dept_name = row.insertCell(3);
                            dept_name.className = "th_description_i";
                            dept_name.innerHTML = emp['dept_name'];
                            //**************************************************
                            // ГРУППА
                            var group_short_name = row.insertCell(4);
                            group_short_name.className = "th_description_i";
                            group_short_name.innerHTML = emp['group_short_name'];
                            //**************************************************
                            // ДОЛЖНОСТЬ
                            var position_name = row.insertCell(5);
                            position_name.className = "th_description_i";
                            position_name.innerHTML = emp['position_name'];
                            //**************************************************
                            // ДАТА РОЖДЕНИЯ
                            var b_day = row.insertCell(6);
                            b_day.className = "th_description_i";
                            b_day.innerHTML = emp['b_day_txt'];
                            //**************************************************
                            // ОБРАЗОВАНИЕ
                            var education_name = row.insertCell(7);
                            education_name.className = "th_description_i";
                            education_name.innerHTML = emp['education_name'];
                            //**************************************************
                            // ТЕКУЩАЯ ЗАРПЛАТА
                            var salary_sum = row.insertCell(8);
                            salary_sum.className = "th_description_i";
                            salary_sum.innerHTML = emp['salary_sum_rub'];
                            //**************************************************
                            // ДАТА изменения ЗП
                            var salary_date = row.insertCell(9);
                            salary_date.className = "th_description_i";
                            salary_date.innerHTML = emp['salary_date_txt'];
                            //**************************************************
                            // СТАТУС 3
                            var status3 = row.insertCell(10);
                            status3.className = "th_description_i";
                            status3.innerHTML = emp['status3'];
                            //**************************************************
                            // ДАТА ПРИЁМА
                            var employment_date = row.insertCell(11);
                            employment_date.className = "th_description_i";
                            employment_date.innerHTML = emp['employment_date_txt'];
                            //**************************************************
                            // ДАТА УВОЛЬНЕНИЯ
                            var date_of_dismissal = row.insertCell(12);
                            date_of_dismissal.className = "th_description_i";
                            date_of_dismissal.innerHTML = emp['date_of_dismissal_txt'];
                            //**************************************************
                            // РАБОЧИХ ДНЕЙ
                            var work_days = row.insertCell(13);
                            work_days.className = "th_description_i";
                            work_days.innerHTML = emp['work_days'];
                            //**************************************************
                            // НОРМА ДНЯ
                            var hours = row.insertCell(14);
                            hours.className = "th_description_i";
                            hours.innerHTML = emp['hours'];
                            //**************************************************
                            // ТРУДОЗАТРАТЫ
                            var labor_status = row.insertCell(15);
                            var checkboxLabor_status = document.createElement('input');
                            checkboxLabor_status.type = "checkbox";
                            if (emp['labor_status']) {
                                checkboxLabor_status.checked = true;
                            }
                            checkboxLabor_status.disabled  = 1;
                            labor_status.appendChild(checkboxLabor_status);
                            //**************************************************
                            // ПОЛНЫХ ЛЕТ
                            var full_years = row.insertCell(16);
                            full_years.className = "th_description_i";
                            full_years.innerHTML = emp['full_years'];
                        }

                        // Прогресс бар
                        progressBarCalc(direction, numRow, data.tab_rows, rowCount);

                    }
                    return
                }
                else if (data.status === 'error') {
                    alert(data.description)
                }
                else {
                    window.location.href = '/employees_list';
                }
        })
        .catch(error => {
        console.error('Error:', error);
    });
    }
};
