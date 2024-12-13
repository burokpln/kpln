function exportToExcel() {

    fetch('/export_to_excel', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": "",

    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert("Файл \"" + data.file + "\" скачан:\n" + data.path);
            }
            else {
                alert(data.description);
            }
        })
        .catch(error => {
            sendErrorToServer(['export_to_excel', error.toString()]);
            console.error('Error:', error);
        });
}

function hidePayment(payment_id) {
    console.log('hidePayment', payment_id);
    fetch('/hide_payment', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
                    'payment_id': payment_id,
                }),

    })
        .then(response => response.json())
        .then(data => {
            window.location.href = document.URL;
        })
        .catch(error => {
            sendErrorToServer(['hidePayment', error.toString()]);
        });
}