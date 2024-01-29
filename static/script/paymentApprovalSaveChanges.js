function saveData(rowId, page='') {
    var paymentSelectedRows = document.getElementById('selectedRows-' + rowId).checked;
    var paymentNumber = document.getElementById('paymentNumber-' + rowId).value;
    var approvalSum = document.getElementById('approvalSum-' + rowId).value;
    var amount = document.getElementById('amount-' + rowId).value;
    var statusId = document.getElementById('status_id-' + rowId);
    var paymentFullStatus = document.getElementById('paymentFullStatus-' + rowId).checked;

    if (statusId) {
        statusId = document.getElementById('status_id-' + rowId).value
    }
    // Если согласованная сумма больше остатка, приравниваем согл.сум к остатку
    if (amount && parseFloat(amount) > parseFloat(approvalSum)) {
        document.getElementById('amount-' + rowId).value = approvalSum;
        amount = approvalSum;
    }
    // Send a POST request to the server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/save_quick_changes_approved_payments', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

    xhr.send('row_id=' + rowId + '&payment_number=' + paymentNumber + '&amount=' + amount + '&status_id=' + statusId +
             '&payment_full_agreed_status=' + paymentFullStatus + '&page=' + page);
}
