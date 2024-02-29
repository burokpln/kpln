$(document).ready(function() {
    tabColorize();
    var userRoleId = document.getElementById('header__auth__role_id').textContent;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    if (userRoleId == 6 && page_url === 'payment-approval') {
        var card_selected = document.getElementById('card_selected_for_approval');
        var card_available = document.getElementById('card_available_money');
        var card_account = document.getElementById('card_account_money');

        card_selected.setAttribute("hidden", "hidden");
        card_available.id = 'card_available_money_alp';
        card_account.id = 'card_account_money_alp';

        var head_cell = document.getElementsByClassName('th_sum_agreed')[0];
        head_cell.setAttribute("hidden", "hidden");

        var column = document.getElementsByClassName('th_sum_agreed_i');
        if (column.length) {
            for (var i = 0; i < column.length; i++) {
                var cell = column[i];
                cell.setAttribute("hidden", "hidden");
            }
        }
    }
});


function tabColorize(rowId = '') {
    if (rowId) {
        var paymentSelectedRows = document.getElementById('selectedRows-' + rowId).checked;
        var approvalSum = document.getElementById('approvalSum-' + rowId).value;
        var amount = document.getElementById('amount-' + rowId).value;
        var statusId = document.getElementById('status_id-' + rowId);
        var paymentFullStatus = document.getElementById('paymentFullStatus-' + rowId).checked;
        var a_m_v = document.getElementById('card_available_money_value').innerHTML;

        a_m_v = parseFloat(a_m_v.replace(',', '.'));

        if (statusId) {
            statusId = statusId.value
        }

        if (a_m_v < 0) {

        }
        else {
            document.getElementById('card_selected_for_approval_value').style.color = "#147d30";
            document.getElementById('card_available_money_value').style.color = "black";
        }

        if (statusId && statusId !== 'Черновик') {
            document.getElementById('status-' + rowId).style.background = "#00000000";
            document.getElementById('row-' + rowId).getElementsByTagName('td')[1].style.background = "#00000000"
            //            document.getElementById('category-' + rowId).style.background = "#00000000"
        }

        if (!paymentSelectedRows) {
            document.getElementById('row-' + rowId).style.borderBottom = "none";
            rowId % 2 ? document.getElementById('row-' + rowId).style.background = "#eaedec" : document.getElementById('row-' + rowId).style.background = "#d7d5d5";

        }
        else {
            if (statusId) {
                if (statusId == 'Реком.' || statusId == 'Черновик') {
                    if (a_m_v < 0) {
                        document.getElementById('card_selected_for_approval_value').style.color = "#cd2727";
                        document.getElementById('card_available_money_value').style.color = "#cd2727";
                        document.getElementById('row-' + rowId).style.background = "#cd2727";
                    }
                    else {
                        if (paymentFullStatus) {
                            document.getElementById('row-' + rowId).style.background = "#bcefca";
                            document.getElementById('row-' + rowId).style.borderBottom = "1px solid #00000036";
                        }
                        else if (!paymentFullStatus) {
                            document.getElementById('row-' + rowId).style.background = "#88df9f";
                            document.getElementById('row-' + rowId).style.borderBottom = "solid 1px #00000036";
                        }
                    }
                }
                else {
                    document.getElementById('row-' + rowId).style.background = "#ffb1b1";
                }
            }
            else {
                if (a_m_v < 0) {
                    document.getElementById('card_selected_for_approval_value').style.color = "red";
                    document.getElementById('card_available_money_value').style.color = "#cd2727";
                    document.getElementById('row-' + rowId).style.background = "#cd2727";
                }
                else {
                    if (paymentFullStatus) {
                        document.getElementById('row-' + rowId).style.background = "#bcefca";
                        document.getElementById('row-' + rowId).style.borderBottom = "1px solid #00000036";
                    }
                    else if (!paymentFullStatus) {
                        document.getElementById('row-' + rowId).style.background = "#88df9f";
                        document.getElementById('row-' + rowId).style.borderBottom = "1px solid #00000036";
                    }
                }
            }
        }
        if (statusId && statusId === 'Черновик') {
            document.getElementById('status-' + rowId).style.background = "#e3e33294";
            document.getElementById('row-' + rowId).getElementsByTagName('td')[1].style.background = "#e3e33294";
            //            document.getElementById('category-' + rowId).style.background = "#e3e33294";
        }
    }

    else {
        var selectedRows = document.getElementsByName('selectedRows');
        var statusId = document.getElementsByName('status_id');

        if (statusId.length) {
            for (var i = 0; i < selectedRows.length; i++) {
                if (statusId[i].value == 'Черновик') {
                    document.getElementById('status-' + (i + 1)).style.background = "#e3e33294";
                    document.getElementById('row-' + (i + 1)).getElementsByTagName('td')[1].style.background = "#e3e33294";
                    //                    document.getElementById('category-' + (i + 1)).style.background = "#e3e33294"
                }
            }
        }
    }
}
