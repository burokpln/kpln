function paymentApprovalNoSelect(rowId) {
    var userRoleId = document.getElementById('header__auth__role_id').textContent;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);
    if (userRoleId == 6 && page_url === 'payment-approval') {
        tabColorize(rowId);
    }
    else{
        var paymentSelectedRows = document.getElementById('selectedRows-' + rowId).checked;

        if (!paymentSelectedRows) {
            document.getElementById('amount-' + rowId).value = '';
        }
    }
    if (page_url === 'payment-approval') {
        totalSelect()
    }
}
