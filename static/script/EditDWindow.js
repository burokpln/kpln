$(document).ready(function() {
    const crossButton = document.querySelector("#crossBtn");
    const closeButton = document.querySelector("#closeBtn");
    const dialog = document.querySelector("#payment-approval__dialog");
    const annulPaymentButton = document.querySelector("#annul__edit_btn");
    const annulApprovalButton = document.querySelector("#annul_approval__edit_btn");
    const saveButton = document.querySelector("#save__edit_btn");
    var page_url = document.URL.substring(document.URL.lastIndexOf('/')+1);

    crossButton.addEventListener("click", closeDialog);
    function closeDialog() {
        dialog.close();
    }
    closeButton.addEventListener("click", closeDialog);
    function closeDialog() {
        dialog.close();
    }

    document.getElementById('cost_items')? document.getElementById('cost_items').addEventListener('change', function() {checkFormNewPayment();}):'';
    document.getElementById('objects_name')? document.getElementById('objects_name').addEventListener('change', function() {checkFormNewPayment();}):'';
    document.getElementById('payment_sum')? document.getElementById('payment_sum').addEventListener('change', function() {numberWithSpaces(event, ' ₽');}):'';
    document.getElementById('sum_approval')? document.getElementById('sum_approval').addEventListener('change', function() {numberWithSpaces(event, ' ₽');}):'';
    document.getElementById('logBtn')? document.getElementById('logBtn').addEventListener('click', function() {window['logDPage'].showModal();}):'';
});


function annulPayment() {
    var paymentId = document.getElementById('payment_id').textContent;
    fetch('/annul_payment', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'paymentId': paymentId,
            'page_url': page_url,
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/${page_url}`;
            } else {
                window.location.href = `/${page_url}`;
            }
        })
        .catch(error => {
            sendErrorToServer(['annul_payment', error.toString()]);
            console.error('Error:', error);
        });
}

function annulApproval() {
    var paymentId = document.getElementById('payment_id').textContent;
    fetch('/annul_approval_payment', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'paymentId': paymentId,
            'page_url': page_url,
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/${page_url}`;
            } else {
                window.location.href = `/${page_url}`;
            }
        })
        .catch(error => {
            sendErrorToServer(['annul_approval_payment', error.toString()]);
            console.error('Error:', error);
        });
}

const crossButtonInside = document.querySelector("#crossBtnInside");
const closeButtonInside = document.querySelector("#closeBtnInside");
const dialogInside = document.querySelector("#logDPage");


crossButtonInside.addEventListener("click", closeDialogInside);
function closeDialogInside() {
    dialogInside.close();
}
closeButtonInside.addEventListener("click", closeDialogInside);
function closeDialogInside() {
    dialogInside.close();
}

function savePayment() {
    var paymentId = document.getElementById('payment_id').textContent;
    var basis_of_payment = document.getElementById('basis_of_payment').value;
    var basis_of_payment_dataset = document.getElementById('basis_of_payment').dataset.value;
    var responsible = document.getElementById('responsible').value;
    var responsible_dataset = document.getElementById('responsible').dataset.value;
    var cost_items = document.getElementById('cost_items').value;
    var cost_items_category = cost_items.split('-@@@-')[0];
    var cost_items_id = cost_items.split('-@@@-')[1];
    var cost_items_id_dataset = document.getElementById('cost_items').dataset.value;
    var objects_name = document.getElementById('objects_name').value;
    var objects_name_dataset = document.getElementById('objects_name').dataset.value;
    var payment_description = document.getElementById('payment_description').value;
    var payment_description_dataset = document.getElementById('payment_description').dataset.value;
    var partners = document.getElementById('partners').value;
    var partners_dataset = document.getElementById('partners').dataset.value;
    var payment_due_date = document.getElementById('payment_due_date').value;
    var payment_due_date_dataset = document.getElementById('payment_due_date').dataset.value;
    var our_company = document.getElementById('our_company').value;
    var our_company_dataset = document.getElementById('our_company').dataset.value;
    var sum_payment = document.getElementById('payment_sum').value;
    var sum_payment_dataset = document.getElementById('payment_sum').dataset.value;
    var sum_approval = document.getElementById('sum_approval').value;
    var sum_approval_dataset = document.getElementById('sum_approval').dataset.value;
    var payment_full_agreed_status = document.getElementById('paymentFullStatus').checked;
    var payment_full_agreed_status_dataset = document.getElementById('paymentFullStatus').dataset.value;

    //    Если вид работ не субподрядчики, то удаляем id проекта
    cost_items_category !== 'Субподрядчики' ? objects_name = '' : 1;

    fetch('/save_payment', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'payment_id': paymentId,
            'basis_of_payment': basis_of_payment,
            'basis_of_payment_dataset': basis_of_payment_dataset,
            'responsible': responsible,
            'responsible_dataset': responsible_dataset,
            'cost_item_id': cost_items_id,
            'cost_item_id_dataset': cost_items_id_dataset,
            'object_id': objects_name,
            'object_id_dataset': objects_name_dataset,
            'payment_description': payment_description,
            'payment_description_dataset': payment_description_dataset,
            'partners': partners,
            'partners_dataset': partners_dataset,
            'payment_due_date': payment_due_date,
            'payment_due_date_dataset': payment_due_date_dataset,
            'our_company_id': our_company,
            'our_company_id_dataset': our_company_dataset,
            'payment_sum': sum_payment,
            'payment_sum_dataset': sum_payment_dataset,
            'sum_approval': sum_approval,
            'sum_approval_dataset': sum_approval_dataset,
            'payment_full_agreed_status': payment_full_agreed_status,
            'p_full_agreed_s_dataset': payment_full_agreed_status_dataset,
            'page_url': page_url
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/${page_url}`;
            } else {
                window.location.href = `/${page_url}`;
            }
        })
        .catch(error => {
            sendErrorToServer(['save_payment', error.toString()]);
            console.error('Error:', error);
        });
}