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