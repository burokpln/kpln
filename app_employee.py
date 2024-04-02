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

employee_app_bp = Blueprint('app_employee', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None

USER_QUERY_JOIN = """
FROM users AS t1

-- ГРУППА
LEFT JOIN (
    SELECT DISTINCT ON (user_id)
        user_id,
        dept_id
    FROM empl_dept
    WHERE date_promotion <= now()
    ORDER BY user_id, date_promotion DESC
) AS t2 ON t1.user_id = t2.user_id

-- ОТДЕЛ и ГРУППА
LEFT JOIN (
    WITH RECURSIVE ParentHierarchy AS (
        SELECT child_id, parent_id, 1 AS level, child_id AS main_id
        FROM dept_relation
        WHERE parent_id IS NOT NULL

        UNION ALL

        SELECT dr.child_id, dr.parent_id, ph.level + 1, ph.main_id
        FROM dept_relation dr
        JOIN ParentHierarchy ph ON dr.child_id = ph.parent_id
    )
    SELECT *
    FROM ParentHierarchy AS ph
    LEFT JOIN list_dept AS ld ON ph.child_id = ld.dept_id
    LEFT JOIN (
            SELECT 
                dept_id AS group_id,
                dept_name AS group_name,
                dept_short_name AS group_short_name,
                head_of_dept_id AS head_of_group_id
            FROM list_dept
    ) AS lg ON ph.main_id = lg.group_id
    WHERE ph.parent_id IS NULL
    
    UNION
    
    SELECT 
        dr2.child_id, 
        dr2.parent_id, 
        1 AS level, 
        dr2.child_id AS main_id,
        dr2.child_id AS dept_id,
        lg2.dept_name,
        lg2.dept_short_name,
        lg2.head_of_dept_id,
        dr2.child_id AS group_id,
        lg2.dept_name AS group_name,
        lg2.dept_short_name AS group_short_name,
        lg2.head_of_dept_id AS head_of_group_id
    FROM dept_relation AS dr2
    LEFT JOIN (
            SELECT 
                dept_id,
                dept_name,
                dept_short_name,
                head_of_dept_id
            FROM list_dept
    ) AS lg2 ON dr2.child_id = lg2.dept_id
    WHERE dr2.parent_id IS NULL 
    
    ORDER BY main_id, level
) AS t3 ON t2.dept_id = t3.main_id

-- должность
LEFT JOIN (
    SELECT
        position_id,
        position_name
    FROM list_position
) AS t4 ON t1.position_id = t4.position_id

-- образование
LEFT JOIN (
    SELECT 
        education_id,
        education_name
    FROM list_education
) AS t5 ON t1.education_id = t5.education_id

-- зарплата
LEFT JOIN (
    SELECT DISTINCT ON (user_id)
        user_id,
        salary_sum,
        salary_date
    FROM salaries
    WHERE salary_date <= now()
    ORDER BY user_id, salary_date DESC
) AS t6 ON t1.user_id = t6.user_id
 
-- проработано дней
LEFT JOIN (
    SELECT 
        user_id, 
        SUM(work_days) AS work_days
    FROM EmployeePeriods
    WHERE hire_date IS NOT NULL
    GROUP BY user_id
) AS t7 ON t1.user_id = t7.user_id
       
-- компания
LEFT JOIN (
    SELECT 
        contractor_id,
        contractor_name
    FROM our_companies
) AS t8 ON t1.contractor_id = t8.contractor_id
                       
-- табельный номер
LEFT JOIN (
    SELECT 
        user_id,
        pers_num
    FROM personnel_number
) AS t9 ON t1.user_id = t9.user_id
                                      
-- норма для
LEFT JOIN (
    SELECT DISTINCT ON (user_id)
        user_id,
        hours
    FROM hour_per_day_norm
    WHERE empl_hours_date <= now()
    ORDER BY user_id, empl_hours_date DESC
) AS t10 ON t1.user_id = t10.user_id
"""

USER_QUERY = f"""
WITH EmployeePeriods AS (
    SELECT
        user_id,
        hire_date,
        COALESCE(LEAD(COALESCE(hire_date, fire_date)) OVER (PARTITION BY user_id ORDER BY COALESCE(hire_date, fire_date)), now()::date) - COALESCE(hire_date, fire_date) + 1 AS work_days
    FROM hire_and_fire
)

SELECT
    t1.user_id,
    t1.contractor_id,
    t8.contractor_name,
    COALESCE(t9.pers_num, NULL) AS pers_num,
    COALESCE(t9.pers_num, -1000) AS f_pers_num,
    t1.last_name,
    t1.first_name,
    t1.surname,
    concat_ws(' ', t1.last_name, t1.first_name, t1.surname) AS name,
    
    t3.dept_id,
    t3.dept_name,
    t3.group_id, 
    t3.group_short_name, 
    
    t1.position_id,
    t4.position_name,
    
    to_char(t1.b_day, 'dd.mm.yyyy') AS b_day_txt,
    COALESCE(t1.b_day, now()::date)::text AS b_day,
    
    t1.education_id,
    t5.education_name,
    
    COALESCE(t6.salary_sum, '0') AS salary_sum,
    TRIM(BOTH ' ' FROM to_char(t6.salary_sum, '999 999 990D99 ₽')) AS salary_sum_rub,

    to_char(t6.salary_date, 'dd.mm.yyyy') AS salary_date_txt,
    COALESCE(t6.salary_date, now()::date)::text AS salary_date,
    
    t1.is_fired AS status1,
    t1.is_maternity_leave AS status2,
    
    CASE 
        WHEN t9.pers_num IS NOT NULL AND t1.is_fired THEN 'увол.'
        WHEN t9.pers_num IS NOT NULL AND t1.is_maternity_leave THEN 'декр.'
        WHEN t9.pers_num IS NOT NULL THEN 'работ.'
        ELSE ' '
    END AS status3,
    
    COALESCE(to_char(t1.employment_date, 'dd.mm.yyyy'), '') AS employment_date_txt,
    COALESCE(t1.employment_date, now()::date)::text AS employment_date,
    
    to_char(t1.date_of_dismissal, 'dd.mm.yyyy') AS date_of_dismissal_txt,
    COALESCE(t1.date_of_dismissal, now()::date)::text AS date_of_dismissal,
    
    t7.work_days AS work_days1,
    COALESCE(t7.work_days, NULL) AS work_days,
    COALESCE(t7.work_days, -1) AS f_work_days,
    COALESCE(t10.hours, NULL) AS hours,
    COALESCE(t10.hours, -1) AS f_hours,
    t1.labor_status,
    date_part('year', age(COALESCE(t1.b_day, now()::date))) AS full_years
{USER_QUERY_JOIN}
"""


@employee_app_bp.before_request
def before_request():
    app_login.before_request()


# Главная страница раздела 'Объекты'
@employee_app_bp.route('/employees-list', methods=['GET'])
@login_required
def get_employees_list():
    """Главная страница раздела 'Объекты' """
    try:
        global hlink_menu, hlink_profile
        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return error_handlers.handle403(403)
        else:

            user_id = app_login.current_user.get_id()

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("users")

            # Список сотрудников
            cursor.execute(
                """
                SELECT 
                    user_id - 1 AS user_id,
                    (COALESCE(employment_date, now()::date) - interval '1 day')::date::text AS employment_date,
                    employment_date::text AS initial_first_val,
                    user_id AS initial_id_val
                FROM users
                ORDER BY employment_date, user_id
                LIMIT 1;
                """
            )
            employee = cursor.fetchall()
            for i in range(len(employee)):
                employee[i] = dict(employee[i])

            # Список должностей
            cursor.execute(
                """
                SELECT
                    position_id,
                    position_name
                FROM list_position;
                """
            )
            position = cursor.fetchall()
            for i in range(len(position)):
                position[i] = dict(position[i])

            # Список отделов
            cursor.execute(
                """
                WITH RECURSIVE ParentHierarchy AS (
                        SELECT 
                            1 AS depth,
                            path,
                            child_id,
                            parent_id,
                            ARRAY[child_id] AS child_path
                        FROM dept_relation
                        WHERE parent_id IS NULL
                        
                        UNION ALL
                        SELECT
                            nlevel(r.path) + 1,
                            n.path,
                            n.child_id,
                            n.parent_id,
                            r.child_path || n.child_id
                        FROM ParentHierarchy AS r
                        JOIN dept_relation AS n ON n.parent_id = r.child_id
      
                    )
                    SELECT 
                        ph.child_id,
                        lg.group_name,
                        lg.group_short_name,
                        ph.parent_id,
                        ld.dept_name,
                        ld.dept_short_name,
                        ph.depth
                    FROM ParentHierarchy AS ph
    
                    LEFT JOIN list_dept AS ld ON ph.parent_id = ld.dept_id
                    LEFT JOIN (
                            SELECT 
                                dept_id,
                                dept_name AS group_name,
                                dept_short_name AS group_short_name
                            FROM list_dept
                    ) AS lg ON ph.child_id = lg.dept_id
                ORDER BY child_path, child_id;
                """
            )
            dept = cursor.fetchall()

            for i in range(len(dept)):
                dept[i] = dict(dept[i])

            # Список образования
            cursor.execute(
                """
                SELECT 
                    education_id,
                    education_name
                FROM list_education;
                """
            )
            education = cursor.fetchall()
            for i in range(len(education)):
                education[i] = dict(education[i])

            # Список компаний
            cursor.execute(
                """
                SELECT 
                    contractor_id,
                    contractor_name
                FROM our_companies
                WHERE inflow_active IS TRUE;
                """
            )
            contractor = cursor.fetchall()
            for i in range(len(contractor)):
                contractor[i] = dict(contractor[i])

            app_login.conn_cursor_close(cursor, conn)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # Список основного меню
            header_menu = get_header_menu(role, link='link_name', cur_name=0)

            # Список колонок для сортировки
            if len(employee):
                sort_col = {
                    'col_1': [11, 0, employee[-1]['employment_date']],  # Первая колонка - ASC
                    'col_id': employee[-1]['user_id']
                }
            else:
                sort_col = {
                    'col_1': [False, 1, False],  # Первая колонка
                    'col_id': False
                }
            tab_rows = 1

            return render_template('employee-list.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                                   header_menu=header_menu, tab_rows=tab_rows, dept=dept, position=position,
                                   education=education, contractor=contractor,
                                   title='Список сотрудников')

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'employee_list: {e}'], category='error')
        return render_template('page_error.html')


@employee_app_bp.route('/get-first-employee', methods=['POST'])
@login_required
def get_first_employee():
    """Постраничная выгрузка списка сотрудников"""

    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return jsonify({
                'employee': '',
                'sort_col': 0,
                'status': 'error',
                'description': 'Доступ запрещен',
            })
        else:
            page_name = request.get_json()['page_url']
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']

            col_id = 't1.user_id'

            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False':
                return jsonify({
                    'employee': '',
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            # # Колонка по которой идёт сортировка в таблице
            # col_num = int(col_1.split('#')[0])
            # # Направление сортировки
            # sort_direction = col_1.split('#')[1]
            #
            # # Список колонок для сортировки
            # sort_col = {
            #     'col_1': [f"{col_num}#{sort_direction}"],  # Первая колонка
            #     'col_id': ''
            # }

            user_id = app_login.current_user.get_id()

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("users")

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
                query_value, sort_col, col_num = \
                get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

            if sort_col_1_order == 'DESC':
                order = '+'
            else:
                order = '-'

            if not where_expression2:
                where_expression2 = 'true'

            # print(f"""                WHERE {where_expression2}
            #     ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
            #     LIMIT {limit};""")
            # print('query_value', query_value)

            cursor.execute(
                f"""
                WITH EmployeePeriods AS (
                SELECT
                    user_id,
                    hire_date,
                    COALESCE(LEAD(COALESCE(hire_date, fire_date)) OVER (PARTITION BY user_id ORDER BY COALESCE(hire_date, fire_date)), now()::date) - COALESCE(hire_date, fire_date) + 1 AS work_days
                FROM
                    hire_and_fire
                )
                
                SELECT
                    t1.user_id {order} 1 AS user_id,
                    t8.contractor_name,
                    COALESCE(t9.pers_num {order} 1, -1000) AS f_pers_num,
                    concat_ws(' ', t1.last_name, t1.first_name, t1.surname) AS name,
                    
                    t3.dept_name,
                    
                    t3.group_short_name, 
                    
                    t4.position_name,
                    
                    (COALESCE(t1.b_day, now()::date) {order} interval '1 day')::text AS b_day,
                    
                    t5.education_name,
                    
                    COALESCE(t6.salary_sum, '0') {order} 1 AS salary_sum,
    
                    (COALESCE(t6.salary_date, now()::date) {order}  interval '1 day')::text AS salary_date,
                    
                    t1.is_fired AS status1,
                    t1.is_maternity_leave AS status2,
    
                    CASE 
                        WHEN t9.pers_num IS NOT NULL AND t1.is_fired THEN 'увол.'
                        WHEN t9.pers_num IS NOT NULL AND t1.is_maternity_leave THEN 'декр.'
                        WHEN t9.pers_num IS NOT NULL THEN 'работ.'
                        ELSE ' '
                    END AS status3,
                    
                    (COALESCE(t1.employment_date, now()::date) {order} interval '1 day')::text AS employment_date,
                    
                    (COALESCE(t1.date_of_dismissal, now()::date) {order} interval '1 day')::text AS date_of_dismissal,
                    
                    COALESCE(t7.work_days {order} 0.01, -1) AS f_work_days,
                    COALESCE(t10.hours {order} 0.01, -1) AS f_hours,
                    t1.labor_status,
                    date_part('year', age(COALESCE(t1.b_day, now()::date)))::int {order} 1  AS full_years
    
                {USER_QUERY_JOIN}
    
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )

            employee = cursor.fetchone()

            app_login.conn_cursor_close(cursor, conn)
            if employee:
                col_0 = employee["contractor_name"]
                col_1 = employee["f_pers_num"]
                col_2 = employee["name"]
                col_3 = employee["dept_name"]
                col_4 = employee["group_short_name"]
                col_5 = employee["position_name"]
                col_6 = employee["b_day"]
                col_7 = employee["education_name"]
                col_8 = employee["salary_sum"]
                col_9 = employee["salary_date"]
                col_10 = employee["status3"]
                col_11 = employee["employment_date"]
                col_12 = employee["date_of_dismissal"]
                col_13 = employee["f_work_days"]
                col_14 = employee["f_hours"]
                col_15 = ""
                col_16 = employee["full_years"]

                if sort_col_1_order == 'DESC':
                    col_0 = col_0 + '+' if col_0 else col_0
                    col_2 = col_2 + '+' if col_2 else col_2
                    col_3 = col_3 + '+' if col_3 else col_3
                    col_4 = col_4 + '+' if col_4 else col_4
                    col_5 = col_5 + '+' if col_5 else col_5
                    col_7 = col_7 + '+' if col_7 else col_7
                    col_10 = col_10 + '+' if col_10 else col_10
                else:
                    col_0 = col_0[:-1] if col_0 else col_0
                    col_2 = col_2[:-1] if col_2 else col_2
                    col_3 = col_3[:-1] if col_3 else col_3
                    col_4 = col_4[:-1] if col_4 else col_4
                    col_5 = col_5[:-1] if col_5 else col_5
                    col_7 = col_7[:-1] if col_7 else col_7
                    col_10 = col_10[:-1] if col_10 else col_10
                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12,
                    col_13, col_14, col_15, col_16
                ]

                sort_col['col_1'].append(filter_col[col_num])
                sort_col['col_id'] = employee["user_id"]

            if not employee:
                return jsonify({
                    'sort_col': sort_col,
                    'status': 'error',
                    'description': 'End of table. Nothing to append',
                })

            return jsonify({
                'sort_col': sort_col,
                'status': 'success',
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': str(e),
        })


@employee_app_bp.route('/get-employee-pagination', methods=['POST'])
@login_required
def get_employee_pagination():
    """Постраничная выгрузка списка сотрудников"""

    try:
        page_name = 'employee-list'
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        col_id = 't1.user_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']

        if col_1.split('#')[0] == 'False':
            return jsonify({
                'employee': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        user_id = app_login.current_user.get_id()

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
            query_value, sort_col, col_num = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        # Когда происходит горизонтальный скролл страницы и нажимается кнопка сортировки, вызывается
        # дополнительная пагинация с пустыми значениями сортировки. Отлавливаем этот случай, ничего не делаем
        if not col_1_val and not col_id_val:
            return jsonify({
                'employee': 0,
                'sort_col': sort_col,
                'status': 'success',
                'description': 'Skip pagination with empty sort data',
            })

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("users")
        try:
            cursor.execute(
                f"""
                {USER_QUERY}
                WHERE  {where_expression}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
            employee = cursor.fetchall()
            # print(query_value)

        except Exception as e:
            current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
            return jsonify({
                'employee': 0,
                'sort_col': 0,
                'status': 'error',
                'description': str(e),
            })

        if not len(employee):
            print('not len(employee)')
            return jsonify({
                'employee': 0,
                'sort_col': sort_col,
                'status': 'success',
                'description': 'End of table. Nothing to append',
            })

        col_0 = employee[-1]["contractor_name"]
        col_1 = employee[-1]["f_pers_num"]
        col_2 = employee[-1]["name"]
        col_3 = employee[-1]["dept_name"]
        col_4 = employee[-1]["group_short_name"]
        col_5 = employee[-1]["position_name"]
        col_6 = employee[-1]["b_day"]
        col_7 = employee[-1]["education_name"]
        col_8 = employee[-1]["salary_sum"]
        col_9 = employee[-1]["salary_date"]
        col_10 = employee[-1]["status3"]
        col_11 = employee[-1]["employment_date"]
        col_12 = employee[-1]["date_of_dismissal"]
        col_13 = employee[-1]["work_days"]
        col_13 = employee[-1]["f_work_days"]
        col_14 = employee[-1]["f_hours"]
        col_15 = employee[-1]["labor_status"]
        col_16 = employee[-1]["full_years"]
        filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16
        ]

        # Список колонок для сортировки, добавляем последние значения в столбах сортировки
        sort_col['col_1'].append(filter_col[col_num])
        sort_col['col_id'] = employee[-1]["user_id"]

        for i in range(len(employee)):
            employee[i] = dict(employee[i])
            # print(employee[i])

        if where_expression2:
            where_expression2 = 'WHERE ' + where_expression2
        else:
            where_expression2 = ''

        # Число заявок
        cursor.execute(
            f"""
                WITH EmployeePeriods AS (
                SELECT
                    user_id,
                    hire_date,
                    COALESCE(LEAD(COALESCE(hire_date, fire_date)) OVER (PARTITION BY user_id ORDER BY COALESCE(hire_date, fire_date)), now()::date) - COALESCE(hire_date, fire_date) + 1 AS work_days
                FROM
                    hire_and_fire
                )
                SELECT
                    COUNT(t1.user_id)
                {USER_QUERY_JOIN}
                {where_expression2}
            """,
            query_value
        )
        tab_rows = cursor.fetchone()[0]

        app_login.conn_cursor_close(cursor, conn)

        # Настройки таблицы
        setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"

        # Return the updated data as a response
        return jsonify({
            'employee': employee,
            'sort_col': sort_col,
            'tab_rows': tab_rows,
            'page': page_name,
            'status': 'success'
        })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'employee': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


@employee_app_bp.route('/get_card_employee/<int:employee_id>', methods=['GET'])
@login_required
def get_card_employee(employee_id):
    try:
        employee_id = employee_id

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return jsonify({
                'employee': 0,
                'status': 'error',
                'description': 'Доступ запрещен',
            })
        else:
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("users")

            # Данные о сотруднике
            cursor.execute(
                f"""{USER_QUERY}
                WHERE t1.user_id = {employee_id}""")
            employee = cursor.fetchone()

            # Список изменений зарплаты
            cursor.execute(
                f"""
                SELECT 
                    to_char(t1.salary_date, 'dd.mm.yyyy') AS salary_date,
                    TRIM(BOTH ' ' FROM to_char(t1.salary_sum, '999 999 990D99 ₽')) AS salary_sum_rub,
                    t1.create_at,
                    t2.dept_short_name
                FROM salaries AS t1
                LEFT JOIN (
                    SELECT 
                        dept_id, 
                        dept_short_name
                    FROM list_dept
                ) AS t2 ON t1.dept_id = t2.dept_id
                WHERE t1.user_id = {employee_id}
                ORDER BY t1.salary_date DESC;
                """
            )
            salaries_list = cursor.fetchall()

            app_login.conn_cursor_close(cursor, conn)

            # print(dict(employee))

            # Return the updated data as a response
            return jsonify({
                'status': 'success',
                'employee': dict(employee),
                'salaries_list': salaries_list
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': str(e),
        })


@employee_app_bp.route('/save_employee', methods=['POST'])
@login_required
def save_employee():
    try:
        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return jsonify({
                'employee': 0,
                'status': 'error',
                'description': 'Доступ запрещен',
            })
        else:
            employee_data = request.get_json()
            print('-' * 30)
            pprint(employee_data)
            print(type(employee_data), '-' * 30)

            # Конвертируем тип данных для записи в БД
            employee_id = int(employee_data['user_id'])
            employee_data['contractor_id'] = int(employee_data['contractor_id'])
            employee_data['pers_num'] = int(employee_data['pers_num'])
            employee_data['dept_id'] = int(employee_data['dept_id'])
            employee_data['position_id'] = int(employee_data['position_id'])
            employee_data['b_day'] = date.fromisoformat(employee_data['b_day'])
            employee_data['education_id'] = int(employee_data['education_id'])
            employee_data['salary_sum'] = app_payment.convert_amount(employee_data['salary_sum'])
            employee_data['salary_date'] = date.fromisoformat(employee_data['salary_date'])
            employee_data['employment_date'] = date.fromisoformat(employee_data['employment_date'])
            if employee_data['hours']:
                employee_data['hours'] = float(employee_data['hours'])

            del employee_data['user_id']

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("users")

            # Данные о сотруднике
            cursor.execute(
                f"""{USER_QUERY}
                WHERE t1.user_id = {employee_id}""")
            employee = cursor.fetchone()

            # Список изменений зарплаты
            cursor.execute(
                f"""
                SELECT 
                    t1.*,
                    t2.dept_short_name
                FROM salaries AS t1
                LEFT JOIN (
                    SELECT 
                        dept_id, 
                        dept_short_name
                    FROM list_dept
                ) AS t2 ON t1.dept_id = t2.dept_id
                WHERE t1.user_id = {employee_id}
                ORDER BY t1.salary_date DESC;
                """
            )
            salaries_list = cursor.fetchall()

            pprint(dict(employee))
            difference_dict = dict()

            for k, v in employee_data.items():
                if k in employee:
                    print(f'k: {k}  --  {v}    __{employee.get(k)}__')
                    if employee.get(k) != v:
                        difference_dict[k] = v

            ########################################################################
            #                       Проверяем, в каких таблицах произойдёт изменение
            ########################################################################
            # FROM users
            columns_empl = ['user_id']
            values_empl = [employee_id]
            query_empl = None

            # FROM personnel_number
            columns_p_n = ('pers_num', 'user_id')
            values_p_n = [None, values_empl[0]]
            query_p_n = None

            # FROM empl_dept
            columns_e_d = ('user_id', 'dept_id', 'date_promotion')
            values_e_d = [values_empl[0], None, date.fromisoformat(str(date.today()))]
            query_e_d = None

            # FROM salaries
            columns_s = ('user_id', 'salary_sum', 'salary_date', 'dept_id')
            values_s = [values_empl[0], None, None, employee_data['dept_id']]
            query_s = None

            # FROM hour_per_day_norm
            columns_h_p_d_n = ('user_id', 'hours', 'empl_hours_date')
            values_h_p_d_n = [values_empl[0], None, date.fromisoformat(str(date.today()))]
            query_h_p_d_n = None

            # FROM hire_and_fire
            columns_h_a_f = ('user_id', 'hire_date', 'fire_date')
            values_h_a_f = [values_empl[0], None, None]
            query_h_a_f = None

            # Столбцы не из таблицы users
            not_users_cols = {'pers_num', 'dept_id', 'salary_sum', 'salary_date', 'hours'}

            for k, v in difference_dict.items():
                if k not in not_users_cols:
                    columns_empl.append(k)
                    values_empl.append(v)
                else:
                    if k in columns_p_n:
                        values_p_n[columns_p_n.index(k)] = v
                    if k in columns_e_d:
                        values_e_d[columns_e_d.index(k)] = v
                    if k in columns_s:
                        print('_____________________', k, v)
                        values_s[columns_s.index(k)] = v
                    if k in columns_h_p_d_n:
                        values_h_p_d_n[columns_h_p_d_n.index(k)] = v

            # Для таблицы hire_and_fire
            if 'employment_date' in difference_dict:
                values_h_a_f[1] = difference_dict['employment_date']

            action = 'INSERT INTO'

            # FROM users
            print('\nquery_empl')
            if len(values_empl) > 1:
                columns_empl = tuple(columns_empl)
                action_empl = 'UPDATE'
                query_empl = app_payment.get_db_dml_query(action=action_empl, table='users', columns=columns_empl)
                print(query_empl)
                print(values_empl)
                execute_values(cursor, query_empl, [values_empl])

            # FROM personnel_number
            print('\nquery_p_n')
            if values_p_n[0]:
                columns_p_n = tuple(columns_p_n)
                action_p_n = 'INSERT CONFLICT UPDATE'
                expr_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns_p_n[:-1]])
                query_p_n = app_payment.get_db_dml_query(action=action_p_n, table='personnel_number', columns=columns_p_n,
                                                         expr_set=expr_set)
                print(expr_set)
                print(query_p_n)
                print(values_p_n)
                execute_values(cursor, query_p_n, [values_p_n])

            # FROM empl_dept
            print('\nquery_e_d')
            if values_e_d[1]:
                columns_e_d = tuple(columns_e_d)
                query_e_d = app_payment.get_db_dml_query(action=action, table='empl_dept', columns=columns_e_d)
                print(query_e_d)
                print(values_e_d)
                execute_values(cursor, query_e_d, [values_e_d])

            # FROM salaries
            print('\nquery_s')
            if values_s[1]:
                columns_s = tuple(columns_s)
                query_s = app_payment.get_db_dml_query(action=action, table='salaries', columns=columns_s)
                print(query_s)
                print(values_s)
                execute_values(cursor, query_s, [values_s])

            # FROM hour_per_day_norm
            print('\nquery_h_p_d_n')
            if values_h_p_d_n[1]:
                columns_h_p_d_n = tuple(columns_h_p_d_n)
                query_h_p_d_n = app_payment.get_db_dml_query(action=action, table='hour_per_day_norm',
                                                             columns=columns_h_p_d_n)
                print(query_h_p_d_n)
                print(values_h_p_d_n)
                execute_values(cursor, query_h_p_d_n, [values_h_p_d_n])

            # FROM hire_and_fire
            if values_h_a_f[1] or values_h_a_f[2]:
                columns_h_a_f = tuple(columns_h_a_f)
                query_h_a_f = app_payment.get_db_dml_query(action=action, table='hire_and_fire', columns=columns_h_a_f)
                print(query_h_a_f)
                print(values_h_a_f)
                execute_values(cursor, query_h_a_f, [values_h_a_f])

            conn.commit()

            app_login.conn_cursor_close(cursor, conn)

            print('=__' * 20)
            pprint(difference_dict)

            # Return the updated data as a response
            return jsonify({
                'status': 'success',
                'employee': dict(employee),
                'salaries_list': salaries_list
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': str(e),
        })


def get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id,
                         manual_type=''):
    # Колонка по которой идёт сортировка в таблице
    col_num = int(col_1.split('#')[0])
    # Направление сортировки
    sort_direction = col_1.split('#')[1]

    # Список колонок для сортировки
    sort_col = {
        'col_1': [f"{col_num}#{sort_direction}"],  # Первая колонка
        'col_id': ''
    }

    query_value = [
    ]

    # столбцы фильтров
    col_0 = "t8.contractor_name"
    col_1 = "COALESCE(t9.pers_num, -1000)"
    col_2 = "concat_ws(' ', t1.last_name, t1.first_name, t1.surname)"
    col_3 = "t3.dept_name"
    col_4 = "t3.group_short_name"
    col_5 = "t4.position_name"
    col_6 = "to_char(t1.b_day, 'dd.mm.yyyy')"
    col_7 = "t5.education_name"
    col_8 = "COALESCE(t6.salary_sum, '0')"
    col_9 = "to_char(t6.salary_date, 'dd.mm.yyyy')"
    col_10 = """CASE 
                    WHEN t9.pers_num IS NOT NULL AND t1.is_fired THEN 'увол.'
                    WHEN t9.pers_num IS NOT NULL AND t1.is_maternity_leave THEN 'декр.'
                    WHEN t9.pers_num IS NOT NULL THEN 'работ.'
                    ELSE ' '
                END"""
    col_11 = "to_char(t1.employment_date, 'dd.mm.yyyy')"
    col_12 = "to_char(t1.date_of_dismissal, 'dd.mm.yyyy')"
    col_13 = "COALESCE(t7.work_days, -1)"
    col_14 = "COALESCE(t10.hours, -1)"
    col_15 = "t1.labor_status"
    col_16 = "date_part('year', age(t1.b_day))"
    list_filter_col = [
        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
        col_14, col_15, col_16
    ]
    # столбцы сортировки
    col_0 = "COALESCE(t8.contractor_name, '')"
    col_1 = "COALESCE(t9.pers_num,  -1000)"
    col_2 = "concat_ws(' ', t1.last_name, t1.first_name, t1.surname)"
    col_3 = "COALESCE(t3.dept_name, '')"
    col_4 = "COALESCE(t3.group_short_name, '')"
    col_5 = "COALESCE(t4.position_name, '')"
    col_6 = "COALESCE(t1.b_day, now()::date)"
    col_7 = "t5.education_name"
    col_8 = "COALESCE(t6.salary_sum, '0')"
    col_9 = "COALESCE(t6.salary_date, now()::date)"
    col_10 = """CASE 
                    WHEN t9.pers_num IS NOT NULL AND t1.is_fired THEN 'увол.'
                    WHEN t9.pers_num IS NOT NULL AND t1.is_maternity_leave THEN 'декр.'
                    WHEN t9.pers_num IS NOT NULL THEN 'работ.'
                    ELSE ' '
                END"""
    col_11 = "COALESCE(t1.employment_date, now()::date)"
    col_12 = "COALESCE(t1.date_of_dismissal, now()::date)"
    col_13 = "COALESCE(t7.work_days, -1)"
    col_14 = "COALESCE(t10.hours, -1)"
    col_15 = "t1.labor_status"
    col_16 = "date_part('year', age(COALESCE(t1.b_day, now()::date)))"
    list_sort_col = [
        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
        col_14, col_15, col_16
    ]
    # типы данных столбцов
    col_0 = "t8.contractor_name"
    col_1 = "t9.pers_num"
    col_2 = "t1.last_name"
    col_3 = "t3.dept_name"
    col_4 = "t3.group_short_name"
    col_5 = "t4.position_name"
    col_6 = "t1.b_day"
    col_7 = "t5.education_name"
    col_8 = "t6.salary_sum"
    col_9 = "t6.salary_date"
    col_10 = "t1.last_name"
    col_11 = "t1.employment_date"
    col_12 = "t1.date_of_dismissal"
    col_13 = "t1.user_id"
    col_14 = "t10.hours"
    col_15 = "t1.labor_status"
    col_16 = "t1.user_id"
    list_type_col = [
        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
        col_14, col_15, col_16
    ]

    sort_col_1, sort_col_1_order = list_sort_col[col_num], 'DESC' if sort_direction == '1' else 'ASC'
    sort_col_id, sort_col_id_order = col_id, 'DESC' if sort_direction == '1' else 'ASC'
    sort_col_1_equal = '>' if sort_col_1_order == 'ASC' else '<'

    # Список таблиц в базе данных и их типы
    all_col_types = get_table_list()
    # Выражение для фильтрации в выражении WHERE
    where_expression = (
        f"({sort_col_1}, {sort_col_id}) {sort_col_1_equal} "
        f"({app_payment.conv_data_to_db(list_type_col[col_num], col_1_val, all_col_types)}, "
        f"{app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)})")
    where_expression2 = []  # Вторая часть условия (пригодится для определения общего кол-ва строк)
    if filter_vals_list:
        for i in filter_vals_list:
            query_value.append('%' + i[1] + '%')
            where_expression2.append(list_filter_col[i[0]])
    where_expression2 = ' AND '.join(map(lambda x: f'{x}::text ILIKE %s', where_expression2))
    if where_expression2:
        where_expression += ' AND ' + where_expression2

    # print(''*10, 'get_sort_filter_data')
    # print('_____filter_vals_list:', filter_vals_list)
    # print('_____sort_col_1:', sort_col_1)
    # print('_____sort_col_1_order:', sort_col_1_order)
    # print('_____sort_col_id:', sort_col_id)
    # print('_____sort_col_id_order:', sort_col_id_order)
    # print('_____where_expression:', where_expression)
    # print('_____where_expression2:', where_expression2)
    # print('_____query_value:', query_value)
    # print('_____sort_col:', sort_col)
    # print('_____col_num:', col_num)
    return sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
        query_value, sort_col, col_num


# Получаем типы данных из всех столбцов всех таблиц БД
def get_table_list():
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("users")

        # Список таблиц в базе данных и их типы
        cursor.execute(
            """
            SELECT column_name, data_type, table_name FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY column_name
            """
        )

        all_col_types = cursor.fetchall()
        app_login.conn_cursor_close(cursor, conn)

        return all_col_types
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'get_table_list: {e}'], category='error')
        return render_template('page_error.html')


def get_header_menu(role: int = 0, link: str = '', cur_name: int = 0):
    # Админ и директор
    if role in (1, 4, 7):
        header_menu = [
            {'link': f'/employees-list', 'name': 'Сотрудники'}
        ]
    else:
        header_menu = [
            {'link': f'/employees-list', 'name': 'Сотрудники'}
        ]
    header_menu[cur_name]['class'] = 'current'
    header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu
