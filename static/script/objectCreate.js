$(document).ready(function() {
    document.getElementById('create_news_form__button')? document.getElementById('create_news_form__button').addEventListener('click', function() {createProject();}):'';

    document.getElementById('obj_checkbox_obj_proj_toggle')? document.getElementById('obj_checkbox_obj_proj_toggle').addEventListener('click', function() {toggleProjectObject(this);}):'';
    document.getElementById('search')? document.getElementById('search').addEventListener('input', function() {searchProjects(this.value);}):'';

});

function createProject() {
    let project_full_name = document.getElementById("project_full_name").value;
    let project_short_name = document.getElementById("project_short_name").value;
    let customer = document.getElementById("customer").value;
    let project_address = document.getElementById("project_address").value;
    let gip_id = document.getElementById("gip_id").value;
    let status_id = document.getElementById("status_id").value;
    let project_total_area = document.getElementById("project_total_area").value;
    let project_title = document.getElementById("project_title").value;
    let project_img = document.getElementById("project_img").value;
    let project_img_middle = document.getElementById("project_img_middle").value;
    let project_img_mini = document.getElementById("project_img_mini").value;
    let link_name = document.getElementById("link_name").value;

    console.log('project_full_name', "_", project_full_name, "_");
    console.log('project_short_name', "_", project_short_name, "_");
    console.log('customer', "_", customer, "_");
    console.log('project_address', "_", project_address, "_");
    console.log('gip_id', "_", gip_id, "_");
    console.log('status_id', "_", status_id, "_");
    console.log('project_total_area', project_total_area, "_");
    console.log('project_title', project_title, "_");
    console.log('project_img', project_img, "_");
    console.log('project_img_middle', project_img_middle, "_");
    console.log('project_img_mini', project_img_mini, "_");
    console.log('link_name', link_name, "_");
    if (!project_full_name || !project_short_name || !customer  || !project_address || !gip_id || !project_total_area
        || !project_title || !project_img || !project_img_middle || !project_img_mini || !link_name) {
        if (!project_full_name) {
            return alert('Ну заполнено: Полное название проекта')
        }
        if (!project_short_name) {
            return alert('Ну заполнено: Аббревиатура проекта')
        }
        if (!customer) {
            return alert('Ну заполнено: Заказчик')
        }
        if (!project_address) {
            return alert('Ну заполнено: Адрес')
        }
        if (!gip_id) {
            return alert('Ну заполнено: ГИП')
        }
        if (!project_total_area) {
            return alert('Ну заполнено: Общая площадь')
        }
        if (!project_title) {
            return alert('Ну заполнено: Описание проекта')
        }
        if (!project_img) {
            return alert('Ну заполнено: Изображение проекта')
        }
        if (!project_img_middle) {
            return alert('Ну заполнено: Img middle size')
        }
        if (!project_img_mini) {
            return alert('Ну заполнено: Img size (20px)')
        }
        if (!link_name) {
            return alert('Ну заполнено: link_name')
        }
    }

    document.getElementById('create_news_form__button').parentNode.submit();
}

//Переключатель проекты/объекты
function toggleProjectObject(toggle) {
    var obj_list_div =  document.getElementById('object-list');
    var obj_list

    if (toggle.checked) {
        obj_list =  document.getElementById('obj_checkbox_proj_list').getElementsByTagName("tr");
        document.getElementById('obj_checkbox').getElementsByClassName('left')[0].hidden = 0;
        document.getElementById('obj_checkbox').getElementsByClassName('right')[0].hidden = 1;
    }
    else {
        obj_list =  document.getElementById('obj_checkbox_obj_list').getElementsByTagName("tr");
        document.getElementById('obj_checkbox').getElementsByClassName('left')[0].hidden = 1;
        document.getElementById('obj_checkbox').getElementsByClassName('right')[0].hidden = 0;
    }
    var proj_list = document.getElementById('obj_checkbox_proj_list').innerText;

    obj_list_div.innerHTML = '';

    for (let i of obj_list) {
        let objectItem = document.createElement('div');
        objectItem.className = "objectItem";
        objectItem.setAttribute("name", i.getElementsByTagName("td")[0].innerText);

            let project_img_div = document.createElement('div');
            project_img_div.className = "project_img_div";
                let project_img_div_img = document.createElement("img");
                if (i.getElementsByTagName("td")[2].innerText) {
                    project_img_div_img.src = i.getElementsByTagName("td")[2].innerText;
                }
                else {
                    project_img_div_img.src = "/static/img/object/empty_image_mini_obj.svg";
                }
                project_img_div_img.setAttribute("alt", i.getElementsByTagName("td")[1].innerText);
                project_img_div_img.className = "image_mini_obj";
            project_img_div.appendChild(project_img_div_img);
            objectItem.appendChild(project_img_div);

            let object_name = document.createElement('div');
            object_name.className = "object_name";
                let linkText = document.createTextNode(i.getElementsByTagName("td")[1].innerText);
                let object_name_content;
                if (i.getElementsByTagName("td")[4].innerText) {
                    object_name_content = document.createElement('a');
                    object_name_content.appendChild(linkText);
                    object_name_content.href = "/objects/" + i.getElementsByTagName("td")[4].innerText;
                    object_name.appendChild(object_name_content);
                }
                else {
                    object_name.innerText = i.getElementsByTagName("td")[1].innerText;
                }
            objectItem.appendChild(object_name);

            if (i.getElementsByTagName("td")[5].innerText) {
                let create_proj_div = document.createElement('div');
                    let create_proj_div_a = document.createElement('a');
                    let linkText = document.createTextNode("Создать проект");
                    create_proj_div_a.appendChild(linkText);
                    create_proj_div_a.href = i.getElementsByTagName("td")[5].innerText;
                create_proj_div.appendChild(create_proj_div_a);
                objectItem.appendChild(create_proj_div);
            }

            if (i.getElementsByTagName("td")[6].innerText) {
                let clock_ico_container = document.createElement('div');
                clock_ico_container.id = "clock_ico_container"
                    let clock_ico_container_a = document.createElement('a');
                    let linkText = document.createTextNode("🕑");
                    clock_ico_container_a.appendChild(linkText);
                    clock_ico_container_a.href = i.getElementsByTagName("td")[6].innerText;
                    clock_ico_container_a.title = "Раздел задачи и проекты";
                clock_ico_container.appendChild(clock_ico_container_a);
                objectItem.appendChild(clock_ico_container);
            }
        obj_list_div.appendChild(objectItem);
    }
}


//Поиск проекта/объекта на главной странице
function searchProjects(txt) {
    var toggle =  document.getElementById('obj_checkbox_obj_proj_toggle');

    var obj_list_div =  document.getElementById('object-list');
    var obj_list

    if (toggle.checked) {
        obj_list =  document.getElementById('obj_checkbox_proj_list').getElementsByTagName("tr");
    }
    else {
        obj_list =  document.getElementById('obj_checkbox_obj_list').getElementsByTagName("tr");
    }

    var proj_list = document.getElementById('obj_checkbox_proj_list').innerText;

    obj_list_div.innerHTML = '';
    var cnt = 0;

    for (let i of obj_list) {
        if (i.getElementsByTagName("td")[1].innerText.toLowerCase().search(txt) > - 1) {
            cnt ++;

            let objectItem = document.createElement('div');
            objectItem.className = "objectItem";
            objectItem.setAttribute("name", i.getElementsByTagName("td")[0].innerText);

                let project_img_div = document.createElement('div');
                project_img_div.className = "project_img_div";
                    let project_img_div_img = document.createElement("img");
                    if (i.getElementsByTagName("td")[2].innerText) {
                        project_img_div_img.src = i.getElementsByTagName("td")[2].innerText;
                    }
                    else {
                        project_img_div_img.src = "/static/img/object/empty_image_mini_obj.svg";
                    }
                    project_img_div_img.setAttribute("alt", i.getElementsByTagName("td")[1].innerText);
                    project_img_div_img.className = "image_mini_obj";
                project_img_div.appendChild(project_img_div_img);
                objectItem.appendChild(project_img_div);

                let object_name = document.createElement('div');
                object_name.className = "object_name";
                    let linkText = document.createTextNode(i.getElementsByTagName("td")[1].innerText);
                    let object_name_content;
                    if (i.getElementsByTagName("td")[4].innerText) {
                        object_name_content = document.createElement('a');
                        object_name_content.appendChild(linkText);
                        object_name_content.href = "/objects/" + i.getElementsByTagName("td")[4].innerText;
                        object_name.appendChild(object_name_content);
                    }
                    else {
                        object_name.innerText = i.getElementsByTagName("td")[1].innerText;
                    }
                objectItem.appendChild(object_name);

                if (i.getElementsByTagName("td")[5].innerText) {
                    let create_proj_div = document.createElement('div');
                        let create_proj_div_a = document.createElement('a');
                        let linkText = document.createTextNode("Создать проект");
                        create_proj_div_a.appendChild(linkText);
                        create_proj_div_a.href = i.getElementsByTagName("td")[5].innerText;
                    create_proj_div.appendChild(create_proj_div_a);
                    objectItem.appendChild(create_proj_div);
                }

                if (i.getElementsByTagName("td")[6].innerText) {
                    let clock_ico_container = document.createElement('div');
                    clock_ico_container.id = "clock_ico_container"
                        let clock_ico_container_a = document.createElement('a');
                        let linkText = document.createTextNode("🕑");
                        clock_ico_container_a.appendChild(linkText);
                        clock_ico_container_a.href = i.getElementsByTagName("td")[6].innerText;
                        clock_ico_container_a.title = "Раздел задачи и проекты";
                    clock_ico_container.appendChild(clock_ico_container_a);
                    objectItem.appendChild(clock_ico_container);
                }
            obj_list_div.appendChild(objectItem);
        }
    }
    if (!cnt) {
        let objectItemEmpty = document.createElement('div');
        objectItemEmpty.className = "objectItemEmpty";
        objectItemEmpty.innerHTML = 'Данные не найдены';
        objectItemEmpty.style.textAlign = "center";
        objectItemEmpty.style.fontStyle = "italic";
        obj_list_div.appendChild(objectItemEmpty);
    }
}