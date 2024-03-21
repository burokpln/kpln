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

contract_app_bp = Blueprint('app_contract', __name__)

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None

# ______________________________________________
QUERY_MAIN_JOIN = """
FROM objects AS t1
"""

QUERY_MAIN = f"""
SELECT
    t1.object_id,
    t1.object_name
{QUERY_MAIN_JOIN}
"""
# ______________________________________________
QUERY_OBJ_JOIN = """
FROM objects AS t1
"""

QUERY_OBJ = f"""
SELECT
    t1.object_id,
    t1.object_name
{QUERY_OBJ_JOIN}
"""
# ______________________________________________
QUERY_CONTRACTS_JOIN = """
FROM objects AS t1
"""

QUERY_CONTRACTS = f"""
SELECT
    t1.object_id,
    t1.object_name
{QUERY_CONTRACTS_JOIN}
"""
# ______________________________________________
QUERY_ACTS_JOIN = """
FROM objects AS t1
"""

QUERY_ACTS = f"""
SELECT
    t1.object_id,
    t1.object_name
{QUERY_ACTS_JOIN}
"""
# ______________________________________________
QUERY_PAYS_JOIN = """
FROM objects AS t1
"""

QUERY_PAYS = f"""
SELECT
    t1.object_id,
    t1.object_name
{QUERY_PAYS_JOIN}
"""


@contract_app_bp.before_request
def before_request():
    app_login.before_request()


@contract_app_bp.route('/get-first-contract', methods=['POST'])
@login_required
def get_first_contract():
    """Постраничная выгрузка списка несогласованных платежей"""
    try:
        page_name = request.get_json()['page_url']
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        if page_name == 'contracts-acts-list' or page_name == 'contracts-objects':
            col_id = 't0.contract_id'
        else:
            col_id = 't1.object_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']

        if col_1.split('#')[0] == 'False':
            return jsonify({
                'payment': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        # Колонка по которой идёт сортировка в таблице
        col_num = int(col_1.split('#')[0])
        # Направление сортировки
        sort_direction = col_1.split('#')[1]

        # Список колонок для сортировки
        sort_col = {
            'col_1': [f"{col_num}#{sort_direction}"],  # Первая колонка
            'col_id': ''
        }

        user_id = app_login.current_user.get_id()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
            query_value, sort_col, col_num = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        if sort_col_1_order == 'DESC':
            order = '+'
        else:
            order = '-'

        if not where_expression2:
            where_expression2 = 'true'

        print(f"""                WHERE {where_expression2}
                        ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                        LIMIT {limit};""")
        print('query_value', query_value)

        if page_name == 'contracts-main':
            cursor.execute(
                f"""
                SELECT
                    object_id {order} 1 AS object_id,
                    object_name
                {QUERY_MAIN_JOIN}
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
        elif page_name == 'contracts-objects':
            col_id = 't0.contract_id'
            cursor.execute(
                f"""
                SELECT 
                    t0.contract_id {order} 1 AS contract_id,
                    t4.cost_item_name,
                    t1.payment_number,
                    t1.basis_of_payment,
                    t1.payment_description, 
                    t3.contractor_name,
                    COALESCE(t6.object_name, ' ') AS object_name,
                    t5.first_name,
                    t5.last_name,
                    t1.partner,
                    t1.payment_sum {order} 1 AS payment_sum,
                    COALESCE(t7.paid_sum, '0') {order} 1 AS paid_sum,
                    t0.approval_sum {order} 1 AS approval_sum,
                    COALESCE(t8.amount, '0') {order} 1 AS amount,
                    (t1.payment_due_date {order} interval '1 day')::text AS payment_due_date,
                    (t1.payment_at {order} interval '1 day')::timestamp without time zone::text AS payment_at
                FROM payments_approval AS t0
                LEFT JOIN (
                    SELECT 
                        contract_id, 
                        payment_number, 
                        basis_of_payment,
                        payment_description,
                        partner,
                        payment_sum,
                        payment_due_date,
                        payment_at,
                        our_companies_id,
                        cost_item_id,
                        responsible,
                        object_id
                    FROM payments_summary_tab
                ) AS t1 ON t0.contract_id = t1.contract_id
                LEFT JOIN (
                    SELECT contractor_id,
                        contractor_name
                    FROM our_companies            
                ) AS t3 ON t1.our_companies_id = t3.contractor_id
                LEFT JOIN (
                    SELECT cost_item_id,
                        cost_item_name
                    FROM payment_cost_items            
                ) AS t4 ON t1.cost_item_id = t4.cost_item_id
                LEFT JOIN (
                        SELECT user_id,
                            first_name,
                            last_name
                        FROM users
                ) AS t5 ON t1.responsible = t5.user_id
                LEFT JOIN (
                        SELECT object_id,
                            object_name
                        FROM objects
                ) AS t6 ON t1.object_id = t6.object_id
                LEFT JOIN (
                        SELECT 
                            DISTINCT contract_id,
                            SUM(paid_sum) OVER (PARTITION BY contract_id) AS paid_sum
                        FROM payments_paid_history
                ) AS t7 ON t0.contract_id = t7.contract_id
                LEFT JOIN (
                        SELECT DISTINCT ON (contract_id) 
                            parent_id::int AS contract_id,
                            parameter_value::numeric AS amount
                        FROM payment_draft
                        WHERE page_name = %s AND parameter_name = %s AND user_id = %s
                        ORDER BY contract_id, create_at DESC
                ) AS t8 ON t0.contract_id = t8.contract_id
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
        elif page_name == 'contracts-list':
            cursor.execute(
                f"""
                SELECT 
                    t1.contract_id {order} 1 AS contract_id,
                    t1.payment_number,
                    t4.cost_item_name,
                    t1.basis_of_payment,
                    t3.contractor_name,
                    t1.payment_description,
                    COALESCE(t6.object_name, ' ') AS object_name,
                    t5.first_name,
                    t5.last_name,
                    t1.partner,
                    t1.payment_sum {order} 1 AS payment_sum,
                    COALESCE(t7.paid_sum, 0) {order} 1 AS paid_sum,
                    (t1.payment_due_date {order} interval '1 day')::text AS payment_due_date,
                    t1.payment_at::timestamp without time zone::text AS payment_at
                FROM payments_summary_tab AS t1
                LEFT JOIN (
                        SELECT DISTINCT ON (contract_id) 
                            contract_id,
                            status_id,
                            SUM(approval_sum) OVER (PARTITION BY contract_id) AS approval_sum
                        FROM payments_approval_history
                        ORDER BY contract_id, create_at DESC
                ) AS t2 ON t1.contract_id = t2.contract_id
                LEFT JOIN (
                    SELECT contractor_id,
                        contractor_name
                    FROM our_companies            
                ) AS t3 ON t1.our_companies_id = t3.contractor_id
                LEFT JOIN (
                    SELECT cost_item_id,
                        cost_item_name
                    FROM payment_cost_items            
                ) AS t4 ON t1.cost_item_id = t4.cost_item_id
                LEFT JOIN (
                        SELECT user_id,
                            first_name,
                            last_name
                        FROM users
                ) AS t5 ON t1.responsible = t5.user_id
                LEFT JOIN (
                        SELECT object_id,
                            object_name
                        FROM objects
                ) AS t6 ON t1.object_id = t6.object_id
                LEFT JOIN (
                            SELECT 
                                DISTINCT contract_id,
                                SUM(paid_sum) OVER (PARTITION BY contract_id) AS paid_sum
                            FROM payments_paid_history
                    ) AS t7 ON t1.contract_id = t7.contract_id
                WHERE (t1.payment_owner = %s OR t1.responsible = %s) AND {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
        elif page_name == 'contracts-acts-list':
            cursor.execute(
                f"""
                SELECT 
                    t0.contract_id {order} 1 AS contract_id,
                    t1.payment_number,
                    t3.contractor_name,
                    t1.basis_of_payment, 
                    t4.cost_item_name,
                    t1.payment_description, 
                    COALESCE(t6.object_name, ' ') AS object_name,
                    t5.first_name,
                    t5.last_name,
                    t1.partner,
                    t1.payment_sum {order} 1 AS payment_sum,
                    t0.approval_sum {order} 1 AS approval_sum,
                    COALESCE(t7.paid_sum {order} 1, null) AS paid_sum,
                    (t1.payment_due_date {order} interval '1 day')::text AS payment_due_date,
                    (t1.payment_at {order} interval '1 day')::timestamp without time zone::text AS payment_at,
                    (t8.create_at {order} interval '1 day')::timestamp without time zone::text AS create_at                    
                FROM payments_approval AS t0
                LEFT JOIN (
                    SELECT 
                        contract_id, 
                        payment_number, 
                        basis_of_payment,
                        payment_description,
                        partner,
                        payment_sum,
                        payment_due_date,
                        payment_at,
                        our_companies_id,
                        cost_item_id,
                        responsible,
                        object_id
                    FROM payments_summary_tab
                ) AS t1 ON t0.contract_id = t1.contract_id
                LEFT JOIN (
                    SELECT contractor_id,
                        contractor_name
                    FROM our_companies            
                ) AS t3 ON t1.our_companies_id = t3.contractor_id
                LEFT JOIN (
                    SELECT cost_item_id,
                        cost_item_name
                    FROM payment_cost_items            
                ) AS t4 ON t1.cost_item_id = t4.cost_item_id
                LEFT JOIN (
                        SELECT user_id,
                            first_name,
                            last_name
                        FROM users
                ) AS t5 ON t1.responsible = t5.user_id
                LEFT JOIN (
                        SELECT object_id,
                            object_name
                        FROM objects
                ) AS t6 ON t1.object_id = t6.object_id
                LEFT JOIN (
                        SELECT 
                            DISTINCT contract_id,
                            SUM(paid_sum) OVER (PARTITION BY contract_id) AS paid_sum
                        FROM payments_paid_history
                ) AS t7 ON t0.contract_id = t7.contract_id
                LEFT JOIN (
                            SELECT DISTINCT ON (contract_id) 
                                contract_id,
                                create_at
                            FROM payments_approval_history
                            ORDER BY contract_id, create_at DESC
                    ) AS t8 ON t0.contract_id = t8.contract_id
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
        elif page_name == 'contracts-payments-list':
            cursor.execute(
                f"""
                WITH t0 AS (
                    SELECT 
                        contract_id,
                        MAX(create_at) AS paid_at,
                        SUM(paid_sum) AS paid_sum
                    FROM payments_paid_history
                    GROUP BY contract_id
                )
                SELECT 
                    t0.contract_id {order} 1 AS contract_id,
                    t1.payment_number,
                    t4.cost_item_name,
                    t1.basis_of_payment,
                    t3.contractor_name,
                    t1.payment_description,
                    COALESCE(t6.object_name, ' ') AS object_name,
                    t5.first_name,
                    t5.last_name,
                    t1.partner,
                    t1.payment_sum {order} 1 AS payment_sum,
                    t2.approval_sum {order} 1 AS approval_sum,
                    t0.paid_sum {order} 1 AS paid_sum,
                    (t1.payment_due_date {order} interval '1 day')::text AS payment_due_date,
                    (t1.payment_at {order} interval '1 day')::timestamp without time zone::text AS payment_at,
                    t8.status_name 
                FROM t0
                LEFT JOIN (
                    SELECT 
                        contract_id, 
                        payment_number, 
                        basis_of_payment,
                        payment_description,
                        partner,
                        payment_sum,
                        payment_due_date,
                        payment_at,
                        our_companies_id,
                        cost_item_id,
                        responsible,
                        object_id
                    FROM payments_summary_tab
                ) AS t1 ON t0.contract_id = t1.contract_id
                LEFT JOIN (
                        SELECT DISTINCT ON (contract_id) 
                            contract_id,
                            SUM(approval_sum) OVER (PARTITION BY contract_id) AS approval_sum
                        FROM payments_approval_history
                        ORDER BY contract_id, create_at DESC
                ) AS t2 ON t0.contract_id = t2.contract_id
                LEFT JOIN (
                    SELECT contractor_id,
                        contractor_name
                    FROM our_companies            
                ) AS t3 ON t1.our_companies_id = t3.contractor_id
                LEFT JOIN (
                    SELECT cost_item_id,
                        cost_item_name
                    FROM payment_cost_items            
                ) AS t4 ON t1.cost_item_id = t4.cost_item_id
                LEFT JOIN (
                        SELECT user_id,
                            first_name,
                            last_name
                        FROM users
                ) AS t5 ON t1.responsible = t5.user_id
                LEFT JOIN (
                        SELECT object_id,
                            object_name
                        FROM objects
                ) AS t6 ON t1.object_id = t6.object_id
                LEFT JOIN (
                        SELECT DISTINCT ON (contract_id) 
                            contract_id,
                            status_id
                        FROM payments_paid_history
                        ORDER BY contract_id, create_at DESC
                ) AS t7 ON t0.contract_id = t7.contract_id
                LEFT JOIN (
                        SELECT payment_agreed_status_id AS status_id,
                            payment_agreed_status_name AS status_name
                        FROM payment_agreed_statuses
                ) AS t8 ON t7.status_id = t8.status_id
                WHERE {where_expression2}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )

        all_contracts = cursor.fetchone()

        app_login.conn_cursor_close(cursor, conn)
        if all_contracts:
            if page_name == 'contracts-main':
                col_0 = all_contracts["object_id"]
                col_1 = all_contracts["object_name"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+'
                else:
                    col_1 = col_1[:-1]
                filter_col = [
                    col_0, col_1
                ]
            elif page_name == 'contracts-objects':
                col_0 = ""
                col_1 = all_contracts["cost_item_name"]
                col_2 = all_contracts["payment_number"]
                col_3 = all_contracts["basis_of_payment"]
                col_4 = f'{all_contracts["contractor_name"]} {all_contracts["payment_description"]}'
                col_5 = all_contracts["object_name"]
                col_6 = f'{all_contracts["last_name"]} {all_contracts["first_name"]}'
                col_7 = all_contracts["partner"]
                col_8 = all_contracts["payment_sum"]
                col_9 = all_contracts["paid_sum"]
                col_10 = all_contracts["approval_sum"]
                col_11 = all_contracts["amount"]
                col_12 = all_contracts["payment_due_date"]
                col_13 = all_contracts["payment_at"]
                col_14 = ""

                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+'
                    col_2 = col_2 + '+'
                    col_3 = col_3 + '+'
                    col_4 = col_4 + '+'
                    col_5 = col_5 + '='
                    col_6 = col_6 + '+'
                    col_7 = col_7 + '+'
                else:
                    col_1 = col_1[:-1]
                    col_2 = col_2[:-1]
                    col_3 = col_3[:-1]
                    col_4 = col_4[:-1]
                    col_5 = col_5[:-1]
                    col_6 = col_6[:-1]
                    col_7 = col_7[:-1]

                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12,
                    col_13,
                    col_14
                ]
            elif page_name == 'contracts-list':
                col_0 = all_contracts["payment_number"]
                col_1 = all_contracts["cost_item_name"]
                col_2 = all_contracts["basis_of_payment"]
                col_3 = f'{all_contracts["contractor_name"]} {all_contracts["payment_description"]}'
                col_4 = all_contracts["object_name"]
                col_5 = f'{all_contracts["last_name"]} {all_contracts["first_name"]}'
                col_6 = all_contracts["partner"]
                col_7 = all_contracts["payment_sum"]
                col_8 = all_contracts["paid_sum"]
                col_9 = all_contracts["payment_due_date"]
                col_10 = all_contracts["payment_at"]
                if sort_col_1_order == 'DESC':
                    col_0 = col_0 + '+'
                    col_1 = col_1 + '+'
                    col_2 = col_2 + '+'
                    col_3 = col_3 + '+'
                    col_4 = col_4 + '='
                    col_5 = col_5 + '+'
                    col_6 = col_6 + '+'
                else:
                    col_0 = col_0[:-1]
                    col_1 = col_1[:-1]
                    col_2 = col_2[:-1]
                    col_3 = col_3[:-1]
                    col_4 = col_4[:-1]
                    col_5 = col_5[:-1]
                    col_6 = col_6[:-1]

                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10
                ]
            elif page_name == 'contracts-acts-list':
                col_0 = all_contracts["payment_number"]
                col_1 = all_contracts["cost_item_name"]
                col_2 = all_contracts["basis_of_payment"]
                col_3 = f'{all_contracts["contractor_name"]} {all_contracts["payment_description"]}'
                col_4 = all_contracts["object_name"]
                col_5 = f'{all_contracts["last_name"]} {all_contracts["first_name"]}'
                col_6 = all_contracts["partner"]
                col_7 = all_contracts["payment_sum"]
                col_8 = all_contracts["approval_sum"]
                col_9 = all_contracts["paid_sum"]
                col_10 = all_contracts["payment_due_date"]
                col_11 = all_contracts["payment_at"]
                col_12 = all_contracts["create_at"]
                if sort_col_1_order == 'DESC':
                    col_0 = col_0 + '+'
                    col_1 = col_1 + '+'
                    col_2 = col_2 + '+'
                    col_3 = col_3 + '+'
                    col_4 = col_4 + '+'
                    col_5 = col_5 + '+'
                    col_6 = col_6 + '+'
                else:
                    col_0 = col_0[:-1]
                    col_1 = col_1[:-1]
                    col_2 = col_2[:-1]
                    col_3 = col_3[:-1]
                    col_4 = col_4[:-1]
                    col_5 = col_5[:-1]
                    col_6 = col_6[:-1]
                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12
                ]
            elif page_name == 'contracts-payments-list':
                col_0 = ""
                col_1 = all_contracts["payment_number"]
                col_2 = all_contracts["cost_item_name"]
                col_3 = all_contracts["basis_of_payment"]
                col_4 = f'{all_contracts["contractor_name"]} {all_contracts["payment_description"]}'
                col_5 = all_contracts["object_name"]
                col_6 = f'{all_contracts["last_name"]} {all_contracts["first_name"]}'
                col_7 = all_contracts["partner"]
                col_8 = all_contracts["payment_sum"]
                col_9 = all_contracts["approval_sum"]
                col_10 = all_contracts["paid_sum"]
                col_11 = all_contracts["payment_due_date"]
                col_12 = all_contracts["payment_at"]
                col_13 = all_contracts["status_name"]

                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+'
                    col_2 = col_2 + '+'
                    col_3 = col_3 + '+'
                    col_4 = col_4 + '+'
                    col_5 = col_5 + '='
                    col_6 = col_6 + '+'
                    col_7 = col_7 + '+'
                    col_13 = col_13 + '+'
                else:
                    col_1 = col_1[:-1]
                    col_2 = col_2[:-1]
                    col_3 = col_3[:-1]
                    col_4 = col_4[:-1]
                    col_5 = col_5[:-1]
                    col_6 = col_6[:-1]
                    col_7 = col_7[:-1]
                    col_13 = col_13[:-1]

                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13
                ]

            sort_col['col_1'].append(filter_col[col_num])
            sort_col['col_id'] = all_contracts["contract_id"]

        # else:
        #     sort_col = {
        #         'col_1': [False, 0, False],  # Первая колонка
        #         'col_id': False
        #     }
        if not all_contracts:
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


@contract_app_bp.route('/get-contractMain-pagination', methods=['POST'])
@login_required
def get_contract_main_pagination():
        """Постраничная выгрузка списка СВОД"""
    # try:
        page_name = 'contracts-main'
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        col_id = 't1.object_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']

        if col_1.split('#')[0] == 'False':
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        user_id = app_login.current_user.get_id()
        user_role_id = app_login.current_user.get_role()

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
            query_value, sort_col, col_num = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        # Когда происходит горизонтальный скролл страницы и нажимается кнопка сортировки, вызывается
        # дополнительная пагинация с пустыми значениями сортировки. Отлавливаем этот случай, ничего не делаем
        if not col_1_val and not col_id_val:
            return jsonify({
                'contract': 0,
                'sort_col': sort_col,
                'status': 'success',
                'description': 'Skip pagination with empty sort data',
            })
        print(f"""
                {QUERY_MAIN}
                WHERE {where_expression}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value)
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")
        try:
            cursor.execute(
                f"""
                {QUERY_MAIN}
                WHERE {where_expression}
                ORDER BY {sort_col_1} {sort_col_1_order}, {sort_col_id} {sort_col_id_order}
                LIMIT {limit};
                """,
                query_value
            )
            all_contracts = cursor.fetchall()

        except Exception as e:
            current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': str(e),
            })

        if not len(all_contracts):
            return jsonify({
                'contract': 0,
                'sort_col': sort_col,
                'status': 'success',
                'description': 'End of table. Nothing to append',
            })

        col_0 = all_contracts[-1]["object_id"]
        col_1 = all_contracts[-1]["object_name"]
        filter_col = [
            col_0, col_1
        ]

        # Список колонок для сортировки, добавляем последние значения в столбах сортировки
        sort_col['col_1'].append(filter_col[col_num])
        sort_col['col_id'] = all_contracts[-1]["object_id"]

        for i in range(len(all_contracts)):
            all_contracts[i] = dict(all_contracts[i])

        if where_expression2:
            where_expression2 = 'WHERE ' + where_expression2
        else:
            where_expression2 = ''

        # Число заявок
        cursor.execute(
            f"""SELECT
                    COUNT(t1.object_id)
                {QUERY_MAIN_JOIN}
                {where_expression2}
            """,
            query_value
        )
        tab_rows = cursor.fetchone()[0]
        print('tab_rows', tab_rows)
        print(all_contracts)

        app_login.conn_cursor_close(cursor, conn)

        # Настройки таблицы
        setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"

        # Return the updated data as a response
        return jsonify({
            'contract': all_contracts,
            'sort_col': sort_col,
            'tab_rows': tab_rows,
            'page': page_name,
            'user_role_id': user_role_id,
            'status': 'success'
        })
    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #     return jsonify({
    #         'contract': 0,
    #         'sort_col': 0,
    #         'status': 'error',
    #         'description': str(e),
    #     })


# Главная страница раздела 'Договоры' - СВОД
@contract_app_bp.route('/contracts-main', methods=['GET'])
@login_required
def get_contracts_main():
    # try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('contracts')
        # Список объектов
        cursor.execute(
            """
            SELECT
                t1.object_id - 1 AS object_id,
                t1.object_name
            FROM objects AS t1
            ORDER BY object_name, object_id
            LIMIT 1;
            """
        )
        objects = cursor.fetchone()
        if objects:
            objects = dict(objects)
            print(objects)
        objects['object_name'] = objects['object_name'][:-1]

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link='', cur_name=0)

        # Список колонок для сортировки
        if len(objects):
            sort_col = {
                'col_1': [1, 0, objects['object_name']],  # Первая колонка - ASC
                'col_id': objects['object_id']
            }
        else:
            sort_col = {
                'col_1': [False, 1, False],  # Первая колонка
                'col_id': False
            }
        tab_rows = 1

        return render_template('contract-main.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                               header_menu=header_menu, tab_rows=tab_rows,
                               objects=objects,
                               title="Сводная таблица договоров. Свод")

    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
    #     flash(message=['Ошибка', f'contracts-main: {e}'], category='error')
    #     return render_template('page_error.html')


# 'Договоры' - Объекты
@contract_app_bp.route('/contracts_objects', methods=['GET'])
@login_required
def get_contracts_objects():
    pass


# 'Договоры' - Договоры
@contract_app_bp.route('/contracts_list', methods=['GET'])
@login_required
def get_contracts_list():
    pass


# 'Договоры' - Акты
@contract_app_bp.route('/contracts_acts_list', methods=['GET'])
@login_required
def get_contracts_acts_list():
    pass


# 'Договоры' - Платежи
@contract_app_bp.route('/contracts_payments_list', methods=['GET'])
@login_required
def get_contracts_payments_list():
    pass


def get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id, manual_type=''):
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

    if page_name == 'contracts-main':
        # столбцы фильтров
        col_0 = "t1.object_id"
        col_1 = "t1.object_name"
        list_filter_col = [
            col_0, col_1
        ]
        # столбцы сортировки
        col_0 = "t1.object_id"
        col_1 = "t1.object_name"
        list_sort_col = [
            col_0, col_1
        ]
        # типы данных столбцов
        col_0 = "t1.object_id"
        col_1 = "t1.object_name"
        list_type_col = [
            col_0, col_1
        ]
    elif page_name == 'contracts-objects':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t4.cost_item_name"
        col_2 = "t1.payment_number"
        col_3 = "t1.basis_of_payment"
        col_4 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_5 = "t6.object_name"
        col_6 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "COALESCE(t7.paid_sum, '0')"
        col_10 = "t0.approval_sum"
        col_11 = "COALESCE(t8.amount, '0')"
        col_12 = "to_char(t1.payment_due_date, 'dd.mm.yyyy')"
        col_13 = "to_char(t1.payment_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        col_14 = ""
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13, col_14
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t4.cost_item_name"
        col_2 = "t1.payment_number"
        col_3 = "t1.basis_of_payment"
        col_4 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_5 = "COALESCE(t6.object_name, '')"
        col_6 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "COALESCE(t7.paid_sum, '0')::numeric"
        col_10 = "t0.approval_sum"
        col_11 = "COALESCE(t8.amount, '0')::numeric"
        col_12 = "t1.payment_due_date"
        col_13 = "t1.payment_at"
        col_14 = ""
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13, col_14
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t4.cost_item_name"
        col_2 = "t1.payment_number"
        col_3 = "t1.basis_of_payment"
        col_4 = "t1.payment_description"
        col_5 = "t6.object_name"
        col_6 = "t5.last_name"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "t7.paid_sum"
        col_10 = "t0.approval_sum"
        col_11 = "t8.approval_sum"
        col_12 = "t1.payment_due_date"
        col_13 = "t1.payment_at"
        col_14 = ""
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13, col_14
        ]
    elif page_name == 'contracts-list':
        # столбцы фильтров
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "concat_ws(': ',  t3.contractor_name, t1.payment_description)"
        col_4 = "t6.object_name"
        col_5 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "COALESCE(t7.paid_sum, '0')"
        col_9 = "to_char(t1.payment_due_date, 'dd.mm.yyyy')"
        col_10 = "to_char(t1.payment_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10
        ]
        # столбцы сортировки
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "concat_ws(': ',  t3.contractor_name, t1.payment_description)"
        col_4 = "COALESCE(t6.object_name, '')"
        col_5 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "COALESCE(t7.paid_sum, '0')"
        col_9 = "t1.payment_due_date"
        col_10 = "t1.payment_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10
        ]
        # типы данных столбцов
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "t1.payment_description"
        col_4 = "t6.object_name"
        col_5 = "t5.last_name"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "t7.paid_sum"
        col_9 = "t1.payment_due_date"
        col_10 = "t1.payment_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10
        ]

        query_value = [
            user_id,
            user_id
        ]
    elif page_name == 'contracts-acts-list':
        # столбцы фильтров
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_4 = "t6.object_name"
        col_5 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "t0.approval_sum"
        col_9 = "t7.paid_sum"
        col_10 = "to_char(t1.payment_due_date, 'dd.mm.yyyy')"
        col_11 = "to_char(t1.payment_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        col_12 = "to_char(t8.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12
        ]
        # столбцы сортировки
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_4 = "COALESCE(t6.object_name, '')"
        col_5 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "t0.approval_sum"
        col_9 = "COALESCE(t7.paid_sum, '0')"
        col_10 = "t1.payment_due_date"
        col_11 = "t1.payment_at"
        col_12 = "t8.create_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12
        ]
        # типы данных столбцов
        col_0 = "t1.payment_number"
        col_1 = "t4.cost_item_name"
        col_2 = "t1.basis_of_payment"
        col_3 = "t1.payment_description"
        col_4 = "t6.object_name"
        col_5 = "t5.last_name"
        col_6 = "t1.partner"
        col_7 = "t1.payment_sum"
        col_8 = "t0.approval_sum"
        col_9 = "t7.paid_sum"
        col_10 = "t1.payment_due_date"
        col_11 = "t1.payment_at"
        col_12 = "t8.create_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12
        ]
        query_value = []
    elif page_name == 'contracts-payments-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t1.payment_number"
        col_2 = "t4.cost_item_name"
        col_3 = "t1.basis_of_payment"
        col_4 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_5 = "t6.object_name"
        col_6 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "t2.approval_sum"
        col_10 = "t0.paid_sum"
        col_11 = "to_char(t1.payment_due_date, 'dd.mm.yyyy')"
        col_12 = "to_char(t1.payment_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        col_13 = "t8.status_name"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t1.payment_number"
        col_2 = "t4.cost_item_name"
        col_3 = "t1.basis_of_payment"
        col_4 = "concat_ws(': ', t3.contractor_name, t1.payment_description)"
        col_5 = "COALESCE(t6.object_name, '')"
        col_6 = "concat_ws(' ', t5.last_name, t5.first_name)"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "t2.approval_sum"
        col_10 = "t0.paid_sum"
        col_11 = "t1.payment_due_date"
        col_12 = "t1.payment_at"
        col_13 = "t8.status_name"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t1.payment_number"
        col_2 = "t4.cost_item_name"
        col_3 = "t1.basis_of_payment"
        col_4 = "t1.payment_description"
        col_5 = "t6.object_name"
        col_6 = "t5.last_name"
        col_7 = "t1.partner"
        col_8 = "t1.payment_sum"
        col_9 = "t2.approval_sum"
        col_10 = "t0.paid_sum"
        col_11 = "t1.payment_due_date"
        col_12 = "t1.payment_at"
        col_13 = "t8.status_name"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13
        ]
        query_value = []

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
    return sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, query_value, sort_col, col_num


# Получаем типы данных из всех столбцов всех таблиц БД
def get_table_list():
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

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
    # Если указана страница проекта
    if link:
        # Админ и директор, юрист
        if role in (1, 4, 5):
            header_menu = [
                {'link': f'/objects/{link}', 'name': 'В проект'},
                {'link': f'/objects/{link}/contracts-list', 'name': 'Договоры'},
                {'link': f'/objects/{link}/contracts-acts-list', 'name': 'Акты'},
                {'link': f'/objects/{link}/contracts-payments-list', 'name': 'Платежи'}
            ]
        else:
            header_menu = [
                {'link': f'/objects/{link}', 'name': 'В проект'}
            ]
    else:
        # Админ и директор
        if role in (1, 4, 5):
            header_menu = [
                {'link': f'/contracts-main', 'name': 'Основное'},
                {'link': f'/contracts-objects', 'name': 'Виды работ'},
                {'link': f'/contracts-list', 'name': 'Договоры'},
                {'link': f'/contracts-acts-list', 'name': 'Календарный график'},
                {'link': f'/contracts-payments-list', 'name': 'Проект и задачи'}
            ]
        else:
            header_menu = [
                {'link': f'/', 'name': 'Главная'}
            ]
    header_menu[cur_name]['class'] = 'current'
    header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu