document.addEventListener("DOMContentLoaded", function () {
  document.querySelector("header").style.display = "none";
  document.querySelector("footer").style.display = "none";
});

window.addEventListener("load", function () {
  setTimeout(function () {
    showObjectScreensaver();
  }, 2000);
});


$(document).ready(function() {
document.getElementById('div_full_screen_image_obj')? document.getElementById('div_full_screen_image_obj').addEventListener('click', function() {showObjectScreensaver()}):'';
});

function showObjectScreensaver() {
    document.querySelector("header").style.display = "flex";
    document.querySelector("footer").style.display = "block";
    document.getElementById("div_full_screen_image_obj").hidden = true;
}
