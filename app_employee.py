import json
import time
import datetime
from psycopg2.extras import execute_values
from pprint import pprint
from flask import g, request, render_template, redirect, flash, url_for, abort, get_flashed_messages, \
    jsonify, Blueprint, current_app, send_file
from datetime import date, datetime
from flask_login import login_required, logout_user
import error_handlers
import app_login
import app_payment
import pandas as pd
from openpyxl import Workbook
import os
import tempfile
import sys

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
        dept_id,
        date_promotion
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
    WHERE haf_type = 'hire'
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
        empl_hours_date,
        full_day_status
    FROM hour_per_day_norm
    WHERE empl_hours_date <= now()
    ORDER BY user_id, empl_hours_date DESC
) AS t10 ON t1.user_id = t10.user_id
                                      
-- первый статус 'hire'
LEFT JOIN (
    SELECT 
        user_id,
        MIN(haf_date) AS haf_date
    FROM hire_and_fire
    WHERE haf_type = 'hire'
    GROUP BY user_id
) AS t11 ON t1.user_id = t11.user_id

-- статус подачи часов
LEFT JOIN (
    SELECT DISTINCT ON (user_id)
        user_id,
        empl_labor_date,
		empl_labor_status
    FROM public.labor_status
    WHERE empl_labor_date <= now()
    ORDER BY user_id, empl_labor_date DESC
) AS t12 ON t1.user_id = t12.user_id
"""

USER_QUERY = f"""
WITH EmployeePeriods AS (
    SELECT
        user_id,
        CASE 
            WHEN haf_type = 'hire' THEN haf_date
            ELSE NULL
        END AS hire_date,
        COALESCE(LEAD(haf_date) OVER (PARTITION BY user_id ORDER BY haf_date), now()::date) - haf_date + 1 AS work_days,
        haf_type
    FROM hire_and_fire
    WHERE haf_type IN ('hire', 'fire')
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
    
    t2.date_promotion,
    to_char(t2.date_promotion, 'dd.mm.yyyy') AS date_promotion_txt,
    
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
    
    --COALESCE(to_char(t1.employment_date, 'dd.mm.yyyy'), '') AS employment_date_txt,
    --COALESCE(t1.employment_date, now()::date + 1000)::text AS employment_date,
    
    CASE 
        WHEN t1.is_fired THEN COALESCE(to_char(t11.haf_date, 'dd.mm.yyyy'), '')
        ELSE COALESCE(to_char(t1.employment_date, 'dd.mm.yyyy'), '')
    END AS employment_date_txt,
    CASE 
        WHEN t1.is_fired THEN COALESCE(t11.haf_date, now()::date)::text
        ELSE COALESCE(t1.employment_date, now()::date + 1000)::text
    END AS employment_date,
    
    to_char(t1.date_of_dismissal, 'dd.mm.yyyy') AS date_of_dismissal_txt,
    COALESCE(t1.date_of_dismissal, now()::date)::text AS date_of_dismissal,
    
    t7.work_days AS work_days1,
    COALESCE(t7.work_days, NULL) AS work_days,
    COALESCE(t7.work_days, -1) AS f_work_days,
    t10.full_day_status,
    COALESCE(t10.empl_hours_date::text, '') AS empl_hours_date,
    COALESCE(to_char(t10.empl_hours_date, 'dd.mm.yyyy'), '') AS empl_hours_date_txt,
    --t1.labor_status,
    
    t12.empl_labor_status AS labor_status,
    COALESCE(t12.empl_labor_date::text, '') AS empl_labor_date,
    COALESCE(to_char(t12.empl_labor_date, 'dd.mm.yyyy'), '') AS empl_labor_date_txt,
    
    date_part('year', age(COALESCE(t1.b_day, now()::date))) AS full_years
{USER_QUERY_JOIN}
"""

DEPT_LIST_FOR_EMPLOYEE = """
SELECT 
    COALESCE(t3.cur_dept, '') AS cur_dept,
    t2.dept_short_name,
    t2.group_name,
    t2.group_short_name,
    t1.date_promotion,
    COALESCE(to_char(t1.date_promotion, 'dd.mm.yyyy'), '') AS date_promotion_txt,
    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt
FROM empl_dept AS t1

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
    SELECT 
        ph.main_id,
        ph.level,
        ld.dept_short_name,
        lg.group_id,
        lg.group_name,
        lg.group_short_name
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
        /*dr2.child_id, 
        dr2.parent_id,*/ 
        1 AS level, 
        /*dr2.child_id AS main_id,
        dr2.child_id AS dept_id,
        lg2.dept_name,*/
        dr2.child_id AS main_id,
        lg2.dept_short_name,
        /*lg2.head_of_dept_id,*/
        dr2.child_id AS group_id,
        lg2.dept_name AS group_name,
        lg2.dept_short_name AS group_short_name/*,
        lg2.head_of_dept_id AS head_of_group_id*/
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
) AS t2 ON t1.dept_id = t2.group_id
LEFT JOIN (
    SELECT DISTINCT ON (user_id)
        empl_dept_id,
        'тек. - ' AS cur_dept
    FROM empl_dept
    WHERE date_promotion <= now() AND user_id = %s
    ORDER BY user_id, date_promotion DESC
    LIMIT 1
) AS t3 ON t1.empl_dept_id = t3.empl_dept_id
WHERE user_id = %s
ORDER BY date_promotion DESC;
"""


# Define a function to retrieve nonce within the application context
def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@employee_app_bp.before_request
def before_request():
    app_login.before_request()


# Проверка, что пользователь не уволен
@employee_app_bp.before_request
def check_user_status():
    app_login.check_user_status()


# Главная страница раздела 'Объекты'
@employee_app_bp.route('/employees-list', methods=['GET'])
@login_required
def get_employees_list():
    """Главная страница раздела 'Объекты' """
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)
        
        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return error_handlers.handle403(403)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("users")

        # Список сотрудников
        cursor.execute(
            """
            SELECT 
                t1.user_id - 1 AS user_id,
                --(COALESCE(t1.employment_date, now()::date) - interval '1 day')::date::text AS employment_date,
                
                CASE 
                    WHEN t1.is_fired THEN (COALESCE(t11.haf_date, now()::date) - interval '1 day')::date::text
                    ELSE (COALESCE(t1.employment_date, now()::date + 1000) - interval '1 day')::date::text
                END AS employment_date,
    
                t1.employment_date::text AS initial_first_val,
                t1.user_id AS initial_id_val
            FROM users AS t1
            
            -- первый статус 'hire'
            LEFT JOIN (
                SELECT 
                    user_id,
                    MIN(haf_date) AS haf_date
                FROM hire_and_fire
                WHERE haf_type = 'hire'
                GROUP BY user_id
            ) AS t11 ON t1.user_id = t11.user_id
            
            ORDER BY CASE 
                    WHEN t1.is_fired THEN (COALESCE(t11.haf_date, now()::date) - interval '1 day')::date::text
                    ELSE (COALESCE(t1.employment_date, now()::date + 1000) - interval '1 day')::date::text
                END, t1.user_id
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
                               education=education, contractor=contractor, nonce=get_nonce(),
                               title='Список сотрудников')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@employee_app_bp.route('/get-first-employee', methods=['POST'])
@login_required
def get_first_employee():
    """Постраничная выгрузка списка сотрудников"""
    try:
        user_id = app_login.current_user.get_id()
        
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

            print(f"""/get-first-employee\\n                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};""")
            print('query_value', query_value)

            cursor.execute(
                f"""
                WITH EmployeePeriods AS (
                SELECT
                    user_id,
                    CASE 
                        WHEN haf_type = 'hire' THEN haf_date
                        ELSE NULL
                    END AS hire_date,
                    COALESCE(LEAD(haf_date) OVER (PARTITION BY user_id ORDER BY haf_date), now()::date) - haf_date + 1 AS work_days,
                    haf_type
                FROM hire_and_fire
                WHERE haf_type IN ('hire', 'fire')
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
                    
                    COALESCE(t5.education_name, ' ') AS education_name,
                    
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
                    
                    --(COALESCE(t1.employment_date, now()::date + 1000) {order} interval '1 day')::text AS employment_date,
                    
                    CASE 
                        WHEN t1.is_fired THEN (COALESCE(t11.haf_date, now()::date) {order} interval '1 day')::text
                        ELSE (COALESCE(t1.employment_date, now()::date + 1000) {order} interval '1 day')::text
                    END AS employment_date,
                    
                    (COALESCE(t1.date_of_dismissal, now()::date) {order} interval '1 day')::text AS date_of_dismissal,
                    
                    COALESCE(t7.work_days {order} 0.01, -1) AS f_work_days,
                    t10.full_day_status,
                    --t1.labor_status,
                    t12.empl_labor_status AS labor_status,
                    date_part('year', age(COALESCE(t1.b_day, now()::date)))::int {order} 1  AS full_years
    
                {USER_QUERY_JOIN}
    
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
            print(cursor.query[-230:])
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
                col_14 = ""
                col_15 = ""
                col_16 = employee["full_years"]

                if sort_col_1_order == 'DESC':
                    col_0 = col_0 + '+' if col_0 else col_0
                    col_2 = col_2 + '+' if col_2 else col_2
                    col_3 = col_3 + '+' if col_3 else col_3
                    col_4 = col_4 + '+' if col_4 else col_4
                    col_5 = col_5 + '+' if col_5 else col_5
                    col_7 = col_7 + '=' if col_7 else col_7
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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@employee_app_bp.route('/get-employee-pagination', methods=['POST'])
@login_required
def get_employee_pagination():
    """Постраничная выгрузка списка сотрудников"""
    try:
        user_id = app_login.current_user.get_id()

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
        # print('/get-employee-pagination\n', '= - ' * 20,
        #       f"""WHERE  {where_expression}
        #         ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
        #         LIMIT {limit};""")
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
            msg_for_user = app_login.create_traceback(info=sys.exc_info(), error_type='warning')
            return jsonify({
                'employee': 0,
                'sort_col': 0,
                'status': 'error',
                'description': msg_for_user,
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
        col_13 = employee[-1]["f_work_days"]
        col_14 = employee[-1]["full_day_status"]
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
                    CASE 
                        WHEN haf_type = 'hire' THEN haf_date
                        ELSE NULL
                    END AS hire_date,
                    COALESCE(LEAD(haf_date) OVER (PARTITION BY user_id ORDER BY haf_date), now()::date) - haf_date + 1 AS work_days,
                    haf_type
                FROM hire_and_fire
                WHERE haf_type IN ('hire', 'fire')
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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'employee': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


@employee_app_bp.route('/get_card_employee/<int:employee_id>', methods=['GET'])
@login_required
def get_card_employee(employee_id):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=employee_id, user_id=user_id)

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

            # Список всех переходов между отделами
            cursor.execute(
                DEPT_LIST_FOR_EMPLOYEE,
                [employee_id, employee_id]
            )
            dept_promotions = cursor.fetchall()
            if dept_promotions:
                # print('     tow_list')
                for i in range(len(dept_promotions)):
                    dept_promotions[i] = dict(dept_promotions[i])
                    if dept_promotions[i]['dept_short_name'] != dept_promotions[i]['group_short_name']:
                        dept_promotions[i]['user_card_hover_history_row_name'] = \
                            (f"{dept_promotions[i]['cur_dept']}{dept_promotions[i]['dept_short_name']} => "
                             f"{dept_promotions[i]['group_name']} ({dept_promotions[i]['group_short_name']})")
                    else:
                        dept_promotions[i]['user_card_hover_history_row_name'] = \
                            (f"{dept_promotions[i]['cur_dept']} "
                             f"{dept_promotions[i]['group_name']} ({dept_promotions[i]['group_short_name']})")

            # Список всех приёмов/увольнений
            cursor.execute(
                f"""
                SELECT
                    t1.haf_date,
                    to_char(t1.haf_date, 'dd.mm.yyyy') AS date_haf_txt,
                    t1.created_at,
                    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt,
                    CASE
                        WHEN t1.haf_type = 'fire' THEN 'увольнение'
                        WHEN t1.haf_type = 'hire' THEN 'приём'
                        WHEN t1.haf_type = 'maternity_leave' THEN 'декрет'
                        ELSE '????'
                    END AS haf_name,
                    COALESCE(t2.cur_haf, '') AS cur_haf
                FROM public.hire_and_fire AS t1
                LEFT JOIN (
                    SELECT DISTINCT ON (user_id)
                        haf_id,
                        'тек. - ' AS cur_haf
                    FROM hire_and_fire
                    WHERE haf_date <= now() AND user_id = %s
                    ORDER BY user_id, haf_date DESC
                    LIMIT 1
                ) AS t2 ON t1.haf_id = t2.haf_id
                WHERE t1.user_id = %s
                ORDER BY t1.haf_date DESC, t1.created_at;
                """,
                [employee_id, employee_id]

            )
            haf_list = cursor.fetchall()
            if haf_list:
                for i in range(len(haf_list)):
                    haf_list[i] = dict(haf_list[i])
                    haf_list[i]['user_card_hover_history_row_name'] = \
                        f"{haf_list[i]['cur_haf']}{haf_list[i]['haf_name']}"

            # Список изменений зарплаты
            cursor.execute(
                f"""
                SELECT 
                    to_char(t1.salary_date, 'dd.mm.yyyy') AS salary_date,
                    TRIM(BOTH ' ' FROM to_char(t1.salary_sum, '999 999 990D99 ₽')) AS salary_sum_rub,
                    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at,
                    t3.dept_short_name,
                    t1.salary_sum,
                    COALESCE(t6.cur_salary, '') AS cur_salary
                FROM 
                    salaries AS t1
                JOIN 
                    empl_dept AS t2 ON t1.user_id = t2.user_id
                LEFT JOIN (
                    SELECT DISTINCT ON (user_id)
                        salary_id,
                        'тек. - ' AS cur_salary
                    FROM salaries
                    WHERE salary_date <= now() AND user_id = %s
                    ORDER BY user_id, salary_date DESC
                    LIMIT 1
                ) AS t6 ON t1.salary_id = t6.salary_id
                LEFT JOIN (
                        SELECT 
                            dept_id, 
                            dept_short_name
                        FROM list_dept
                    ) AS t3 ON t2.dept_id = t3.dept_id
                WHERE 
                    t1.user_id = %s AND
                    t2.date_promotion = (
                        SELECT 
                            MAX(sub_t2.date_promotion)
                        FROM empl_dept AS sub_t2
                        WHERE sub_t2.user_id = t1.user_id AND sub_t2.date_promotion <= t1.salary_date
                    )
                ORDER BY t1.salary_date;
                """,
                [employee_id, employee_id]
            )
            salaries_list = cursor.fetchall()
            if salaries_list:
                # print('     tow_list')
                for i in range(len(salaries_list)):
                    salaries_list[i] = dict(salaries_list[i])

            # Список всех изменений статуса трудозатрат
            cursor.execute(
                f"""
                    SELECT
                        t1.empl_labor_date,
                        to_char(t1.empl_labor_date, 'dd.mm.yyyy') AS empl_labor_date_txt,
                        t1.created_at,
                        to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt,
                        CASE
                            WHEN t1.empl_labor_status IS TRUE THEN 'Добавлен'
                            WHEN t1.empl_labor_status IS FALSE THEN 'Отменен'
                            ELSE '????'
                        END AS empl_labor_status_name,
                        COALESCE(t2.cur_labor_status, '') AS cur_labor_status
                    FROM public.labor_status AS t1
                    LEFT JOIN (
                        SELECT DISTINCT ON (user_id)
                            empl_labor_status_id,
                            'тек. - ' AS cur_labor_status
                        FROM labor_status
                        WHERE empl_labor_date <= now() AND user_id = %s
                        ORDER BY user_id, empl_labor_date DESC
                        LIMIT 1
                    ) AS t2 ON t1.empl_labor_status_id = t2.empl_labor_status_id
                    WHERE t1.user_id = %s
                    ORDER BY t1.empl_labor_date DESC, t1.created_at;
                    """,
                [employee_id, employee_id]

            )
            labor_status_list = cursor.fetchall()
            hour_per_day_norm_list = []
            if labor_status_list:
                for i in range(len(labor_status_list)):
                    labor_status_list[i] = dict(labor_status_list[i])
                    labor_status_list[i]['user_card_hover_history_row_name'] = \
                        f"{labor_status_list[i]['cur_labor_status']}{labor_status_list[i]['empl_labor_status_name']}"

                # Список всех изменений статуса почасовой оплаты
                cursor.execute(
                    f"""
                        SELECT
                            t1.empl_hours_date,
                            to_char(t1.empl_hours_date, 'dd.mm.yyyy') AS empl_hours_date_txt,
                            t1.created_at,
                            to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt,
                            CASE
                                WHEN t1.full_day_status IS TRUE THEN 'Добавлен'
                                WHEN t1.full_day_status IS FALSE THEN 'Отменен'
                                ELSE '????'
                            END AS full_day_status_name,
                            COALESCE(t2.cur_full_day_status, '') AS cur_full_day_status
                        FROM public.hour_per_day_norm AS t1
                        LEFT JOIN (
                            SELECT DISTINCT ON (user_id)
                                empl_hours_status_id,
                                'тек. - ' AS cur_full_day_status
                            FROM public.hour_per_day_norm
                            WHERE empl_hours_date <= now() AND user_id = %s
                            ORDER BY user_id, empl_hours_date DESC
                            LIMIT 1
                        ) AS t2 ON t1.empl_hours_status_id = t2.empl_hours_status_id
                        WHERE t1.user_id = %s
                        ORDER BY t1.empl_hours_date DESC, t1.created_at;
                        """,
                    [employee_id, employee_id]

                )
                hour_per_day_norm_list = cursor.fetchall()
                if hour_per_day_norm_list:
                    for i in range(len(hour_per_day_norm_list)):
                        hour_per_day_norm_list[i] = dict(hour_per_day_norm_list[i])
                        hour_per_day_norm_list[i]['user_card_hover_history_row_name'] = \
                            (f"{hour_per_day_norm_list[i]['cur_full_day_status']}"
                             f"{hour_per_day_norm_list[i]['full_day_status_name']}")

            app_login.conn_cursor_close(cursor, conn)

            # print(dict(employee))

            # Return the updated data as a response
            return jsonify({
                'status': 'success',
                'employee': dict(employee),
                'salaries_list': salaries_list,
                'dept_promotions': dept_promotions,
                'haf_list': haf_list,
                'labor_status_list': labor_status_list,
                'hour_per_day_norm_list': hour_per_day_norm_list,
            })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@employee_app_bp.route('/save_employee', methods=['POST'])
@login_required
def save_employee():
    try:
        user_id = app_login.current_user.get_id()
        try:
            employee_id = int(request.get_json()['user_id'])
        except:
            employee_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=employee_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return jsonify({
                'employee': 0,
                'status': 'error',
                'description': 'Доступ запрещен',
            })

        employee_data = request.get_json()
        print(f'employee_data.keys()  {employee_data.keys()}')

        # Конвертируем тип данных для записи в БД
        for i in employee_data.keys():
            if i == 'contractor_id':
                employee_data['contractor_id'] = int(employee_data['contractor_id'])
            elif i == 'pers_num':
                employee_data['pers_num'] = int(employee_data['pers_num'])
            elif i == 'dept_id':
                employee_data['dept_id'] = int(employee_data['dept_id'])
            elif i == 'date_promotion':
                employee_data['date_promotion'] = date.fromisoformat(employee_data['date_promotion'])
            elif i == 'position_id':
                employee_data['position_id'] = int(employee_data['position_id'])
            elif i == 'b_day':
                employee_data['b_day'] = date.fromisoformat(employee_data['b_day'])
            elif i == 'education_id':
                employee_data['education_id'] = int(employee_data['education_id'])
            elif i == 'salary_sum':
                employee_data['salary_sum'] = app_payment.convert_amount(employee_data['salary_sum'])
            elif i == 'salary_date':
                employee_data['salary_date'] = date.fromisoformat(employee_data['salary_date'])
            elif i == 'employment_date':
                employee_data['employment_date'] = date.fromisoformat(employee_data['employment_date'])

        # Отдельно проверяем, изменилась ли ЗП, отдел
        salary_data = {
            'salary_sum': employee_data['salary_sum'],
            'salary_date': employee_data['salary_date']
        }
        promotion_data = {
            'dept_id': employee_data['dept_id'],
            'date_promotion': employee_data['date_promotion']
        }

        hire_date = employee_data['employment_date']

        del employee_data['user_id']
        del employee_data['salary_sum']
        del employee_data['salary_date']
        del employee_data['dept_id']
        del employee_data['date_promotion']

        print('1. employee_data ------------------------------')
        print(employee_data)
        print(type(employee_data), '-' * 30)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("users")

        # Данные о сотруднике
        cursor.execute(
            f"""{USER_QUERY}
            WHERE t1.user_id = {employee_id}""")
        employee = cursor.fetchone()

        print('2. employee ------------------------------')
        print(employee)
        print(type(employee), '-' * 30)

        employee['b_day'] = date.fromisoformat(employee['b_day'])
        employee['salary_date'] = date.fromisoformat(employee['salary_date'])
        employee['employment_date'] = date.fromisoformat(employee['employment_date'])

        # Список изменений отделов
        cursor.execute(
            f"""
            SELECT 
                t1.dept_id,
                t1.date_promotion,
                to_char(t1.date_promotion, 'dd.mm.yyyy') AS date_promotion_txt,
                to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt,
                t2.dept_name
            FROM empl_dept AS t1
            LEFT JOIN list_dept AS t2 ON t1.dept_id = t2.dept_id
            WHERE t1.user_id = {employee_id}
            ORDER BY t1.date_promotion;
            """
        )
        empl_dept_list = cursor.fetchall()

        if empl_dept_list:
            for i in range(len(empl_dept_list)):
                empl_dept_list[i] = dict(empl_dept_list[i])

        print('3. empl_dept_list ------------------------------')
        print(empl_dept_list)
        print(type(empl_dept_list), '-' * 30)

        # Список изменений зарплаты
        cursor.execute(
            f"""
            SELECT 
                salary_date,
                to_char(salary_date, 'dd.mm.yyyy') AS salary_date_txt,
                salary_sum,
                TRIM(BOTH ' ' FROM to_char(salary_sum, '999 999 990D99 ₽')) AS salary_sum_rub,
                to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt
            FROM salaries
            WHERE user_id = {employee_id};
            """
        )
        salaries_list = cursor.fetchall()

        if salaries_list:
            for i in range(len(salaries_list)):
                salaries_list[i] = dict(salaries_list[i])

        print('4. salaries_list ------------------------------')
        print(salaries_list)
        print(type(salaries_list), '-' * 30)

        difference_dict = dict()

        for k, v in employee_data.items():
            if k in employee:
                if employee.get(k) != v:
                    print(f'k: {k}  --  {v}    __{employee.get(k)}__  {employee.get(k) != v} {type(employee.get(k))} {type(v)}')
                    difference_dict[k] = v

        # FROM empl_dept. Проверяем изменение отдела
        columns_e_d = ('user_id', 'dept_id', 'date_promotion')
        values_e_d = []
        query_e_d = None

        if empl_dept_list:
            for j in range(len(empl_dept_list)):
                i = empl_dept_list[j]
                # Изменений нет
                if i['dept_id'] == promotion_data['dept_id'] and i['date_promotion'] == promotion_data['date_promotion']:
                    values_e_d = []
                    break
                # Определяем валидность изменения
                else:
                    # Изменён отдел и указана дата одного из сохранений
                    if i['dept_id'] != promotion_data['dept_id'] and i['date_promotion'] == promotion_data['date_promotion']:
                        return jsonify({
                            'status': 'error',
                            'description': ['Ошибка', 'Нельзя изменить отдел в указанную дату',
                                            'В базе данных есть запись:',
                                            f'"{i["dept_name"]}" => {i["date_promotion_txt"]}',
                                            f'Дата добавление в БД: {i["created_at_txt"]}'],
                        })
                    if i != 0 and i != len(empl_dept_list) - 1:
                        pass
                    # Дата сохранения меньше самой новой записи. Нельзя сохранить более ранние переходы,
                    # т.к. это может вызвать коллизии в отправленных часах
                    if promotion_data['date_promotion'] < i['date_promotion']:
                        return jsonify({
                            'status': 'error',
                            'description': ['Ошибка', 'Нельзя сохранить изменения за указанную дату, т.к. сотрудник мог '
                                                   'отправить часы начиная с указанной даты за старый отдел',
                                            'В базе данных есть запись:',
                                            f'"{i["dept_name"]}" => {i["date_promotion_txt"]}',
                                            f'Дата добавление в БД: {i["created_at_txt"]}'],
                        })
                    # Если всё проверили и последний перевод совпадает
                    if i != 0 and i == len(empl_dept_list)-1 and empl_dept_list[j-1]['dept_id'] == promotion_data['dept_id']:
                        return jsonify({
                            'status': 'error',
                            'description': ['Ошибка', 'Нельзя изменить отдел, т.к. предыдущее изменение '
                                                      'было в тот же отдел',
                                            'В базе данных есть запись:',
                                            f'"{i["dept_name"]}" => {i["date_promotion_txt"]}',
                                            f'Дата добавление в БД: {i["created_at_txt"]}'],
                        })
                    # Это смена отдела
                    values_e_d = [employee_id, promotion_data['dept_id'], promotion_data['date_promotion']]
        else:
            values_e_d = [employee_id, promotion_data['dept_id'], promotion_data['date_promotion']]

        # FROM salaries
        columns_s = ('user_id', 'salary_sum', 'salary_date')
        query_s = None

        values_s = []
        query_s = None
        if salaries_list:
            for j in range(len(salaries_list)):
                i = salaries_list[j]
                # Изменений нет
                if i['salary_sum'] == salary_data['salary_sum'] and i['salary_date'] == salary_data['salary_date']:
                    query_s = []
                    break
                # Определяем валидность изменения
                elif i['salary_date'] == salary_data['salary_date']:
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', 'Нельзя изменить зарплату в указанную дату',
                                        'В базе данных есть запись:',
                                        f'{i["salary_sum_rub"]} => {i["salary_date_txt"]}',
                                        f'Дата добавление в БД: {i["created_at_txt"]}'],
                    })
                # Всё ок
                values_s = [employee_id, salary_data['salary_sum'], salary_data['salary_date']]
        else:
            values_s = [employee_id, salary_data['salary_sum'], salary_data['salary_date']]

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

        # FROM hour_per_day_norm
        columns_h_p_d_n = ('user_id', 'full_day_status', 'empl_hours_date')
        values_h_p_d_n = [values_empl[0], None, date.fromisoformat(str(date.today()))]
        query_h_p_d_n = None

        # FROM hire_and_fire
        columns_h_a_f = ('user_id', 'haf_date', 'haf_type')
        values_h_a_f = [values_empl[0], None, None]
        query_h_a_f = None

        # Столбцы не из таблицы users
        not_users_cols = {'pers_num', 'dept_id', 'salary_sum', 'salary_date', 'labor_status', 'full_day_status'}

        for k, v in difference_dict.items():
            if k not in not_users_cols:
                columns_empl.append(k)
                values_empl.append(v)
            else:
                # FROM personnel_number
                if k in columns_p_n:
                    values_p_n[columns_p_n.index(k)] = v
                if k in columns_h_p_d_n:
                    values_h_p_d_n[columns_h_p_d_n.index(k)] = v

        # Список всех приёмов/увольнений сотрудника
        cursor.execute(
            f"""
                SELECT 
                    haf_date,
                    created_at,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt, 
                    haf_type AS type,
                    to_char(haf_date, 'dd.mm.yyyy') AS haf_date_txt
                FROM hire_and_fire
                WHERE  user_id = {employee_id} AND haf_type IN ('hire', 'fire')
                ORDER BY haf_date ASC, created_at ASC;
                """
        )
        hire_and_fire_list = cursor.fetchall()
        print('hire_and_fire_list', hire_and_fire_list)

        if hire_and_fire_list:
            if hire_and_fire_list[0][3] != 'hire':
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', 'Первая запись о сотруднике не приём или увольнение',
                                    'Обратитесь к администратору сайта'],
                })
            last_type = 'fire' if hire_and_fire_list[0][3] == 'hire' else hire_and_fire_list[0][3]
            print('last_type', last_type, last_type not in ('fire', 'fire'))

            for i in range(len(hire_and_fire_list)):
                j = dict(hire_and_fire_list[i])
                # Проверка, что два приёма или увольнения не назначены в один день
                if last_type == j['type']:
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', f'Сотрудник уже уволен с {j["haf_date_txt"]}',
                                        f'Дата создания {j["created_at_txt"]} {j["type"]}'],
                    })
                last_type = j['type']
                if hire_date < j['haf_date']:
                    if last_type == 'hire':
                        last_type = 'приём'
                    elif last_type == 'fire':
                        last_type = 'увольнение'
                    elif last_type == 'maternity_leave':
                        last_type = 'декрет'
                    else:
                        last_type = '????'
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка',
                                        f'Была найдена запись с более поздней датой {last_type} с {hire_date}',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })
                # Если дата увольнения совпадает с датой приёма - ошибка,
                # нельзя создать записи не с уникальной датой для пользователя
                if j['haf_date'] == hire_date and j['type'] == 'hire':
                    values_h_a_f = None
                    break
                # Если нашли похожую запись об увольнении
                if j['haf_date'] == hire_date and j['type'] == 'fire':
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', f'Запись об увольнении сотрудника с {hire_date} была создана ранее',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })
            if values_h_a_f:
                # Если не нашли запись, значит добавляем новую
                values_h_a_f[1] = hire_date
                values_h_a_f[2] = 'hire'
        else:
            values_h_a_f[1] = hire_date
            values_h_a_f[2] = 'hire'

        action = 'INSERT INTO'

        # FROM users
        if len(values_empl) > 1:
            print('\n5. FROM users', len(values_empl))
            columns_empl = tuple(columns_empl)
            action_empl = 'UPDATE'
            query_empl = app_payment.get_db_dml_query(action=action_empl, table='users', columns=columns_empl)
            print(query_empl)
            print(values_empl)
            execute_values(cursor, query_empl, [values_empl])

        # FROM personnel_number
        if values_p_n[0]:
            print('\n6. FROM personnel_number')
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
        if len(values_e_d):
            print('\n7. FROM empl_dept')
            columns_e_d = tuple(columns_e_d)
            query_e_d = app_payment.get_db_dml_query(action=action, table='empl_dept', columns=columns_e_d)
            print(query_e_d)
            print(values_e_d)
            execute_values(cursor, query_e_d, [values_e_d])

        # FROM salaries
        if len(values_s):
            print('\n8. FROM salaries')
            columns_s = tuple(columns_s)
            query_s = app_payment.get_db_dml_query(action=action, table='salaries', columns=columns_s)
            print(query_s)
            print(values_s)
            execute_values(cursor, query_s, [values_s])

        # FROM hour_per_day_norm
        if values_h_p_d_n[1]:
            print('\n9. FROM hour_per_day_norm')
            columns_h_p_d_n = tuple(columns_h_p_d_n)
            query_h_p_d_n = app_payment.get_db_dml_query(action=action, table='hour_per_day_norm',
                                                         columns=columns_h_p_d_n)
            print(query_h_p_d_n)
            print(values_h_p_d_n)
            execute_values(cursor, query_h_p_d_n, [values_h_p_d_n])

        # FROM hire_and_fire
        if values_h_a_f:
            print('\n10. FROM hire_and_fire')
            columns_h_a_f = tuple(columns_h_a_f)
            query_h_a_f = app_payment.get_db_dml_query(action=action, table='hire_and_fire', columns=columns_h_a_f)
            print(query_h_a_f)
            print(values_h_a_f)
            execute_values(cursor, query_h_a_f, [values_h_a_f])

        if (len(values_empl) < 2 and not values_p_n[0] and not len(values_e_d) and not len(values_s) and
                not values_h_p_d_n[1] and values_h_a_f is None):
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            app_login.conn_cursor_close(cursor, conn)
            return jsonify({
                'status': 'info',
                'description': ['Изменений не обнаружено', 'Данные не сохранены']
            })

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        print('=__' * 20)
        pprint(difference_dict)

        flash(message=[f"Карточка сотрудника сохранена", ], category='success')

        # Return the updated data as a response
        return jsonify({
            'status': 'success',
            'employee': dict(employee),
        })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@employee_app_bp.route('/fire_employee', methods=['POST'])
@login_required
def fire_employee():
    try:
        user_id = app_login.current_user.get_id()
        try:
            employee_id = int(request.get_json()['user_id'])
        except:
            employee_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=employee_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 7):
            return jsonify({
                'employee': 0,
                'status': 'error',
                'description': 'Доступ запрещен',
            })

        employee_data = request.get_json()

        employee_id = int(employee_data['employee_id'])
        fire_date =  date.fromisoformat(employee_data['fire_date']) if employee_data['fire_date'] else None

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("users")

        # Данные о сотруднике
        cursor.execute(
            f"""
                SELECT 
                    user_id,
                    concat_ws(' ', last_name, LEFT(first_name, 1) || '.', CASE
                        WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
                    END) AS short_full_name,
                    date_of_dismissal
                FROM users
                WHERE user_id = {employee_id};
                """
        )
        employee_data_db = dict(cursor.fetchone())
        employee_name = employee_data_db['short_full_name']

        # Список всех приёмов/увольнений сотрудника
        cursor.execute(
            f"""
                SELECT 
                    haf_date,
                    created_at,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt, 
                    haf_type AS type,
                    to_char(haf_date, 'dd.mm.yyyy') AS haf_date_txt
                FROM hire_and_fire
                WHERE  user_id = {employee_id} AND haf_type IN ('hire', 'fire')
                ORDER BY haf_date ASC, created_at ASC;
                """
        )
        hire_and_fire_list = cursor.fetchall()
        print('hire_and_fire_list', hire_and_fire_list)

        last_hire = None
        last_fire = None
        last_type = None

        if hire_and_fire_list:
            if hire_and_fire_list[0][3] != 'hire':
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', 'Первая запись о сотруднике не приём или увольнение',
                                    'Обратитесь к администратору сайта'],
                })

            last_type = 'fire' if hire_and_fire_list[0][3] == 'hire' else hire_and_fire_list[0][3]
            print('last_type', last_type, last_type not in ('fire', 'fire'))

            for i in range(len(hire_and_fire_list)):
                j = dict(hire_and_fire_list[i])
                # Проверка, что два приёма или увольнения не назначены в один день (прошлая и текущая строка)
                if last_type == j['type']:
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', f'Сотрудник уже уволен с {j["haf_date_txt"]}',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })
                last_type = j['type']
                if fire_date < j['haf_date']:
                    last_type = 'приём' if last_type == 'hire' else 'увольнение'
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка',
                                        f'Была найдена запись с более поздней датой {last_type} с {fire_date}',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })
                # Если дата увольнения совпадает с датой приёма - ошибка,
                # нельзя создать записи не с уникальной датой для пользователя
                if j['haf_date'] == fire_date and j['type'] == 'hire':
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка',
                                        f'Нельзя уволить сотрудника в день приёма',
                                        f'Найдена запись: дата приёма {j["haf_date_txt"]}',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })
                # Если нашли похожую запись об увольнении
                if j['haf_date'] == fire_date and j['type'] == 'fire':
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', f'Запись об увольнении сотрудника с {fire_date} была создана ранее',
                                        f'Дата создания {j["created_at_txt"]}'],
                    })

        now = date.today()

        print('employee_data_db')
        print(employee_data_db)
        print('hire_and_fire_list')
        print(hire_and_fire_list)

        print(now, fire_date, now >= fire_date)

        columns_haf = tuple(('user_id', 'haf_date', 'haf_type'))
        values_haf = [employee_id, fire_date, 'fire']
        action_haf = 'INSERT INTO'
        query_haf = app_payment.get_db_dml_query(action=action_haf, table='hire_and_fire', columns=columns_haf)
        print(query_haf)
        print(values_haf)
        execute_values(cursor, query_haf, [values_haf])

        if now >= fire_date:
            columns_u = tuple(('user_id', 'is_fired::boolean', 'employment_date::date', 'date_of_dismissal'))
            values_u = [employee_id, 'TRUE', None, fire_date]
            action_empl = 'UPDATE'
            query_u = app_payment.get_db_dml_query(action=action_empl, table='users', columns=columns_u)
            print(query_u)
            print(values_u)
            execute_values(cursor, query_u, [values_u])

            # subquery_pn = 'ON CONFLICT DO NOTHING'
            # action_pn = 'DELETE'
            # columns_pn = 'user_id::int'
            # query_pn = app_payment.get_db_dml_query(action=action_pn, table='personnel_number', columns=columns_pn,
            #                                             subquery=subquery_pn)
            # print(action_pn)
            # print(query_pn)
            # execute_values(cursor, query_pn, ((employee_id,),))

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        flash(message=['Изменение сохранены', f'Сотрудник: {employee_name}', f'id: {employee_id}', f'Будет уволен: {fire_date}'], category='success')

        # Return the updated data as a response
        return jsonify({
            'status': 'success',
        })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


def get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id,
                         manual_type=''):
    # Колонка по которой идёт сортировка в таблице
    # print(col_1.split('#'))
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
    col_11 = """CASE 
        WHEN t1.is_fired THEN COALESCE(to_char(t11.haf_date, 'dd.mm.yyyy'), '')
        ELSE COALESCE(to_char(t1.employment_date, 'dd.mm.yyyy'), '')
    END"""
    col_12 = "to_char(t1.date_of_dismissal, 'dd.mm.yyyy')"
    col_13 = "COALESCE(t7.work_days, -1)"
    col_14 = "t10.full_day_status"
    col_15 = "t12.empl_labor_status"
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
    col_7 = "COALESCE(t5.education_name, '')"
    col_8 = "COALESCE(t6.salary_sum, '0')"
    col_9 = "COALESCE(t6.salary_date, now()::date)"
    col_10 = """CASE 
                    WHEN t9.pers_num IS NOT NULL AND t1.is_fired THEN 'увол.'
                    WHEN t9.pers_num IS NOT NULL AND t1.is_maternity_leave THEN 'декр.'
                    WHEN t9.pers_num IS NOT NULL THEN 'работ.'
                    ELSE ' '
                END"""
    col_11 = """CASE 
        WHEN t1.is_fired THEN COALESCE(t11.haf_date, now()::date)
        ELSE COALESCE(t1.employment_date, now()::date + 1000)
    END"""
    col_12 = "COALESCE(t1.date_of_dismissal, now()::date)"
    col_13 = "COALESCE(t7.work_days, -1)"
    col_14 = "t10.full_day_status"
    col_15 = "t12.empl_labor_status"
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
    col_14 = "t10.full_day_status"
    col_15 = "t12.empl_labor_status"
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
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return False


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
