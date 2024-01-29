$(document).ready(function () {
    const toggleNewPassword = document.querySelector("#toggleNewPassword");
    const new_password = document.querySelector("#new_password");

    const toggleConfPassword = document.querySelector("#toggleConfPassword");
    const confirm_password = document.querySelector("#confirm_password");

    toggleNewPassword.addEventListener("click", function () {
        // toggle the type attribute
        const type = new_password.getAttribute("type") === "password" ? "text" : "password";
        new_password.setAttribute("type", type);

        // toggle the icon
        this.classList.toggle("bi-eye");
    });

    toggleConfPassword.addEventListener("click", function () {
        // toggle the type attribute
        const type = confirm_password.getAttribute("type") === "password" ? "text" : "password";
        confirm_password.setAttribute("type", type);

        // toggle the icon
        this.classList.toggle("bi-eye");
    });
});

function checkPasswordCompliant() {
    const new_password = document.querySelector("#new_password").value;
    const confirm_password = document.querySelector("#confirm_password").value;

    var saveBtn = document.getElementById('change_password_form__button');

    function checkWord(word) {
        var hasMinLength = word.length > 8;

        var hasUppercase = '[A-Z]';
        var hasUppercase = word.match(hasUppercase);

        var hasLowercase = '[a-z]';
        var hasLowercase = word.match(hasLowercase);

        var hasDigits = '[0-9]';
        var hasDigits = word.match(hasDigits);

        var hasSpecialCharacters = '[!@#$%^&*(),.?":{}|<>]';
        var hasSpecialCharacters = word.match(hasSpecialCharacters);
        return hasUppercase && hasLowercase && hasDigits && hasSpecialCharacters && hasMinLength
    }

    check_new_pas = checkWord(new_password);
    check_conf_pas = checkWord(confirm_password);

    if (new_password === confirm_password && check_new_pas && check_conf_pas) {
        saveBtn.disabled = false;
    }
    else if ((new_password !== confirm_password || !check_new_pas || !check_conf_pas) && !saveBtn.disabled) {
        saveBtn.disabled = true;
    }
}

function changePas() {
    const new_password = document.querySelector("#new_password").value;
    const confirm_password = document.querySelector("#confirm_password").value;
    fetch('/changePas', {
        "headers": {
            'Content-Type': 'application/json'
        },
        "method": "POST",
        "body": JSON.stringify({
            'new_password': new_password,
            'confirm_password': confirm_password,
        }),

    })
        .then(response => response.json())
        .then(data => {
            window.location.href = '/profile';
        })
        .catch(error => {
            console.error('Error:', error);
        });
}