document.addEventListener("DOMContentLoaded", function () {
    var menu = document.getElementById("menu");
    var image = document.getElementById("image_menu");

    document.addEventListener("click", (event) => {
        const menuClick = event.target == menu || menu.contains(event.target)
        const menuButtonClick = event.target == image
        if (!menuClick && !menuButtonClick) {
            menu.style.display = "none";
            image.src = '/static/img/interface/menu.png'
        }
    });

    image.addEventListener("click", function () {
        var isMenuVisible = menu.style.display === "flex";
        if (isMenuVisible) {
            menu.style.display = "none";
            image.src = '/static/img/interface/menu.png'
        } else {
            menu.style.display = "flex";
            image.src = '/static/img/interface/menuend.png'
        }
    });
});