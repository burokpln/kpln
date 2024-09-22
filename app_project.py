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
from FDataBase import FDataBase
import pandas as pd
from openpyxl import Workbook
import os
import tempfile
import sys

project_app_bp = Blueprint('app_project', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None

TOW_LIST1 = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        t.*,
        ARRAY[t.lvl, t.tow_id] AS child_path,
        c.reserve_cost
    FROM types_of_work AS t
    LEFT JOIN (SELECT tow_id, reserve_cost FROM reserves WHERE reserve_type_id = %s) c on c.tow_id = t.tow_id
    WHERE parent_id IS NULL AND project_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.*,
        r.child_path || n.lvl || n.tow_id,
        cn.reserve_cost
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.parent_id = r.tow_id
    LEFT JOIN (SELECT tow_id, reserve_cost FROM reserves WHERE reserve_type_id = %s) cn on cn.tow_id = n.tow_id
    WHERE r.project_id = %s
)
SELECT
    DISTINCT t0.tow_id,
    t0.child_path,
    t0.tow_name,
    COALESCE(t1.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    t11.is_not_edited,
    
    t2.summary_contracts_cost AS tow_contract_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t2.summary_contracts_cost, '999 999 990D99 ₽')), '') AS tow_contract_cost_rub,
    t2.summary_fot_cost AS tow_fot_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t2.summary_fot_cost, '999 999 990D99 ₽')), '') AS tow_fot_cost_rub,
    t2.summary_expenditure_contracts_cost AS tow_expenditure_contract_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t2.summary_expenditure_contracts_cost, '999 999 990D99 ₽')), '') AS tow_expenditure_contract_cost_rub,
    t2.summary_expenditure_fot_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t2.summary_expenditure_fot_cost, '999 999 990D99 ₽')), '') AS summary_expenditure_fot_cost_rub,
    
    --0 AS child_sum,
    --'' AS child_sum_rub,
    --0 AS parent_percent_sum,
    
    t0.reserve_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t0.reserve_cost, '999 999 990D99 ₽')), '') AS reserve_cost_rub,
    
    CASE 
        WHEN t0.reserve_cost != 0 THEN null
        ELSE COALESCE(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), 0)
    END AS child_sum,
    
    CASE 
        WHEN t0.reserve_cost != 0 THEN ''
        ELSE COALESCE(TRIM(BOTH ' ' FROM to_char(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), '999 999 990D99 ₽')), '')
    END AS child_sum_rub,
    
    CASE 
        WHEN t0.parent_id IS NOT NULL THEN 
            ROUND((CASE 
                WHEN t0.reserve_cost != 0 THEN t0.reserve_cost
                ELSE COALESCE(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), null)
            END
            /
            SUM(tr.reserve_cost) OVER(PARTITION BY t0.parent_id))::numeric * 100,
                  2)
    END AS parent_percent_sum
    
    
FROM rel_rec AS t0
LEFT JOIN (
    SELECT
        dept_id,
        dept_short_name
    FROM list_dept
) AS t1 ON t0.dept_id = t1.dept_id
LEFT JOIN (
    SELECT t111.tow_id, true AS is_not_edited
        FROM (
            SELECT tow_id FROM tows_contract GROUP BY tow_id
            UNION ALL
            SELECT tow_id FROM tows_act GROUP BY tow_id
            UNION ALL
            SELECT tow_id FROM tows_payment GROUP BY tow_id
        ) AS t111
    GROUP BY t111.tow_id
) AS t11 ON t0.tow_id = t11.tow_id
LEFT JOIN (
    --сумма стоимостей договоров tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t51.type_id = 1 THEN
                CASE 
                    WHEN t52.tow_cost != 0 THEN t52.tow_cost / t51.vat_value::numeric
                    WHEN t52.tow_cost_percent != 0 THEN t52.tow_cost_percent * t51.contract_cost / (t51.vat_value * 100)::numeric
                    ELSE NULL
                END
            ELSE NULL
        END) AS summary_contracts_cost,
        SUM(CASE 
            WHEN t51.type_id = 1 THEN
                CASE 
                    WHEN t52.tow_cost != 0 THEN t52.tow_cost * t51.fot_percent / t51.vat_value::numeric
                    WHEN t52.tow_cost_percent != 0 THEN t52.tow_cost_percent * t51.contract_cost * t51.fot_percent / (t51.vat_value::numeric * 100)::numeric
                    ELSE NULL
                END
            ELSE NULL
        END) / 100 AS summary_fot_cost,
        SUM(CASE 
            WHEN t51.type_id = 2 THEN
                CASE 
                    WHEN t52.tow_cost != 0 THEN t52.tow_cost / t51.vat_value::numeric
                    WHEN t52.tow_cost_percent != 0 THEN t52.tow_cost_percent * t51.contract_cost / (t51.vat_value::numeric * 100)::numeric
                    ELSE NULL
                END
            ELSE NULL
        END) AS summary_expenditure_contracts_cost,
        SUM(CASE 
            WHEN t51.type_id = 2 THEN
                CASE 
                    WHEN t52.tow_cost != 0 THEN t52.tow_cost * t51.fot_percent / t51.vat_value::numeric
                    WHEN t52.tow_cost_percent != 0 THEN t52.tow_cost_percent * t51.contract_cost * t51.fot_percent / (t51.vat_value::numeric * 100)::numeric
                    ELSE NULL
                END
            ELSE NULL
        END) / 100 AS summary_expenditure_fot_cost
    FROM contracts AS t51
    RIGHT JOIN (
        SELECT
            contract_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_contract
    ) AS t52 ON t51.contract_id = t52.contract_id
    WHERE t51.object_id = %s AND t51.allow IS TRUE
    GROUP BY t52.tow_id--, t51.type_id
) AS t2 ON t0.tow_id = t2.tow_id

JOIN (
    SELECT
        tow_id,
        path,
        CASE 
            WHEN t0.reserve_cost != 0 THEN t0.reserve_cost
            ELSE null
        END AS reserve_cost
    FROM rel_rec AS t0
) AS tr ON tr.path <@ t0.path
ORDER BY child_path, lvl;
"""

# Дря рукОтдела
TOW_LIST_rukOtdela = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        t.*,
        ARRAY[t.lvl, t.tow_id] AS child_path,
        c.reserve_cost
    FROM types_of_work AS t
    LEFT JOIN (SELECT tow_id, reserve_cost FROM reserves WHERE reserve_type_id = %s) c on c.tow_id = t.tow_id AND t.dept_id = %s
    WHERE parent_id IS NULL AND project_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.*,
        r.child_path || n.lvl || n.tow_id,
        cn.reserve_cost
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.parent_id = r.tow_id
    LEFT JOIN (SELECT tow_id, reserve_cost FROM reserves WHERE reserve_type_id = %s) cn on cn.tow_id = n.tow_id AND n.dept_id = %s
    WHERE r.project_id = %s
)
SELECT
    DISTINCT t0.tow_id,
    t0.child_path,
    t0.tow_name,
    COALESCE(t1.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    true AS is_not_edited,

    t0.reserve_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t0.reserve_cost, '999 999 990D99 ₽')), '') AS reserve_cost_rub,
    
    t2.gip_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t2.gip_cost, '999 999 990D99 ₽')), '') AS gip_cost_rub,

    CASE 
        WHEN t0.reserve_cost != 0 THEN null
        ELSE COALESCE(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), 0)
    END AS child_sum,

    CASE 
        WHEN t0.reserve_cost != 0 THEN ''
        ELSE COALESCE(TRIM(BOTH ' ' FROM to_char(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), '999 999 990D99 ₽')), '')
    END AS child_sum_rub,

    CASE 
        WHEN t0.parent_id IS NOT NULL THEN 
            ROUND((CASE 
                WHEN t0.reserve_cost != 0 THEN t0.reserve_cost
                ELSE COALESCE(SUM(tr.reserve_cost) OVER(PARTITION BY t0.tow_id), null)
            END
            /
            SUM(tr.reserve_cost) OVER(PARTITION BY t0.parent_id))::numeric * 100,
                  2)
    END AS parent_percent_sum

FROM rel_rec AS t0
LEFT JOIN (
    SELECT
        dept_id,
        dept_short_name
    FROM list_dept
) AS t1 ON t0.dept_id = t1.dept_id
LEFT JOIN (
    --Резерв гипа
    SELECT 
        tow_id, 
        reserve_cost AS gip_cost
    FROM reserves WHERE reserve_type_id = 3
) AS t2 ON t0.tow_id = t2.tow_id
JOIN (
    SELECT
        tow_id,
        path,
        CASE 
            WHEN t0.reserve_cost != 0 THEN t0.reserve_cost
            ELSE null
        END AS reserve_cost
    FROM rel_rec AS t0
) AS tr ON tr.path <@ t0.path
ORDER BY child_path, lvl;
"""

# Для обычных сотрудников - без стоимостей
TOW_LIST = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        *,
        ARRAY[lvl, tow_id] AS child_path
    FROM types_of_work
    WHERE parent_id IS NULL AND project_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.*,
        r.child_path || n.lvl || n.tow_id
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.parent_id = r.tow_id
    WHERE r.project_id = %s
)
SELECT
    t0.tow_id,
    t0.child_path,
    t0.tow_name,
    COALESCE(t1.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    true AS is_not_edited
FROM rel_rec AS t0
LEFT JOIN (
    SELECT
        dept_id,
        dept_short_name
    FROM list_dept
) AS t1 ON t0.dept_id = t1.dept_id
ORDER BY child_path, lvl;
"""


def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@project_app_bp.before_request
def before_request():
    app_login.before_request()


# Проверка, что пользователь не уволен
@project_app_bp.before_request
def check_user_status():
    app_login.check_user_status()


# Главная страница раздела 'Объекты'
@project_app_bp.route('/', methods=['GET'])
@login_required
def objects_main():
    """Главная страница раздела 'Объекты' """
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

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
                # {'link': '#', 'name': 'НАСТРОЙКИ'},
                # {'link': '#', 'name': 'ОТЧЁТЫ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        elif role == 7:
            left_panel.extend([
                {'link': '/employees-list', 'name': 'СОТРУДНИКИ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])
        else:
            if is_head_of_dept is not None:
                left_panel.extend([{'link': '#', 'name': 'ПРОВЕРКА ЧАСОВ'}, {'link': '#', 'name': 'ОТЧЁТЫ'}])
            left_panel.extend([
                # {'link': '#', 'name': 'НАСТРОЙКИ'},
                {'link': '/payments', 'name': 'ПЛАТЕЖИ'}
            ])

        return render_template('index-objects-main.html', menu=hlink_menu, menu_profile=hlink_profile, objects=objects,
                               projects=projects, left_panel=left_panel, nonce=get_nonce(),
                               title='Объекты, главная страница')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@project_app_bp.route('/objects/<obj_id>/create', methods=["GET", "POST"])
@login_required
def create_project(obj_id):
    """Страница видов работ"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        role = app_login.current_user.get_role()

        if request.method == 'GET':
            try:
                # print('                ----   get_create_project')
                # print(obj_id)

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

                # print(object_name)

                # Список ГИПов
                cursor.execute(
                    """
                    SELECT 
                        user_id, last_name, first_name 
                    FROM users 
                    WHERE is_fired = FALSE 
                    ORDER BY last_name, first_name
                    """)
                gip = cursor.fetchall()

                app_login.conn_cursor_close(cursor, conn)

                return render_template('object-create.html', menu=hlink_menu, menu_profile=hlink_profile, gip=gip,
                                       object_name=object_name, nonce=get_nonce(), left_panel='left_panel',
                                       title=f"{object_name.upper()} - СОЗДАТЬ ПРОЕКТ")

            except Exception as e:
                msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
                return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())

        elif request.method == 'POST':
            try:
                # print('                   set_create_project')
                # print(obj_id)

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

                # pprint([{
                #         'obj_id':obj_id,
                #         'project_full_name': project_full_name,
                #         'project_short_name': project_short_name,
                #         'customer': customer,
                #         'project_address': project_address,
                #         'gip_id': gip_id,
                #         # status_id,
                #         'project_total_area': project_total_area,
                #         'project_title': project_title,
                #         'project_img': project_img,
                #         'project_img_middle': project_img_middle,
                #         'project_img_mini': project_img_mini,
                #         'link_name': link_name,
                #         'owner': owner
                #     }])

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
                msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
                return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info())
        flash(message=['Ошибка', f'object-create: {sys.exc_info()}'], category='error')
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Главная страница объекта
@project_app_bp.route('/objects/<link_name>', methods=['GET'])
@login_required
def get_object(link_name):
    """Главная страница объекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link_name, user_id=user_id)

        role = app_login.current_user.get_role()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

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

        # Список ГИПов
        cursor.execute(
            """
            SELECT 
                user_id, 
                last_name, 
                first_name,
                surname,
                concat_ws(' ', last_name, LEFT(first_name, 1) || '.', CASE
                    WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
                END) AS short_full_name
            FROM users 
            WHERE is_fired = FALSE 
            ORDER BY last_name, first_name;""")
        gip_list = cursor.fetchall()
        for i in range(len(gip_list)):
            gip_list[i] = dict(gip_list[i])

        # Список всех заказчиков
        cursor.execute(
            """
            SELECT 
                DISTINCT(customer) AS customer
            FROM projects 
            ORDER BY customer;""")
        customer_list = cursor.fetchall()
        for i in range(len(customer_list)):
            customer_list[i] = dict(customer_list[i])

        if project:
            project = dict(project)
        else:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))

        project['gip_name'] = f"""{gip_name['last_name']} {gip_name['first_name'][0]}.{
        gip_name['surname'][0] + '.' if gip_name['surname'] else ''}"""

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=0, is_head_of_dept=is_head_of_dept)

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

        # Статус, что пользователь может редактировать карточку (он ГИП или админ)
        if project['gip_id'] == user_id or role in (1, 4):
            is_editor = True
        else:
            is_editor = False

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile, proj=project,
                               left_panel='left_panel', header_menu=header_menu, tep_info=tep_info, nonce=get_nonce(),
                               gip_list=gip_list, customer_list=customer_list, is_editor=is_editor,
                               title=f"{project['object_name']} - Объекты, главная страница")

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Сохранение изменения карточки проекта
@project_app_bp.route('/save_project/<link>', methods=['POST'])
@login_required
def save_project(link: str):
    """Сохранение изменения карточки проекта"""
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link, user_id=user_id)

        role = app_login.current_user.get_role()

        print('request.get_json()')
        print(request.get_json())

        customer = request.get_json()['customer']
        project_full_name = request.get_json()['project_full_name']
        project_address = request.get_json()['project_address']
        gip_id = int(request.get_json()['gip_id']) if request.get_json()['gip_id'].isdigit() else None
        project_total_area = request.get_json()['project_total_area']
        try:
            project_total_area = float(project_total_area)
        except ValueError:
            project_total_area = None

        if not gip_id:
            return jsonify({
                'status': 'error',
                'description': ['Не указан ГИП'],
            })
        if not project_total_area:
            return jsonify({
                'status': 'error',
                'description': ['Не указана площадь'],
            })

        project = get_proj_info(link)
        if project[0] == 'error':
            return jsonify({
                'status': 'error',
                'description': [project[1]],
            })
        elif not project[1]:
            return jsonify({
                'status': 'error',
                'description': ['ОШИБКА. Проект не найден'],
            })

        project = project[1]

        print('project', project)

        values_p_upd = list((project['project_id'],))
        columns_project = ['project_id::smallint', 'customer::text', 'project_full_name::text', 'project_address::text',
                           'gip_id::smallint', 'project_total_area::numeric']
        columns_p_upd = list(('project_id',))
        # Проверяем, какие данные были изменены
        if customer != project['customer']:
            values_p_upd.append(customer)
            columns_p_upd.append('customer')
        if project_full_name != project['project_full_name']:
            values_p_upd.append(project_full_name)
            columns_p_upd.append('project_full_name')
        if project_address != project['project_address']:
            values_p_upd.append(project_address)
            columns_p_upd.append('project_address')
        if gip_id != project['gip_id']:
            values_p_upd.append(gip_id)
            columns_p_upd.append('gip_id')
        if project_total_area != project['project_total_area']:
            values_p_upd.append(project_total_area)
            columns_p_upd.append('project_total_area')

        if len(columns_p_upd) > 1:
            action = 'UPDATE'
            table_p= 'projects'
            query_ta_upd = app_payment.get_db_dml_query(action=action, table=table_p, columns=columns_p_upd)
            print(action)
            print(query_ta_upd)
            pprint(values_p_upd)

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('objects')

            execute_values(cursor, query_ta_upd, (values_p_upd,))
            conn.commit()

            app_login.conn_cursor_close(cursor, conn)

            flash(message=['Карточка проекта обновлена', ''], category='success')
            return jsonify({
                'status': 'success',
                'link': link,
            })
        else:
            flash(message=['Изменений не найдено', ''], category='success')
            return jsonify({
                'status': 'success',
                'link': link,
            })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@project_app_bp.route('/objects/<link_name>/tow', methods=['GET'])
@login_required
def get_type_of_work(link_name):
    """Страница видов работ"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link_name, user_id=user_id)

        role = app_login.current_user.get_role()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

        # Статус, что пользователь может редактировать карточку (он ГИП, рукОтдела, админ)
        is_editor = False

        # ТЭПы и информация о готовности проекта
        tep_info = False

        # Панель вех
        milestones = get_milestones_menu(role, link=link_name, cur_name=1)

        ####################################################################################################
        # Если страница открыта админом, руководством или ГИПом
        ####################################################################################################
        if project['gip_id'] == user_id or role in (1, 4):
            # Тип распределения (пока это ГИП - id 3)
            if project['gip_id'] == user_id:
                res_type_id = 3
            elif role in (1, 4):
                res_type_id = 2

            # Список tow
            cursor.execute(
                TOW_LIST1,
                [res_type_id, project['project_id'],
                 res_type_id, project['project_id'],
                 project['object_id']]
            )
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])


            # Сумма распределенных средств ГИПа
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(reserve_cost), 0) AS contract_cost,
                    COALESCE(TRIM(BOTH ' ' FROM to_char(SUM(reserve_cost), '999 999 990D99 ₽')), '') AS contract_cost_rub
                FROM reserves 
                WHERE reserve_type_id = %s AND tow_id IN (SELECT tow_id FROM types_of_work WHERE project_id = %s)
                """,
                [res_type_id, project['project_id']]
            )
            reserve_cost = cursor.fetchone()
            print('reserve_cost', reserve_cost)

            # Добавляем нераспределенное ГИПом в milestones
            tmp_dict = {
                'func': f'',
                'name': 'РАСП.: \n' + reserve_cost[1],
                'contract_cost': reserve_cost[0],
                'title': 'Общая сумма распределенных средств',
                'id': 'id_div_milestones_contractCost'
            }
            milestones.append(tmp_dict)

            is_editor = True
            tep_info = 1

        ####################################################################################################
        # Если страница открыта админом, руководством или ГИПом
        ####################################################################################################
        elif is_head_of_dept:
            is_head_of_dept = is_head_of_dept[0]
            tep_info = 'rukOtdela'
            res_type_id = 4

            # Список tow
            cursor.execute(
                TOW_LIST_rukOtdela,
                [res_type_id, is_head_of_dept, project['project_id'],
                 res_type_id, is_head_of_dept, project['project_id']]
            )
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])

            # Сумма распределенных средств ГИПа
            cursor.execute(
                """
                SELECT 
                    SUM(reserve_cost) AS contract_cost,
                    COALESCE(TRIM(BOTH ' ' FROM to_char(SUM(reserve_cost), '999 999 990D99 ₽')), '') AS contract_cost_rub
                FROM reserves 
                WHERE reserve_type_id = %s AND tow_id IN (SELECT tow_id FROM types_of_work WHERE project_id = %s AND dept_id = %s)
                """,
                [res_type_id, project['project_id'], is_head_of_dept]
            )
            reserve_cost = cursor.fetchone()
            print('reserve_cost', reserve_cost)
        else:
            # Список tow
            cursor.execute(
                TOW_LIST,
                [project['project_id'], project['project_id']]
            )
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])

        # Список отделов без подразделений
        dept_list = get_main_dept_list(user_id)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=1, is_head_of_dept=is_head_of_dept)

        print('tep_info', tep_info)

        return render_template('object-tow.html', menu=hlink_menu, menu_profile=hlink_profile, proj=project, tow=tow,
                               left_panel='left_panel', header_menu=header_menu, milestones=milestones,
                               dept_list=dept_list, nonce=get_nonce(), tep_info=tep_info, is_editor=is_editor,
                               title=f"{project['object_name']} - Виды работ")

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


def get_main_dept_list(user_id):
    """Получаем список отделов (без подотделов)"""
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')
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

        app_login.conn_cursor_close(cursor, conn)
        return dept_list
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return False


@project_app_bp.route('/save_tow_changes/<link_name>', methods=['POST'])
@project_app_bp.route('/save_contract/<contract_id>', methods=['POST'])
@project_app_bp.route('/save_contract/new/<link_name>/<int:contract_type>/<int:subcontract>', methods=['POST'])
@project_app_bp.route('/save_contract/new/<int:contract_type>/<int:subcontract>', methods=['POST'])
@login_required
def save_tow_changes(link_name=None, contract_id=None, contract_type=None, subcontract=None):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name,
                               log_description=f"link_name: {link_name}, contract_id: {contract_id}", user_id=user_id)

        print('save_tow_changes', request.get_json())
        # print('- - - - - - - - request.get_json() - - - - - - - -')
        # print(request.path.split('/'))
        # print(request.get_json())
        # print('_ ' * 30)
        user_changes = request.get_json()['userChanges']
        edit_description = request.get_json()['editDescrRowList']
        new_tow = request.get_json()['list_newRowList']
        deleted_tow = request.get_json()['list_deletedRowList']
        reserves_changes = False

        description = list()  # Описание результата сохранения

        is_head_of_dept = False  # Статус, является ли пользователь руководителем отдела
        role = app_login.current_user.get_role()
        req_path = request.path.split('/')[1]
        project = None  # Информация о проекте

        contract_tow_list = None
        checked_list = set()

        ctr_card = None
        data_new_contract = None
        data_old_contract = None

        # Проверка списка tow на актуальность; ищем object_id, project_id, link_name
        if req_path == 'save_contract':
            # Если сохранение из договора, проверяем, что это админ, рук, юрист
            if role not in (1, 4, 5):
                return {
                    'status': 'error',
                    'description': ["Ограничен доступ для внесения нового договора"]
                }

            contract_tow_list = request.get_json()['list_towList']
            ctr_card = request.get_json()['ctr_card']

            # Если пересохраняем договор и не указали описание изменений
            if contract_id and not ctr_card['text_comment']:
                flash(message=['Ошибка', 'Изменения не сохранены', 'Описание изменений не найдено'], category='error')
                return jsonify({
                    'contract': 0,
                    'status': 'error',
                    'description': [['Изменения не сохранены', 'Описание изменений не найдено']],
                })

            if len(contract_tow_list):
                for i in contract_tow_list:
                    checked_list.add(i['id'])

            object_id = int(request.get_json()['ctr_card']['object_id'])
            proj_info = app_contract.get_proj_id(object_id=object_id)
            project_id = proj_info['project_id']
            link_name = proj_info['link_name']
            ctr_card['project_id'] = project_id
            ctr_card['link_name'] = link_name
        else:
            proj_info = app_contract.get_proj_id(link_name=link_name)
            object_id = proj_info['object_id']
            project_id = proj_info['project_id']
            link_name = proj_info['link_name']

            reserves_changes = request.get_json()['reservesChanges']

            # Проверка прав на изменение списка tow и пр.
            project = get_proj_info(link_name)
            if project[0] == 'error':
                flash(message=project[1], category='error')
                return redirect(url_for('.objects_main'))
            elif not project[1]:
                flash(message=['ОШИБКА. Проект не найден'], category='error')
                return redirect(url_for('.objects_main'))
            project = project[1]

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('contracts')

            is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)
            ###############################################################
            # ПРоверка, что отдел привязан к проекту
            ##########################################
            app_login.conn_cursor_close(cursor, conn)

            if project['gip_id'] == user_id or role in (1, 4) or is_head_of_dept:
                pass
            else:
                return {
                    'status': 'error',
                    'description': ["Ограничен доступ для внесения изменений"]
                }

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        if edit_description:
            checked_list.update(edit_description.keys())
        if deleted_tow:
            checked_list.update(deleted_tow)
        if new_tow:
            checked_list.update(new_tow)
        if user_changes:
            checked_list.update(user_changes.keys())
            for k, v in user_changes.items():
                if 'parent_id' in v:
                    checked_list.add(v['parent_id'])

        tow_is_actual = tow_list_is_actual(checked_list=checked_list, project_id=project_id, user_id=user_id)
        if not tow_is_actual[0]:
            flash(message=['Ошибка', tow_is_actual[1]], category='error')
            return jsonify({
                'contract': 0,
                'status': 'error',
                'description': [tow_is_actual[1]],
            })

        # Отдельная проверка для списка удаляемых tow
        if deleted_tow:
            contract_id = None
            if req_path == 'save_contract':
                contract_id = int(ctr_card['contract_id']) if ctr_card['contract_id'] != 'new' else None
            tow_is_actual = tow_list_is_actual(checked_list=set(deleted_tow), object_id=object_id,
                                               project_id=project_id,
                                               user_id=user_id, tow='delete', contract_id=contract_id,
                                               contract_deleted_tow=set(deleted_tow))
            if not tow_is_actual[0]:
                # flash(message=['Ошибка', tow_is_actual[1]], category='error')
                return jsonify({
                    'contract': 0,
                    'status': 'error',
                    'description': tow_is_actual[1],
                })

        # Если сохранение из карточки договора
        if req_path == 'save_contract':
            if role not in (1, 4, 5):
                flash(message=['Ошибка', 'Доступ запрещен'], category='error')
                return jsonify({
                    'contract': 0,
                    'status': 'error',
                    'description': ['Доступ запрещен'],
                })

            ######################################################################################
            # Проверяем,что список tow_contract и манипуляции со списком tow валидны
            ######################################################################################
            check_contract_data = app_contract.check_contract_data_for_correctness(ctr_card, contract_tow_list, role,
                                                                                   user_id)
            if check_contract_data['status'] == 'error':
                # print(check_contract_data['description'])
                return jsonify({'status': 'error', 'description': [check_contract_data['description']]})
            else:
                # print('757', check_contract_data.keys(), check_contract_data['data_contract'].keys())
                data_status = check_contract_data['status']
                description.extend(check_contract_data['description'])
                # print('760', description)
                if 'new_contract' in check_contract_data['data_contract'].keys():
                    data_new_contract = check_contract_data['data_contract']['new_contract']
                    change_log = data_new_contract['change_log']
                    data_new_contract['user_id'] = user_id
                elif 'old_contract' in check_contract_data['data_contract'].keys():
                    data_old_contract = check_contract_data['data_contract']['old_contract']
                    change_log = data_old_contract['change_log']
                    data_old_contract['user_id'] = user_id
            # Если список tow не был изменен, обновляем данные договора
            if [user_changes, edit_description, new_tow, deleted_tow] == [None, None, None, None]:
                if role not in (1, 4, 5):
                    contract_status = {
                        'status': 'error',
                        'description': ['Доступ запрещен']
                    }
                    description.extend(contract_status['description'])
                else:
                    if data_new_contract:
                        contract_status = app_contract.save_contract(new_contract=data_new_contract)
                    elif data_old_contract:
                        contract_status = app_contract.save_contract(old_contract=data_old_contract)
                    else:
                        contract_status = {
                            'status': 'error',
                            'description': ['Ошибка сохранения договора', 'Отсутствую данные для сохранения']
                        }
                    description.extend(contract_status['description'])
                if contract_status['status'] == 'error':
                    # flash(message=['Ошибка', f'Сохранение данных контракта: '
                    #                          f'{contract_status["description"]}'], category='error')
                    return jsonify({'status': 'error', 'description': description})
                else:
                    if 'Договор: Договор и виды работ договора не были изменены' in description:
                        # flash(message=['Изменения сохранены', description[0], 'Проект: Проект не был изменен'],
                        # category='info')
                        # description.append('!!!!Проект: Проект не был изменен')
                        description.insert(0, 'Изменений не найдено')
                        description.insert(1, '')
                        description.append('Проект: Проект не был изменен')
                        contract_id = contract_status['contract_id']
                        return jsonify({'status': 'success', 'contract_id': contract_id, 'description': description,
                                        'without_change': True})
                    else:
                        message = ['Изменения сохранены', '']
                        message.extend(description)
                        message.append('Проект: Проект не был изменен')
                        flash(message=message, category='success')
                        description.append('Проект: Проект не был изменен')
                        contract_id = contract_status['contract_id']
                        return jsonify({'status': 'success', 'contract_id': contract_id, 'description': description})

                    # flash(message=['Изменения сохранены', description[0], 'Проект: Проект не был изменен'],
                    # category='success')
                    # description.append('Проект: Проект не был изменен')
                    # contract_id = contract_status['contract_id']
                    # return jsonify({'status': 'success', 'contract_id': contract_id, 'description': description})

        conn, cursor = app_login.conn_cursor_init_dict('objects')

        ######################################################################################
        # Проверяем, что список tow_contract и манипуляции со списком tow валидны
        ######################################################################################
        if req_path == 'save_contract' and (len(new_tow) or len(deleted_tow)):
            for ctl in contract_tow_list:
                if ctl['id'] in deleted_tow:
                    print('        __________удаляем что-то, что не должны')

        ######################################################################################
        # Если добавлялись новые строки
        ######################################################################################
        values_new_tow = []
        sorted_new_tow = []
        new_tow_dict = {}
        new_tow_dict_reverse = {}
        new_tow_set = set()
        if len(new_tow):
            # Список новых tow value
            columns_tow = (
            'tow_name', 'project_id', 'dept_id', 'time_tracking', 'parent_id', 'lvl', 'owner', 'last_editor')

            for tow in new_tow:
                tmp_1 = 'Название не задано'  # tow_name
                tmp_2 = ''  # project_id
                tmp_3 = None  # dept_id
                tmp_4 = 'false'  # time_tracking
                tmp_5 = None  # parent_id - пока оставляем пустым
                tmp_6 = ''  # lvl
                tmp_7 = user_id  # owner
                tmp_8 = user_id  # last_editor

                if tow in edit_description:
                    if 'input_tow_name' in edit_description[tow]:
                        tmp_1 = edit_description[tow]['input_tow_name']
                    if 'select_tow_dept' in edit_description[tow]:
                        tmp_3 = edit_description[tow]['select_tow_dept']
                        if tmp_3 == 'None' or tmp_3 == '':
                            tmp_3 = None
                    if 'checkbox_time_tracking' in edit_description[tow] and req_path != 'save_contract':
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
                    tmp_7,  # owner
                    tmp_8,  # last_editor
                ])
                sorted_new_tow.append([tow, tmp_6])

            values_new_tow = sorted(values_new_tow, key=lambda x: x[-3])
            sorted_new_tow = sorted(sorted_new_tow, key=lambda x: x[-1])

            action_new_tow = 'INSERT INTO'
            table_new_tow = 'types_of_work'
            columns_new_tow = ('tow_name::text', 'project_id::smallint', 'dept_id::smallint', 'time_tracking::boolean',
                               'parent_id::integer', 'lvl::smallint', 'owner::integer', 'last_editor::integer')
            subquery_new_tow = " ON CONFLICT DO NOTHING RETURNING tow_id;"

            expr_tow = ', '.join([f"{col} = t1.{col} + EXCLUDED.{col}" for col in columns_new_tow[:-1]])
            query_tow = app_payment.get_db_dml_query(action=action_new_tow, table=table_new_tow, columns=columns_tow,
                                                     subquery=subquery_new_tow)
            print('- - - - - - - - INSERT INTO types_of_work - - - - - - - -', query_tow, values_new_tow, sep='\n')

            execute_values(cursor, query_tow, values_new_tow, page_size=len(values_new_tow))
            tow_id = cursor.fetchall()

            conn.commit()

            # Список старых и новых id для вновь созданных tow
            values_new_tow_old = values_new_tow
            values_new_tow = dict()
            for i in range(len(tow_id)):
                values_new_tow[tow_id[i][0]] = values_new_tow_old[i]
                new_tow_dict[sorted_new_tow[i][0]] = tow_id[i][0]
                new_tow_dict_reverse[tow_id[i][0]] = sorted_new_tow[i][0]
                new_tow_set.add(tow_id[i][0])

            print('_' * 30, '\nnew_tow_dict')
            pprint(new_tow_dict)
            print('new_tow_dict_reverse')
            pprint(new_tow_dict_reverse)
            print('new_tow_set')
            print(new_tow_set, '\n','_' * 30)
            print('values_new_tow')
            print(values_new_tow, '\n', '_' * 30)

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
                print('- - - - - - - - UPDATE - - - - - - - -', query_new_tow_upd, values_new_tow_upd, sep='\n')
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
                'lvl': ['lvl', 'int', '::smallint'],
                'last_editor': ['last_editor', 'int', 'last_editor::integer']
            }
            if not edit_description.keys():
                for k, v in user_changes.items():
                    edit_description[int(k)] = user_changes[k]
            elif user_changes.keys() and edit_description.keys():
                for k in list(edit_description.keys())[:]:
                    if k in user_changes:
                        for k1, v1 in user_changes[k].items():
                            edit_description[k][k1] = v1
                        edit_description[int(k)] = edit_description.pop(k)
                        user_changes.pop(k)
                for k in list(user_changes.keys())[:]:
                    edit_description[k] = user_changes[k]
                    edit_description[int(k)] = edit_description.pop(k)
                    user_changes.pop(k)
            else:
                for k in list(edit_description.keys())[:]:
                    if isinstance(k, str):
                        edit_description[int(k)] = edit_description.pop(k)

            # print('_-^-_' * 10, '\n- - - - - - - - edit_description - - - - - - - -')
            # pprint(edit_description)
            # print('_-^-_' * 10, '\n- - - - - - - - user_changes - - - - - - - -')
            # pprint(user_changes)
            # print('_-^-_' * 10)

            for k, v in edit_description.items():
                columns_tow_upd = ["tow_id::integer", "last_editor::integer"]
                values_tow_upd = [[k, user_id]]
                for k1, v1 in edit_description[k].items():
                    if k1 in col_dict:
                        columns_tow_upd.append(col_dict[k1][0] + col_dict[k1][2])
                        values_tow_upd[0].append(
                            conv_tow_data_upd(val=v1, col_type=col_dict[k1][1])
                        )

                query_tow_upd = app_payment.get_db_dml_query(action='UPDATE', table='types_of_work',
                                                             columns=columns_tow_upd)
                execute_values(cursor, query_tow_upd, values_tow_upd)
                conn.commit()

        ######################################################################################
        # Если удалялись строки если были
        ######################################################################################
        # print('  *   *   *   *   *   deleted_tow')
        # print(deleted_tow)
        if len(deleted_tow):
            columns_del_tow = 'tow_id'
            valued_del_tow = []
            for i in deleted_tow:
                valued_del_tow.append((int(i),))

            query_del_tow = app_payment.get_db_dml_query(action='DELETE', table='types_of_work',
                                                         columns=columns_del_tow)
            execute_values(cursor, query_del_tow, (valued_del_tow,))
            conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        # Если сохранение из карточки договора, то сохраняем договорные данные
        if req_path == 'save_contract':
            # Изменяем tow_id для новых tow
            if len(new_tow):
                # print('857', contract_tow_list)
                for i in contract_tow_list[:]:
                    if i['id'] in new_tow_dict:
                        i['id'] = new_tow_dict[i['id']]
                        # contract_tow_list[new_tow_dict[k]] = contract_tow_list.pop(k)
                # print('863', contract_tow_list)

                # for k in list(contract_tow_list.keys())[:]:
                #     if k in new_tow_dict:
                #         contract_tow_list[new_tow_dict[k]] = contract_tow_list.pop(k)

            # print(['        ctr_card', ctr_card])
            # print('        contract_tow_list')
            # for i in contract_tow_list:
            #     print(['_  _  _  _', contract_tow_list])

            # Список новых tow для логирования
            if data_new_contract:
                data_contract = data_new_contract
                data_new_contract['tow_id_list_ins'] = None
                data_contract_keys = data_new_contract.keys()
                values_tc_ins = data_new_contract['values_tc_ins']
                tow_id_list_ins = set()
            elif data_old_contract:
                data_contract = data_old_contract
                # print('data_contract')
                # print(data_contract)
                data_old_contract['tow_id_list_ins'] = None
                data_contract_keys = data_old_contract.keys()
                if 'values_tc_ins' in data_contract_keys:
                    values_tc_ins = data_old_contract['values_tc_ins']['values_tc_ins']
                else:
                    values_tc_ins = set()
                tow_id_list_ins = set()
            else:
                contract_status = {
                    'status': 'error',
                    'description': ['Ошибка сохранения договора', 'Отсутствую данные для сохранения']
                }

            if 'values_tc_ins' in data_contract_keys:
                for i in values_tc_ins:
                    # print('____________ i[1]', i[1], 'new_tow_dict.keys()', new_tow_dict.keys())
                    if i[1] in new_tow_dict.keys():
                        i[1] = new_tow_dict[i[1]]
                        tow_id_list_ins.add(i[1])

                        tow_name = values_new_tow[i[1]][0]
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        if i[2]:
                            cl_02_tow_ins = f" - {tow_name}: стоимость ({i[2]} ₽)"
                        elif i[3]:
                            cl_02_tow_ins = f" - {tow_name}: % суммы ({i[3]} %)"
                        else:
                            cl_02_tow_ins = f" - {tow_name}: стоимость не указана"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)
                    else:
                        tow_id_list_ins.add(i[1])
                        tow_id = i[1]

                data_contract['tow_id_list_ins'] = tow_id_list_ins

            if data_new_contract:
                # Ждём, чтобы подписка TOW обновилась в БД kpln_contracts
                time.sleep(3)
                contract_status = app_contract.save_contract(new_contract=data_contract)
            elif data_old_contract:
                # Ждём, чтобы подписка TOW обновилась в БД kpln_contracts
                time.sleep(3)
                contract_status = app_contract.save_contract(old_contract=data_contract)

            description.extend(contract_status['description'])

            if contract_status['status'] == 'error':
                # flash(message=['Ошибка', f'Сохранение данных контракта: '
                #                          f'{contract_status["description"]}'], category='error')
                return jsonify({'status': 'error', 'description': description})
            contract_id = contract_status['contract_id']

        print('req_path', req_path)
        if req_path == 'save_tow_changes' and reserves_changes:
            # Информация о проекте
            #project = get_proj_info(link_name)[1]
            reserve_type_id = 0

            if project['gip_id'] == user_id or role in (1, 4):
                if project['gip_id'] == user_id:
                    reserve_type_id = 3
                elif role in (1, 4):
                    reserve_type_id = 2

                print(new_tow_dict, new_tow_dict.keys())
                print('reserves_changes___', reserves_changes)

                # if new_tow_dict:
                for k in list(reserves_changes.keys())[:]:
                    if k in new_tow_dict.keys():
                        tmp = reserves_changes.pop(k)
                        tmp = tmp if tmp else None
                        reserves_changes[new_tow_dict[k]] = tmp
                    else:
                        tmp = reserves_changes.pop(k)
                        tmp = tmp if tmp else None
                        reserves_changes[int(k)] = tmp
                # if new_tow_dict:
                #     for k, v in new_tow_dict.items():
                #         if k in reserves_changes.keys():
                #             reserves_changes[v] = reserves_changes.pop(k)

                print(reserves_changes)

                print('save_reserves:', 'user_id:', user_id, 'reserve_type_id:', reserve_type_id, 'project_id',
                      project['project_id'])
                save_reserves(reserves_changes, user_id, reserve_type_id, project['project_id'])


        # if description != '':
        #     description = ['', description]
        description = [description]
        message = ['Изменения сохранены', '']
        message.extend(description[0])
        if len(new_tow) or user_changes.keys() or edit_description.keys() or len(deleted_tow):
            # print(11111111111111111111)
            # print(description)
            message.append('Проект: Изменения сохранены')
            flash(message=message, category='success')
            description.append('Проект: Изменения сохранены')
        else:
            # print(22222222222222222222)
            message.append('Проект: Проект не был изменен')
            flash(message=message, category='success')
            description.append('Проект: Проект не был изменен')
        return jsonify({'status': 'success', 'contract_id': contract_id, 'description': description})
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error',
                        'description': [msg_for_user],
                        })


def save_reserves(reserves: dict, user_id: int, reserve_type_id: int, project_id: int):
    # try:
    app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=project_id, user_id=user_id)

    print('save_reserves:', 'user_id:', user_id, 'reserve_type_id:', reserve_type_id, 'project_id', project_id)

    # Connect to the database
    conn, cursor = app_login.conn_cursor_init_dict("objects")

    # Список tow
    cursor.execute(
        """
            SELECT 
                tow_id, 
                reserve_cost 
            FROM reserves 
            WHERE reserve_type_id = %s AND tow_id IN (SELECT tow_id FROM types_of_work WHERE project_id = %s);
        """,
        (reserve_type_id, project_id)
    )

    tow = cursor.fetchall()

    values_r_ins = list()
    values_r_upd = list()
    values_r_del = list()

    tow_db_list = dict()
    # Преобразовываем данные из БД
    if tow:
        for i in range(len(tow)):
            tow_db_list[tow[i][0]] = tow[i][1]
    print('tow_db_list', '\n', tow_db_list)
    # Проходим по каждой паре k, v и формируем списки добавления, изменения, удаления
    for k, v in reserves.items():
        if k in tow_db_list.keys():
            if not v:
                values_r_del.append((k, reserve_type_id))
            if tow_db_list[k] != v:
                values_r_upd.append((k, reserve_type_id, v, user_id))
        else:
            if not v:
                values_r_del.append((k, reserve_type_id))
            else:
                values_r_ins.append((reserve_type_id, k, v, user_id, user_id))

    table_r = 'reserves'
    subquery = 'ON CONFLICT DO NOTHING'

    if values_r_del:
        action = 'DELETE'
        columns_r_del = 'tow_id::int, reserve_type_id::int'
        query_r_del = app_payment.get_db_dml_query(action=action, table=table_r, columns=columns_r_del,
                                                    subquery=subquery)
        print(action)
        print(query_r_del)
        print(values_r_del)
        execute_values(cursor, query_r_del, (values_r_del,))
    if values_r_ins:
        action = 'INSERT INTO'
        columns_r_ins = ('reserve_type_id', 'tow_id', 'reserve_cost', 'owner', 'last_editor')
        query_r_ins = app_payment.get_db_dml_query(action=action, table=table_r, columns=columns_r_ins,
                                                    subquery=subquery)
        print(action)
        print(query_r_ins)
        print(values_r_ins)
        execute_values(cursor, query_r_ins, values_r_ins)
    if values_r_upd:
        action = 'UPDATE DOUBLE'
        columns_r_upd = [['tow_id::int', 'reserve_type_id::int'], 'reserve_cost::numeric', 'last_editor::numeric']
        query_r_upd = app_payment.get_db_dml_query(action=action, table=table_r, columns=columns_r_upd)
        print(action)
        print(query_r_upd)
        print(values_r_upd)
        execute_values(cursor, query_r_upd, values_r_upd)

    if values_r_del or values_r_ins or values_r_upd:
        conn.commit()

    app_login.conn_cursor_close(cursor, conn)

    # except Exception as e:
    #     msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
    #     return jsonify({'status': 'error',
    #                     'description': [msg_for_user],
    #                     })


@project_app_bp.route('/objects/<link_name>/calendar-schedule', methods=['GET'])
@login_required
def get_object_calendar_schedule(link_name):
    """Календарный график"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link_name, user_id=user_id)

        # print('       get_object_calendar_schedule')
        # print(link_name)

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile, nonce=get_nonce(),
                               objects='objects', left_panel='left_panel', proj=project,
                               title='Календарный график')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@project_app_bp.route('/objects/<link_name>/weekly_readiness', methods=['GET'])
@login_required
def get_object_weekly_readiness(link_name):
    """Еженедельный процент готовности"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link_name, user_id=user_id)
        # print('       get_object_weekly_readiness')
        # print(link_name)

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile, objects='objects',
                               left_panel='left_panel', nonce=get_nonce(), proj=project,
                               title='Еженедельный процент готовности')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@project_app_bp.route('/objects/<link_name>/statistics', methods=['GET'])
@login_required
def get_object_statistics(link_name):
    """Статистика проекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=link_name, user_id=user_id)

        if app_login.current_user.get_role() not in (1, 4):
            # flash(message=['Запрещено изменять данные', ''], category='error')
            return error_handlers.handle403(403)

        # print('       get_object_statistics')
        # print(link_name)

        # Информация о проекте
        project = get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        return render_template('object-project.html', menu=hlink_menu, menu_profile=hlink_profile, objects='objects',
                               left_panel='left_panel', nonce=get_nonce(), proj=project, title='Статистика проекта')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@project_app_bp.route('/error_handler_save_tow_changes', methods=['POST'])
@login_required
def error_handler_save_tow_changes():
    try:
        log_url = request.get_json()['log_url']
        error_description = request.get_json()['error_description']
        log_description = f'log_url: {log_url} error_description:{error_description}'
        try:
            user_id = app_login.current_user.get_id()
        except:
            user_id = None
        app_login.set_warning_log(log_url=sys._getframe().f_code.co_name,
                                  log_description=log_description,
                                  user_id=user_id)
        flash(message=['Ошибка',
                       'При сохранении видов работ/договора произошла ошибка.',
                       'Изменения не сохранены, страница обновлена'], category='error')
        return jsonify({'status': 'success'})

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error',
                        'description': [msg_for_user],
                        })


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


def get_milestones_menu(role: int = 0, link: str = '', cur_name: int = 0):
    # Вехи на листе tow
    if role in (1, 4):
        milestones = [
            {'func': f'getMilestones', 'name': 'ВЕХИ', 'id': 'id_div_milestones_getMilestones'},
            {'func': f'getReserves', 'name': 'РЕЗЕРВЫ', 'id': 'id_div_milestones_getReserves'},
            # {'func': f'getContractsList', 'name': 'СПИСОК ДОГОВОРОВ', 'id': 'id_div_milestones_getContractsList'},
        ]
    else:
        milestones = [
            {'func': f'getMilestones', 'name': 'ВЕХИ', 'id': 'id_div_milestones_getMilestones'},
        ]
    return milestones


def conv_tow_data_upd(val, col_type):
    # Конвертируем значение в нужный тип
    if col_type == 'str':
        val = str(val)
    elif col_type == 'int':
        if not val:  # Если данных нет, отправляем
            return None
        val = int(val)
    elif col_type == 'float':
        if not val:  # Если данных нет, отправляем
            return None
        val = float(val)
    return val


def get_proj_info(link_name):
    try:
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

        app_login.conn_cursor_close(cursor, conn)
        if project:
            project = dict(project)
        return ['success', project]
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info())
        return ['error', msg_for_user]


def tow_list_is_actual(checked_list: set = None, object_id: int = None, project_id: int = None, user_id: int = None,
                       tow=None, contract_id: int = None, act_id: int = None, payment_id: int = None,
                       contract_deleted_tow=None, act_deleted_tow=None, pay_deleted_tow=None):
    try:
        description = 'Список видов работ не актуален (v.2). Обновите страницу'
        # Обрабатываем полученные id. Удаляем все не цифровые id

        for i in checked_list.copy():
            if not i.isdigit():
                checked_list.remove(i)
            else:
                checked_list.remove(i)
                checked_list.add(int(i))
        if checked_list:
            if not tow:
                # Connect to the database
                conn, cursor = app_login.conn_cursor_init_dict('objects')
                # Список tow
                cursor.execute(
                    """SELECT tow_id FROM types_of_work WHERE project_id = %s""",
                    (project_id,)
                )
                tow = cursor.fetchall()
                app_login.conn_cursor_close(cursor, conn)

                if len(tow):
                    for i in tow.copy():
                        if i[0] in checked_list:
                            checked_list.remove(i[0])
                            tow.remove(i)

                else:
                    return [False, 'Список видов работ не актуален (v.1/1). Обновите страницу']
                if checked_list:
                    return [False, description]
                else:
                    return [True, 'Список видов работ актуален']

            elif tow == 'delete':
                # Connect to the database
                conn, cursor = app_login.conn_cursor_init_dict('contracts')

                description = ['Список удаляемых видов работ не актуален (v.3). Обновите страницу']

                # Проверяем, нет ли привязанных видов работ к договорам/актам/платежам
                where_contract_id_query = ''
                where_act_id_query = ''
                where_payment_id_query = ''

                vars_list = list()
                object_id = tuple([object_id])
                vars_list.append(object_id)
                contract_id = tuple([contract_id]) if contract_id else None

                if contract_id:
                    where_contract_id_query = ' WHERE t_c.contract_id NOT IN %s'
                    contract_id = tuple([contract_id])
                    vars_list.append(contract_id)
                    if contract_deleted_tow:
                        contract_deleted_tow = tuple(contract_deleted_tow)
                        # where_contract_id_query += ' AND tow_id NOT IN %s '
                        where_contract_id_query += ' AND t_c.tow_id NOT IN %s '
                        vars_list.append(contract_deleted_tow)
                else:
                    where_act_id_query = ''' 
                    WHERE act_id IN (
                        SELECT act_id FROM acts WHERE contract_id IN (
                            SELECT contract_id FROM contracts WHERE object_id IN %s
                            )
                        ) '''
                    vars_list.append(object_id)

                    where_payment_id_query = '''
                    WHERE payment_id IN (
                        SELECT payment_id FROM payments WHERE contract_id IN (
                                SELECT contract_id FROM contracts WHERE object_id IN %s
                            )
                        )
                    '''
                    vars_list.append(object_id)

                if act_id:
                    vars_list.append(contract_id)
                    if act_deleted_tow:
                        where_act_id_query
                    where_act_id_query = 'WHERE act_id NOT IN %s'
                    vars_list.append(act_id)

                if payment_id:
                    vars_list.append(contract_id)
                    where_payment_id_query = 'WHERE payment_id NOT IN %s'
                    vars_list.append(payment_id)

                cursor.execute(
                    f"""
                    SELECT t1.*
                    FROM (
                    
                        SELECT t_c.tow_id, '1_contract' AS type_tow 
                        FROM (
                            SELECT tow_id, contract_id
                            FROM tows_contract
                            WHERE contract_id IN (
                                SELECT contract_id FROM contracts WHERE object_id IN %s
                            )
                        ) AS t_c
                        {where_contract_id_query}
                        GROUP BY t_c.tow_id
                    
                    
                        UNION ALL
                        SELECT tow_id, '2_act' AS type_tow FROM tows_act
                        {where_act_id_query}
                        GROUP BY tow_id
                        
                        UNION ALL
                        SELECT tow_id, '3_payment' AS type_tow FROM tows_payment
                        {where_payment_id_query}
                        GROUP BY tow_id
                    
                    ) AS t1
                    ORDER BY tow_id, type_tow;
                    """,
                    vars_list
                )
                tow = cursor.fetchall()

                app_login.conn_cursor_close(cursor, conn)

                tow_collision = dict()
                if len(tow):
                    for i in tow:
                        if i[0] in checked_list:
                            collision_type = 'Договор' if i[1] == '1_contract' else (
                                'Акт' if i[1] == '2_act' else 'Платеж')
                            if i[0] not in tow_collision.keys():
                                tow_collision[i[0]] = collision_type
                            else:
                                tow_collision[i[0]] += f', {collision_type}'

                else:
                    return [True, 'Список видов работ актуален']
                if tow_collision:
                    description.append('Список коллизий видов работ:')
                    for k, v in tow_collision.items():
                        description.append(f'id: {k} Тип коллизии: {v}')
                    return [False, description]
                else:
                    return [True, 'Список видов работ актуален']

        return [True, 'Нет видов работ для проверки']
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return [False, f'Ошибка при проверки актуальности списка видов работ: {msg_for_user}']
