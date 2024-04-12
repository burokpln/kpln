$(document).ready(function() {
    if (document.getElementById('payment_description')) {
        document.getElementById('payment_description').addEventListener('input', function() {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('responsible')) {
        $('#responsible').on('change', function(e) {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('cost_items')) {
        $('#cost_items').on('change', function(e) {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('objects_name')) {
        $('#objects_name').on('change', function(e) {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('payment_due_date')) {
        document.getElementById('payment_due_date').addEventListener('input', function() {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('our_company')) {
        $('#our_company').on('change', function(e) {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('payment_sum')) {
        document.getElementById('payment_sum').addEventListener('input', function() {
            checkFormNewPayment();
        });
    }
    if (document.getElementById('custom_tittle_in_form')) {
        document.getElementById('custom_tittle_in_form').addEventListener('click', function() {
            window['tableCustom'].showModal();
        });
    }
    if (document.getElementById('submit_button_in_form')) {
        document.getElementById('submit_button_in_form').addEventListener('click', function() {
            this.form.submit();
            this.disabled=true;
        });
    }

});

function checkFormNewPayment() {
    var field1 = document.getElementById('basis_of_payment').value;
    var field2 = document.getElementById('responsible').value;
    var field3 = document.getElementById('cost_items').value;
    var field4 = document.getElementById('objects_name').value;
    var field5 = document.getElementById('payment_description').value;
    var field6 = document.getElementById('payment_due_date').value;
    var field7 = document.getElementById('our_company').value;
    var field8 = document.getElementById('payment_sum').value;
    var category = field3.split('-@@@-')[0];

    if (category === 'Субподрядчики') {
        document.getElementById("objects_name_div").style.display = "flex";
        document.getElementById("objects_name").required = true;
    }
    else if (category && !field4) {
        field4 = "пусто"
    }

    if (category !== 'Субподрядчики') {
        document.getElementById("objects_name_div").style.display = "none";
        document.getElementById("objects_name").required = false;
    }
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);

    field8_1 = parseFloat(field8.replaceAll('₽', '').replaceAll(" ", "").replaceAll(" ", "").replaceAll(",", "."))


    if (field1 !== '' && field2 !== '' && field3 !== '' && field4 !== '' && field5 !== '' && field6 !== '' &&
        field7 !== '' && field8 !== '' && !isNaN(field8_1) && field8_1) {
        if (page_url === 'payment-approval') {
            document.getElementById('save__edit_btn_i').disabled = false
        }
        else {
            document.getElementById('submit_button_in_form').disabled = false;
        }
    } else {
        if (page_url === 'payment-approval') {
            document.getElementById('save__edit_btn_i').disabled = true
        }
        else {
            document.getElementById('submit_button_in_form').disabled = true;
        }
    }
}
