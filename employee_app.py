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
import login_app
import payment_app
import pandas as pd
from openpyxl import Workbook
import os
import tempfile


employee_app_bp = Blueprint('object_app', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None


@employee_app_bp.before_request
def before_request():
    login_app.before_request()


# Главная страница раздела 'Объекты'
@employee_app_bp.route('/', methods=['GET'])
@login_required
def get_employees_list():
    """Главная страница раздела 'Объекты' """
    try:
        global hlink_menu, hlink_profile

        user_id = login_app.current_user.get_id()

        # Connect to the database
        conn, cursor = login_app.conn_cursor_init_dict()

        role = login_app.current_user.get_role()

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

        print(objects[0])

        login_app.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = login_app.func_hlink_profile()

        if role not in [1, 4]:
            left_panel = [
                {'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ (для руководителей)'},
                {'link': '#', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '#', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ]
        else:
            left_panel = [
                {'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ (для руководителей)'},
                {'link': '#', 'name': 'РЕЕСТР ДОГОВОРОВ'},
                {'link': '#', 'name': 'СОТРУДНИКИ'},
                {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ]

        return render_template('index-objects-main.html', menu=hlink_menu, menu_profile=hlink_profile,
                               objects=objects,
                               left_panel=left_panel,
                               title='Объекты, главная страница')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {login_app.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'objects-main: {e}'], category='error')
        return render_template('page_error.html')


