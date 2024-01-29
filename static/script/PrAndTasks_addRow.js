function addRow(button, route) {
    var row = button.parentNode.parentNode;
    var className = row.className;

    var newRow = row.cloneNode(true);

    var columns = row.cells.length;

    var rowNumber = row.rowIndex;
    var rowNumber2 = rowNumber+1;


    if (className === 'book') {
        var nextRow = row.nextElementSibling;
        var taskRow = row.nextElementSibling;
        while (taskRow && !taskRow.classList.contains('task')) {
            taskRow = taskRow.nextElementSibling;
        }
        taskRow = taskRow.cloneNode(true);

        for (var i=0; i<taskRow.getElementsByTagName('td').length; i++) {
            var tagN = taskRow.getElementsByTagName('td')[i].children;
            for (var i1=0; i1<tagN.length; i1++) {
                if (tagN[i1].tagName == 'INPUT') {
                    tagN[i1].value = '';
                }
            }
        }
    }

    for (var i=0; i<newRow.getElementsByTagName('td').length; i++) {
        var tagN = newRow.getElementsByTagName('td')[i].children;
        for (var i1=0; i1<tagN.length; i1++) {
            if (tagN[i1].tagName == 'INPUT') {
                tagN[i1].value = ''
            }
        }
    }


    if (route === 'Before') {
        if (className === 'book') {
            row.parentNode.insertBefore(newRow, row);
            if (taskRow) {
                newRow.parentNode.insertBefore(taskRow, row);
            }
        }
        else if (className === 'task') {
            row.parentNode.insertBefore(newRow, row);
        }
    }

    else if (route === 'After') {
        if (className === 'book') {
            while (nextRow && !nextRow.classList.contains(className)) {
                nextRow = nextRow.nextElementSibling;
            }
            if (nextRow) {
                if (taskRow) {
                    nextRow.parentNode.insertBefore(taskRow, nextRow);
                }
                taskRow.parentNode.insertBefore(newRow, taskRow);
            }
            else {
                row.parentNode.appendChild(newRow);
                if (taskRow) {
                    row.parentNode.appendChild(taskRow);
                }
            }
        }
        else if (className === 'task') {
            row.parentNode.insertBefore(newRow, row.nextSibling);
        }
    }
}



