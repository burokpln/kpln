function shiftTow(button, route) {
    var row = button.closest('tr');
    var className = row.className;
    var cur_lvl = parseInt(className.split('lvl-')[1])
    var newRow = row.cloneNode(true);
    var columns = row.cells.length;
    var rowNumber = row.rowIndex;
    var currentRow = button.closest('tr');
    var preRow = row.previousElementSibling;
    var nextRow = row.nextElementSibling;
    var taskRow = row.nextElementSibling;
    var pre_lvl = preRow? parseInt(preRow.className.split('lvl-')[1]):0;
    var p_id = -1;
    if  (!['Left', 'Right', 'Up', 'Down'].includes(route) || (cur_lvl <= 0 && route == 'Left')|| (cur_lvl >= 9 && route == 'Right')) {
        return createDialogWindow(status='error', description=['Ошибка', 'Направление смещения видов работ указанно неверно']);
    }

   // Список создаваемых строк
    var children_list = []

    var tow_lvl = nextRow? parseInt(nextRow.className.split('lvl-')[1]):'';

    //Проверка, на нарушения предельного сдвига вправо/влево
    while (nextRow && tow_lvl > cur_lvl) {
        tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
        // Ищем всех детей (те, чей лвл вложенности выше)
        if (tow_lvl > cur_lvl) {
            if (route == 'Right') {
                if (tow_lvl+1 > 10) {
                    return createDialogWindow(status='error', description=['Ошибка', 'Превышена максимальная глубина вложенности']);
                }
            }
            if (route == 'Left') {
                if (tow_lvl < 0) {
                    return createDialogWindow(status='error', description=['Ошибка', 'Уровень вложенности не может быть меньше 1']);
                }
            }
            nextRow = nextRow.nextElementSibling;
        }
    }

    var nextRow = row.nextElementSibling;
    var tow_lvl = nextRow? parseInt(nextRow.className.split('lvl-')[1]):'';

    while (nextRow && tow_lvl > cur_lvl) {
        tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
        // Ищем всех детей (те, чей лвл вложенности выше)
        if (tow_lvl > cur_lvl) {
            if (route == 'Right') {
                nextRow.className = 'lvl-' + (tow_lvl+1)
            }
            if (route == 'Left') {
                nextRow.className = 'lvl-' + (tow_lvl-1)
            }

            var child = nextRow

            children_list.push(child)
            nextRow = nextRow.nextElementSibling;
        }
    }

    if (route == 'Right') {
        newRow.className = 'lvl-' + (cur_lvl)
        row.className = 'lvl-' + (cur_lvl+1)
        newRow.id = proj_url + '_' + route + '_' + new Date().getTime()
        for (var i=0; i<newRow.getElementsByTagName('td').length; i++) {
            var tagN = newRow.getElementsByTagName('td')[i].children;
            for (var i1=0; i1<tagN.length; i1++) {
                if (tagN[i1].tagName == 'INPUT') {
                    tagN[i1].value = '';
                }
            }
        }
        // Очищаем все поля в новой строке
        if (newRow) {
            clearDataAttributeValue(newRow);
            var textInputs = newRow.querySelectorAll('input[type="text"]');
            // Loop through each text input and clear its value
            textInputs.forEach(function (input) {
                input.value = '';
            });
            // Find the checkbox within the selected row and uncheck it
            var checkbox = newRow.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = false;
            }
        }
        row.parentNode.insertBefore(newRow, row);
        // Добавляем функции в ячейки
        addButtonsForNewRow(newRow);

        preRow = newRow.previousElementSibling? newRow.previousElementSibling: row;
        pre_lvl = preRow? parseInt(preRow.className.split('lvl-')[1]):cur_lvl;
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        UserChangesLog(c_id=newRow.id, rt='New', u_p_id=p_id, c_row=newRow);
        UserChangesLog(c_id=row.id, rt=route, u_p_id=newRow.id, c_row=row);

        // Если страница договора, то вызываем функцию редактирования для карточки договора
        if (document.URL.split('/contract-list/card/').length > 1) {
            setNewRowContractFunc(newRow);
            isEditContract();
            return;
        }
        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow();
        }
        return;
    }

    else if (route == 'Up') {
        while (preRow) {
            var tow_lvl = parseInt(preRow.className.split('lvl-')[1])
            prePreRow = preRow.previousElementSibling;
            if (prePreRow) {
                var pre_lvl = parseInt(prePreRow.className.split('lvl-')[1]);
            }
            else if (tow_lvl != cur_lvl && !prePreRow) {
                return createDialogWindow(status='error', description=['Ошибка', 'Перемещение невозможно', 'В структуре выше нет подходящего по уровню вида работ']);
            }

            if (tow_lvl == cur_lvl || (tow_lvl < cur_lvl && pre_lvl == cur_lvl) || pre_lvl+1 == cur_lvl) {
                row.parentNode.insertBefore(row, preRow);

                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=prePreRow);

                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.insertBefore(tow, preRow);
                    }
                }

                // Если страница договора, то вызываем функцию редактирования для карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    isEditContract();
                    return;
                }
                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow();
                }
                return;
            }
            preRow = preRow.previousElementSibling;
        }
        return createDialogWindow(status='error', description=['Ошибка', '✨ Перемещение невозможно. Выше только звёзды 🌌']);
    }
    else if (['Down', 'Left'].includes(route)) {
        var extra_row = 1; //Дополнительная строка, для кнопки "вниз" - это плюс один. Иначе нуль

        if (route == 'Left') {
            //newRow.className = row.className;
            row.className = 'lvl-' + (cur_lvl-1);
            cur_lvl = cur_lvl-1;
            extra_row = 0;
            if (!nextRow) {
                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow, route_fP=route);
                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);

                // Если страница договора, то вызываем функцию редактирования для карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    isEditContract();
                    return;
                }
                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow();
                }
                return;
            }
        }

        while (nextRow) {

            var tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
            nextNextRow = nextRow.nextElementSibling;

            if (nextNextRow) {
                var next_lvl = parseInt(nextNextRow.className.split('lvl-')[1])
            }
            else if (!nextNextRow &&  cur_lvl > tow_lvl + extra_row) {
                return createDialogWindow(status='error', description=['Ошибка', 'Перемещение невозможно', 'В структуре ниже нет подходящего по уровню вида работ']);
            }
            var row_after = nextRow;

            ver1 = 0;
            ver2 = 0;
            ver3 = 0;
            // Уровень текущей строки (tow) РАВЕН нажатой строки и номер текущей строки не равен нажатой + размер всех детей
            if (tow_lvl == cur_lvl && row.rowIndex + children_list.length + extra_row != nextRow.rowIndex) {
                row_after = nextRow;
                ver1 = 1;
            }
            else if (tow_lvl >= cur_lvl && cur_lvl > next_lvl) {
                // Уровень текущей строки (tow) БОЛЬШЕ нажатой строки и уровень нажатой строки БОЛЬШЕ следующей
                row_after = nextNextRow;
                ver2 = 1;
            }
            else if (cur_lvl == tow_lvl + 1) {
                // В противном случае, если текущая строка на уровень меньше нажатой строки
                row_after = route == 'Left'? nextRow:nextNextRow;
                ver3 = 1;
            }

            if (ver1 || ver2 || ver3) {
                row.parentNode.insertBefore(row, row_after);
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.insertBefore(tow, row_after);
                    }
                }

                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow, route_fP=route);

                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);
                UserChangesLog(c_id=preRow.id, rt=route, u_p_id=p_id, c_row=preRow);

                // Если страница договора, то вызываем функцию редактирования для карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    isEditContract();
                    return;
                }
                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow();
                }
                return;
            }
            else if (!nextNextRow && (tow_lvl >= cur_lvl || cur_lvl == tow_lvl + 1)) {
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.appendChild(tow);
                    }
                    row.parentNode.insertBefore(row, children_list[0]);
                    // Добавляем функции в ячейки
//                    addButtonsForNewRow(row);
                }
                else {
                    row.parentNode.appendChild(row);
                }
                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow, route_fP=route);

                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);

                // Если страница договора, то вызываем функцию редактирования для карточки договора
                if (document.URL.split('/contract-list/card/').length > 1) {
                    isEditContract();
                    return;
                }
                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow();
                }
                return;
            }

            nextRow = nextRow.nextElementSibling;
        }
        return createDialogWindow(status='error', description=['Ошибка', '🐋 Перемещение невозможно. Вы в самом низу структуры 🤿']);
    }
}

function findParent(curRow_fP, cur_lvl_fP, pre_lvl_fP, preRow_fP, route_fP=1) {
    var p_id = -1;
    if (curRow_fP.className=='lvl-0') {
        p_id = '';
        return p_id;
    }
    else {
        if (cur_lvl_fP-1 == pre_lvl_fP) {
            p_id = preRow_fP.id;
        }
        else {
            while (cur_lvl_fP-1 != pre_lvl_fP && preRow_fP) {
                var pre_lvl_fP = parseInt(preRow_fP.className.split('lvl-')[1]);
                if (!preRow_fP.previousElementSibling) {
                    return preRow_fP.id
                }
                preRow_fP = preRow_fP.previousElementSibling;
            }
            p_id = preRow_fP.nextElementSibling.id;
        }
    }
    if (p_id == -1) {
    }
    return p_id
}

function UserChangesLog(c_id, rt, u_p_id, c_row=false, change_lvl=false) {
        if (!highestRow.length) {
            highestRow = [c_row.rowIndex, c_row.id];
        }
        else {
            if (c_row.rowIndex < highestRow[0]) {
                highestRow = [c_row.rowIndex, c_row.id];
            }
        }
        userChanges[c_id] = {parent_id: u_p_id};

        if (['Before', 'After', 'New'].includes(rt)) {
            newRowList.add(c_id);
        }
}

function editTow() {
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

    var input_tow_name = tab_tr0.querySelectorAll(".input_tow_name");
    var div_tow_button = tab_tr0.querySelectorAll(".div_tow_button");
    var select_tow_dept = tab_tr0.querySelectorAll(".select_tow_dept");
    var checkbox_time_tracking = tab_tr0.querySelectorAll(".checkbox_time_tracking");
    for (var inp of input_tow_name) {
        inp.readOnly = 0;
    }
    for (var dtb of div_tow_button) {
        dtb.hidden = 0;
    }
    for (var sel of select_tow_dept) {
        sel.disabled = 0;
    }
    for (var che of checkbox_time_tracking) {
        che.disabled = 0;
    }
}

function editDescription(button, type='', editDescription_row=false) {
    if (!editDescription_row) {
        var editDescription_row = button.closest('tr');
    }
    else {

    }
    var row_id = editDescription_row.id;

    var elem = editDescription_row.querySelectorAll('.'+type)[0];

    var elem_value = null;
    var first_value = null;
    if (elem.type == 'select-one') {
        if (elem.disabled) {
            return
        }
        elem_value = elem.options[elem.selectedIndex].text;
        first_value = elem_value;
    }
    else if (elem.type == 'checkbox') {
        if (elem.disabled) {
            return
        }
        elem_value = elem.checked;
        //first_value = elem_value? !elem_value:elem_value;
        first_value = 3;
    }
    else {
        if (elem.readOnly) {
            return
        }
        elem_value = elem.value;
        first_value = null;
    }
    //Если параметр tow ещё не внесен, записываем в массив исходное значение [0] и текущее значение[1]
    if (!editDescrRowList[row_id]) {
        editDescrRowList[row_id] = {}
    }
    if (!editDescrRowList[row_id][type]) {
        editDescrRowList[row_id][type] = [first_value, elem_value]
    }
    else if (editDescrRowList[row_id][type][1] != elem_value) {
        editDescrRowList[row_id][type][1] = elem_value
    }
}

function saveTowChanges() {
    deletedRowList.forEach(deletedRowList_row => {
        if (userChanges[deletedRowList_row]) {
            delete userChanges[deletedRowList_row];
        }
        if (editDescrRowList[deletedRowList_row]) {
            delete editDescrRowList[deletedRowList_row];
        }
        if (newRowList.has(deletedRowList_row)) {
            newRowList.delete(deletedRowList_row);
            deletedRowList.delete(deletedRowList_row);
        }
    });


    var edit_btn = document.getElementById("edit_btn");
    var save_btn = document.getElementById("save_btn");
    var cancel_btn = document.getElementById("cancel_btn");
    if (edit_btn.hidden) {
        edit_btn.hidden = 0;
        save_btn.hidden = 1;
        cancel_btn.hidden = 1;
    }
    else {
        edit_btn.hidden = 1;
        save_btn.hidden = 0;
        cancel_btn.hidden = 0;
    }
    const tab = document.getElementById("towTable");

    //////////////////////////////////////////////////////////////////////////////////////////////
    // Ищем номер строки

    for (const [k, v] of Object.entries(userChanges)) {
        var userChanges_x = tab.querySelector(`[id='${k}']`);
        userChanges[k]['lvl'] = userChanges_x.rowIndex;
    }
    var div_tow_first_row = tab.getElementsByTagName('tbody')[0].getElementsByTagName('tr')[0].className;
    if (highestRow.length && div_tow_first_row != 'div_tow_first_row') {
        var row_highestRow = tab.querySelector(`[id='${highestRow[1]}']`);
        userChanges[row_highestRow.id]['lvl'] = row_highestRow.rowIndex;

        var newRow_highestRow = row_highestRow.nextElementSibling;

        while (newRow_highestRow) {
            if (!userChanges[newRow_highestRow.id]) {
                userChanges[newRow_highestRow.id] = {lvl: newRow_highestRow.rowIndex};
            }
            newRow_highestRow = newRow_highestRow.nextElementSibling;
        }
    }

    //////////////////////////////////////////////////////////////////////////////////////////////
    // Проверяем, есть ли изменения по отношению к изначальным данным, если нет, удаляем запись
    for (const [k, v] of Object.entries(editDescrRowList)) {
        // Проходим в tow по каждому изменяемому ключу
        for (const [k2, v2] of Object.entries(v)) {
            // Ищем tow на странице, берем данные проверяемого ключа k2 (это класс изменяемой ячейки)
            //var elem = tab.querySelector("#"+k.toString()).querySelector("."+k2);
            var elem = tab.querySelector(`[id='${k}']`).querySelector("."+k2);

            var elem_value = null;
            if (elem.type == 'select-one') {
                elem_value = elem.options[elem.selectedIndex].value;
            }
            else if (elem.type == 'checkbox') {
                elem_value = elem.checked;
            }
            else {
                elem_value = elem.value;
            }

            // Текущее значение равно изначальному, удаляем ключ k2
            if (elem_value == v2[0]) {
                delete editDescrRowList[k][k2];
            }
            else {
                editDescrRowList[k][k2] = elem_value;
            }
            // если у изменённый tow остался без ключей, удаляем tow из массива
            if (!Object.keys(editDescrRowList[k]).length) {
                delete editDescrRowList[k];
            }
        }
    }


    if (Object.keys(userChanges).length || Object.keys(editDescrRowList).length || newRowList.size || deletedRowList.size) {

        list_newRowList = [];
        newRowList.forEach(newRowList_row => {
            list_newRowList.push(newRowList_row);
        });

        list_deletedRowList = [];
        deletedRowList.forEach(newRowList_row => {
            list_deletedRowList.push(newRowList_row);
        });

        console.log('       userChanges')
        console.log(userChanges)
        console.log('___________________')
        console.log('       editDescrRowList')
        console.log(editDescrRowList)
        console.log('___________________')
        console.log('       list_newRowList')
        console.log(list_newRowList)
        console.log('___________________')
        console.log('       list_deletedRowList')
        console.log(list_deletedRowList)
        console.log('___________________')

        var page_url = null;

        //        var sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

        if (document.URL.split('/objects/').length > 1) {
            page_url = decodeURIComponent(document.URL.substring(document.URL.lastIndexOf('/objects')+9, document.URL.lastIndexOf('/')));
            fetch(`/save_tow_changes/${page_url}`, {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'userChanges': userChanges,
                    'editDescrRowList': editDescrRowList,
                    'list_newRowList': list_newRowList,
                    'list_deletedRowList': list_deletedRowList,

                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                    //                        (async () => {
                    //                            createDialogWindow(status='success', description=['Изменения сохранены']);
                    //                            await sleep(2000);
                                                return location.reload();
                    //                        })();
                    }
                    else {
                        let description = data.description;
                        description.unshift('Ошибка');
                        return createDialogWindow(status='error', description=description);
                    }
                })
            return;
        }
        else if (document.URL.split('/contract-list/card/').length > 1) {
            contract_id = document.URL.split('/contract-list/card/')[1];
            var save_contract = saveContract();
            if (save_contract[0] == 'error') {
                return createDialogWindow(status='error', description=save_contract[1]);
            }
            fetch(`/save_contract/${contract_id}`, {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'userChanges': userChanges,
                    'editDescrRowList': editDescrRowList,
                    'list_newRowList': list_newRowList,
                    'list_deletedRowList': list_deletedRowList,
                    'ctr_card': save_contract['ctr_card'],
                    'list_towList': save_contract['list_towList'],
                })
            })
                .then(response => response.json())
                .then(data => {

                    if (data.status === 'success') {
                            //                        (async () => {
                            //                            createDialogWindow(status='success', description=['Изменения сохранены']);
                            //                            console.log('success 2');
                            //                            await sleep(2000);
                            //                            console.log('success22 3');
                            //                        })
                        if (data.contract_id) {
                            return window.location.href = `/contract-list/card/${data.contract_id}`;
                        }
                        else {
                            return location.reload();
                        }


                            //                        if (data.contract_id) {
                            //                            (async () => {
                            //                                createDialogWindow(status='success', description=['Изменения сохранены']);
                            //                                await sleep(2 000);
                            //                                return window.location.href = `/contract-list/card/${data.contract_id}`;
                            //
                            //                        }
                            //
                            //                        createDialogWindow(status='success', description=['Изменения сохранены']);
                            //                        await sleep(2 000);
                            //                        return location.reload();
                    }
                    else {
                        console.log(data)
                        let description = data.description;
                        description.unshift('Ошибка');
                        return createDialogWindow(status='error', description=description);
                    }
                })
        }
    }
    else {
        if (document.URL.split('/objects/').length > 1) {
                //            location.reload();
            return createDialogWindow(status='error', description=['Ошибка', 'Изменений не обнаружено']);
        }
        else if (document.URL.split('/contract-list/card/').length > 1) {
            contract_id = document.URL.split('/contract-list/card/')[1];
            var save_contract = saveContract();
            console.log('2   save_contract', save_contract)
            if (save_contract[0] == 'error') {

                return createDialogWindow(status='error', description=save_contract[1]);
            }
            fetch(`/save_contract/${contract_id}`, {
                "headers": {
                    'Content-Type': 'application/json'
                },
                "method": "POST",
                "body": JSON.stringify({
                    'userChanges': null,
                    'editDescrRowList': null,
                    'list_newRowList': null,
                    'list_deletedRowList': null,
                    'ctr_card': save_contract['ctr_card'],
                    'list_towList': save_contract['list_towList'],
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        //                        (async () => {
                        //                            createDialogWindow(status='success', description=['Изменения сохранены']);
                        //                            await sleep(2000);
                        //                            if (data.contract_id) {
                        //                                return window.location.href = `/contract-list/card/${data.contract_id}`;
                        //                            }
                        //                            else {
                        //                                return location.reload();
                        //                            }
                        //                        })
                        if (data.without_change) {
                            return createDialogWindow(status='info', description=data.description);
                        }
                        if (data.contract_id) {
                            return window.location.href = `/contract-list/card/${data.contract_id}`;
                        }
                        else {
                            return location.reload();
                        }



                        //                        if (data.contract_id) {
                        //                            createDialogWindow(status='success', description=['Изменения сохранены'])
                        //                            await sleep(2 000);
                        //                            return window.location.href = `/contract-list/card/${data.contract_id}`;
                        //                        }
                        //                        createDialogWindow(status='success', description=['Изменения сохранены'])
                        //                        await sleep(2 000);
                        //                        return location.reload();

                        //                        return ;
                    }
                    else {
                        let description = data.description;
                        description.unshift('Ошибка');
                        return createDialogWindow(status='error', description=description);
                    }
                })
        }
    }
}

function cancelTowChanges() {
    window.location.href = document.URL;
    return createDialogWindow(status='error', description=['Изменения отменены, страница обновлена']);
}

function createDialogWindow(status='error', description='', func=false, buttons=false) {
    let dialog = document.createElement("dialog");
    dialog.classList.add("window", status);
    dialog.id = "logInfo";

    let desc = ''
    for (let i of description) {
        desc += i + '<br>';
    }

    let div_flash = document.createElement("div");
    div_flash.innerHTML = desc;

    dialog.appendChild(div_flash);

    let ok_button = document.createElement("button");
    ok_button.id = "flash_ok_button";
    ok_button.innerHTML = 'ОК';
    ok_button.addEventListener('click', function() {
        removeLogInfo();
    });
    if (func) {
        for (let i of func) {
            ok_button.addEventListener(i[0], function() {
                i[1][0](i[1][1]);
            });
        }
    }
    dialog.appendChild(ok_button);

    if (buttons) {
        for (b of buttons)
            button_i = document.createElement("button");
            button_i.id = b.id;
            button_i.innerHTML = b.innerHTML;
            button_i.addEventListener('click', function() {
                removeLogInfo();
            });
            if (b.func) {
                for (let i of b.func) {
                    button_i.addEventListener(i[0], function() {
                        i[1][0](i[1][1]);
                    });
                }
            }
            dialog.appendChild(button_i);
    }


    document.body.appendChild(dialog)

    dialog.showModal();
}

function clearDataAttributeValue(tow_cdav) {
    console.log('   clearDataAttributeValue')
    let tow_cdav_dataset_value = tow_cdav.querySelectorAll("[data-value]");

    tow_cdav_dataset_value.forEach(function (input) {
        if (input.dataset.value) {
            input.dataset.value = null;
        }

    });

}