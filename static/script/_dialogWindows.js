function createDialogWindow(status='error', description='', func=false, buttons=false) {
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

    let ok_button = document.createElement("button");
    ok_button.id = "flash_ok_button";
    ok_button.innerHTML = 'ОК';
    ok_button.addEventListener('click', function() {
        removeLogInfo();
    });
    if (func) {
        for (let i of func) {
            ok_button.addEventListener(i[0], function() {
                i[1][0](i[1][1]);
            });
        }
    }
    dialog.appendChild(ok_button);

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


    document.body.appendChild(dialog)

    dialog.showModal();
}