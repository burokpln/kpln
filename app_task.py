import json
import time
from psycopg2.extras import execute_values
from pprint import pprint
from flask import g, request, render_template, redirect, flash, url_for, session, abort, get_flashed_messages, \
    jsonify, Blueprint, current_app, send_file
from datetime import date, datetime, timezone, timedelta
from flask_login import login_required
import error_handlers
import app_login
import app_payment
import app_contract
import app_project
from FDataBase import FDataBase
import pandas as pd
from openpyxl import Workbook
import os
import tempfile
import sys

task_app_bp = Blueprint('app_task', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None

# Список tow для tasks main
TOW_LIST = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        tow_id,
        tow_name,
        project_id,
        dept_id,
        time_tracking,
        parent_id,
        lvl,
		path,
        
        NULL::int AS task_id,
        ARRAY[lvl, tow_id] AS child_path
    FROM types_of_work
    WHERE parent_id IS NULL AND project_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.tow_id,
        n.tow_name,
        n.project_id,
        n.dept_id,
        n.time_tracking,
        n.parent_id,
        n.lvl,
		n.path,
        
        NULL::int AS task_id,
        r.child_path || n.lvl || n.tow_id
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.parent_id = r.tow_id
    WHERE r.project_id = %s
)
SELECT
    t0.depth,
	t0.tow_id,
	t0.task_id,
	t0.project_id,
	t0.dept_id,
	t0.time_tracking,
	t0.parent_id,
	t0.lvl,
	t0.path,
	
	t0.child_path,
	t0.tow_name

FROM rel_rec AS t0
LEFT JOIN (
    SELECT
        dept_id,
        dept_short_name
    FROM list_dept
) AS t1 ON t0.dept_id = t1.dept_id

UNION ALL
SELECT
	r1.depth + nlevel(t2.path) - 1 AS depth,
	r1.tow_id,
	t2.task_id,
	r1.project_id,
	r1.dept_id,
	r1.time_tracking,
	r1.parent_id,
	r1.lvl + 1,
	t2.path,
	
	r1.child_path || ARRAY[t2.lvl] || t2.task_id AS child_path,
	t2.task_name AS tow_name
FROM tasks AS t2
LEFT JOIN rel_rec AS r1 ON r1.tow_id=t2.tow_id
WHERE t2.parent_id IS NULL AND r1.project_id = %s

ORDER BY child_path, lvl;
"""

def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@task_app_bp.before_request
def before_request():
    app_login.before_request()


# Проверка, что пользователь не уволен
@task_app_bp.before_request
def check_user_status():
    app_login.check_user_status()


# Страница раздела 'Задачи' проекта
@task_app_bp.route('/objects/<link_name>/tasks', methods=['GET'])
@login_required
def get_all_tasks(link_name):
    """Страница раздела 'Задачи' проекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

        project = app_project.get_proj_info(link_name)

        # print(session)
        # print('_+____')

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        role = app_login.current_user.get_role()

        # Для обычных сотрудников не отображаем закрытые проекты
        where_query = " "
        if role not in (1, 4):
            where_query = " WHERE t2.project_close_status IS NOT true "


        # print(role, objects[0])
        # print(role, objects[1])

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()
        left_panel = list()

        if role in (1, 4):
            left_panel.extend([
                {'link': '/contract-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        elif role in (5, 6):
            left_panel.extend([
                {'link': '/contract-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        else:
            if is_head_of_dept is not None:
                left_panel.extend([{'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ'}, {'link': '#', 'name': 'ОТЧЁТЫ'}])
            left_panel.extend([
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])

        tep_info = True
        project = app_project.get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        proj = project[1]

        return render_template('task-main.html', menu=hlink_menu, menu_profile=hlink_profile,
                               left_panel=left_panel, nonce=get_nonce(), tep_info=tep_info, proj=proj,
                               title='Объекты, главная страница')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Страница раздела 'Задачи с подзадачами' проекта
@task_app_bp.route('/objects/<link_name>/tasks/<int:tow_id>', methods=['GET'])
@login_required
def get_tasks_on_id(link_name, tow_id):
    """Страница раздела 'Задачи с подзадачами' проекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

        project = app_project.get_proj_info(link_name)

        # print(session)
        # print('_+____')

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        role = app_login.current_user.get_role()

        # Для обычных сотрудников не отображаем закрытые проекты
        where_query = " "
        if role not in (1, 4):
            where_query = " WHERE t2.project_close_status IS NOT true "

        # Список объектов
        cursor.execute(
            f"""
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
            {where_query}
            ORDER BY t1.object_name;""")
        objects = cursor.fetchall()
        for i in range(len(objects)):
            objects[i] = dict(objects[i])
            if role not in [1, 4]:
                objects[i]['create_obj'] = ''
        # Список проектов
        cursor.execute(
            f"""
            SELECT
                t1.object_id,
                t1.object_name,
                COALESCE(t2.project_img_mini, '') AS project_img_mini,
                COALESCE(t2.project_close_status::text, '') AS project_close_status,
                CASE WHEN t2.project_close_status=false THEN t2.link_name ELSE '' END AS obj_link,
                CASE WHEN t2.project_close_status is null THEN concat_ws('/', 'objects', t1.object_id, 'create') ELSE '' END AS create_obj,
                CASE WHEN t2.project_close_status=false THEN 'часы' ELSE '' END AS project_and_tasks
            FROM projects AS t2
            LEFT JOIN (
                SELECT
                    object_id,
                    object_name
                FROM objects
            ) AS t1 ON t1.object_id = t2.object_id
            {where_query}
            ORDER BY t1.object_name;""")
        projects = cursor.fetchall()

        for i in range(len(projects)):
            projects[i] = dict(projects[i])
            if role not in [1, 4]:
                projects[i]['create_obj'] = ''

        # print(role, objects[0])
        # print(role, objects[1])

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()
        left_panel = list()

        if role in (1, 4):
            left_panel.extend([
                {'link': '/contract-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        elif role in (5, 6):
            left_panel.extend([
                {'link': '/contract-main', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        else:
            if is_head_of_dept is not None:
                left_panel.extend([{'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ'}, {'link': '#', 'name': 'ОТЧЁТЫ'}])
            left_panel.extend([
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])

        return render_template('task-tasks.html', menu=hlink_menu, menu_profile=hlink_profile, objects=objects,
                               projects=projects, left_panel=left_panel, nonce=get_nonce(),
                               title='Объекты, главная страница')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())



def get_header_menu(role: int = 0, link: str = '', cur_name: int = 0, is_head_of_dept=None):
    header_menu = []
    # Админ и директор
    if role in (1, 4):
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'Основное'},
            {'link': f'/objects/{link}/tow', 'name': 'Виды работ'},
            {'link': f'/objects/{link}/contract-list', 'name': 'Договоры'},
            {'link': f'/objects/{link}/calendar-schedule', 'name': 'Календарный график'},
            {'link': f'/objects/{link}/weekly_readiness', 'name': 'Готовность проекта'},
            {'link': f'#', 'name': 'Состав проекта'},
            {'link': f'/objects/{link}/statistics', 'name': 'Статистика'},
            {'link': f'/objects/{link}/tasks', 'name': 'Проект и задачи'}
        ])
    elif role == 5:
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'Основное'},
            {'link': f'/objects/{link}/contract-list', 'name': 'Договоры'},
            {'link': f'#', 'name': 'Состав проекта'}
        ])

    else:
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'Основное'},
            {'link': f'/objects/{link}/tow', 'name': 'Виды работ'},
            {'link': f'/objects/{link}/calendar-schedule', 'name': 'Календарный график'},
            {'link': f'/objects/{link}/weekly_readiness', 'name': 'Готовность проекта'},
            {'link': f'#', 'name': 'Состав проекта'},
            {'link': f'/objects/{link}/tasks', 'name': 'Проект и задачи'}
        ])
    header_menu[cur_name]['class'] = 'current'
    header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu

