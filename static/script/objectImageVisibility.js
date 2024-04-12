document.addEventListener("DOMContentLoaded", function () {
  document.querySelector("header").style.display = "none";
  document.querySelector("footer").style.display = "none";
});

window.addEventListener("load", function () {
  setTimeout(function () {
    document.querySelector("header").style.display = "flex";
    document.querySelector("footer").style.display = "block";
    document.getElementById("div_full_screen_image_obj").hidden = true;
  }, 1500);
});
