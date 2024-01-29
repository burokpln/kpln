function refreshSortValChb(rowId) {
    var tableRow = document.getElementById("payment-table").getElementsByTagName("tr")[1];

    for (var i = 0; i < tableRow.getElementsByTagName("td").length; i++) {
        try {
            if (tableRow.getElementsByTagName("td")[i].getElementsByTagName("input")[0].getAttribute('type') === 'checkbox') {
                var checkbox_val = document.getElementById('row-' + rowId).getElementsByTagName('td')[i].getElementsByTagName("input")[0].checked;
                checkbox_val? checkbox_val=1:checkbox_val=0;

                if (checkbox_val) {
                    document.getElementById('row-' + rowId).getElementsByTagName('td')[i].dataset.sort=1;
                }
                else {
                    document.getElementById('row-' + rowId).getElementsByTagName('td')[i].dataset.sort=0;
                }
            }
        }
        catch {
        }
    }
}

function refreshSortValAmount(rowId) {
    var tableRow = document.getElementById("payment-table").getElementsByTagName("tr")[1];

    for (var i = 0; i < tableRow.getElementsByTagName("td").length; i++) {
        try {
            if (tableRow.getElementsByTagName("td")[i].getElementsByTagName("input")[0].name === 'amount') {
                var amount_value = document.getElementById('amount-' + rowId).value;
                amount_value = parseFloat(amount_value.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));

                isNaN(amount_value)? amount_value = 0: 1;

                document.getElementById('row-' + rowId).getElementsByTagName('td')[i].dataset.sort=amount_value;
            }
        }
        catch {
        }
    }
}
