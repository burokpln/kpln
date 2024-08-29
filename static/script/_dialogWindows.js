function createDialogWindow(status='error', description='', func=false, buttons=false, text_comment=false,
                            loading_windows=false, text_comment_type='text') {
    let dialog = document.createElement("dialog");
    dialog.classList.add("window", status);
    dialog.id = "logInfo";

    let desc = ''
    for (let i of description) {
        desc += i + '<br>';
    }

    let div_flash = document.createElement("div");
    div_flash.innerHTML = desc;

    dialog.appendChild(div_flash);

    //Окно сохранения информации
    if (loading_windows) {
        let comment_label = document.createElement("div");
        comment_label.classList.add("dialog_window_text_comment_label");

        let img_loading = document.createElement("img");
        img_loading.src = "/static/img/contract/image_save_processing_1.gif";
        img_loading.setAttribute("alt", 'Сохраняем данные...');
        img_loading.className = "image_mini_obj";
        comment_label.appendChild(img_loading);

        dialog.appendChild(comment_label);

        document.body.appendChild(dialog)

        return dialog.showModal();
    }

    if (text_comment) {
        let comment_label = document.createElement("div");
        comment_label.classList.add("dialog_window_text_comment_label");
        comment_label.innerHTML = '<br>Описание';
        dialog.appendChild(comment_label);


        if (text_comment_type === 'date') {
            let comment_input = document.createElement('input');
            comment_input.type = "text";
            comment_input.classList.add("dialog_window_text_comment_input");
            comment_input.id = "dialog_window_text_comment_input";
            comment_input.placeholder = "Дата";
            comment_input.addEventListener('focusin', function() {convertOnfocusDate(this, 'focusin');});
            comment_input.addEventListener('focusout', function() {convertOnfocusDate(this, 'focusout');});
            dialog.appendChild(comment_input);

        }
        else {
            let comment_input = document.createElement('textarea');
            comment_input.classList.add("dialog_window_text_comment_input");
            comment_input.id = "dialog_window_text_comment_input";
            comment_input.placeholder = "Добавьте описание";

            dialog.appendChild(comment_input);
        }

    }

    if (buttons) {
        for (b of buttons)
            button_i = document.createElement("button");
            button_i.id = b.id;
            button_i.innerHTML = b.innerHTML;
            button_i.addEventListener('click', function() {
                removeLogInfo();
            });
            if (b.func) {
                for (let i of b.func) {
                    button_i.addEventListener(i[0], function() {
                        i[1][0](i[1][1]);
                    });
                }
            }
            dialog.appendChild(button_i);
    }

    let ok_button = document.createElement("button");
    ok_button.id = "flash_ok_button";
    ok_button.innerHTML = 'ОК';
    if (!text_comment) {
        ok_button.addEventListener('click', function() {
            removeLogInfo();
        });
    }
    if (func) {
        for (let i of func) {
            ok_button.addEventListener(i[0], function() {
                i[1][0](...i[1].slice(1));
            });
        }
    }
    dialog.appendChild(ok_button);


    document.body.appendChild(dialog)

    dialog.showModal();

    function convertOnfocusDate(empDate, focusStatus='') {
        if (!empDate.value) {
            empDate.type = focusStatus == 'focusin'? 'date':'text';
        }
        else if (empDate.type == 'text' && focusStatus == 'focusin') {
            tmp_value = convertDate(empDate.value);
            empDate.value = tmp_value;
            empDate.type = 'date';
        }
        else if (empDate.type == 'date' && focusStatus == 'focusout') {
            tmp_value = convertDate(empDate.value, "-");
            empDate.type = 'text';
            empDate.value = tmp_value;
        }
    }
}