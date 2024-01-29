function logOut() {
    fetch('/logout', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": "",

    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = '/';
            } else {
                window.location.href = '/page_error';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
