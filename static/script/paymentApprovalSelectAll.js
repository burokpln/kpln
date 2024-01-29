function paymentSelectAll() {
    var status = document.getElementById('selectAll').checked;
    var allRows = document.querySelectorAll('[id*="selectedRows-"]');
    var allRows_clone = Array.prototype.slice.call(allRows)
    for (i of allRows) {
        if (i.checked !== status) {
            i.checked = status;
            paymentApprovalRecalcCards(allRows_clone.indexOf(i)+1)
        }
    }
    totalSelect()
}

function totalSelect() {
    var total_select = 0;
    var total_amount = 0;

    var selectRows = document.querySelectorAll('[id*="selectedRows-"]');
    var statusRows = document.querySelectorAll('[id*="status_id-"]');
    var approvalRows = document.querySelectorAll('[id*="approvalSum-"]');

    for (var i=0; i<selectRows.length; i++) {
        selectRows[i].checked? total_select ++:0;
        if (selectRows[i].checked && (statusRows[i].value == 'Реком.' || statusRows[i].value == 'Черновик')) {
            approvalSum = approvalRows[i].value? parseFloat(approvalRows[i].value.replace(',', '.')).toFixed(2) * 1.00 : 0;
            total_amount += approvalSum
        }
    }
    document.getElementsByClassName("totalSelectRows__value")[0].innerText = total_select;
    document.getElementsByClassName("totalSumRemain__value")[0].innerText = total_amount.toLocaleString() + ' ₽'

    if (total_select && document.getElementById("totalSelectInfo").style.display) {
        document.getElementById("totalSelectInfo").style.display = 'flex';
    }
    else {
        document.getElementById("totalSelectInfo").style.display = 'none';
    }
    if (!total_select) {
        if (!document.getElementById('submitButton').disabled) {
            document.getElementById('submitButton').disabled = true;
        }
        document.getElementById('selectAll').checked? status = document.getElementById('selectAll').checked = false :0;
    }
    else {
        document.getElementById('submitButton').disabled = false;
    }
}