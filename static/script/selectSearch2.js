function checkSelect2Status() {
    var windowWidth = window.innerWidth;
    var selectElement = document.getElementsByClassName('selectSearch2');

    if (windowWidth <= 720) {

        if ($('select').data('select2')) {
            $(selectElement).select2('destroy');
        }

    } else {

        $(document).ready(function() {
            $('.selectSearch2').select2();
        });
    }
}

var currentWindowWidth = window.innerWidth;

window.addEventListener('resize', function () {
    var windowWidth = window.innerWidth;

    if (windowWidth !== currentWindowWidth) {
        checkSelect2Status();
        currentWindowWidth = windowWidth;
    }
});

checkSelect2Status();
