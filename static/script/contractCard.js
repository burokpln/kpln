$(document).ready(function() {
    document.getElementById('edit_btn')? document.getElementById('edit_btn').addEventListener('click', function() {editContract();}):'';
    document.getElementById('save_btn')? document.getElementById('save_btn').addEventListener('click', function() {saveContract();}):'';
    document.getElementById('cancel_btn')? document.getElementById('cancel_btn').addEventListener('click', function() {cancelContractChanges();}):'';

    document.getElementById('ctr_card_full_obj')? document.getElementById('ctr_card_full_obj').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_full_contract_number')? document.getElementById('ctr_card_full_contract_number').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_full_status_name')? document.getElementById('ctr_card_full_status_name').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_full_cost')? document.getElementById('ctr_card_full_cost').addEventListener('focusin', function() {convertCost(this, 'in');}):'';
    document.getElementById('ctr_card_full_cost')? document.getElementById('ctr_card_full_cost').addEventListener('focusout', function() {convertCost(this, 'out');}):'';
    document.getElementById('ctr_card_contract_full_vat_label')? document.getElementById('ctr_card_contract_full_vat_label').addEventListener('click', function() {foo();}):'';
    document.getElementById('ctr_card_contract_full_prolongation_label')? document.getElementById('ctr_card_contract_full_prolongation_label').addEventListener('click', function() {foo2();}):'';
    document.getElementById('ctr_card_date_start')? document.getElementById('ctr_card_date_start').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('ctr_card_date_start')? document.getElementById('ctr_card_date_start').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('ctr_card_date_finish')? document.getElementById('ctr_card_date_finish').addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');}):'';
    document.getElementById('ctr_card_date_finish')? document.getElementById('ctr_card_date_finish').addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');}):'';
    document.getElementById('id_ctr_card_attach_file')? document.getElementById('id_ctr_card_attach_file').addEventListener('click', function() {editFullNameUserCard();}):'';
    document.getElementById('id_ctr_card_add_reserve')? document.getElementById('id_ctr_card_add_reserve').addEventListener('click', function() {editFullNameUserCard();}):'';
    document.getElementById('id_ctr_hide_full_card_info_button')? document.getElementById('id_ctr_hide_full_card_info_button').addEventListener('click', function() {hideFullCardInfo();}):'';
    document.getElementById('ctr_card_obj')? document.getElementById('ctr_card_obj').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_contract_number')? document.getElementById('ctr_card_contract_number').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_status_name')? document.getElementById('ctr_card_status_name').addEventListener('change', function() {editContractCardData(this);}):'';
    document.getElementById('ctr_card_cost')? document.getElementById('ctr_card_cost').addEventListener('focusin', function() {convertCost(this, 'in');}):'';
    document.getElementById('ctr_card_cost')? document.getElementById('ctr_card_cost').addEventListener('focusout', function() {convertCost(this, 'out');}):'';
    document.getElementById('ctr_card_contract_vat_label')? document.getElementById('ctr_card_contract_vat_label').addEventListener('click', function() {foo();}):'';
    document.getElementById('ctr_card_contract_prolongation_label')? document.getElementById('ctr_card_contract_prolongation_label').addEventListener('click', function() {foo2();}):'';
    document.getElementById('id_ctr_card_attach_file_button')? document.getElementById('id_ctr_card_attach_file_button').addEventListener('click', function() {showFullCardInfo();}):'';
    document.getElementById('id_ctr_card_multiselect_on')? document.getElementById('id_ctr_card_multiselect_on').addEventListener('click', function() {setMultiselectFillOn(this);}):'';
    document.getElementById('id_ctr_card_columns_settings')? document.getElementById('id_ctr_card_columns_settings').addEventListener('click', function() {hideFullCardInfo();}):'';
    document.getElementById('id_ctr_card_focus_in')? document.getElementById('id_ctr_card_focus_in').addEventListener('click', function() {hideFullCardInfo();}):'';

    let tow_cost = document.getElementsByClassName('tow_cost');
    for (let i of tow_cost) {
        i.addEventListener('change', function() {undistributedCost(this);})
    }
    let checkbox_time_tracking = document.getElementsByClassName('checkbox_time_tracking');
    for (let i of checkbox_time_tracking) {
        i.addEventListener('click', function() {selectContractTow(this);})
    }
    let tow_cost_percent = document.getElementsByClassName('tow_cost_percent');
    for (let i of tow_cost_percent) {
        i.addEventListener('change', function() {undistributedCost(this, percent='percent');})
    }

    let tow_date_start = document.getElementsByClassName('tow_date_start');
    for (let i of tow_date_start) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout'); });
    }

    let tow_date_finish = document.getElementsByClassName('tow_date_finish');
    for (let i of tow_date_finish) {
        i.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin'); });
        i.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout'); });
    }


});

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
    fullCardInfoButton.hidden = true;
    fullCardInfo.hidden = true;
    miniCardInfo.hidden = false;
}

function showFullCardInfo() {
    var fullCardInfo = document.getElementById('ctr_full_card_div');
    var fullCardInfoButton = document.getElementById('ctr_hide_full_card_info');
    var miniCardInfo = document.getElementById('ctr_mini_card_div');
    fullCardInfoButton.hidden = false;
    fullCardInfo.hidden = false;
    miniCardInfo.hidden = true;
}

function getContractCard(button) {
    var td_0 = button.closest('tr').getElementsByTagName("td")[0];
    var contract_id = td_0.dataset.sort;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    window.open(`/contracts-list/card/${contract_id}`, '_blank');
};

function selectContractTow(check_box) {
    editContract();
    //Проверяем даты вида работ
    if (check_box.checked) {
        //Даты вида работ
        var date_start = check_box.closest('tr').getElementsByClassName("tow_date_start")[0];
        var date_finish = check_box.closest('tr').getElementsByClassName("tow_date_finish")[0];
        //Даты из договора
        var contract_date_start = document.getElementById('ctr_card_date_start').value;
        var contract_date_finish = document.getElementById('ctr_card_date_finish').value;

        console.log('date_start:', date_start.value, new Date(convertDate(date_start.value)), typeof convertDate(date_start.value), 'date_finish:', date_finish.value)
        console.log('contract_date_start:', contract_date_start, new Date(convertDate(contract_date_start)), typeof convertDate(contract_date_start), 'contract_date_finish:', contract_date_finish)
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
            return;
        }
        //Проверяем, есть ли нераспределенные средства, если нет - завершаем
        var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
        var undistributed_cost = undistributed.dataset.undistributed_cost;
        var undistributed_cost_float = parseFloat(undistributed_cost);
        if (undistributed_cost_float < 0) {
            console.log('1Нет нераспределенных ДС. Нельзя увеличить сумму вида работ');
            return alert('1Нет нераспределенных ДС. Нельзя увеличить сумму вида работ')
        }

        //Стоимость и процент родителя
        var tow_cost = check_box.closest('tr').getElementsByClassName("tow_cost")[0];
        tow_cost = parseFloat(tow_cost.dataset.value);
        tow_cost = isNaN(tow_cost)? 0:tow_cost;
        console.log(tow_cost)
        var cell_tow_cost_percent = check_box.closest('tr').getElementsByClassName("tow_cost_percent")[0];
        var tow_cost_percent = parseFloat(cell_tow_cost_percent.dataset.value);
        tow_cost_percent = isNaN(tow_cost_percent)? 0:tow_cost_percent;
        //Общая стоимость договора
        var contract_cost = document.getElementById('ctr_card_full_cost').value;
        contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
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
        console.log('             tow_cnt', tow_cnt)
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
        while (nextRow && tow_lvl > cur_lvl) {
            tow_lvl = parseInt(nextRow.className.split('lvl-')[1]);
            tow_id = nextRow.id;

            if (tow_lvl > cur_lvl) {
                tow_cnt = nextRow.dataset.tow_cnt;
                console.log('             tow_cnt2', tow_cnt)

                tow_cost = cost_list[tow_lvl];
                tow_cost_percent = percent_list[tow_lvl];

                cost_per_child = tow_cnt? (tow_cost / tow_cnt):0;
                percent_per_child = tow_cnt? (tow_cost_percent / tow_cnt):0;
                cost_list[tow_lvl+1] = cost_per_child;
                percent_list[tow_lvl+1] = percent_per_child;

                tows_array = Object.assign({tow_id: {lvl:tow_lvl, tow_cnt:0}}, tows_array);
                if (!nextRow.getElementsByClassName("checkbox_time_tracking")[0].disabled) {
                    console.log('cost_list', cost_list)
                    console.log('         percent_list', percent_list)
                    nextRow.getElementsByClassName("checkbox_time_tracking")[0].checked = new_status;
                    nextRow.getElementsByClassName("tow_cost_percent")[0].value = percent_list[tow_lvl] + ' %'

                    undistributedCost(nextRow.getElementsByClassName("tow_cost_percent")[0], percent='percent');
                }

                nextRow = nextRow.nextElementSibling;
            }
        }
    }
    else {
        var tow_cost = check_box.closest('tr').getElementsByClassName("tow_cost")[0];
        undistributedCost(check_box, percent=false, input_cost=false, subtraction='true')
    }

}

function undistributedCost(cell, percent=false, input_cost=false, subtraction=false) {
    var dept_id = cell.closest('tr').getElementsByClassName("tow_dept")[0].value;
    if (!subtraction) {
        //Выбираем чекбокс привязывающий tow к договору
        cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0].checked = true;

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
        var cost1_float = parseFloat(cost1.replaceAll(' ', '').replaceAll(' ', '').replace(value_type, '').replace(",", "."));
        var cost2 = cell.dataset.value;
        var cost2_float = parseFloat(cost2);

        cost1_float = isNaN(cost1_float)? 0:cost1_float;
        cost2_float = isNaN(cost2_float)? 0:cost2_float;

        //Если не указан отдел, возвращаем всю сумму в стоимость договора и ставим нули у суммы
        if (input_cost===false && dept_id && !subtraction) {
            // Обновляем значение нераспределенных средств
            var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
            var undistributed_cost = undistributed.dataset.undistributed_cost;
            var undistributed_cost_float = parseFloat(undistributed_cost);

            undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;
            console.log('   1  undistributed_cost_float:', undistributed_cost_float)

            if (undistributed_cost_float < 0 && cost1_float >= cost2_float) {
                console.log('Нет нераспределенных ДС. нельзя увеличить сумму вида работ');
                alert('Нет нераспределенных ДС. нельзя увеличить сумму вида работ')
                //возвращаем прошлое значение из дата атрибута в value
                if (cost2_float) {
                    cost2_float = cost2_float.toFixed(2) * 1.00;
                    cost2_float = cost2_float.toLocaleString() + ` ${value_type}`;
                }
                else {
                    cost2_float = `0 ${value_type}`;
                }
                cell.value = cost2_float;
                return;
            }
        }

        //Если ячейка с процентом суммы, то пересчитываем и значение ячейки "сумма"
        if (percent) {
            //Сумма договора, если не указали вручную при вызове функции
            if (input_cost===false) {
                var contract_cost = document.getElementById('ctr_card_full_cost').value;
                contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
                contract_cost = isNaN(contract_cost)? 0:contract_cost;
            }
            else {
                var contract_cost = input_cost;
            }
            //Сумма tow
            var value_cell = cell.closest('tr').getElementsByClassName("tow_cost")[0];
            var value_cost1 = value_cell.value;
            var value_cost1_float = parseFloat(value_cost1.replaceAll(' ', '').replaceAll(' ', '').replace(value_type, '').replace(",", "."));
            var value_cost2 = value_cell.dataset.value;
            var value_cost2_float = parseFloat(value_cost2);
            value_cost1_float = isNaN(value_cost1_float)? 0:value_cost1_float;
            value_cost2_float = isNaN(value_cost2_float)? 0:value_cost2_float;

            tow_cost = contract_cost * cost1_float / 100;

            //Нераспределенный остаток
            console.log(`${undistributed_cost_float} - ${tow_cost} + ${value_cost2_float}`);
            if (dept_id) {
                undistributed_cost = undistributed_cost_float - tow_cost + value_cost2_float;
                if (undistributed_cost < 0) {
                    if (cost2_float) {
                        cost2_float = cost2_float.toFixed(2) * 1.00;
                        cost2_float = cost2_float.toLocaleString() + ` ${value_type}`;
                    }
                    else {
                        cost2_float = `0 ${value_type}`;
                    }
                    cell.value = cost2_float;
                    console.log('2Нет нераспределенных ДС. Нельзя увеличить сумму вида работ', undistributed_cost);
                    return alert('2Нет нераспределенных ДС. Нельзя увеличить сумму вида работ')
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
                    console.log('Нет нераспределенных ДС. Нельзя увеличить сумму вида работ');
                    return alert('Нет нераспределенных ДС. Нельзя увеличить сумму вида работ')
                }
            }
            //Пересчитываем "% суммы"
            var contract_cost = document.getElementById('ctr_card_full_cost').value;
            contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
            contract_cost = isNaN(contract_cost)? 0:contract_cost;
            var cell_tow_cost_percent = cell.closest('tr').getElementsByClassName("tow_cost_percent")[0];
            ctcp_value = cost1_float/contract_cost*100
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
            undistributed.dataset.undistributed_cost = undistributed_cost;
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
        selectContractTow(cell.closest('tr').getElementsByClassName("checkbox_time_tracking")[0]);
    }
    else {
        if (dept_id) {
            // Обновляем значение нераспределенных средств
            var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
            var undistributed_cost = undistributed.dataset.undistributed_cost;
            var undistributed_cost_float = parseFloat(undistributed_cost);

            undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;

            //Сумма договора, если не указали вручную при вызове функции
            if (input_cost === false) {
                var contract_cost = document.getElementById('ctr_card_full_cost').value;
                contract_cost = parseFloat(contract_cost.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
                contract_cost = isNaN(contract_cost)? 0:contract_cost;
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
            undistributed.dataset.undistributed_cost = undistributed_cost;

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
    console.log(val==select1, val==select2, $('#select2-ctr_card_full_status_name-container').text())

}


function editContractCardData(val) {

    var val_id = val.id;
    var val_value = val.value;
    console.log(val_id, val_value, val)
    if (val_id == 'ctr_card_full_contract_number' || val_id == 'ctr_card_contract_number') {
        document.getElementById('ctr_card_full_contract_number').value = val_value;
        document.getElementById('ctr_card_contract_number').value = val_value;
        console.log('contract_number:', val_value)
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
    }
    console.log(document.getElementById(val_id).value)


}

function convertCost(val, status) {
    var cost = val.value;
    if (status == 'in') {
        var cost_value = parseFloat(val.value.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));
        document.getElementById('ctr_card_cost').value = cost_value;
        document.getElementById('ctr_card_full_cost').value = cost_value;
    }
    else if (status == 'out') {
        var cost_value = parseFloat(cost);
        if (isNaN(cost_value)) {
            cost_value = 0;
        }

        // Обновляем значение нераспределенных средств
        var undistributed = document.getElementById('div_above_qqqq_undistributed_cost');
        var undistributed_cost = undistributed.dataset.undistributed_cost;
        var undistributed_cost_float = parseFloat(undistributed_cost);
        var last_contract_cost = undistributed.dataset.contract_cost;
        var last_contract_cost_float = parseFloat(last_contract_cost);

        undistributed_cost_float = isNaN(undistributed_cost_float)? 0:undistributed_cost_float;
        last_contract_cost_float = isNaN(last_contract_cost_float)? 0:last_contract_cost_float;

        console.log(undistributed_cost_float, last_contract_cost_float)

        undistributed_cost = undistributed_cost_float + cost_value - last_contract_cost_float
        var undistributed_cost_tc = undistributed_cost

        if (undistributed_cost_tc) {
            undistributed_cost_tc = undistributed_cost_tc.toFixed(2) * 1.00;
            undistributed_cost_tc = undistributed_cost_tc.toLocaleString() + ' ₽';
        }
        else {
            undistributed_cost_tc = '0 ₽'
        }
        undistributed.textContent = undistributed_cost_tc;
        undistributed.dataset.undistributed_cost = undistributed_cost;
        undistributed.dataset.contract_cost = cost_value;

        cost_value = cost_value.toFixed(2) * 1.00;
        cost_value = cost_value.toLocaleString();

        cost_value += ' ₽';

        document.getElementById('ctr_card_cost').value = cost_value;
        document.getElementById('ctr_card_full_cost').value = cost_value;
    }
}

function setMultiselectFillOn(button) {
    button.className = button.className=="ctr_card_multiselect_on"? "ctr_card_multiselect_off":"ctr_card_multiselect_on";
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
    }

    const tab = document.getElementById("towTable");
    var tab_tr0 = tab.getElementsByTagName('tbody')[0];
}

function saveContract() {
    var contract_id = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    //Карточка проекта
    var ctr_card_obj = document.getElementById('ctr_card_full_obj').value;
    var ctr_card_contract_number = document.getElementById('ctr_card_full_contract_number').value;
    var ctr_card_partner = document.getElementById('ctr_card_partner').value;
    var ctr_card_status_name = document.getElementById('ctr_card_full_status_name').value;
    var user_card_allow = document.getElementById('user_card_allow').checked;
    var ctr_card_contractor = document.getElementById('ctr_card_contractor').value;
    var ctr_card_fot_value = document.getElementById('ctr_card_fot_value').value;
    var ctr_card_contract_description = document.getElementById('ctr_card_contract_description').value;
    var ctr_card_cost = document.getElementById('ctr_card_full_cost').value;
    var ctr_card_contract_full_vat_label = document.getElementById('ctr_card_contract_full_vat_label').value;
    var ctr_card_contract_full_prolongation_label = document.getElementById('ctr_card_contract_full_prolongation_label').className.split('lvl-')[4];
    var ctr_card_date_start = document.getElementById('ctr_card_date_start').value;
    ctr_card_date_start = ctr_card_date_start? convertDate(ctr_card_date_start):null;
    var ctr_card_date_finish = document.getElementById('ctr_card_date_finish').value;
    ctr_card_date_finish = ctr_card_date_finish? convertDate(ctr_card_date_finish):null;

    const tab = document.getElementById("towTable");
    var tab_numRow = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    //Список tow
    list_towList = [];

    for (let i of tab_numRow) {
        let tow_checkBox = i.getElementsByClassName('checkbox_time_tracking')[0].checked;
        if (tow_checkBox) {
            let date_start = i.getElementsByClassName('tow_date_start')[0].value;
            let date_finish = i.getElementsByClassName('tow_date_finish')[0].value;
            date_start = date_start? convertDate(date_start):null;
            date_finish = date_finish? convertDate(date_finish):null;


            list_towList.push({
                id: i.id,
                cost: i.getElementsByClassName('tow_cost')[0].dataset.value,
                percent: i.getElementsByClassName('tow_cost_percent')[0].dataset.value,
                dept_id: i.getElementsByClassName('tow_dept')[0].dataset.value,
                date_start: date_start,
                date_finish: date_finish,
                type: i.dataset.value_type
            });
        }
    }
    console.log(contract_id)
    console.log(list_towList)

    var ctr_card = {
        object_id: ctr_card_obj,
        contract_number: ctr_card_contract_number,
        partner: ctr_card_partner,
        status: ctr_card_status_name,
        allow: user_card_allow,
        contractor: ctr_card_contractor,
        fot: ctr_card_fot_value,
        description: ctr_card_contract_description,
        cost: ctr_card_cost,
        vat: ctr_card_contract_full_vat_label,
        prolongation: ctr_card_contract_full_prolongation_label,
        date_start: ctr_card_date_start,
        date_finish: ctr_card_date_finish
    }
    console.log(ctr_card)



    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    fetch(`/save_contract/${contract_id}`, {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'ctr_card': ctr_card,
                'list_towList': list_towList

            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = `/contracts-list/card/${contract_id}`;
                    alert('Изменения сохранены')
                }
                else {
                    alert(data.description)
                }
            })

//    else {
//        alert('Изменений не обнаружено')
//        location.reload();
//    }
}

function cancelContractChanges() {
    window.location.href = document.URL;
    alert('Изменения отменены, страница обновлена')
}