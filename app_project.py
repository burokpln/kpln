import json

import time
import datetime
from psycopg2.extras import execute_values
from pprint import pprint
from flask import g, request, render_template, redirect, flash, url_for, session, abort, get_flashed_messages, \
    jsonify, Blueprint, current_app, send_file
from datetime import date, datetime
from flask_login import login_required
import error_handlers
import app_login
import app_payment
import pandas as pd
from openpyxl import Workbook
import os
import tempfile


project_app_bp = Blueprint('app_project', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None


@project_app_bp.before_request
def before_request():
    app_login.before_request()


# Главная страница раздела 'Объекты'
@project_app_bp.route('/', methods=['GET'])
@login_required
def objects_main():
    """Главная страница раздела 'Объекты' """
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        role = app_login.current_user.get_role()

        # Список объектов
        cursor.execute(
            """
            SELECT 
                t1.object_id,
                t1.object_name,
                COALESCE(t2.project_img_mini, '') AS project_img_mini,
                COALESCE(t2.project_close_status::text, '') AS project_close_status,
                CASE WHEN t2.project_close_status=false THEN t2.link_name ELSE '' END AS obj_link,
                CASE WHEN t2.project_close_status is null THEN concat_ws('/', 'objects', t1.object_id, 'create') ELSE '' END AS create_obj,
                CASE WHEN t2.project_close_status=false THEN 'часы' ELSE '' END AS project_and_tasks
            FROM objects AS t1
            LEFT JOIN (
                SELECT
                    object_id,
                    project_img_mini,
                    project_close_status,
                    project_short_name,
                    link_name
                FROM projects
            ) AS t2 ON t1.object_id = t2.object_id
            ORDER BY t1.object_id DESC""")
        objects = cursor.fetchall()

        for i in range(len(objects)):
            objects[i] = dict(objects[i])
            if role not in [1, 4]:
                objects[i]['create_obj'] = ''

        print(role, objects[0])

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        if role in (1, 4):
            left_panel = [
                {'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ (для руководителей)'},
                {'link': '/contracts-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ]
        else:
            left_panel = [
                {'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ (для руководителей)'},
                {'link': '/contracts-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ]

        return render_template('index-objects-main.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects=objects,
                               left_panel=left_panel,
                               title='Объекты, главная страница')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/objects/<obj_id>/create', methods=["GET", "POST"])
@login_required
def create_project(obj_id):
    """Страница видов работ"""
    try:
        global hlink_menu, hlink_profile

        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        if request.method == 'GET':
            try:
                print('                ----   get_create_project')
                print(obj_id)

                if role not in (1, 4):
                    flash(message=['Доступ ограничен', ''], category='error')
                    return redirect(url_for('.objects_main'))

                # Connect to the database
                conn, cursor = app_login.conn_cursor_init_dict('objects')

                # Список объектов
                cursor.execute(
                    """
                    SELECT
                        *
                    FROM objects 
                    WHERE object_id = %s ;
                    """,
                    [obj_id]
                )
                object_name = cursor.fetchone()['object_name']

                print(object_name)

                # Список ГИПов
                cursor.execute(
                    "SELECT user_id, last_name, first_name FROM users WHERE is_fired = FALSE")
                gip = cursor.fetchall()

                app_login.conn_cursor_close(cursor, conn)

                return render_template('object-create.html', menu=hlink_menu, menu_profile=hlink_profile,
                                       object_name=object_name,
                                       gip=gip,
                                       left_panel='left_panel',
                                       title=f"{object_name.upper()} - СОЗДАТЬ ПРОЕКТ")

            except Exception as e:
                current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
                flash(message=['Ошибка', f'get-object-create: {e}'], category='error')
                return render_template('page_error.html')

        elif request.method == 'POST':
            try:
                print('                   set_create_project')
                print(obj_id)

                if role not in (1, 4):
                    flash(message=['Доступ ограничен', ''], category='error')
                    return redirect(url_for('.objects_main'))

                # Connect to the database
                conn, cursor = app_login.conn_cursor_init_dict('objects')

                # Ищем проекты с нашим object_id
                cursor.execute(
                    """
                    SELECT
                        object_id
                    FROM projects 
                    WHERE object_id = %s ;
                    """,
                    [obj_id]
                )
                objects = cursor.fetchall()

                # Если проект создан - сообщаем ошибку повторного создания
                if objects:
                    flash(message=['ОШИБКА. Проект уже создан'], category='error')
                    return redirect(url_for('.objects_main'))

                # Добавляем проект
                project_full_name = request.form.get('project_full_name')
                project_short_name = request.form.get('project_short_name')
                customer = request.form.get('customer')
                project_address = request.form.get('project_address')
                gip_id = request.form.get('gip_id')
                status_id = request.form.get('status_id')
                project_total_area = request.form.get('project_total_area')
                project_title = request.form.get('project_title')
                project_img = request.form.get('project_img')
                project_img_middle = request.form.get('project_img_middle')
                project_img_mini = request.form.get('project_img_mini')
                link_name = request.form.get('link_name')
                owner = user_id

                cursor.execute(
                    """
                    INSERT INTO projects (
                        object_id,
                        project_full_name,
                        project_short_name,
                        customer,
                        project_address,
                        gip_id,
                        -- status_id,
                        project_total_area,
                        project_title,
                        project_img,
                        project_img_middle,
                        project_img_mini,
                        link_name,
                        owner
                    ) VALUES %s 
                ON CONFLICT DO NOTHING; """,
                    [(
                        obj_id,
                        project_full_name,
                        project_short_name,
                        customer,
                        project_address,
                        gip_id,
                        # status_id,
                        project_total_area,
                        project_title,
                        project_img,
                        project_img_middle,
                        project_img_mini,
                        link_name,
                        owner
                    )]
                )

                conn.commit()

                app_login.conn_cursor_close(cursor, conn)

                flash(message=[f'Проект {project_full_name} создан', ''], category='success')

                return redirect(url_for('.get_object', link_name=link_name))

            except Exception as e:
                current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
                flash(message=['Ошибка', f'get-object-create: {e}'], category='error')
                return render_template('page_error.html')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'object-create: {e}'], category='error')
        return render_template('page_error.html')


# Главная страница объекта
@project_app_bp.route('/objects/<link_name>', methods=['GET'])
@login_required
def get_object(link_name):
    """Главная страница объекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        print(link_name)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Список объектов
        cursor.execute(
            """
            SELECT
                t1.*,
                t2.object_name,
                SUBSTRING(t1.project_title, 1,370) AS project_title_short
                
            FROM projects AS t1
            LEFT JOIN (
                SELECT
                    object_id,
                        object_name
                FROM objects 
            ) AS t2 ON t1.object_id = t2.object_id
            WHERE t1.link_name = %s 
            LIMIT 1;""",
            [link_name]
        )
        project = cursor.fetchone()

        # ФИО ГИПа
        cursor.execute(
            """
            SELECT
                last_name,
                LEFT(first_name, 1) || '.' AS first_name,
                CASE
                    WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
                END AS surname
            FROM users
            WHERE user_id = %s ;""",
            [project['gip_id']]
        )
        gip_name = cursor.fetchone()
        print(gip_name)
        print(list(gip_name.keys()))
        # project['gip_name'] = f"{gip_name['last_name']} {gip_name['first_name'][0]}.{gip_name['first_name'][0]}."
        print(type(project))
        # Список ГИПов
        cursor.execute(
            "SELECT user_id, last_name, first_name FROM users WHERE is_fired = FALSE ORDER BY last_name, first_name")
        gip = cursor.fetchall()

        if project:
            project = dict(project)
        else:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))

        project['gip_name'] = f"""{gip_name['last_name']} {gip_name['first_name'][0]}.{
        gip_name['surname'][0] + '.' if gip_name['surname'] else ''}"""

        print(project)
        print(list(project.keys()))
        print(project['object_name'])
        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=0)

        # ТЭПы и информация о готовности проекта
        if role in (1, 4):
            tep_info = [
                {'label': 'Получено всего', 'value': '!!! ₽'},
                {'label': 'Стоимость договора без субподрядчиков', 'value': '!!! ₽'},
                {'label': 'Закрыто по актам', 'value': '!!! ₽'},
                {'label': '%', 'value': '!!!'},
                {'label': 'Готовность объекта', 'value': '!!! ₽'},
                {'label': '%', 'value': '!!!'},
                {'label': 'Потрачено ФОТ', 'value': '!!! ₽'},

            ]
        else:
            tep_info = ''

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
                               proj=project,
                               left_panel='left_panel',
                               header_menu=header_menu,
                               tep_info=tep_info,
                               title=f"{project['object_name']} - Объекты, главная страница")

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/set_tow', methods=['POST'])
@login_required
def set_type_of_work():
    print(request.method, request.url, request.base_url, request.url_charset, request.url_root, str(request.url_rule),
          request.host_url, request.host, request.script_root, request.path, request.full_path, request.args,
          request.args.get('x'))


@project_app_bp.route('/get_dept_list/<location>', methods=['GET'])
@login_required
def get_dept_list(location):
    """Список отделов"""
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        if location == 'tow':
            # Список отделов
            cursor.execute("""
                SELECT 
                    t1.child_id AS id,
                    t2.dept_short_name AS name
                FROM dept_relation AS t1
                LEFT JOIN (
                        SELECT dept_id,
                            dept_short_name
                        FROM list_dept
                ) AS t2 ON t1.child_id = t2.dept_id
                WHERE t1.parent_id IS null
                """)
            dept_list = cursor.fetchall()
        else:
            # Список отделов
            cursor.execute("""SELECT * FROM list_dept""")
            dept_list = cursor.fetchall()

        if dept_list:
            for i in range(len(dept_list)):
                dept_list = dict(dept_list)
            return jsonify({
                'dept_list': dept_list,
                'status': 'success'
            })
        else:
            flash(message=['Список отделов не подгружен', ''], category='error')
            return jsonify({
                'status': 'error',
                'description': 'Список отделов не подгружен'})
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': str(e),
        })


@project_app_bp.route('/objects/<link_name>/tow', methods=['GET'])
@login_required
def get_type_of_work(link_name):
    """Страница видов работ"""
    try:
        print(link_name)
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Список объектов
        cursor.execute(
            """
            SELECT
                t1.project_title,
                t1.project_img_middle,
                t2.object_name,
                t1.project_id

            FROM projects AS t1
            LEFT JOIN (
                SELECT
                    object_id,
                        object_name
                FROM objects 
            ) AS t2 ON t1.object_id = t2.object_id
            WHERE t1.link_name = %s 
            LIMIT 1;""",
            [link_name]
        )
        project = cursor.fetchone()

        if project:
            project = dict(project)
        else:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))

        # Список tow
        cursor.execute(
            """WITH
                RECURSIVE rel_rec AS (
                        SELECT
                            1 AS depth,
                            *,
                            ARRAY[lvl] AS child_path
                        FROM types_of_work
                        WHERE parent_id IS NULL AND project_id = %s
                        -- child_id in (SELECT tow_id FROM tow)

                        UNION ALL
                        SELECT
                            nlevel(r.path) + 1,
                            n.*,
                            r.child_path || n.lvl
                        FROM rel_rec AS r
                        JOIN types_of_work AS n ON n.parent_id = r.tow_id
                        WHERE r.project_id = %s
                        -- r.child_id in (SELECT tow_id FROM tow)
                        )
                SELECT
                    tow_id,
                    child_path,
                    tow_name,
                    COALESCE(t0.dept_id, null) AS dept_id,
                    COALESCE(t0.dept_short_name, '') AS dept_short_name,
                    time_tracking,
                    depth-1 AS depth,
                    lvl
                FROM rel_rec
                LEFT JOIN (
                    SELECT
                        dept_id,
                        dept_short_name
                    FROM list_dept
                ) AS t0 ON rel_rec.dept_id = t0.dept_id
                ORDER BY child_path, lvl;""",
            [project['project_id'], project['project_id']]
        )
        tow = cursor.fetchall()

        if tow:
            for i in range(len(tow)):
                print(tow[i])
                tow[i] = dict(tow[i])

        # Список отделов
        cursor.execute("""
            SELECT 
                t1.child_id AS id,
                t2.dept_short_name AS name
            FROM dept_relation AS t1
            LEFT JOIN (
                    SELECT dept_id,
                        dept_short_name
                    FROM list_dept
            ) AS t2 ON t1.child_id = t2.dept_id
            WHERE t1.parent_id IS null
            """)
        dept_list = cursor.fetchall()

        # if dept_list:
        #     dept_list = dict(dept_list)

        """
        ВЗЯТЬ КУСОК ДЕРЕВА
        
        SELECT * FROM section WHERE parent_path <@ 'root.7.11';
        """

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(app_login.current_user.get_role(), link=link_name, cur_name=1)

        # Панель вех
        milestones = get_milestones_menu(app_login.current_user.get_role(), link=link_name, cur_name=1)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-tow.html', menu=hlink_menu, menu_profile=hlink_profile,
                               proj=project,
                               tow=tow,
                               left_panel='left_panel',
                               header_menu=header_menu,
                               milestones=milestones,
                               dept_list=dept_list,
                               title=f"{project['object_name']} - Виды работ")

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'get_type_of_work: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/save_tow_changes/<link_name>', methods=['POST'])
@login_required
def save_tow_changes(link_name):
    """Сохраняем изменения видов работ"""
    try:
        pprint(request.get_json())
        user_changes = request.get_json()['userChanges']
        edit_description = request.get_json()['editDescrRowList']
        new_tow = request.get_json()['list_newRowList']
        deleted_tow = request.get_json()['list_deletedRowList']

        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Список объектов
        cursor.execute(
            "SELECT project_id FROM projects WHERE link_name = %s LIMIT 1;",
            [link_name]
        )
        project_id = cursor.fetchone()[0]

        ######################################################################################
        # Если добавлялись новые строки
        ######################################################################################
        if len(new_tow):
            # Список новых tow value
            columns_tow = ('tow_name', 'project_id', 'dept_id', 'time_tracking', 'parent_id', 'lvl')
            # columns_tow = ('tow_name::text', 'project_id::smallint', 'dept_id::smallint', 'time_tracking::boolean',
            #                'parent_id::integer', 'lvl::smallint')
            values_new_tow = []
            sorted_new_tow = []
            new_tow_dict = {}
            new_tow_set = set()

            for tow in new_tow:
                tmp_1 = 'Название не задано'  # tow_name
                tmp_2 = ''  # project_id
                tmp_3 = None  # dept_id
                tmp_4 = 'false'  # time_tracking
                tmp_5 = None  # parent_id - пока оставляем пустым
                tmp_6 = ''  # lvl

                if tow in edit_description:
                    if 'input_tow_name' in edit_description[tow]:
                        tmp_1 = edit_description[tow]['input_tow_name']
                    if 'select_tow_dept' in edit_description[tow]:
                        tmp_3 = edit_description[tow]['select_tow_dept']
                        if tmp_3 == 'None' or tmp_3 == '':
                            tmp_3 = None
                    if 'checkbox_time_tracking' in edit_description[tow]:
                        tmp_4 = edit_description[tow]['checkbox_time_tracking']


                if project_id:
                    tmp_2 = project_id
                if tow in user_changes and 'lvl' in user_changes[tow]:
                    tmp_6 = user_changes[tow]['lvl']

                values_new_tow.append([
                    tmp_1,  # tow_name
                    tmp_2,  # project_id
                    tmp_3,  # dept_id
                    tmp_4,  # time_tracking
                    tmp_5,  # parent_id - пока оставляем пустым
                    tmp_6,  # lvl
                ])
                sorted_new_tow.append([tow, tmp_6])

            values_new_tow = sorted(values_new_tow, key=lambda x: x[-1])
            sorted_new_tow = sorted(sorted_new_tow, key=lambda x: x[-1])

            action_new_tow = 'INSERT INTO'
            table_new_tow = 'types_of_work'
            columns_new_tow = ('tow_name::text', 'project_id::smallint', 'dept_id::smallint', 'time_tracking::boolean',
                               'parent_id::integer', 'lvl::smallint')
            subquery_new_tow = " ON CONFLICT DO NOTHING RETURNING tow_id;"

            expr_tow = ', '.join([f"{col} = t1.{col} + EXCLUDED.{col}" for col in columns_new_tow[:-1]])
            query_tow = app_payment.get_db_dml_query(action=action_new_tow, table=table_new_tow, columns=columns_tow,
                                                     expr_set=expr_tow, subquery=subquery_new_tow)

            print(query_tow, values_new_tow, sep='\n')
            execute_values(cursor, query_tow, values_new_tow)
            tow_id = cursor.fetchall()

            conn.commit()

            # Список старых и новых id для вновь созданных tow
            for i in range(len(tow_id)):
                new_tow_dict[sorted_new_tow[i][0]] = tow_id[i][0]
                new_tow_set.add(tow_id[i][0])

            # Изменяем parent_id новых tow
            for k, v in user_changes.items():
                if 'parent_id' not in user_changes[k].keys():
                    continue
                p_id = user_changes[k]['parent_id']
                if p_id in new_tow_dict:
                    user_changes[k]['parent_id'] = new_tow_dict[p_id]
                elif not user_changes[k]['parent_id']:
                    user_changes[k]['parent_id'] = None

            # Изменяем tow_id для новых tow
            for k in list(user_changes.keys())[:]:
                if k in new_tow_dict:
                    user_changes[new_tow_dict[k]] = user_changes.pop(k)

            # Изменяем tow_id для новых tow
            for k in list(edit_description.keys())[:]:
                if k in new_tow_dict:
                    edit_description[new_tow_dict[k]] = edit_description.pop(k)

            # обновляем родителей новых tow
            columns_new_tow_upd = ("tow_id", "parent_id")
            values_new_tow_upd = []
            for k, v in new_tow_dict.items():
                try:
                    p_id_tmp = int(user_changes[v]['parent_id'])
                    values_new_tow_upd.append((int(v), p_id_tmp))
                except:
                    p_id_tmp = None

            if len(values_new_tow_upd):
                query_new_tow_upd = app_payment.get_db_dml_query(action='UPDATE', table='types_of_work',
                                                                 columns=columns_new_tow_upd)
                print(query_new_tow_upd, values_new_tow_upd, sep='\n')
                execute_values(cursor, query_new_tow_upd, values_new_tow_upd)
                conn.commit()

            # Удаляем строки с новыми tow, т.к. их уже внесли
            for k in list(user_changes.keys())[:]:
                if k in new_tow_set:
                    user_changes.pop(k)
            for k in list(edit_description.keys())[:]:
                if k in new_tow_set:
                    edit_description.pop(k)

        ######################################################################################
        # Если есть измененные не новые tow
        ######################################################################################
        if user_changes.keys() or edit_description.keys():
            col_dict = {
                'input_tow_name': ['tow_name', 'str', '::text'],
                'select_tow_dept': ['dept_id', 'int', '::smallint'],
                'checkbox_time_tracking': ['time_tracking', 'boolean', '::boolean'],
                'parent_id': ['parent_id', 'int', '::integer'],
                'lvl': ['lvl', 'int', '::smallint']
            }
            if not edit_description.keys():
                for k, v in user_changes.items():
                    print('     id:', k, type(k))
                    edit_description[int(k)] = user_changes[k]
            elif user_changes.keys() and edit_description.keys():
                for k in list(edit_description.keys())[:]:
                    if k in user_changes:
                        print('_id:', k, type(k))
                        for k1, v1 in user_changes[k].items():
                            edit_description[k][k1] = v1
                        edit_description[int(k)] = edit_description.pop(k)
                        user_changes.pop(k)
                for k in list(user_changes.keys())[:]:
                    print('__id:', k, type(k))
                    edit_description[k] = user_changes[k]
                    edit_description[int(k)] = edit_description.pop(k)
                    user_changes.pop(k)
            else:
                for k in list(edit_description.keys())[:]:
                    print('_____ id:', k, type(k))
                    if isinstance(k, str):
                        edit_description[int(k)] = edit_description.pop(k)

            print('_-^-_' * 10)
            pprint(edit_description)
            print('_-^-_' * 10)
            pprint(user_changes)
            print('_-^-_' * 10)

            for k, v in edit_description.items():
                columns_tow_upd = ["tow_id"]
                values_tow_upd = [[k]]
                for k1, v1 in edit_description[k].items():
                    if k1 in col_dict:
                        columns_tow_upd.append(col_dict[k1][0]+col_dict[k1][2])
                        values_tow_upd[0].append(
                            conv_tow_data_upd(val=v1, col_type=col_dict[k1][1])
                        )

                query_tow_upd = app_payment.get_db_dml_query(action='UPDATE', table='types_of_work',
                                                             columns=columns_tow_upd)
                print(' --', query_tow_upd, values_tow_upd, sep='\n')
                execute_values(cursor, query_tow_upd, values_tow_upd)
                conn.commit()

        ######################################################################################
        # Если удалялись строки если были
        ######################################################################################
        print(deleted_tow)
        if len(deleted_tow):
            columns_del_tow = 'tow_id'
            valued_del_tow = []
            for i in deleted_tow:
                valued_del_tow.append((int(i),))

            query_del_tow = app_payment.get_db_dml_query(action='DELETE', table='types_of_work', columns=columns_del_tow)
            execute_values(cursor, query_del_tow, (valued_del_tow,))
            conn.commit()


        app_login.conn_cursor_close(cursor, conn)

        flash(message=['Изменения сохранены', ''], category='success')
        return jsonify({'status': 'success'})

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', str(e)], category='error')
        return jsonify({'status': 'error',
                        'description': str(e),
                        })


# @project_app_bp.route('/objects/<link_name>/contracts', methods=['GET'])
# @login_required
# def get_object_contracts(link_name):
#     """Страница договоров объекта"""
#     try:
#         global hlink_menu, hlink_profile
#         if app_login.current_user.get_role() not in (1, 4):
#             flash(message=['Доступ к разделу "Договоры" ограничен', ''], category='error')
#             return error_handlers.handle403(403)
#         user_id = app_login.current_user.get_id()
#         print('        get_object_contracts')
#         print(link_name)
#
#         # Список меню и имя пользователя
#         hlink_menu, hlink_profile = app_login.func_hlink_profile()
#
#         return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
#                                objects='objects',
#                                left_panel='left_panel',
#                                title='ДОГОВОРЫ')
#
#     except Exception as e:
#         current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
#         flash(message=['Ошибка', f'objects-main: {e}'], category='error')
#         return render_template('page_error.html')


@project_app_bp.route('/objects/<link_name>/calendar-schedule', methods=['GET'])
@login_required
def get_object_calendar_schedule(link_name):
    """Календарный график"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        print('       get_object_calendar_schedule')
        print(link_name)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects='objects',
                               left_panel='left_panel',
                               title='Календарный график')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/objects/<link_name>/weekly_readiness', methods=['GET'])
@login_required
def get_object_weekly_readiness(link_name):
    """Еженедельный процент готовности"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        print('       get_object_weekly_readiness')
        print(link_name)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects='objects',
                               left_panel='left_panel',
                               title='Еженедельный процент готовности')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/objects/<link_name>/statistics', methods=['GET'])
@login_required
def get_object_statistics(link_name):
    """Статистика проекта"""
    try:
        global hlink_menu, hlink_profile

        if app_login.current_user.get_role() not in (4):
            flash(message=['Запрещено изменять данные', ''], category='error')
            return error_handlers.handle403(403)

        user_id = app_login.current_user.get_id()
        print('       get_object_statistics')
        print(link_name)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects='objects',
                               left_panel='left_panel',
                               title='Статистика проекта')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


@project_app_bp.route('/objects/<link_name>/tasks', methods=['GET'])
@login_required
def get_object_tasks(link_name):
    """Проекты и задачи"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        print('       get_object_statistics')
        print(link_name)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects='objects',
                               left_panel='left_panel',
                               title='Задачи проекта')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


def get_header_menu(role: int = 0, link: str = '', cur_name: int = 0):
    # Админ и директор
    if role in (1, 4):
        header_menu = [
            {'link': f'/objects/{link}', 'name': 'Основное'},
            {'link': f'/objects/{link}/tow', 'name': 'Виды работ'},
            {'link': f'/objects/{link}/contracts-list', 'name': 'Договоры'},
            {'link': f'/objects/{link}/calendar-schedule', 'name': 'Календарный график'},
            {'link': f'/objects/{link}/weekly_readiness', 'name': 'Готовность проекта'},
            {'link': f'#', 'name': 'Состав проекта'},
            {'link': f'/objects/{link}/statistics', 'name': 'Статистика'},
            {'link': f'/objects/{link}/tasks', 'name': 'Проект и задачи'}
        ]
    else:
        header_menu = [
            {'link': f'/objects/{link}', 'name': 'Основное'},
            {'link': f'/objects/{link}/tow', 'name': 'Виды работ'},
            {'link': f'/objects/{link}/calendar-schedule', 'name': 'Календарный график'},
            {'link': f'/objects/{link}/weekly_readiness', 'name': 'Готовность проекта'},
            {'link': f'#', 'name': 'Состав проекта'},
            {'link': f'/objects/{link}/tasks', 'name': 'Проект и задачи'}
        ]
    header_menu[cur_name]['class'] = 'current'
    header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu


def get_milestones_menu(role: int = 0, link: str = '', cur_name: int = 0):
    # Вехи на листе tow
    if role in (1, 4):
        milestones = [
            {'func': f'getMilestones', 'name': 'ВЕХИ'},
            {'func': f'getReserves', 'name': 'РЕЗЕРЫ'},
            {'func': f'getContractsList', 'name': 'СПИСОК ДОГОВОРОВ'},
        ]
    else:
        milestones = [
            {'func': f'getMilestones', 'name': 'ВЕХИ'},
        ]
    return milestones


def conv_tow_data_upd(val, col_type):
    # Конвертируем значение в нужный тип
    if col_type == 'str':
        val = str(val)
    elif col_type == 'int':
        if not val:                 # Если данных нет, отправляем
            return None
        val = int(val)
    elif col_type == 'float':
        if not val:                 # Если данных нет, отправляем
            return None
        val = float(val)
    return val