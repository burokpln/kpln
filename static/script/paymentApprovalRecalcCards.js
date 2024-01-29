function paymentApprovalRecalcCards(rowId) {
    var userRoleId = document.getElementById('header__auth__role_id').textContent;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);



    if (userRoleId == 6 && page_url === 'payment-approval') {
        tabColorize(rowId);
    }
    else{
        var s_f_a_p = document.getElementById('card_selected_for_approval_value').dataset.value;
        var a_m_v = document.getElementById('card_available_money_value').dataset.value;

        var choiceRows = document.getElementsByName('selectedRows');

        var paymentSelectedRows = document.getElementById('selectedRows-' + rowId).checked;
        var statusId = document.getElementById('status_id-' + rowId);
        var approvalSum = document.getElementById('approvalSum-' + rowId).value;
        var amount_value = document.getElementById('amount-' + rowId).value;
        var amount_dataset = document.getElementById('amount-' + rowId).dataset.amount

        amount_value = parseFloat(amount_value.replaceAll(' ', '').replaceAll(' ', '').replace('₽', '').replace(",", "."));

        s_f_a_p ? s_f_a_p = parseFloat(s_f_a_p.replace(',', '.')).toFixed(2) * 1.00 : s_f_a_p = 0;
        a_m_v ? a_m_v = parseFloat(a_m_v.replace(',', '.')).toFixed(2) * 1.00 : a_m_v = 0;
        approvalSum ? approvalSum = parseFloat(approvalSum.replace(',', '.')).toFixed(2) * 1.00 : approvalSum = 0;
        isNaN(amount_value)? amount_value = approvalSum : 0;
        amount_dataset ? amount_dataset = parseFloat(amount_dataset.replace(',', '.')).toFixed(2) * 1.00 : amount_dataset = 0;

        if (statusId) {
            statusId = document.getElementById('status_id-' + rowId).value;
        }

        if (paymentSelectedRows) {
            if (statusId) {
                if (statusId == 'Аннулирован') {
                    s_f_a_p -= amount_dataset;
                    a_m_v += amount_dataset;
                    document.getElementById('amount-' + rowId).value = 0;
                    document.getElementById('amount-' + rowId).dataset.amount = 0;
                }
                else if (statusId == 'Реком.' || statusId == 'Черновик') {
                    s_f_a_p -= amount_dataset;
                    a_m_v += amount_dataset;

                    amount_value <= 0 ? amount_value = 0 : 0;
                    amount_value > approvalSum ? amount_value = approvalSum : 0;
                    amount_value > a_m_v ? amount_value = a_m_v : 0;

                    s_f_a_p += amount_value;
                    a_m_v -= amount_value;
                    document.getElementById('amount-' + rowId).value = amount_value.toLocaleString() + ' ₽';
                    document.getElementById('amount-' + rowId).dataset.amount = amount_value;
                }
            }
            else {
                s_f_a_p -= amount_dataset;
                a_m_v += amount_dataset;

                amount_value <= 0 ? amount_value = 0 : 0;
                amount_value > approvalSum ? amount_value = approvalSum : 0;
                amount_value > a_m_v ? amount_value = a_m_v : 0;

                s_f_a_p += amount_value;
                a_m_v -= amount_value;
                document.getElementById('amount-' + rowId).value = amount_value.toLocaleString() + ' ₽';
                document.getElementById('amount-' + rowId).dataset.amount = amount_value;
            }
        }
        else {
            s_f_a_p -= amount_dataset;
            a_m_v += amount_dataset;
            document.getElementById('amount-' + rowId).dataset.amount = 0;
        }

        tabColorize(rowId);

        if (a_m_v < 0) {
            if (page_url === 'payment-approval') {
                if (!document.getElementById('submitButton').disabled) {
                    document.getElementById('submitButton').disabled = true;
                }
            }
            else {
                for (var i = 0; i < choiceRows.length; i++) {
                    if (!choiceRows[i].checked ) {
                        document.getElementById('selectedRows-' + (i + 1)).disabled = true;
                    }
                }
            }
        }
        else {
            if (page_url === 'payment-approval') {
                if (document.getElementById('submitButton').disabled) {
                    document.getElementById('submitButton').disabled = false;
                }
            }
            else {
                for (var i = 0; i < choiceRows.length; i++) {
                    if (!choiceRows[i].checked) {
                        document.getElementById('selectedRows-' + (i + 1)).disabled = false;
                    }
                }
            }
        }

        document.getElementById('card_selected_for_approval_value').dataset.value = s_f_a_p;
        document.getElementById('card_available_money_value').dataset.value = a_m_v;

        if (s_f_a_p == 0) {
            s_f_a_p = '0 ₽';
        }
        else {
            s_f_a_p = s_f_a_p.toFixed(2) * 1.00;
            s_f_a_p = s_f_a_p.toLocaleString();
            s_f_a_p += ' ₽';
        }

        if (a_m_v == 0) {
            a_m_v = '0 ₽';
        }
        else {
            a_m_v = a_m_v.toFixed(2) * 1.00;
            a_m_v = a_m_v.toLocaleString();
            a_m_v += ' ₽';
        }

        document.getElementById('card_selected_for_approval_value').innerHTML = s_f_a_p;
        document.getElementById('card_available_money_value').innerHTML = a_m_v;

        if (page_url !== 'payment-approval') {
            var selectCnt = document.getElementById('submitButton').dataset.selectcnt;
            paymentSelectedRows? selectCnt++:selectCnt--;
            document.getElementById('submitButton').dataset.selectcnt = selectCnt;
            if (!selectCnt) {
                if (!document.getElementById('submitButton').disabled) {
                    document.getElementById('submitButton').disabled = true;
                }
            }
            else {
                document.getElementById('submitButton').disabled = false;
            }
        }
    }
}


