const crossButtonNAW = document.querySelector("#crossBtnNAW");
const dialogNAW = document.querySelector(".window_news");

crossButtonNAW.addEventListener("click", closeDialog);
function closeDialog() {
    dialogNAW.close();
}

fetch('/get_news_alert', {
    "headers": {
        'Content-Type': 'application/json'
    },
    "method": "POST",
})
    .then(response => response.json())
    .then(data => {
        if (data.news) {

            const dialog = document.querySelector(".window_news");

            const first_alerts = document.querySelector(".news_card");

            for (var n = 1; n < data.news.length; n++) {
                var new_alerts = first_alerts.cloneNode(true);


                if (data.news[n].news_category) {
                    new_alerts.getElementsByClassName("news_category")[0].classList.add("news_category", data.news[n].news_category);
                }
                new_alerts.getElementsByClassName("window_news__datetime")[0].innerHTML = data.news[n].created_at
                new_alerts.getElementsByClassName("window_news__h2")[0].innerHTML = data.news[n].news_title
                if (data.news[n].news_img_link) {
                    var img = document.createElement("img");
                    img.src = data.news[n].news_img_link;
                    new_alerts.getElementsByClassName("window_news__img")[0].appendChild(img);
                }
                new_alerts.getElementsByClassName("window_news__h3")[0].innerHTML = data.news[n].news_subtitle
                for (var i = 0; i < data.news[n].news_description.length; i++) {
                    var p = document.createElement("p");
                    p.innerHTML = data.news[n].news_description[i]
                    new_alerts.getElementsByClassName("window_news__description")[0].appendChild(p);
                }
                dialog.appendChild(new_alerts);
            }

            if (data.news[0].news_category) {
                first_alerts.getElementsByClassName("news_category")[0].classList.add("news_category", data.news[0].news_category);
            }
            first_alerts.getElementsByClassName("window_news__datetime")[0].innerHTML = data.news[0].created_at
            first_alerts.getElementsByClassName("window_news__h2")[0].innerHTML = data.news[0].news_title
            if (data.news[0].news_img_link) {
                var img = document.createElement("img");
                img.src = data.news[0].news_img_link;
                first_alerts.getElementsByClassName("window_news__img")[0].appendChild(img);
            }
            first_alerts.getElementsByClassName("window_news__h3")[0].innerHTML = data.news[0].news_subtitle
            for (var i = 0; i < data.news[0].news_description.length; i++) {
                var p = document.createElement("p");
                p.innerHTML = data.news[0].news_description[i]
                first_alerts.getElementsByClassName("window_news__description")[0].appendChild(p);
            }
            dialog.showModal();
        }
    })
    .catch(error => {
        sendErrorToServer(['get_news_alert', error.toString()]);
        console.error('Error:', error);
    });