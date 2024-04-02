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

    var row_val = row.getElementsByTagName('td')[2].getElementsByTagName('input')[0].value;

    if  (!['Left', 'Right', 'Up', 'Down'].includes(route) || (cur_lvl <= 0 && route == 'Left')|| (cur_lvl >= 9 && route == 'Right')) {
        alert('Направление смещения видов работ указанно неверно');
        return
    }

    // Удалить переменную, как всё будет готово
    var rowIndex = Array.from(currentRow.parentNode.children).indexOf(currentRow);


   // Список создаваемых строк
    var children_list = []

    var tow_lvl = nextRow? parseInt(nextRow.className.split('lvl-')[1]):'';

    //Проверка, на нарушения предельного сдвига вправо/влево
    while (nextRow && tow_lvl >
    ) {
        tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
        // Ищем всех детей (те, чей лвл вложенности выше)
        if (tow_lvl > cur_lvl) {
            if (route == 'Right') {
                if (tow_lvl+1 > 10) {
                    alert(`Превышена максимальная глубина вложенности - ${nextRow}`);
                    return
                }
            }
            if (route == 'Left') {
                if (tow_lvl < 0) {
                    alert(`Уровень вложенности не может быть меньше 1 - ${nextRow}`);
                    return
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
            // var child = nextRow.cloneNode(true)
            var child = nextRow
                //            if (['Left', 'Right'].includes(route)) {
                //                for (var i=0; i<child.getElementsByTagName('td').length; i++) {
                //                    var tagN = child.getElementsByTagName('td')[i].children;
                //                    for (var i1=0; i1<tagN.length; i1++) {
                //                        if (tagN[i1].tagName == 'INPUT') {
                //                            tagN[i1].value = '';
                //                        }
                //                    }
                //                }
                //            }
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

        preRow = newRow.previousElementSibling? newRow.previousElementSibling: row;
        pre_lvl = preRow? parseInt(preRow.className.split('lvl-')[1]):cur_lvl;
        p_id = findParent(curRow_fP=newRow, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow);

        UserChangesLog(c_id=newRow.id, rt='New', u_p_id=p_id, c_row=newRow);
        UserChangesLog(c_id=row.id, rt=route, u_p_id=newRow.id, c_row=row);

        var edit_btn = document.getElementById("edit_btn");
        if (!edit_btn.hidden) {
            editTow()
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
                alert('Перемещение невозможно. В структуре выше нет подходящего по уровню вида работ');
                return
            }
//            //Изменение lvl пройдённой строки
//            UserChangesLog(c_id=preRow.id, rt='change_lvl', u_p_id='-1', change_lvl=true);

            if (tow_lvl == cur_lvl || (tow_lvl < cur_lvl && pre_lvl == cur_lvl) || pre_lvl+1 == cur_lvl) {
                row.parentNode.insertBefore(row, preRow);

                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=prePreRow);

                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.insertBefore(tow, preRow);
                    }
                }

                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow()
                }

                return;
            }
            preRow = preRow.previousElementSibling;
        }
        alert('✨ Перемещение невозможно. Выше только звёзды 🌌');
        return
    }
    else if (['Down', 'Left'].includes(route)) {
        var extra_row = 1; //Дополнительная строка, для кнопки "вниз" - это плюс один. Иначе нуль

        if (route == 'Left') {
            newRow.className = row.className;
            row.className = 'lvl-' + (cur_lvl-1);
            cur_lvl = cur_lvl-1;
            extra_row = 0;
            if (!nextRow) {
                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow, route_fP=route);
                console.log('    route Left', preRow, p_id)
                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);

                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow()
                }
                return;
            }
        }

        while (nextRow) {
//            //Изменение lvl пройдённой строки
//            UserChangesLog(c_id=nextRow.id, rt='change_lvl', u_p_id='-1', change_lvl=true);

            var tow_lvl = parseInt(nextRow.className.split('lvl-')[1])
            nextNextRow = nextRow.nextElementSibling;

            if (nextNextRow) {
                var next_lvl = parseInt(nextNextRow.className.split('lvl-')[1])
            }
            else if (!nextNextRow &&  cur_lvl > tow_lvl + extra_row) {
                alert('Перемещение невозможно. В структуре ниже нет подходящего по уровню вида работ');
                return
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

                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow()
                }
                return;
            }
            else if (!nextNextRow && (tow_lvl >= cur_lvl || cur_lvl == tow_lvl + 1)) {
                if (children_list.length){
                    for (tow of children_list) {
                        row.parentNode.appendChild(tow);
                    }
                    row.parentNode.insertBefore(row, children_list[0]);
                }
                else {
                    row.parentNode.appendChild(row);
                }
                preRow = row.previousElementSibling;
                pre_lvl = parseInt(preRow.className.split('lvl-')[1]);
                p_id = findParent(curRow_fP=row, cur_lvl_fP=cur_lvl, pre_lvl_fP=pre_lvl, preRow_fP=preRow, route_fP=route);

                UserChangesLog(c_id=row.id, rt=route, u_p_id=p_id, c_row=row);

                var edit_btn = document.getElementById("edit_btn");
                if (!edit_btn.hidden) {
                    editTow()
                }
                return
            }

            nextRow = nextRow.nextElementSibling;
        }
        alert('🐋 Перемещение невозможно. Вы в самом низу структуры 🤿');
        return
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

//            //Изменение lvl пройдённой строки
//            UserChangesLog(c_id=p_id, rt='change_lvl', u_p_id='-1', change_lvl=true);
        }
        else {
            while (cur_lvl_fP-1 != pre_lvl_fP && preRow_fP) {
                var pre_lvl_fP = parseInt(preRow_fP.className.split('lvl-')[1]);
                if (!preRow_fP.previousElementSibling) {

//                    //Изменение lvl пройдённой строки
//                    UserChangesLog(c_id=preRow_fP.id, rt='change_lvl', u_p_id='-1', change_lvl=true);

                    return preRow_fP.id
                }
                preRow_fP = preRow_fP.previousElementSibling;

//                //Изменение lvl пройдённой строки
//                UserChangesLog(c_id=preRow_fP.id, rt='change_lvl', u_p_id='-1', change_lvl=true);
            }

            p_id = preRow_fP.nextElementSibling.id;
        }

    }
//    //Изменение lvl пройдённой строки
//    if (!p_id || p_id != -1) {
//        UserChangesLog(c_id=p_id, rt='change_lvl', u_p_id='-1', change_lvl=true);
//    }
    if (p_id == -1) {
    }
    return p_id
}

function UserChangesLog(c_id, rt, u_p_id, c_row=false, change_lvl=false) {
//    if (change_lvl) {
//        if (userChanges[c_id] === undefined) {
//            userChanges[c_id] = {lvl: ''}
//            return;
//        }
//        return;
//    }
//    else {
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
        first_value = elem_value;
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
                console.log('- = -  =  -  =  -  =  - = -  =  -  =  -  =  - = -  =  -  =  -  =  - = -  =  -  =  -  =  ')
                console.log(editDescrRowList[deletedRowList_row])
                console.log('- = -  =  -  =  -  =  - = -  =  -  =  -  =  - = -  =  -  =  -  =  - = -  =  -  =  -  =  ')
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
    console.log(userChanges)
    const tab = document.getElementById("towTable");

    //////////////////////////////////////////////////////////////////////////////////////////////
    // Ищем номер строки
    console.log('          userChanges.length')
    console.log(Object.keys(userChanges).length)

    for (const [k, v] of Object.entries(userChanges)) {
        var userChanges_x = tab.querySelector(`[id='${k}']`);
        userChanges[k]['lvl'] = userChanges_x.rowIndex;
    }

    if (highestRow.length) {
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
    console.log('          userChanges.length')
    console.log(Object.keys(userChanges).length)
//        for (const [k, v] of Object.entries(userChanges)) {
//            //var x = tab.querySelector("#"+k.toString());
//            var userChanges_x = tab.querySelector(`[id='${k}']`);
//
//    //        console.log(k, '--', x.rowIndex)
//    //        console.log(v)
//            userChanges[k]['lvl'] = userChanges_x.rowIndex
//    //        closest('tr');
//        }
//    }

    console.log('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    console.log(editDescrRowList)
    console.log('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')

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
//                elem_value = elem.options[elem.selectedIndex].text;
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
//                v2[1] = elem_value;
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

        var page_url = document.URL.substring(document.URL.lastIndexOf('/objects')+9, document.URL.lastIndexOf('/'));

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
                    window.location.href = `/objects/${page_url}/tow`;
                    alert('Изменения сохранены')
                }
                else {
                    alert(data.description)
                }
            })
    }
    else {
        alert('Изменений не обнаружено')
        location.reload();
    }
}

function cancelTowChanges() {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/objects')+9, document.URL.lastIndexOf('/'));
    window.location.href = `/objects/${page_url}/tow`;
    alert('Изменения отменены, страница обновлена')
}