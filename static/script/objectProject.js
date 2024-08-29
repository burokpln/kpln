document.addEventListener("DOMContentLoaded", function () {
    if (document.URL.split('/').length - document.URL.split('/').indexOf("objects") == 2 && document.getElementById("div_full_screen_image_obj")) {
        document.querySelector("header").style.display = "none";
        document.querySelector("footer").style.display = "none";
    }
});

window.addEventListener("load", function () {
    if (document.URL.split('/').length - document.URL.split('/').indexOf("objects") == 2 && document.getElementById("div_full_screen_image_obj")) {
        setTimeout(function () {
            showObjectScreensaver();
        }, 1700);
    }
});

$(document).ready(function() {
    if (document.URL.split('/tow').length > 1) {
        document.getElementById("mergeTowRowButton")? document.getElementById("mergeTowRowButton").style.display = "none":'';
        //Для рук
        if (document.getElementById("towTable").dataset.tep_info == '1') {
            let tab_tr0 = document.getElementById("towTable").getElementsByTagName('tbody')[0];
            if (tab_tr0) {
                for (let row of tab_tr0.rows) {
                    row.addEventListener('click', function() { mergeTowRow(this);});
                }
            }
            document.getElementById("mergeTowRowButton")? document.getElementById("mergeTowRowButton").style.display = "none":'';
            document.getElementById('mergeTowRowButton')? document.getElementById('mergeTowRowButton').addEventListener('click', function() {showSaveMergeTowRowDialogWindow()}):'';
        }

        let tow_cost = document.getElementsByClassName('tow_cost');
        for (let i of tow_cost) {
            i.addEventListener('focusin', function() {convertProjectTowCost(this, 'in');});
            i.addEventListener('focusout', function() {convertProjectTowCost(this, 'out');});
            i.addEventListener('change', function() {checkParentOrChildProjectCost(this);})
        }
    }
    //Главная страница проекта
    if (document.URL.split('/').length - document.URL.split('/').indexOf("objects") == 2) {
        document.getElementById("div_full_screen_image_obj")
            ? document
                .getElementById("div_full_screen_image_obj")
                .addEventListener("click", function () {
                    showObjectScreensaver();
                })
            : "";
        document.getElementById('save_btn')? document.getElementById('save_btn').addEventListener('click', function() {showSaveProjectCardDialogWindow();}):'';

        document.getElementById('edit_btn')? document.getElementById('edit_btn').addEventListener('click', function() {editObjectProject();}):'';
        document.getElementById('cancel_btn')? document.getElementById('cancel_btn').addEventListener('click', function() {editObjectProject();}):'';
    }
});

function showSaveProjectCardDialogWindow() {
    //Функция вызвана не с главной страницы проекта - отмена
    if (document.URL.split('/').length - document.URL.split('/').indexOf("objects") != 2) {
        return console.error('wrong way');
    }
    return createDialogWindow(status='info',
            description=['Подтвердите сохранение изменений'],
            func=[['click', [saveProjectCard, '']]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ',
                },
            ],
            );
}

function saveProjectCard() {
    link_name = document.URL.split('/objects/')[1].split('/')[0];

    let customer = document.getElementById('customer').value;
    let project_full_name = document.getElementById('project_full_name').value;
    let project_address = document.getElementById('project_address').value;
    let gip_id = $('#gip_name').val();
    let project_total_area = document.getElementById('project_total_area').value;

    console.log('  saveProjectCard', link_name)
    fetch(`/save_project/${link_name}`, {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
                'customer': customer,
                'project_full_name': project_full_name,
                'project_address': project_address,
                'gip_id': gip_id,
                'project_total_area': project_total_area,
            })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                return window.location.href = `/objects/${data.link}`;
            }
            else {
                let description = data.description;
                description.unshift('Ошибка');
                return createDialogWindow(status='error2', description=description);
            }
        })
}

function showObjectScreensaver() {
  document.querySelector("header").style.display = "flex";
  document.querySelector("footer").style.display = "block";
  document.getElementById("div_full_screen_image_obj").hidden = true;
}

// Режим редактирования карточки договора
function editObjectProject() {
    if (document.URL.split('/tow').length > 1) {
        return;
    }
    let edit_btn = document.getElementById("edit_btn");
    let save_btn = document.getElementById("save_btn");
    let cancel_btn = document.getElementById("cancel_btn");

    let customer = document.getElementById('customer');
    let project_full_name = document.getElementById('project_full_name');
    let project_address = document.getElementById('project_address');
    let gip_name = $('#gip_name');
    let project_total_area = document.getElementById('project_total_area');

    //Если режим уже включен, то отключаем его
    if (edit_btn.hidden) {

        edit_btn.hidden = 0;
        save_btn.hidden = true;
        cancel_btn.hidden = true;

        customer.readOnly = true;
        project_full_name.readOnly = true;
        project_address.readOnly = true;
        gip_name.prop("disabled", true);
        project_total_area.readOnly = true;

        window.location.href = document.URL;

        return;
    }

    edit_btn.hidden = true;
    save_btn.hidden = 0;
    cancel_btn.hidden = 0;

    customer.readOnly = false;
    project_full_name.readOnly = false;
    project_address.readOnly = false;
    gip_name.prop("disabled", false);
    project_total_area.readOnly = false;
    return;

}

function isEditProject() {
    var edit_btn = document.getElementById("edit_btn");
    if (!edit_btn.hidden) {
        editObjectProject();
    }
}

// focus in/out и изменение стоимости договора/акта/платежа
function convertProjectTowCost(val, status, percent=false) {
    isEditProject();
    var cost = val.value;
    if (!cost) {
        return;
    }
    //Тип единицы измерения редактируемого значения (рубли или проценты)
    value_type = ' ₽';
    if (status == 'in') {
        var cost_value =  rubToFloat(val.value);

        return val.value = cost_value;
    }
    else if (status == 'out') {
        var cost_value = parseFloat(cost);
        if (isNaN(cost_value)) {
            cost_value = 0;
        }
        cost_value = cost_value.toFixed(2) * 1.00;
        cost_value = cost_value.toLocaleString();
        cost_value += value_type;

        return val.value = cost_value;
    }
    else if (status == 'change') {
        let cost_value = parseFloat(cost.replace(",", "."));
        if (isNaN(cost_value)) {
            cost_value = 0;
        }

        //Информация об НДС
        let vat = 1;
        // Обновляем значение распределенных средств
        let undistributed = document.getElementById('id_div_milestones_getContractsList');
        //var undistributed_cost = undistributed.dataset.undistributed_cost;
        //var undistributed_cost_float = parseFloat(undistributed_cost);
        let last_contract_cost = undistributed.dataset.contract_cost;
        let last_contract_cost_float = parseFloat(last_contract_cost);
        last_contract_cost_float = (last_contract_cost * 1.00).toFixed(2) * 1.00;

        //undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;
        last_contract_cost_float = isNaN(last_contract_cost_float)? 0:last_contract_cost_float;
        last_contract_cost_float = (cost_value * 1) - last_contract_cost_float;
        last_contract_cost_float = last_contract_cost_float.toFixed(2) * 1.00
        //undistributed_cost =  (cost_value * 1) - last_contract_cost_float + undistributed_cost_float;
        //var undistributed_cost_tc = undistributed_cost;
        let last_contract_cost_float_tc = last_contract_cost_float;

        if (last_contract_cost_float_tc) {
            last_contract_cost_float_tc = last_contract_cost_float_tc.toLocaleString() + value_type;
        }
        else {
            last_contract_cost_float_tc = '0' + value_type
        }
        undistributed.textContent = last_contract_cost_float_tc;
        undistributed.dataset.contract_cost = last_contract_cost_float;

        return;
    }
}

// Пересчёт стоимостей родителей и детей
function checkParentOrChildProjectCost(cell, input_cost=false, subtraction=false, contract_cost_change=false,
lst_con_cost=0, children_parent=false) {
    console.log('   checkParentOrChildProjectCost')
    let tow = cell.closest('tr');
    let cur_tow = tow;
    let tow_lvl = parseInt(tow.className.split('lvl-')[1]);
    let parent_lvl = tow_lvl;
    let child_lvl = tow_lvl;
    let cur_tow_lvl = tow_lvl;

    // Если значение удалено, то добавляем в нераспределенное
    if (!cell.value) {
        return undistributedProjectTowCost(tow, input_cost=false, subtraction=true, children_parent=true);
    }

    // Удаляем суммы у всех родителей
    while (tow) {
        tow = tow.previousElementSibling;
        if (!tow || cur_tow_lvl < 1) {
            break;
        }

        parent_lvl = parseInt(tow.className.split('lvl-')[1]);

        // Убираем значения у всех родителей
        if (cur_tow_lvl > parent_lvl) {
            // Обновляем сумму детей
            let parent_data_cost = tow.getElementsByClassName('tow_cost')[0].dataset.value;
            if (!parent_data_cost) {
                cur_tow_lvl --;
                continue;
            }

            //Убираем значение ячейки и вызываем функцию пересчёта нераспр. остатка
            tow.getElementsByClassName('tow_cost')[0].value = '';
            undistributedProjectTowCost(tow, input_cost=false, subtraction=true, children_parent=true);

            cur_tow_lvl --;
            if (cur_tow_lvl < 1) {
                break;
            }
        }
    }
    // Удаляем стоимости всех детей
    if (cur_tow.nextElementSibling) {
        child = cur_tow.nextElementSibling;
        child_lvl = parseInt(child.className.split('lvl-')[1]);

        //Определяем, что следующая строка - ребенок: lvl ребенка на 1 больше родителя
        while (child && child_lvl > tow_lvl) {
            //Убираем значение ячейке и вызываем функцию пересчёта нераспр. остатка
            child.getElementsByClassName('tow_cost')[0].value = '';
            undistributedProjectTowCost(child, input_cost=false, subtraction=true, children_parent=true);

            child = child.nextElementSibling;
            if (!child) {
                break;
            }
            child_lvl = parseInt(child.className.split('lvl-')[1]);
        }
    }

    undistributedProjectTowCost(cell, input_cost=input_cost, subtraction=false,
                          contract_cost_change=contract_cost_change, lst_con_cost=lst_con_cost);

}

function undistributedProjectTowCost(cell, input_cost=false, subtraction=false, contract_cost_change=false,
lst_con_cost=0, children_parent=false) {

    let tow = cell.closest('tr');
    var tow_name = cell.closest('tr').querySelectorAll(".input_tow_name")[0].value;

    isEditProject();

    var undistributed = document.getElementById('id_div_milestones_contractCost');
    var last_contract_cost = undistributed.dataset.contract_cost;
    last_contract_cost = parseFloat(last_contract_cost);

    //Сумма договора, если не указали вручную при вызове функции
    if (input_cost === false) {
        var contract_cost = last_contract_cost;
    }
    else {
        var contract_cost = input_cost;
    }

    if (!subtraction) {
        var tow_cost = 0; //Сумма tow

        //Тип единицы измерения редактируемого значения (рубли или проценты)
        value_type = '₽';

        //Текущее и прошлое значение ячейки(нужно для пересчета нераспределенной суммы)
        var cost1 = cell.value;
        var cost1_float = rubToFloat(cost1, value_type);
        var cost2 = cell.dataset.value;
        var cost2_float = parseFloat(cost2);

        var tow_cost_protect = cell.dataset.tow_cost_protect;

        tow_cost_protect = tow_cost_protect? parseFloat(tow_cost_protect): tow_cost_protect;

        cost1_float = isNaN(cost1_float)? 0:cost1_float;
        cost2_float = isNaN(cost2_float)? 0:cost2_float;

        // Если стоимость tow меньше минимальной возможной (когда к tow привязан акт или платёж)
        if (tow_cost_protect &&tow_cost_protect > cost1_float) {
            //возвращаем прошлое значение из дата атрибута в value
            cost2_float = cost2_float? cost2_float:0;
            cell.value = cost2_float;

            tow_cost_protect = tow_cost_protect.toFixed(2) * 1.00;
            tow_cost_protect = tow_cost_protect.toLocaleString() + ` ${value_type}`;

            let description = [
                    'Ошибка rev-1.1',
                    tow_name,
                    'К виду работ привязано ЧТО-ТО, ЧТО ЗАВИСИТ РАСПРЕДЕЛЕНИЯ ГИПА (распр.рукОтдела)',
                    'Минимальная стоимость вида работ не может быть меньше: ' + tow_cost_protect
                ];

            return createDialogWindow(status='error', description=description);
        }

        tow_cost = cost1_float;

        //Обновляем данные в редактируемой ячейки
        cell.dataset.value = cost1_float;
        cell.value = cost1_float;

        //Выбираем чекбокс привязывающий tow к учёту часов
        cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0].checked = true;
        //        selectContractTow(cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0]);

        // Пересчёт суммы стоимости детей и % от суммы родителя
        recalcChildrenSum2(cell.closest('tr'), cost1_float - cost2_float);

        //Обновляем значение распределенной суммы
        last_contract_cost = last_contract_cost + cost1_float - cost2_float
        undistributed.dataset.contract_cost = last_contract_cost
        recalculateContractCost(last_contract_cost);


        //Добавляем распределенную сумму
        reservesChanges[tow.id] = cost1_float;
    }
    else {
        cell = tow.getElementsByClassName('tow_cost')[0];

        //Сумма tow
        var value_cost2 = cell.dataset.value;
        var value_cost2_float = parseFloat(value_cost2);
        value_cost2_float = isNaN(value_cost2_float)? 0:value_cost2_float;

        cell.dataset.value = '';
        cell.value = '';

        // Пересчёт суммы стоимости детей и % от суммы родителя
        recalcChildrenSum2(tow, - value_cost2_float);

        //Обновляем значение распределенной суммы
        last_contract_cost = last_contract_cost - value_cost2_float
        undistributed.dataset.contract_cost = last_contract_cost
        recalculateContractCost(last_contract_cost);

        //Добавляем распределенную сумму
        reservesChanges[tow.id] = '';

    }
}

function recalcChildrenSum2(cell, tow_sum) {
    var tow = cell.closest('tr');
    let tow_lvl = parseInt(tow.className.split('lvl-')[1]);
    let cur_tow_lvl = tow_lvl;
    let parent_tow = null;
    let parent_sum = 0;
    let same_lvl = false; // Проверка, что предыдущих родителя имеют разные лвл, иначе ∑ ВЛОЖ.
                          //посчитается и не у родителя, когда лвл не друг за другом идут 1 => 3

    // Пересчёт суммы детей родителя
    while (tow) {
        tow = tow.previousElementSibling;
        if (!tow || cur_tow_lvl < 1) {
            break;
        }
        same_lvl = tow_lvl == parseInt(tow.className.split('lvl-')[1]);

        tow_lvl = parseInt(tow.className.split('lvl-')[1]);

        // Пересчёт суммы детей родителя
        if (cur_tow_lvl > tow_lvl && !same_lvl) {
            // Обновляем сумму детей
            let parent_data_cost = tow.getElementsByClassName('tow_child_cost')[0].dataset.value;
            if (!parent_data_cost) {
                continue;
            }

            parent_data_cost = parent_data_cost!='None'? parseFloat(parent_data_cost):0;

            let new_child_cost = parent_data_cost + tow_sum;
            tow.getElementsByClassName('tow_child_cost')[0].dataset.value = new_child_cost;
            tow.getElementsByClassName('tow_child_cost')[0].value = (new_child_cost.toFixed(2) * 1.00).toLocaleString() + ' ₽';

            // Запоминаем первого родителя
            if (!parent_tow) {
                parent_tow = tow;
                parent_sum = new_child_cost.toFixed(2) * 1.00;
            }

            cur_tow_lvl --;
            if (cur_tow_lvl < 1) {
                break;
            }
        }
    }
    // Пересчёт процентов детей от родительской суммы
    if (parent_tow) {
        tow = parent_tow;
        if (!parent_tow.nextElementSibling) {
            return;
        }
        tow_lvl = parseInt(parent_tow.nextElementSibling.className.split('lvl-')[1]);
        while (tow) {
            tow = tow.nextElementSibling;
            if (!tow || parseInt(tow.className.split('lvl-')[1]) != tow_lvl) {
                break;
            }
            let child_cost = tow.getElementsByClassName('tow_cost')[0].dataset.value;
            if (!child_cost) {
                tow.getElementsByClassName('tow_parent_percent_cost')[0].value = '';
                tow.getElementsByClassName('tow_parent_percent_cost')[0].dataset.value = 0;
                continue;
            }
            child_cost = parseFloat(child_cost)
            let child_data_percent = ((child_cost / parent_sum * 100).toFixed(2) * 1.00);
            tow.getElementsByClassName('tow_parent_percent_cost')[0].dataset.value = child_data_percent;
            if (!child_data_percent) {
                tow.getElementsByClassName('tow_parent_percent_cost')[0].value = '';
            }
            else {
                tow.getElementsByClassName('tow_parent_percent_cost')[0].value = child_data_percent + ' %';
            }
        }
    }
}

// Анимация пересчёта распределенных средств
function recalculateContractCost(originalValue) {
    console.log('originalValue', originalValue)
    let element = document.getElementById('id_div_milestones_contractCost');
    let lenOriginalValue = 0;

    if (!isNaN(parseInt(originalValue))) {
        lenOriginalValue =  parseInt(originalValue).toString().length;
        originalValue =  originalValue.toFixed(2) * 1.00;
        originalValue =  originalValue.toLocaleString() + ' ₽';
    }
    else {
        lenOriginalValue =  rubToFloat(originalValue).toString().length;
    }

    const duration = 150; // 0.2 seconds
    const interval = 50; // Update every 5ms
    let elapsed = 0;

    const randomize = () => {
        const randomValue = `${Math.floor(Math.random() * (10**lenOriginalValue))} ₽`;
        element.textContent = `РАСП.: ${randomValue}`;
    };

    const intervalId = setInterval(() => {
        if (elapsed >= duration) {
            clearInterval(intervalId);
            element.textContent = `РАСП.: ${originalValue}`;
        } else {
            randomize();
            elapsed += interval;
        }
    }, interval);
}
