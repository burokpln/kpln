$(document).ready(function () {
  //    var img = document.getElementById("div_full_screen_image_obj");
  //
  //    setTimeout(function() {
  //      img.style.display = "none";
  //    }, 2000);
  document.getElementById("div_full_screen_image_obj")
    ? document
        .getElementById("div_full_screen_image_obj")
        .addEventListener("click", function () {
          this.hidden = true;
        })
    : "";
});
