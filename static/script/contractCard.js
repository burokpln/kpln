$(document).ready(function() {
    var page_url = document.URL;
    if (document.URL.split('/contract-list/card/').length > 1) {
        document.getElementById('edit_btn')? document.getElementById('edit_btn').addEventListener('click', function() {editContract();}):'';
        document.getElementById('delete_btn')? document.getElementById('delete_btn').addEventListener('click', function() {showDeleteContractDialogWindow();}):'';

    }
    if (document.URL.split('/contract-list/card/new/').length > 1) {
        isEditContract();
        showFullCardInfo();
        document.getElementById('delete_btn')? document.getElementById('delete_btn').hidden='hidden':false;
    }

    if (document.URL.split('/contract-list/card/').length > 1) {
        document.getElementById('ctr_card_full_contract_number')? document.getElementById('ctr_card_full_contract_number').addEventListener('change', function() {editContractCardData(this); isEditContract();}):'';
        let ctr_card_full_cost = document.getElementById('ctr_card_full_cost');
        if (ctr_card_full_cost) {
            ctr_card_full_cost.addEventListener('focusin', function() {convertCost(this, 'in');});
            ctr_card_full_cost.addEventListener('focusout', function() {convertCost(this, 'out');});
            ctr_card_full_cost.addEventListener('change', function() {isEditContract(); convertCost(this, 'change');});
        }
        document.getElementById('ctr_card_contract_full_vat_label')? document.getElementById('ctr_card_contract_full_vat_label').addEventListener('click', function() {changeContractVatLabel();}):'';
        document.getElementById('ctr_card_contract_full_prolongation_label')? document.getElementById('ctr_card_contract_full_prolongation_label').addEventListener('click', function() {foo2();}):'';
        let ctr_card_date_start = document.getElementById('ctr_card_date_start');
        if (ctr_card_date_start) {
            ctr_card_date_start.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
            ctr_card_date_start.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
            ctr_card_date_start.addEventListener('change', function() {isEditContract();});
        }
        let ctr_card_date_finish = document.getElementById('ctr_card_date_finish');
        if (ctr_card_date_start) {
            ctr_card_date_finish.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
            ctr_card_date_finish.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
            ctr_card_date_finish.addEventListener('change', function() {isEditContract();});
        }
        document.getElementById('id_ctr_card_attach_file')? document.getElementById('id_ctr_card_attach_file').addEventListener('click', function() {editFullNameUserCard();}):'';
        document.getElementById('id_ctr_card_add_reserve')? document.getElementById('id_ctr_card_add_reserve').addEventListener('click', function() {editFullNameUserCard();}):'';
        document.getElementById('id_ctr_hide_full_card_info_button')? document.getElementById('id_ctr_hide_full_card_info_button').addEventListener('click', function() {hideFullCardInfo();}):'';
        document.getElementById('ctr_card_contract_number')? document.getElementById('ctr_card_contract_number').addEventListener('change', function() {editContractCardData(this); isEditContract();}):'';
        let ctr_card_cost = document.getElementById('ctr_card_cost');
        if (ctr_card_cost) {
            ctr_card_cost.addEventListener('focusin', function() {convertCost(this, 'in');});
            ctr_card_cost.addEventListener('focusout', function() {convertCost(this, 'out');});
            ctr_card_cost.addEventListener('change', function() {isEditContract(); convertCost(this, 'change');});
        }
        document.getElementById('ctr_card_contract_vat_label')? document.getElementById('ctr_card_contract_vat_label').addEventListener('click', function() {changeContractVatLabel();}):'';
        document.getElementById('ctr_card_contract_prolongation_label')? document.getElementById('ctr_card_contract_prolongation_label').addEventListener('click', function() {foo2();}):'';
        document.getElementById('id_ctr_card_attach_file_button')? document.getElementById('id_ctr_card_attach_file_button').addEventListener('click', function() {showFullCardInfo();}):'';
        document.getElementById('id_ctr_card_multiselect_on')? document.getElementById('id_ctr_card_multiselect_on').addEventListener('click', function() {setMultiselectFillOn(this);}):'';
        document.getElementById('id_ctr_card_columns_settings')? document.getElementById('id_ctr_card_columns_settings').addEventListener('click', function() {hideFullCardInfo();}):'';
        document.getElementById('id_ctr_card_focus_in')? document.getElementById('id_ctr_card_focus_in').addEventListener('click', function() {hideFullCardInfo();}):'';
        $('#ctr_card_status_name')? $('#ctr_card_status_name').on('select2:select', function (e) {editContractCardData(this); isEditContract();}):'';
        $('#ctr_card_obj')? $('#ctr_card_obj').on('select2:select', function (e) {editContractCardData(this);}):'';
        $('#ctr_card_full_obj')? $('#ctr_card_full_obj').on('select2:select', function (e) {editContractCardData(this);}):'';
        $('#ctr_card_partner')? $('#ctr_card_partner').on('select2:select', function (e) {isEditContract()}):'';
        $('#ctr_card_full_status_name')? $('#ctr_card_full_status_name').on('select2:select', function (e) {editContractCardData(this); isEditContract();}):'';
        $('#ctr_card_contractor')? $('#ctr_card_contractor').on('select2:select', function (e) {isEditContract()}):'';

        document.getElementById('user_card_allow')? document.getElementById('user_card_allow').addEventListener('change', function() {isEditContract();}):'';
        document.getElementById('ctr_card_fot_value')? document.getElementById('ctr_card_fot_value').addEventListener('change', function() {isEditContract();}):'';
        document.getElementById('ctr_card_contract_description')? document.getElementById('ctr_card_contract_description').addEventListener('change', function() {isEditContract();}):'';
        document.getElementById('ctr_card_date_start')? document.getElementById('ctr_card_date_start').addEventListener('change', function() {isEditContract();}):'';
        document.getElementById('ctr_card_date_finish')? document.getElementById('ctr_card_date_finish').addEventListener('change', function() {isEditContract();}):'';
    }

    if (document.URL.split('/contract-list/').length > 1) {
        document.getElementById('add_btn')? document.getElementById('add_btn').addEventListener('click', function() {modalCreateNewContract();}):'';
        document.getElementById('user_card_crossBtnNAW')? document.getElementById('user_card_crossBtnNAW').addEventListener('click', function() {closeModal();}):'';
        document.getElementById('employeeCardWin')? document.getElementById('employeeCardWin').addEventListener('click', function() {closeModal();}):'';

        document.getElementById('create_contract_button_income_contract_frame')? document.getElementById('create_contract_button_income_contract_frame').addEventListener('click', function() {createNewContract(this);}):'';
        document.getElementById('create_contract_button_income_subcontract_frame')? document.getElementById('create_contract_button_income_subcontract_frame').addEventListener('click', function() {createNewContract(this);}):'';
        document.getElementById('create_contract_button_expenditure_contract_frame')? document.getElementById('create_contract_button_expenditure_contract_frame').addEventListener('click', function() {createNewContract(this);}):'';
        document.getElementById('create_contract_button_expenditure_subcontract_frame')? document.getElementById('create_contract_button_expenditure_subcontract_frame').addEventListener('click', function() {createNewContract(this);}):'';
    }

    if (document.getElementById('ctr_card_partner_label')) {
        document.getElementById('ctr_card_partner_label').addEventListener('click', function() {showNewPartnerDialog();});
        document.getElementById('ctr_card_partner_label').addEventListener('mouseenter', function() {this.innerText = 'ДОБАВИТЬ КОНТРАГЕНТА';});
        document.getElementById('ctr_card_partner_label').addEventListener('mouseout', function() {this.innerText = 'КОНТРАГЕНТ';});

    }

    let tow_cost = document.getElementsByClassName('tow_cost');
    for (let i of tow_cost) {
        i.addEventListener('change', function() {undistributedCost(this);})
    }
    let checkbox_time_tracking = document.getElementsByClassName('checkbox_time_tracking');
    for (let i of checkbox_time_tracking) {
        i.addEventListener('click', function() {selectContractTow(this);});
    }
    let tow_cost_percent = document.getElementsByClassName('tow_cost_percent');
    for (let i of tow_cost_percent) {
        i.addEventListener('change', function() {undistributedCost(this, percent='percent');});
    }

    let tow_date_start = document.getElementsByClassName('tow_date_start');
    for (let i of tow_date_start) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {isEditContract();});

    }

    let tow_date_finish = document.getElementsByClassName('tow_date_finish');
    for (let i of tow_date_finish) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
        i.addEventListener('change', function() {isEditContract();});
    }

    if (document.URL.split('/contract-list').length == 1) {
//        calcTowChildWithDept();
    }

    $('#ctr_card_contractor').on("select2:open", function(e) {
        ctr_card_contractor_label
        document.getElementById('ctr_card_contractor_label').dataset.value = this.options[this.selectedIndex].value;
        document.getElementById('ctr_card_contractor_label').dataset.innerText = this.options[this.selectedIndex].innerText;
        document.getElementById('ctr_card_contractor_label').dataset.vat = this.options[this.selectedIndex].getAttribute("data-vat");
    });
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        event.preventDefault();
    }
});

function dontChangeContractorInCard() {
    // Если пользователь не захотел менять заказчика, возвращаем прошлое значение
    let dValue = document.getElementById('ctr_card_contractor_label').dataset.value;
    let dInnerText = document.getElementById('ctr_card_contractor_label').dataset.innerText;
    $('#ctr_card_contractor').val(dValue).trigger('change');

}

//Обновляем значение vat при изменении компании
document.addEventListener("DOMContentLoaded", function() {
    $('#ctr_card_contractor').on('select2:select', function (e) {
        var selectedOption = this.options[this.selectedIndex];
        var dataVat = selectedOption.getAttribute("data-vat");
        document.getElementById('ctr_card_contractor').dataset.vat=dataVat;
        let vat_status = dataVat != 'True'? "С НДС":"БЕЗ НДС";
        return createDialogWindow(status='info',
            description=['Смена компании может повлиять на тип НДС договора.', 'Подтвердите изменение компании'],
            func=[['click', [changeVatInCard, vat_status]]],
                buttons=[
                    {
                        id:'flash_cancel_button',
                        innerHTML:'ОТМЕНИТЬ',
                        func:[['click', [dontChangeContractorInCard, '']]]
                    },
                ]
            );
        })
    }
);

function convertDate(empDate, dec=".") {
    var sep = dec=="."?"-":".";
    var dateParts = empDate.split(dec);
    dateParts = `${dateParts[2]}${sep}${dateParts[1]}${sep}${dateParts[0]}`;
    return dateParts;
}

function convertOnfocusDate(empDate, focusStatus='') {
    if (!empDate.value) {
        empDate.type = focusStatus == 'focusin'? 'date':'text';
    }
    else if (empDate.type == 'text' && focusStatus == 'focusin') {
        tmp_value = convertDate(empDate.value);
        empDate.value = tmp_value;
        empDate.type = 'date';
    }
    else if (empDate.type == 'date' && focusStatus == 'focusout') {
        tmp_value = convertDate(empDate.value, "-");
        empDate.type = 'text';
        empDate.value = tmp_value;
    }
}

function hideFullCardInfo() {
    var fullCardInfo = document.getElementById('ctr_full_card_div');
    var fullCardInfoButton = document.getElementById('ctr_hide_full_card_info');
    var miniCardInfo = document.getElementById('ctr_mini_card_div');
    fullCardInfoButton.style.display = "none";
    fullCardInfo.style.display = "none";
    miniCardInfo.style.display = "flex";
//    isEditContract();
}

function showFullCardInfo() {
    var fullCardInfo = document.getElementById('ctr_full_card_div');
    var fullCardInfoButton = document.getElementById('ctr_hide_full_card_info');
    var miniCardInfo = document.getElementById('ctr_mini_card_div');
    fullCardInfoButton.style.display = "flex";
      fullCardInfo.style.display = "flex";
      miniCardInfo.style.display = "none";
//    isEditContract();
}

function getContractCard(button) {
    var td_0 = button.closest('tr').getElementsByTagName("td")[0];
    var contract_id = td_0.dataset.sort;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    window.open(`/contract-list/card/${contract_id}`, '_blank');
};

function getActCard(button) {
    var td_0 = button.closest('tr').getElementsByTagName("td")[0];
    var contract_id = td_0.dataset.sort;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    window.open(`/contract-acts-list/card/${contract_id}`, '_blank');
};

var isExecuting = false;

function selectContractTow(check_box) {
    // Предыдущее выполнение функции не завершено
    if (isExecuting) {
        return;
    }
    isExecuting = true;

    isEditContract()

    if (check_box.checked) {
        //Проверяем даты вида работ
        //Даты вида работ
        var date_start = check_box.closest('tr').getElementsByClassName("tow_date_start")[0];
        var date_finish = check_box.closest('tr').getElementsByClassName("tow_date_finish")[0];
        //Даты из договора
        var contract_date_start = document.getElementById('ctr_card_date_start').value;
        var contract_date_finish = document.getElementById('ctr_card_date_finish').value;

        //Информация об НДС
        let vat = document.getElementById('ctr_card_contract_vat_label').dataset.vat;

        if (!date_start.value && contract_date_start) {
            if (!date_finish.value) {
                date_start.value = contract_date_start;
            }
            else if (date_finish.value && new Date(convertDate(date_finish.value)) > new Date(convertDate(contract_date_start))) {
                date_start.value = contract_date_start;
            }

        }
        if (!date_finish.value && contract_date_finish ) {
            if (!date_start.value) {
                date_finish.value = contract_date_finish;
            }
            else if (date_start.value && new Date(convertDate(date_start.value)) < new Date(convertDate(contract_date_finish))) {
                date_finish.value = contract_date_finish;
            }
        }

        //Если режим выбор - одиночный выбор - завершаем
        if (document.getElementsByClassName("ctr_card_multiselect_off")[0] ||!check_box.checked) {
            isExecuting = false;
            return;
        }
        //Проверяем, есть ли нераспределенные средства, если нет - завершаем
        var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
        var undistributed_cost = undistributed.dataset.undistributed_cost;
        var undistributed_cost_float = parseFloat(undistributed_cost);
        if (undistributed_cost_float < 0) {
            isExecuting = false;
            return alert('1Нет нераспределенных ДС. Нельзя увеличить сумму вида работ')
        }

        //Стоимость и процент родителя
        var tow_cost = check_box.closest('tr').getElementsByClassName("tow_cost")[0];
        tow_cost = parseFloat(tow_cost.dataset.value);
        tow_cost = isNaN(tow_cost)? 0:tow_cost;

        var cell_tow_cost_percent = check_box.closest('tr').getElementsByClassName("tow_cost_percent")[0];
        var tow_cost_percent = parseFloat(cell_tow_cost_percent.dataset.value);
        tow_cost_percent = isNaN(tow_cost_percent)? 0:tow_cost_percent;
        //Общая стоимость договора
        var contract_cost = document.getElementById('ctr_card_full_cost').value;
//        contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
        contract_cost = rubToFloat(contract_cost);
        contract_cost = isNaN(contract_cost)? 0:contract_cost;
        //Список стоимости и процента для каждого tow lvl
        var cost_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        var percent_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        //Данные родительской ячейки
        var row = check_box.closest('tr');
        var tow_cnt = row.dataset.tow_cnt;
        var className = row.className;
        //    var new_status = check_box.getElementsByClassName("checkbox_time_tracking")[0].checked;
        var new_status = check_box.checked;
        var cur_id = row.id;
        var cur_lvl = parseInt(className.split('lvl-')[1]);
        var currentRow = check_box.closest('tr');
        var nextRow = row.nextElementSibling;
        var taskRow = row.nextElementSibling;
        if (!taskRow) {
            taskRow = row;
        }
        if (!nextRow) {
            nextRow = row;
        }

        //Стоимость и процент tow на текущем и следующем lvl
        var cost_per_child = tow_cnt? (tow_cost / tow_cnt):0;
        var percent_per_child = tow_cnt? (tow_cost_percent / tow_cnt):0;
        var tows_array = [[cur_id, cur_lvl+1, cost_per_child, percent_per_child]];
        //Записываем данные в списки
        cost_list[cur_lvl] = tow_cost;
        percent_list[cur_lvl] = tow_cost_percent;
        cost_list[cur_lvl+1] = cost_per_child;
        percent_list[cur_lvl+1] = percent_per_child;

        var tow_lvl = nextRow? parseInt(nextRow.className.split('lvl-')[1]):'';
        var tow_id = nextRow? row.id:'';

        //Ищем всех детей
        while (nextRow && tow_lvl > cur_lvl ) {
            tow_lvl = parseInt(nextRow.className.split('lvl-')[1]);
            tow_id = nextRow.id;

            if (tow_lvl > cur_lvl) {
                tow_cnt = nextRow.dataset.tow_cnt;

                tow_cost = cost_list[tow_lvl];
                tow_cost_percent = percent_list[tow_lvl];

                cost_per_child = tow_cnt? (tow_cost / tow_cnt):0;
                percent_per_child = tow_cnt? (tow_cost_percent / tow_cnt):0;
                cost_list[tow_lvl+1] = cost_per_child;
                percent_list[tow_lvl+1] = percent_per_child;

                tows_array = Object.assign({tow_id: {lvl:tow_lvl, tow_cnt:0}}, tows_array);
                if (undistributed_cost_float < cost_per_child) {
                    alert('Нет нераспределенных ДС. нельзя увеличить сумму вида работ');
                    break;
                }

                if (!nextRow.getElementsByClassName("checkbox_time_tracking")[0].disabled) {
                    nextRow.getElementsByClassName("tow_cost_percent")[0].value = percent_list[tow_lvl] + ' %'
                    undistributedStatus = undistributedCost(nextRow.getElementsByClassName("tow_cost_percent")[0], percent='percent');
                    if (undistributedStatus === false) {
                        break;
                    }
                    nextRow.getElementsByClassName("checkbox_time_tracking")[0].checked = new_status;
                }
                nextRow = nextRow.nextElementSibling;
            }
        }
    }
    else {
        var tow_cost = check_box.closest('tr').getElementsByClassName("tow_cost")[0];
        undistributedCost(check_box, percent=false, input_cost=false, subtraction=true);
    }
    isExecuting = false;
}

function undistributedCost(cell, percent=false, input_cost=false, subtraction=false) {
    isEditContract();
    //Перераспределение для Кати, когда не учитываются отделы, принудительно указываем, что есть отдела
    var dept_id = null;
    if (document.URL.split('/contract-list/card/').length > 1) {
        dept_id = 1111;
    }
    else {
        dept_id = cell.closest('tr').querySelectorAll(".select_tow_dept")[0];
        dept_id = dept_id.options[dept_id.selectedIndex].value;
    }
    //Информация об НДС
    let vat = document.getElementById('ctr_card_contract_vat_label').dataset.vat;
    var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
    var undistributed_cost = undistributed.dataset.undistributed_cost;
    var undistributed_cost_float = parseFloat(undistributed_cost);
    var last_contract_cost = undistributed.dataset.contract_cost;

    if (!subtraction) {
        //% ФОТ
        var fot_cost_percent = document.getElementById("ctr_card_fot_value").value;
        fot_cost_percent = parseFloat(fot_cost_percent);
        if (isNaN(fot_cost_percent)) {
            fot_cost_percent = 0;
        }

        var contract_type = document.getElementById("contract_type").innerText;  //Тип договора

        var tow_cost = 0; //Сумма tow

        //Тип единицы измерения редактируемого значения (рубли или проценты)
        value_type = percent? '%':'₽';

        //Текущее и прошлое значение ячейки(нужно для пересчета нераспределенной суммы)
        var cost1 = cell.value;
        var cost1_float = rubToFloat(cost1, value_type);
        var cost2 = cell.dataset.value;
        var cost2_float = parseFloat(cost2);

        cost1_float = isNaN(cost1_float)? 0:cost1_float;
        cost2_float = isNaN(cost2_float)? 0:cost2_float;

        //Если не указан отдел, возвращаем всю сумму в стоимость договора и ставим нули у суммы
        if (input_cost===false && dept_id && !subtraction) {
            // Обновляем значение нераспределенных средств
//            var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
//            var undistributed_cost = undistributed.dataset.undistributed_cost;
//            var undistributed_cost_float = parseFloat(undistributed_cost);

            undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;

            if (undistributed_cost_float < 0 && cost1_float >= cost2_float) {
                //возвращаем прошлое значение из дата атрибута в value
                if (cost2_float) {
                    cost2_float = cost2_float.toFixed(2) * 1.00;
                    cost2_float = cost2_float.toLocaleString() + ` ${value_type}`;
                }
                else {
                    cost2_float = `0 ${value_type}`;
                }
                cell.value = cost2_float;
                return createDialogWindow(status='error', description=['Нет нераспределенных ДС. нельзя увеличить сумму вида работ']);
            }
        }

        //Если ячейка с процентом суммы, то пересчитываем и значение ячейки "сумма"
        if (percent) {
            //Сумма договора, если не указали вручную при вызове функции
            if (input_cost===false) {
//                var contract_cost = document.getElementById('ctr_card_full_cost').value;
//                contract_cost = rubToFloat(contract_cost);
//                contract_cost = isNaN(contract_cost)? 0:contract_cost;
                var contract_cost = last_contract_cost;
            }
            else {
                var contract_cost = input_cost;
            }
            //Сумма tow
            var value_cell = cell.closest('tr').getElementsByClassName("tow_cost")[0];
            var value_cost1 = value_cell.value;
            var value_cost1_float = rubToFloat(value_cost1, value_type);
            var value_cost2 = value_cell.dataset.value;
            var value_cost2_float = parseFloat(value_cost2);
            value_cost1_float = isNaN(value_cost1_float)? 0:value_cost1_float;
            value_cost2_float = isNaN(value_cost2_float)? 0:value_cost2_float;

            tow_cost = contract_cost * cost1_float / 100;

            //Нераспределенный остаток
            if (dept_id) {
                undistributed_cost = undistributed_cost_float - tow_cost + value_cost2_float;
                if (undistributed_cost < -0.001) {
                    if (cost2_float) {
                        cost2_float = cost2_float.toFixed(2) * 1.00;
                        cost2_float = cost2_float.toLocaleString() + ` ${value_type}`;
                    }
                    else {
                        cost2_float = `0 ${value_type}`;
                    }
                    cell.value = cost2_float;
                    return createDialogWindow(status='error', description=[`Нераспределенных ДС не хватает (${(undistributed_cost * -1).toLocaleString() + ' ₽'}) для изменения суммы вида работ`]);
                }
            }

            //Обновляем значения ячейки "Сумма"
            value_cell.dataset.value = tow_cost;
            value_cost1 = (tow_cost).toFixed(2) * 1.00;
            value_cost1 = value_cost1.toLocaleString() + ' ₽';
            value_cell.value = value_cost1;
        }
        else {
            //Если редактируется ячейка "Сумма"
            tow_cost = cost1_float;
            if (dept_id) {
                console.log(undistributed_cost_float, '-', cost1_float, '+', cost2_float)
                undistributed_cost = undistributed_cost_float - cost1_float + cost2_float;
                if (undistributed_cost < 0) {
                    var value_cell = cell.closest('tr').getElementsByClassName("tow_cost")[0];
                    if (cost2_float) {
                        cost2_float = cost2_float.toFixed(2) * 1.00;
                        cost2_float = cost2_float.toLocaleString() + ` ${value_type}`;
                    }
                    else {
                        cost2_float = `0 ${value_type}`;
                    }
                    cell.value = cost2_float;
                    return createDialogWindow(status='error', description=['Нет нераспределенных ДС v_1. Нельзя увеличить сумму вида работ']);

                }
            }
            //Пересчитываем "% суммы"
//            var contract_cost = document.getElementById('ctr_card_full_cost').value;
//            contract_cost = rubToFloat(contract_cost);
//            contract_cost = isNaN(contract_cost)? 0:contract_cost;
            var contract_cost = last_contract_cost;
            var cell_tow_cost_percent = cell.closest('tr').getElementsByClassName("tow_cost_percent")[0];
            ctcp_value = cost1_float /(contract_cost) *100
            cell_tow_cost_percent.dataset.value = ctcp_value;
            ctcp_value = ctcp_value.toFixed(2) * 1.00;
            ctcp_value = ctcp_value.toLocaleString() + ' %';
            cell_tow_cost_percent.value = ctcp_value;
        }

        if (input_cost===false && dept_id) {
            var undistributed_cost_tc = undistributed_cost

            if (undistributed_cost_tc) {
                undistributed_cost_tc = undistributed_cost_tc.toFixed(2) * 1.00;
                undistributed_cost_tc = undistributed_cost_tc.toLocaleString() + ' ₽';
            }
            else {
                undistributed_cost_tc = '0 ₽';
            }

            //Обновляем значение нераспределенной суммы
            undistributed.textContent = undistributed_cost_tc;
            undistributed.dataset.undistributed_cost = undistributed_cost.toFixed(2) * 1.00;
        }

        //Обновляем данные в редактируемой ячейки
        cell.dataset.value = cost1_float;
        cost1_float = cost1_float.toFixed(2) * 1.00;
        cost1_float = cost1_float.toLocaleString();
        cost1_float += ` ${value_type}`;
        cell.value = cost1_float;

        //указываем тип введенной суммы (рубли/проценты)
        cell.closest('tr').dataset.value_type = value_type;

        //Обновляем данные в ячейке СУММА ФОТ
        if (true) {
            var fot_cost_cell = cell.closest('tr').getElementsByClassName("tow_fot_cost")[0];
            var fot_cost = tow_cost * fot_cost_percent / 100;
            var fot_cost2 = fot_cost;
            if (fot_cost2) {
                fot_cost2 = fot_cost2.toFixed(2) * 1.00;
                fot_cost2 = fot_cost2.toLocaleString() + ' ₽';
            }
            else {
                fot_cost2 = '0 ₽';
            }
            //Обновляем данные в СУММА ФОТ
            fot_cost_cell.dataset.value = fot_cost;
            fot_cost_cell.value = fot_cost2;
        }

        //Меняем стили ячеек сумм на manual/calc
        cell.className = cell.className.replace('calc', 'manual')
        if (percent) {
            let tow_cost = cell.closest('tr').getElementsByClassName("tow_cost")[0];
            tow_cost.className = tow_cost.className.replace('manual', 'calc');
        }
        else {
            let tow_cost_percent = cell.closest('tr').getElementsByClassName("tow_cost_percent")[0];
            tow_cost_percent.className = tow_cost_percent.className.replace('manual', 'calc');
        }

        //Выбираем чекбокс привязывающий tow к договору
        cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0].checked = true;

        selectContractTow(cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0]);
    }
    else {
        if (dept_id) {
            // Обновляем значение нераспределенных средств
//            var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
//            var undistributed_cost = undistributed.dataset.undistributed_cost;
//            var undistributed_cost_float = parseFloat(undistributed_cost);

            undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;

            //Сумма договора, если не указали вручную при вызове функции
            if (input_cost === false) {
//                var contract_cost = document.getElementById('ctr_card_full_cost').value;
////                contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
//                contract_cost =  rubToFloat(contract_cost);
//                contract_cost = isNaN(contract_cost)? 0:contract_cost;
                var contract_cost = last_contract_cost;
            }
            else {
                var contract_cost = input_cost;
            }
            //Сумма tow
            var value_cell = cell.closest('tr').getElementsByClassName("tow_cost")[0];
            var value_cost2 = value_cell.dataset.value;
            var value_cost2_float = parseFloat(value_cost2);
            value_cost2_float = isNaN(value_cost2_float)? 0:value_cost2_float;

            //Обновляем значение нераспределенной суммы
            undistributed_cost = undistributed_cost_float + value_cost2_float;
            var undistributed_cost_tc = undistributed_cost
            if (undistributed_cost_tc) {
                undistributed_cost_tc = undistributed_cost_tc.toFixed(2) * 1.00;
                undistributed_cost_tc = undistributed_cost_tc.toLocaleString() + ' ₽';
            }
            else {
                undistributed_cost_tc = '0 ₽';
            }

            undistributed.textContent = undistributed_cost_tc;
            undistributed.dataset.undistributed_cost = undistributed_cost.toFixed(2) * 1.00;

            value_cell.dataset.value = '';
            value_cell.value = '';
            if (percent) {
                cell.dataset.value = '';
                cell.value = '';
            }
            else {
                var percent_cell = cell.closest('tr').getElementsByClassName("tow_cost_percent")[0];
                percent_cell.dataset.value = '';
                percent_cell.value = '';
            }
        }
    }
}

function editContractCardStatusName(val) {
    const select1 = document.getElementById('ctr_card_full_status_name');
    const select2 = document.getElementById('ctr_card_status_name');
    var val_value = val.value;

    if (val==select1 && $('#ctr_card_status_name').val() != val_value) {
        $('#ctr_card_status_name').val(val_value); // Select the option with a value of '1'
        $('#ctr_card_status_name').trigger('change');
    }
    else if (val==select2 && $('#ctr_card_full_status_name').val() != val_value) {
        $('#ctr_card_full_status_name').val(val_value); // Select the option with a value of '1'
        $('#ctr_card_full_status_name').trigger('change');
    }
}

function editContractCardData(val) {
    var val_id = val.id;
    var val_value = val.value;

    if (val_id == 'ctr_card_full_contract_number' || val_id == 'ctr_card_contract_number') {
        document.getElementById('ctr_card_full_contract_number').value = val_value;
        document.getElementById('ctr_card_contract_number').value = val_value;
    }
    else if (val_id == 'ctr_card_full_status_name' || val_id == 'ctr_card_status_name') {
        const select1 = document.getElementById('ctr_card_full_status_name');
        const select2 = document.getElementById('ctr_card_status_name');

        if (val==select1 && $('#ctr_card_status_name').val() != val_value) {
            $('#ctr_card_status_name').val(val_value); // Select the option with a value of '1'
            $('#ctr_card_status_name').trigger('change');
        }
        else if (val==select2 && $('#ctr_card_full_status_name').val() != val_value) {
            $('#ctr_card_full_status_name').val(val_value); // Select the option with a value of '1'
            $('#ctr_card_full_status_name').trigger('change');
        }
    }
    else if (val_id == 'ctr_card_full_obj' || val_id == 'ctr_card_obj') {
        const select1 = document.getElementById('ctr_card_full_obj');
        const select2 = document.getElementById('ctr_card_obj');

        if (val==select1 && $('#ctr_card_obj').val() != val_value) {
            $('#ctr_card_obj').val(val_value); // Select the option with a value of '1'
            $('#ctr_card_obj').trigger('change');
        }
        else if (val==select2 && $('#ctr_card_full_obj').val() != val_value) {
            $('#ctr_card_full_obj').val(val_value); // Select the option with a value of '1'
            $('#ctr_card_full_obj').trigger('change');
        }
        //Меняем список tow при смене объекта
        changeObjectInCard();
    }
}

function convertCost(val, status) {
    isEditContract();
    var cost = val.value;
    if (status == 'in') {
//        var cost_value = parseFloat(val.value.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
        var cost_value =  rubToFloat(val.value);
        document.getElementById('ctr_card_cost').value = cost_value;
        document.getElementById('ctr_card_full_cost').value = cost_value;
    }
    else if (status == 'out') {
        var cost_value = parseFloat(cost);
        if (isNaN(cost_value)) {
            cost_value = 0;
        }
        cost_value = cost_value.toFixed(2) * 1.00;
        cost_value = cost_value.toLocaleString();

        cost_value += ' ₽';

        document.getElementById('ctr_card_cost').value = cost_value;
        document.getElementById('ctr_card_full_cost').value = cost_value;
    }
    else if (status == 'change') {
        var cost_value = parseFloat(cost);
        if (isNaN(cost_value)) {
            cost_value = 0;
        }
        //Информация об НДС
        let vat = document.getElementById('ctr_card_contract_vat_label').dataset.vat;
        // Обновляем значение нераспределенных средств
        var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
        var undistributed_cost = undistributed.dataset.undistributed_cost;
        var undistributed_cost_float = parseFloat(undistributed_cost);
        var last_contract_cost = undistributed.dataset.contract_cost;
        var last_contract_cost_float = parseFloat(last_contract_cost);
        var last_contract_cost_float = (last_contract_cost * 1.00).toFixed(2) * 1.00;

        undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;
        last_contract_cost_float = isNaN(last_contract_cost_float)? 0:last_contract_cost_float;
        undistributed_cost =  (cost_value * 1) - last_contract_cost_float + undistributed_cost_float
        var undistributed_cost_tc = undistributed_cost

        if (undistributed_cost_tc) {
            undistributed_cost_tc = undistributed_cost_tc.toFixed(2) * 1.00;
            undistributed_cost_tc = undistributed_cost_tc.toLocaleString() + ' ₽';
        }
        else {
            undistributed_cost_tc = '0 ₽'
        }
        undistributed.textContent = undistributed_cost_tc;
        undistributed.dataset.undistributed_cost = undistributed_cost.toFixed(2) * 1.00;
        undistributed.dataset.contract_cost = (cost_value * 1).toFixed(2) * 1.00;

        cost_value = cost_value.toFixed(2) * 1.00;
//        cost_value = cost_value.toLocaleString();
//
//        cost_value += ' ₽';

        document.getElementById('ctr_card_cost').value = cost_value;
        document.getElementById('ctr_card_full_cost').value = cost_value;
    }

}

function setMultiselectFillOn(button) {
    if (document.URL.split('/contract-list/card/').length == 1) {
        button.className = button.className=="ctr_card_multiselect_on"? "ctr_card_multiselect_off":"ctr_card_multiselect_on";
    }

}

function isEditContract() {
    var edit_btn = document.getElementById("edit_btn");
    if (!edit_btn.hidden) {
        editContract();
    }
}

function editContract() {
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

    const tab = document.getElementById("towTable");
    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
}

function saveContract() {
    var contract_id = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    if (document.URL.split('/new/').length > 1) {
        contract_id = 'new'
    }
    //Карточка проекта
    var ctr_card_obj = document.getElementById('ctr_card_full_obj').value;
    var ctr_card_parent_id = null;
    var cc_parent_id = null;
    var ctr_card_contract_number = document.getElementById('ctr_card_full_contract_number').value;
    if (document.getElementById('ctr_card_full_parent_number_div')) {
        // Если объект был выбран, то для допника находим номер основного договора
        if (ctr_card_obj) {
            ctr_card_parent_id = $('#ctr_card_parent_number').val()? $('#ctr_card_parent_number').val():document.getElementById('ctr_card_full_parent_number').value;
        }
        cc_parent_id = document.getElementById('ctr_card_full_parent_number_label');
    }
    var ctr_card_partner = document.getElementById('ctr_card_partner').value;
    var ctr_card_status_name = document.getElementById('ctr_card_full_status_name').value;
    var user_card_allow = document.getElementById('user_card_allow').checked;
    var ctr_card_contractor = document.getElementById('ctr_card_contractor').value;
    var ctr_card_fot_value = document.getElementById('ctr_card_fot_value').value;
    var ctr_card_contract_description = document.getElementById('ctr_card_contract_description').value;
    var ctr_card_cost = document.getElementById('ctr_card_full_cost').value;
    var ctr_card_contract_vat_label = document.getElementById('ctr_card_contract_vat_label').innerText;
    var ctr_card_contract_vat_value = document.getElementById('ctr_card_contract_vat_label').dataset.vat;
    var ctr_card_contract_full_prolongation_label = document.getElementById('ctr_card_contract_full_prolongation_label').value;
    ctr_card_contract_full_prolongation_label = false;  //Функционал автопродления не введен
    var ctr_card_date_start = document.getElementById('ctr_card_date_start').value;
    ctr_card_date_start = ctr_card_date_start? convertDate(ctr_card_date_start):null;
    var ctr_card_date_finish = document.getElementById('ctr_card_date_finish').value;
    ctr_card_date_finish = ctr_card_date_finish? convertDate(ctr_card_date_finish):null;

    var type_id = document.getElementById('contract_type').innerText;

    var cc_obj = document.getElementById('ctr_card_full_obj_label');
    var cc_contract_number = document.getElementById('ctr_card_full_contract_number_label');
    var cc_partner = document.getElementById('ctr_card_partner_label');
    var cc_status_name = document.getElementById('ctr_card_status_full_name_label');
    var cc_contractor = document.getElementById('ctr_card_contractor_label');
    var cc_cost = document.getElementById('ctr_card_full_cost_label');
    var cc_date_start = document.getElementById('ctr_card_date_start_label');
    var cc_date_finish = document.getElementById('ctr_card_date_finish_label');

    // Проверяем, все ли данные договора заполнены
    check_lst1 = [cc_obj, cc_parent_id, cc_contract_number, cc_partner, cc_status_name,
    cc_contractor, cc_cost, cc_date_start, cc_date_finish]
    check_lst2 = [ctr_card_obj, ctr_card_parent_id, ctr_card_contract_number, ctr_card_partner, ctr_card_status_name,
    ctr_card_contractor, ctr_card_cost, ctr_card_date_start, ctr_card_date_finish]

    check_lst = [
        [ctr_card_obj, cc_obj],
        [ctr_card_parent_id, cc_parent_id],
        [ctr_card_contract_number, cc_contract_number],
        [ctr_card_partner, cc_partner],
        [ctr_card_status_name, cc_status_name],
        [ctr_card_contractor, cc_contractor],
        [ctr_card_cost, cc_cost],
        [ctr_card_date_start, cc_date_start],
        [ctr_card_date_finish, cc_date_finish]
    ]


    description_lst = ["Объект", "Основной договор", "Номер договора", "Контрагент", "Статус", "Заказчик", "Стоимость", "Дата начала", "Дата окончания"]

    var description = [];

    for (var i=0; i<check_lst.length; i++) {
        if (!check_lst[i][0]) {
            if (check_lst[i][1]) {
                check_lst[i][1].style.borderRight = "solid #FB3F4A";
                description.push(' ' + description_lst[i]);
            }
        }
        else {
            check_lst[i][1].style.borderRight = "none";
        }
    }
    if (description.length) {
        showFullCardInfo();
        description.unshift('Заполнены не все поля:');
        return ['error', description]
    }

    const tab = document.getElementById("towTable");
    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    //Список tow
    list_towList = [];
    if (tab_numRow[0].className !='div_tow_first_row') {
        for (let i of tab_numRow) {
            let tow_checkBox = i.getElementsByClassName('checkbox_time_tracking')[0].checked;
            if (tow_checkBox) {
                let date_start = i.getElementsByClassName('tow_date_start')[0].value;
                let date_finish = i.getElementsByClassName('tow_date_finish')[0].value;
                date_start = date_start? convertDate(date_start):null;
                date_finish = date_finish? convertDate(date_finish):null;

                var dept_id = i.querySelectorAll(".select_tow_dept")[0];
                dept_id = dept_id.options[dept_id.selectedIndex].value;

                list_towList.push({
                    id: i.id,
                    cost: i.getElementsByClassName('tow_cost')[0].dataset.value,
                    percent: i.getElementsByClassName('tow_cost_percent')[0].dataset.value,
                    dept_id: dept_id,
                    date_start: date_start,
                    date_finish: date_finish,
                    type: i.dataset.value_type
                });
            }
        }
    }

    var ctr_card = {
        contract_id: contract_id,
        object_id: ctr_card_obj,
        parent_id: ctr_card_parent_id,
        contract_number: ctr_card_contract_number,
        partner_id: ctr_card_partner,
        contract_status_id: ctr_card_status_name,
        allow: user_card_allow,
        contractor_id: ctr_card_contractor,
        fot_percent: ctr_card_fot_value,
        contract_description: ctr_card_contract_description,
        contract_cost: ctr_card_cost,
        vat: ctr_card_contract_vat_label,
        vat_value: ctr_card_contract_vat_value,
        auto_continue: ctr_card_contract_full_prolongation_label,
        date_start: ctr_card_date_start,
        date_finish: ctr_card_date_finish,
        type_id: type_id
    }


    return {'ctr_card': ctr_card,'list_towList': list_towList}
}

function cancelContractChanges() {
    window.location.href = document.URL;
    alert('Изменения отменены, страница обновлена')
}

function modalCreateNewContract() {
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
};

function createNewContract(button) {
    let link_name = '';
    if (document.URL.split('/objects/').length > 1) {
        link_name = document.URL.split('/objects/')[1].split('/')[0] + '/'
    }
    let id = button.id;
    if (id == 'create_contract_button_income_contract_frame') {
        // Создание доходного договора
        window.open(`/contract-list/card/new/${link_name}1/0`, '_blank');
        return closeModal();
    }
    else if (id == 'create_contract_button_income_subcontract_frame') {
        // Создание доходного допника
        window.open(`/contract-list/card/new/${link_name}1/1`, '_blank');
        return closeModal();
    }
    else if (id == 'create_contract_button_expenditure_contract_frame') {
        // Создание расходного договора
        window.open(`/contract-list/card/new/${link_name}2/0`, '_blank');
        return closeModal();
    }
    else if (id == 'create_contract_button_expenditure_subcontract_frame') {
        // Создание расходного допника
        window.open(`/contract-list/card/new/${link_name}2/1`, '_blank');
        return closeModal();
    }
    else {
        return alert('Ошибка при попытке создать договор')
    }
}

function calcTowChildWithDept2() {
    const tab = document.getElementById("towTable");
    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    //Список tow
    list_towList1 = [];
    for (let i of tab_numRow) {
        let dept_id = i.querySelectorAll(".select_tow_dept")[0];
        dept_id = dept_id.options[dept_id.selectedIndex].value;
        list_towList1.push([
            i.id,
            parseInt(i.dataset.lvl),
            dept_id,
            0,
            i.getElementsByClassName('input_tow_name')[0].value
        ])
    }


    let dept_cnt = 0;
    let cnt_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for (let i=list_towList1.length-1; i>0; i--) {
        let row = list_towList1[i];
        let aboveRow = list_towList1[i-1];
        //        row[3] = 1;
        if (row[2] != "None") {
            dept_cnt++;
            row[3] = 1;
            cnt_list[row[1]] += 1;
        }

        if (row[1]<aboveRow[1]) {
            row[3] = dept_cnt;
            cnt_list[row[1]] = 1;

            for (let cl=row[1]+1; cl<10; cl++) {
                cnt_list[cl] = 0;
            }
            dept_cnt = 0;
        }

        if (row[1]>aboveRow[1]) {
            aboveRow[3] = dept_cnt;
            cnt_list[aboveRow[1]] += 1;
            dept_cnt = dept_cnt? 1:0;
            for (let cl=row[1]; cl<10; cl++) {
                cnt_list[cl] = 0;
            }
        }

        row[3] = !row[3]? 1:row[3];
    }
    for (let i=0; i<tab_numRow.length; i++) {
            tab_numRow[i].dataset.tow_cnt = list_towList1[i][3]

    }
}

//Расчёт кол-ва детей tow
function calcTowChildWithDept() {
    const tab = document.getElementById("towTable");
    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    //Список tow
    list_towList1 = [];
    for (let i of tab_numRow) {
        let dept_id = i.querySelectorAll(".select_tow_dept")[0];
        dept_id = dept_id.options[dept_id.selectedIndex].value;
        list_towList1.push([
            i.id,
            parseInt(i.dataset.lvl),
            dept_id,
//            i.getElementsByClassName('tow_dept')[0].dataset.value,
            0,
            i.getElementsByClassName('input_tow_name')[0].value
        ])
    }
    //Список детей на каждом lvl
    let cnt_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    //Проходим по всему списку tow снизу вверх
    for (let i=list_towList1.length-1; i>0; i--) {
        let row = list_towList1[i];
        let aboveRow = list_towList1[i-1];

        //если у строки не было указано кол-во детей - значение равно 1 иначе сохраняем значение
        row[3] = row[3]? row[3]:1;

        //Если у строки есть привязка к отделу, то прибавляем ребёнка на текущий lvl
        if (row[2] != "None") {
            cnt_list[row[1]] += 1;
        }

        //Если сверху родитель (cur row lvl > above row lvl)
        if (row[1]>aboveRow[1]) {
            //Если на текущем lvl есть дети с dept, то добавляем родителю dept чтобы информация дошла до верха
            aboveRow[3] = cnt_list[row[1]];
            if (cnt_list[row[1]]) {
                aboveRow[2] = 111;
            }
            //Обнуляем часть списка детей от текущего lvl до последнего, т.к. далее будут уже дети но новой ветки
            for (let cl=row[1]; cl<10; cl++) {
                cnt_list[cl] = 0;
            }
        }

        //Если строка выше - начало новой ветки (cur row lvl < above row lvl)
        if (row[1]<aboveRow[1]) {
            //Добавляем значение кол-ва детей
            row[3] = cnt_list[row[1]];
            //Обнуляем часть списка начиная с уровня выше текущего и до последнего. Сохраняем значение текущего lvl,
            //т.к. при нахождении родителя, нам понадобится значение детей на lvl текущей строки
            for (let cl=row[1]+1; cl<10; cl++) {
                cnt_list[cl] = 0;
            }
        }
    }
    //Обновляем значение детей в таблице tow
    for (let i=0; i<tab_numRow.length; i++) {
        tab_numRow[i].dataset.tow_cnt = list_towList1[i][3]
    }
}

// Добавляем функции на вновьсозданную строку в карточке договора
function setNewRowContractFunc(conRow) {
    conRow.getElementsByClassName('tow_cost')[0].addEventListener('change', function() {undistributedCost(this);});
    conRow.getElementsByClassName('checkbox_time_tracking')[0].addEventListener('click', function() {selectContractTow(this);});
    conRow.getElementsByClassName('tow_cost_percent')[0].addEventListener('change', function() {undistributedCost(this, percent='percent');});
    conRow.getElementsByClassName('tow_date_start')[0].addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
    conRow.getElementsByClassName('tow_date_start')[0].addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout'); });
    conRow.getElementsByClassName('tow_date_start')[0].addEventListener('change', function() {isEditContract();});
    conRow.getElementsByClassName('tow_date_finish')[0].addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
    conRow.getElementsByClassName('tow_date_finish')[0].addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout'); });
    conRow.getElementsByClassName('tow_date_finish')[0].addEventListener('change', function() {isEditContract();});

    if (conRow.getElementsByClassName('tow_cost')[0].classList.contains('manual')) {
        conRow.getElementsByClassName('tow_cost')[0].classList.remove('manual');
        conRow.getElementsByClassName('tow_cost')[0].classList.add('calc');
    }
    if (conRow.getElementsByClassName('tow_cost_percent')[0].classList.contains('manual')) {
        conRow.getElementsByClassName('tow_cost_percent')[0].classList.remove('manual');
        conRow.getElementsByClassName('tow_cost_percent')[0].classList.add('calc');
    }
    conRow.dataset.value_type = '';
}

function reloadPage() {
    location.reload();
}

function changeObjectInCard() {
    let object_id = $('#ctr_card_obj').val();
    let type_id = document.getElementById('contract_type').innerText;
    let contract_id = document.URL.substring(document.URL.lastIndexOf('/')+1);
    if (document.URL.split('/contract-list/card/new/').length > 1) {
        contract_id = 'new';
    }
    else {
//        console.log('Изменить объект можно только при создании нового договора/доп.соглашения')
//        return alert('Изменить объект можно только при создании нового договора/доп.соглашения')
//        return location.reload();
        return createDialogWindow(status='error', description=['Изменить объект можно только при создании нового договора/доп.соглашения'], func=[['click', [reloadPage, '']]]);

    }

    fetch(`/tow-list-for-object/${object_id}/${type_id}/${contract_id}`, {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": ""
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    //Нераспределенный остаток
//                    var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
//                    undistributed.textContent = 1
//                    undistributed.dataset.undistributed_cost =  parseFloat('undistributed_cost');
                    if (contract_id == 'new' && document.getElementById("ctr_card_parent_number")) {
                        // Обновляем список договоров из карточки договора
                        var contract_list_select = document.getElementById("ctr_card_parent_number");
                        contract_list_select.disabled = false;
                        $('#ctr_card_parent_number').empty();

                        data.contracts.forEach(function (c) {
                            $('#ctr_card_parent_number').append($('<option>', {
                                value: c.contract_id,
                                text: c.contract_number

                            }));
                        });

                        $('#ctr_card_parent_number').trigger('change');
                    }




//                    $.each(data.contracts, function(index, value) {
//                        $('#ctr_card_parent_number').append($('<option>', {
//                            value: value,
//                            text: value
//                        }));
//                    });
//                    // Trigger change event to update Select2
//                    $('#ctr_card_parent_number').trigger('change');


                    // Обновляем tow
                    const tab = document.getElementById("towTable");
                    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
                    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
                    // Удаляем всё из таблицы tow
                    for (var i = 1; i<=tab_numRow.length;) {
                        tab.deleteRow(1);
                    }
                    // Добавляем tow выбранного Объекта
                    if (data.tow.length) {
                        for (let t of data.tow) {
                            let row = tab_tr0.insertRow(tab_numRow.length);

                            // id
                            row.className = `lvl-${t.depth}`;
                            row.setAttribute("data-lvl", t.depth);
                            row.setAttribute("data-del", t.del);
                            row.setAttribute("data-tow_cnt", t.tow_cnt4);
                            row.setAttribute("data-value_type", t.value_type? t.value_type:'');
                            row.id = t.tow_id;

                            //**************************************************
                            // Наименование видов работ
                            let towName = row.insertCell(0);
                            towName.className = "tow_name";
                                let div_tow_name = document.createElement("div");
                                div_tow_name.className = "div_tow_name";
                                    let input_tow_name = document.createElement('input');
                                    input_tow_name.type = "text";
                                    input_tow_name.className = "input_tow_name";
                                    t.is_not_edited? input_tow_name.classList.add("is_not_edited"):0;
                                    input_tow_name.placeholder = "Введите название работы";
                                    input_tow_name.setAttribute('value', t.tow_name)
                                    input_tow_name.disabled = true;
                                div_tow_name.appendChild(input_tow_name);
                                    let div_tow_button = document.createElement("div");
                                    div_tow_button.className = "div_tow_button";
                                    div_tow_button.hidden = true;
                            towName.appendChild(div_tow_name);
                            towName.appendChild(div_tow_button);

//                            // Настраиваем кнопки
                            addButtonsForNewRow(div_tow_button, createNewRow=true);

                            //**************************************************
                            // Выбор tow
                            let cellCheckbox = row.insertCell(1);
                            cellCheckbox.className = "tow_contract";
                                let checkbox = document.createElement('input');
                                checkbox.type = "checkbox";
                                checkbox.className = "checkbox_time_tracking";
                                if (t.contract_tow) {
                                    checkbox.checked = true;
                                }
                            cellCheckbox.appendChild(checkbox);

                            //**************************************************
                            // Отдел
                            let cellDept = row.insertCell(2);
                            cellDept.classList.add("dept", "tow_dept");
                                let selectDept = document.createElement('select');
                                selectDept.disabled = true;
                                selectDept.className = "select_tow_dept";
                                    let option = document.createElement('option');
                                    option.value = "";
                                selectDept.appendChild(option);
                                    for (let dept of data.dept_list) {
                                        let option = document.createElement('option');
                                        option.value = dept[0];
                                        option.text = dept[1];
                                        if (dept[0] == t.dept_id) {
                                            option.setAttribute('selected', 'selected');
                                        }
                                        selectDept.appendChild(option);
                                    }
                            cellDept.appendChild(selectDept);

                            //**************************************************
                            // Сумма
                            let cost = row.insertCell(3);
                            cost.className = "cost";
                                let tow_cost = document.createElement('input');
                                tow_cost.type = "text";
                                tow_cost.classList.add("tow_cost", t.tow_cost_status);
                                tow_cost.setAttribute("data-value", t.tow_cost);
                                tow_cost.value = t.tow_cost_rub;
                            cost.appendChild(tow_cost);

                            //**************************************************
                            // % сумма
                            let cost_percent = row.insertCell(4);
                            cost_percent.className = "cost_percent";
                                let tow_cost_percent = document.createElement('input');
                                tow_cost_percent.type = "text";
                                tow_cost_percent.classList.add("tow_cost_percent", t.tow_cost_percent_status);
                                tow_cost_percent.setAttribute("data-value", t.tow_cost_percent);
                                tow_cost_percent.value = t.tow_cost_percent_txt? `${t.tow_cost_percent_txt} %`:"";
                            cost_percent.appendChild(tow_cost_percent);

                            //**************************************************
                            // Сумма ФОТ
                            let fot_cost = row.insertCell(5);
                            fot_cost.className = "fot_cost";
                                let tow_fot_cost = document.createElement('input');
                                tow_fot_cost.type = "text";
                                tow_fot_cost.className = "tow_fot_cost";
                                tow_fot_cost.setAttribute("data-value", t.tow_fot_cost);
                                tow_fot_cost.value = t.tow_fot_cost_rub;
                                tow_fot_cost.disabled = true;
                            fot_cost.appendChild(tow_fot_cost);

                            //**************************************************
                            // Субп. проекта
                            let subcontractor_cost = row.insertCell(6);
                            subcontractor_cost.className = "subcontractor_cost";
                                let tow_subcontractor_cost = document.createElement('input');
                                tow_subcontractor_cost.type = "text";
                                tow_subcontractor_cost.className = "tow_subcontractor_cost";
                                tow_subcontractor_cost.setAttribute("data-value", t.tow_subcontractor_cost);
                                tow_subcontractor_cost.value = t.summary_subcontractor_cost_rub;
                                tow_subcontractor_cost.disabled = true;
                            subcontractor_cost.appendChild(tow_subcontractor_cost);

                            //**************************************************
                            // Начало
                            let date_start = row.insertCell(7);
                            date_start.className = "date_start";
                                let tow_date_start = document.createElement('input');
                                tow_date_start.type = "text";
                                tow_date_start.className = "tow_date_start";
                                tow_date_start.setAttribute("data-value", t.tow_date_start);
                                tow_date_start.value = t.date_start_txt;
                            date_start.appendChild(tow_date_start);

                            //**************************************************
                            // Окончание
                            let date_finish = row.insertCell(8);
                            date_finish.className = "date_finish";
                                let tow_date_finish = document.createElement('input');
                                tow_date_finish.type = "text";
                                tow_date_finish.className = "tow_date_finish";
                                tow_date_finish.setAttribute("data-value", t.tow_date_finish);
                                tow_date_finish.value = t.date_finish_txt;
                            date_finish.appendChild(tow_date_finish);

                            // Добавляем функции в ячейки
                            setNewRowContractFunc(row);
//                            addButtonsForNewRow(row);
                        }
                    }
                    else {
                        // Если в объекте не было создано tow, то добавляем кнопку создать tow
                        let row = tab_tr0.insertRow(0);
                        row.className = "div_tow_first_row";
                        row.colSpan = 3;
                            let button_tow_first_cell = document.createElement("button");
                            button_tow_first_cell.className = 'button_tow_first_cell';
                            button_tow_first_cell.innerHTML = '+ Начать создание состава работ';
                            button_tow_first_cell.addEventListener('click', function() {FirstRow();})
                        row.appendChild(button_tow_first_cell);
                    }
                    return;
                }
                else {
                    alert(data.description)
                }
            })
}

function showNewPartnerDialog() {
    let dialog = document.createElement("dialog");
    dialog.className = "new_partner_dialog";
    dialog.id = "logInfo1";

    let new_partner_div_header = document.createElement("div");
    new_partner_div_header.id="new_partner_div_header";
        let new_partner_label_header = document.createElement("label");
        new_partner_label_header.innerHTML = 'ДОБАВИТЬ НОВОГО КОНТРАГЕНТА';

        let new_partner_img_header = document.createElement("img");
        new_partner_img_header.className = "crossBtnNAW";
        new_partner_img_header.id="user_card_crossBtnNAW";
        new_partner_img_header.src="/static/img/employee/cross.svg"
        new_partner_img_header.addEventListener('click', function() {
            closeNewPartnerDialog();
        });
    new_partner_div_header.appendChild(new_partner_label_header);
    new_partner_div_header.appendChild(new_partner_img_header);

    let new_partner_full_name = document.createElement("div");
    new_partner_full_name.className = "new_partner_div_name";
        let new_partner_full_name_label = document.createElement('label');
        new_partner_full_name_label.id = "new_partner_full_name_label";
        new_partner_full_name_label.className = "new_partner_name_label";
        new_partner_full_name_label.innerHTML = "ПОЛНОЕ НАИМЕНОВАНИЕ";
    new_partner_full_name.appendChild(new_partner_full_name_label);
        let new_partner_full_name_input = document.createElement('input');
        new_partner_full_name_input.type = "text";
        new_partner_full_name_input.id = "new_partner_full_name_input";
        new_partner_full_name_input.className = "new_partner_name_input";
        new_partner_full_name_input.placeholder = "Введите полное наименование контрагента";
    new_partner_full_name.appendChild(new_partner_full_name_input);

    let new_partner_short_name = document.createElement("div");
    new_partner_short_name.className = "new_partner_div_name";
        let new_partner_short_name_label = document.createElement('label');
        new_partner_short_name_label.id = "new_partner_short_name_label";
        new_partner_short_name_label.className = "new_partner_name_label";
        new_partner_short_name_label.innerHTML = "КРАТКОЕ НАИМЕНОВАНИЕ";
    new_partner_short_name.appendChild(new_partner_short_name_label);
        let new_partner_short_name_input = document.createElement('input');
        new_partner_short_name_input.type = "text";
        new_partner_short_name_input.id = "new_partner_short_name_input";
        new_partner_short_name_input.className = "new_partner_name_input";
        new_partner_short_name_input.placeholder = "Введите краткое наименование контрагента";
    new_partner_short_name.appendChild(new_partner_short_name_input);

    let new_partner_div_button_group = document.createElement("div");
    new_partner_div_button_group.className = "new_partner_div_button_group";
        let new_partner_div_button_group_apply = document.createElement('button');
        new_partner_div_button_group_apply.id = "apply__edit_btn_i";
        new_partner_div_button_group_apply.innerHTML = "СОХРАНИТЬ";
        new_partner_div_button_group_apply.addEventListener('click', function() {
            saveNewPartnerDialog();
        });
        let new_partner_div_button_group_cancel = document.createElement('button');
        new_partner_div_button_group_cancel.id = "apply__edit_btn_i";
        new_partner_div_button_group_cancel.innerHTML = "ОТМЕНИТЬ";
        new_partner_div_button_group_cancel.addEventListener('click', function() {
            closeNewPartnerDialog();
        });
    new_partner_div_button_group.appendChild(new_partner_div_button_group_cancel);
    new_partner_div_button_group.appendChild(new_partner_div_button_group_apply);


    dialog.appendChild(new_partner_div_header);
    dialog.appendChild(new_partner_full_name);
    dialog.appendChild(new_partner_short_name);
    dialog.appendChild(new_partner_div_button_group);

        dialog.addEventListener('cancel', function() {
            closeNewPartnerDialog();
        });

    document.body.appendChild(dialog)

    dialog.showModal();
}

function saveNewPartnerDialog() {
    let new_partner_full_name_input = document.getElementById('new_partner_full_name_input');
    let new_partner_short_name_input = document.getElementById('new_partner_short_name_input');

    let full_name_label = document.getElementById('new_partner_full_name_label');
    let short_name_label = document.getElementById('new_partner_short_name_label');

    let full_name = new_partner_full_name_input.value;
    let short_name = new_partner_short_name_input.value;

    full_name_label.style.borderRight = !full_name? "solid #FB3F4A": "solid #F3F3F3";
    short_name_label.style.borderRight = !short_name? "solid #FB3F4A": "solid #F3F3F3";

    let description = [];

    if (!full_name) {
        description.push('Полное наименование')
    }
    if (!short_name) {
        description.push('Краткое наименование')
    }

    if (description.length) {
        description.unshift('Ошибка','Заполнены не все поля:');
        return createDialogWindow(status='error', description=description);
    }
    //Записываем данные в БД
    fetch('/save_new_partner', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'full_name': full_name,
            'short_name': short_name,

        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {

                var newState = new Option(full_name, data.id, true, true);
                $('#ctr_card_partner').append(newState).trigger('change');
                isEditContract();
                return createDialogWindow(status='success', description=['Контрагент сохранен'], func=[['click', [removeDialog, 'logInfo1']]]);
            }
            else {
                let description = data.description;
                description.unshift('Ошибка, не удалось добавить контрагента');
                return createDialogWindow(status='error', description=description);
            }
        })
    return;
}

function closeNewPartnerDialog() {
    let new_partner_full_name_input = document.getElementById('new_partner_full_name_input');
    let new_partner_short_name_input = document.getElementById('new_partner_short_name_input');

    let full_name = new_partner_full_name_input.value;
    let short_name = new_partner_short_name_input.value;

    if (full_name || short_name) {
        return createDialogWindow(status='error', description=['Закрыть окно и отменить сохранение контрагента?'], func=[['click', [removeDialog, 'logInfo1']]]);
    }
    else {
        return removeDialog('logInfo1');
    }

}

function removeDialog(id=false) {
    if (id) {
        var element = document.getElementById(id);
        if (element) {
            element.parentNode.removeChild(element);
        }
    }
}

function showDeleteContractDialogWindow() {
    //Проверка, что нажали кнопку не с листа создания нового договора
    if (document.URL.split('/contract-list/card/new/').length > 1) {
        return false;
    }
    return createDialogWindow(status='info',
        description=['Подтвердите удаление договора'],
        func=[['click', [deleteContract, '']]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ',

                },
            ]

        );
    ;
}

function deleteContract() {
    //Проверка, что нажали кнопку не с листа создания нового договора
    if (document.URL.split('/contract-list/card/new/').length > 1) {
        return false;
    }

    var contract_id = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    fetch('/delete_contract', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'contract_id': contract_id,
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                return window.location.href = `/objects/${data.link}/contract-list`;
            }
            else {
                let description = data.description;
                description.unshift('Ошибка');
                return createDialogWindow(status='error2', description=description);
            }
        })
    return;
}

function changeContractVatLabel() {
    createDialogWindow(status='info',
        description=['Подтвердите изменение типа НДС'],
        func=[
            ['click', [changeVatInCard, '']]],
            buttons=[
                {
                    id:'flash_cancel_button',
                    innerHTML:'ОТМЕНИТЬ'
                },
            ]
        );
}

function rubToFloat(cost=0, value_type='₽') {
    return parseFloat(cost.replaceAll(' ', '').replaceAll(' ', '').replace(value_type, '').replace(",", "."));
}

function changeVatInCard(vat_status=null) {
    isEditContract();

    let cost_value = document.getElementById('ctr_card_cost').value;
    cost_value = rubToFloat(cost_value);

    let ctr_card_contract_full_vat_label = document.getElementById('ctr_card_contract_full_vat_label');
    let ctr_card_contract_vat_label = document.getElementById('ctr_card_contract_vat_label');

    vat_status = !vat_status? ctr_card_contract_vat_label.innerText:vat_status;

    let checkbox_time_tracking = document.getElementsByClassName('checkbox_time_tracking');
    let tow_cost = document.getElementsByClassName('tow_cost')

    let un_cost = document.getElementById('div_above_qqqq_undistributed_cost');
    let un_cost_value = un_cost.dataset.undistributed_cost;
    let all_tow_cost = 0;

    if (vat_status == 'БЕЗ НДС') {
        ctr_card_contract_full_vat_label.dataset.vat = 1.2;
        ctr_card_contract_full_vat_label.className = "ctr_card_contract_vat_positive";
        ctr_card_contract_full_vat_label.innerText = "С НДС";
        ctr_card_contract_vat_label.dataset.vat = 1.2;
        ctr_card_contract_vat_label.className = "ctr_card_contract_vat_positive";
        ctr_card_contract_vat_label.innerText = "С НДС";
    }
    else {
        ctr_card_contract_full_vat_label.dataset.vat = 1.0;
        ctr_card_contract_full_vat_label.className = "ctr_card_contract_vat_negative";
        ctr_card_contract_full_vat_label.innerText = "БЕЗ НДС";
        ctr_card_contract_vat_label.dataset.vat = 1.0;
        ctr_card_contract_vat_label.className = "ctr_card_contract_vat_negative";
        ctr_card_contract_vat_label.innerText = "БЕЗ НДС";
    }

    for (let i=0; i<checkbox_time_tracking.length; i++) {
        if (checkbox_time_tracking[i].checked) {
            all_tow_cost += rubToFloat(tow_cost[i].value);
            tow_cost[i].dataset.value = rubToFloat(tow_cost[i].value);
        }
    }

    un_cost_value = cost_value - all_tow_cost;
    un_cost.dataset.undistributed_cost = un_cost_value.toFixed(2) * 1.00;
    un_cost.dataset.contract_cost = cost_value.toFixed(2) * 1.00;
    un_cost_value = un_cost_value? un_cost_value.toLocaleString() + ' ₽':'0 ₽';
    un_cost.textContent = un_cost_value;
}