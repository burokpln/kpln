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
WITH_CONTRACTS = """
WITH t1 AS (
    SELECT
        t1_2.contract_id,
        t1_2.object_id,
        t1_2.contract_number,
        t1_2.date_start,
        t1_2.date_finish,
        t1_2.type_id,
        '' AS subcontract_number,
        NULL AS subdate_start,
        NULL AS subdate_finish,
        t1_2.contractor_id,
        t1_2.partner_id,
        t1_2.contract_description,
        t1_2.contract_status_id,
        t1_2.contract_cost,
        t1_2.allow,
        t1_2.create_at
    FROM subcontract AS t1_1
    LEFT JOIN (
        SELECT
            object_id,
            contract_id,
            contract_number,
            date_start,
            date_finish,
            type_id,
            contractor_id,
            partner_id,
            contract_description,
            contract_status_id,
            contract_cost,
            allow,
            create_at
        FROM contracts
    ) AS t1_2 ON t1_1.child_id = t1_2.contract_id
    WHERE t1_1.parent_id IS NULL
    
    UNION
    
    SELECT
        t2_2.contract_id,
        t2_2.object_id,
        t2_3.contract_number,
        NULL AS date_start,
        NULL AS date_finish,
        t2_2.type_id,
        t2_2.contract_number AS subcontract_number,
        t2_2.date_start AS subdate_start,
        t2_2.date_finish AS subdate_finish,
        t2_2.contractor_id,
        t2_2.partner_id,
        t2_2.contract_description,
        t2_2.contract_status_id,
        t2_2.contract_cost,
        t2_2.allow,
        t2_2.create_at
    FROM subcontract AS t2_1
    LEFT JOIN (
        SELECT
            object_id,
            contract_id,
            contract_number,
            date_start,
            date_finish,
            type_id,
            contractor_id,
            partner_id,
            contract_description,
            contract_status_id,
            contract_cost,
            allow,
            create_at
        FROM contracts
    ) AS t2_2 ON t2_1.child_id = t2_2.contract_id
    LEFT JOIN (
        SELECT
            contract_id,
            contract_number
        FROM contracts
    ) AS t2_3 ON t2_1.parent_id = t2_3.contract_id
    WHERE t2_1.parent_id IS NOT NULL
)
"""

QUERY_CONTRACTS_JOIN = """
FROM t1
LEFT JOIN (
    SELECT
        object_id,
        object_name
    FROM objects
) AS t2 ON t1.object_id = t2.object_id
LEFT JOIN (
    SELECT
        type_id,
        type_name
    FROM contract_types
) AS t3 ON t1.type_id = t3.type_id
LEFT JOIN (
    SELECT
        contractor_id,
        contractor_name,
        vat,
        contractor_value
    FROM our_companies
) AS t4 ON t1.contractor_id = t4.contractor_id
LEFT JOIN (
    SELECT
        partner_id,
        partner_name
    FROM partners
) AS t5 ON t1.partner_id = t5.partner_id
LEFT JOIN (
    SELECT
        contract_status_id,
        status_name
    FROM contract_statuses
) AS t6 ON t1.contract_status_id = t6.contract_status_id


"""

SELECT_CONTRACTS = f"""
SELECT
    t1.contract_id,
    t2.object_name,
    t3.type_id,
    t3.type_name,
    t1.contract_number,
    to_char(t1.date_start, 'dd.mm.yyyy') AS date_start_txt,
    to_char(t1.date_finish, 'dd.mm.yyyy') AS date_finish_txt,
    t1.subcontract_number,
    to_char(t1.subdate_start, 'dd.mm.yyyy') AS subdate_start_txt,
    to_char(t1.subdate_finish, 'dd.mm.yyyy') AS subdate_finish_txt,
    CASE 
        WHEN t1.type_id = 1 THEN t4.contractor_name
        WHEN t1.type_id = 2 THEN t5.partner_name
        ELSE ' '
    END AS contractor_name,
    CASE 
        WHEN t1.type_id = 1 THEN t5.partner_name
        WHEN t1.type_id = 2 THEN t4.contractor_name
        ELSE ' '
    END AS partner_name,
    t1.contract_description,
    t1.contract_status_id,
    t6.status_name,
    t1.allow,
    t4.vat,
    t1.contract_cost,
    TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')) AS contract_cost_rub,
    t1.contract_cost / t4.contractor_value AS contract_cost_without_vat,
    TRIM(BOTH ' ' FROM to_char(t1.contract_cost / t4.contractor_value, '999 999 990D99 ₽')) AS contract_cost_without_vat_rub,
    to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS create_at_txt,
    t1.create_at
"""
# ______________________________________________
QUERY_ACTS_JOIN = """
FROM acts AS t1
LEFT JOIN contract_statuses 
AS t2 ON t1.contract_status_id = t2.contract_status_id
LEFT JOIN (
    SELECT
        contract_id,
        contract_number,
        object_id,
        contractor_id,
        allow
    FROM contracts
) AS t3 ON t1.contract_id = t3.contract_id
LEFT JOIN (
    SELECT
        object_id,
        object_name
    FROM objects
) AS t4 ON t3.object_id = t4.object_id
LEFT JOIN (
    SELECT
        act_id,
        COUNT(tow_id) AS count_tow
    FROM tows_act
    GROUP BY act_id
) AS t5 ON t1.act_id = t5.act_id
LEFT JOIN (
    SELECT
        contractor_id,
        vat,
        contractor_value
    FROM our_companies
) AS t6 ON t3.contractor_id = t6.contractor_id
LEFT JOIN (
    SELECT
        type_id,
        type_name
    FROM contract_types
) AS t7 ON t1.type_id = t7.type_id

"""

SELECT_ACTS = f"""
SELECT
    t1.act_id,
    t4.object_name,
    t7.type_name,
    t3.contract_number,
    t1.act_number,
    to_char(t1.act_date, 'dd.mm.yyyy') AS act_date_txt,
    t2.status_name,
    t6.vat,
    t1.act_cost,
    TRIM(BOTH ' ' FROM to_char(t1.act_cost, '999 999 990D99 ₽')) AS act_cost_rub,
    t1.act_cost / t6.contractor_value AS act_cost_without_vat,
    TRIM(BOTH ' ' FROM to_char(t1.act_cost / t6.contractor_value, '999 999 990D99 ₽')) AS act_cost_without_vat_rub,
    t5.count_tow,
    t6.contractor_value,
    t3.allow,
    t1.create_at,
    to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS create_at_txt
"""
# ______________________________________________
QUERY_PAYS_JOIN = """
FROM payments AS t1

LEFT JOIN (
    SELECT
        contract_id,
        contract_number,
        object_id,
        contractor_id,
        allow
    FROM contracts
) AS t3 ON t1.contract_id = t3.contract_id
LEFT JOIN (
    SELECT
        object_id,
        object_name
    FROM objects
) AS t4 ON t3.object_id = t4.object_id

LEFT JOIN (
    SELECT
        contractor_id,
        vat,
        contractor_value
    FROM our_companies
) AS t6 ON t3.contractor_id = t6.contractor_id
LEFT JOIN (
    SELECT
        type_id,
        type_name
    FROM contract_types
) AS t7 ON t1.type_id = t7.type_id
LEFT JOIN (
    SELECT
        payment_type_id,
        payment_type_name
    FROM payment_types
) AS t8 ON t1.payment_type_id = t8.payment_type_id
LEFT JOIN (
    SELECT
        act_id,
        act_number
    FROM acts
) AS t9 ON t1.act_id = t9.act_id
"""

QUERY_PAYS = f"""
SELECT
    t1.payment_id,
    t1.act_id,
    t4.object_name,
    t7.type_name,
    t3.contract_number,
    t8.payment_type_name,
    t9.act_number,
    t1.payment_number,
    to_char(t1.payment_date, 'dd.mm.yyyy') AS payment_date_txt,
    t1.payment_date,
    t6.vat,
    t1.payment_cost,
    TRIM(BOTH ' ' FROM to_char(t1.payment_cost, '999 999 990D99 ₽')) AS payment_cost_rub,
    t1.payment_cost / t6.contractor_value AS payment_cost_without_vat,
    TRIM(BOTH ' ' FROM to_char(t1.payment_cost / t6.contractor_value, '999 999 990D99 ₽')) AS payment_cost_without_vat_rub,

    t6.contractor_value,
    t3.allow,
    t1.create_at,
    to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS create_at_txt
{QUERY_PAYS_JOIN}
"""


# Define a function to retrieve nonce within the application context
def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@contract_app_bp.before_request
def before_request():
    app_login.before_request()


@contract_app_bp.route('/get-first-contract', methods=['POST'])
@login_required
def get_first_contract():
    """Постраничная выгрузка списка несогласованных платежей"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = request.get_json()['page_url']
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            if page_name == 'contracts-main':
                col_id = 't1.object_id'
            elif page_name == 'contracts-list':
                col_id = 't1.contract_id'
            elif page_name == 'contracts-objects':
                col_id = 't1.object_id'
            elif page_name == 'contracts-acts-list':
                col_id = 't1.act_id'
            elif page_name == 'contracts-payments-list':
                col_id = 't1.payment_id'
            else:
                col_id = 't1.object_id'

            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'sort_col': None,
                    'status': 'error',
                    'description': 'Нет данных',
                })
            print("_" * 30)
            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    if page_name == 'contracts-list':
                        where_object_id = f"and t1.object_id = {object_id}"
                    elif page_name == 'contracts-acts-list':
                        where_object_id = f"and t3.object_id = {object_id}"
                    elif page_name == 'contracts-payments-list':
                        where_object_id = f"and t3.object_id = {object_id}"

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
                query_value, sort_col, col_num, sort_sign = \
                get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

            if sort_col_1_order == 'DESC':
                order = '+'
                sort_sign = ''
            else:
                order = '-'
                sort_sign = '-'

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
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                    query_value
                )
            elif page_name == 'contracts-objects':
                cursor.execute(
                    f"""
                    SELECT
                        object_id {order} 1 AS object_id,
                        object_name
                    {QUERY_MAIN_JOIN}
                    WHERE {where_expression2}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                    query_value
                )
            elif page_name == 'contracts-list':
                cursor.execute(
                    f"""
                    {WITH_CONTRACTS}
                    SELECT
                        t1.contract_id {order} 1 AS contract_id,
                        t2.object_name,
                        t3.type_name,
                        t1.contract_number,
                        (COALESCE(t1.date_start {order} interval '1 day', '{sort_sign}infinity'::date))::text AS date_start,
                        (COALESCE(t1.date_finish {order} interval '1 day', '{sort_sign}infinity'::date))::text AS date_finish,
                        t1.subcontract_number,
                        (COALESCE(t1.subdate_start {order} interval '1 day', '{sort_sign}infinity'::date))::text AS subdate_start,
                        (COALESCE(t1.subdate_finish {order} interval '1 day', '{sort_sign}infinity'::date))::text AS subdate_finish,
                        CASE 
                            WHEN t1.type_id = 1 THEN t4.contractor_name
                            WHEN t1.type_id = 2 THEN t5.partner_name
                            ELSE ' '
                        END AS contractor_name,
                        CASE 
                            WHEN t1.type_id = 1 THEN t5.partner_name
                            WHEN t1.type_id = 2 THEN t4.contractor_name
                            ELSE ' '
                        END AS partner_name,
                        t1.contract_description,
                        t6.status_name,
                        t1.allow::text AS allow,
                        t4.vat::text AS vat,
                        (t1.contract_cost / t4.contractor_value) {order} 0.01 AS contract_cost_without_vat,
                        (t1.create_at {order} interval '1 microseconds')::timestamp without time zone::text AS create_at
                    {QUERY_CONTRACTS_JOIN}
                    WHERE {where_expression2} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                    query_value
                )
            elif page_name == 'contracts-acts-list':
                cursor.execute(
                    f"""
                    SELECT
                        t1.act_id {order} 1 AS act_id,
                        t4.object_name,
                        t7.type_name,
                        t3.contract_number,
                        t1.act_number,
                        (COALESCE(t1.act_date {order} interval '1 day', '{sort_sign}infinity'::date))::text AS act_date,
                        t2.status_name,
                        t6.vat::text AS vat,
                        (t1.act_cost / t6.contractor_value) {order} 0.01 AS act_cost_without_vat,
                        t5.count_tow {order} 1 AS count_tow,
                        t3.allow::text AS allow,
                        (t1.create_at {order} interval '1 microseconds')::timestamp without time zone::text AS create_at
                    {QUERY_ACTS_JOIN}
                    WHERE {where_expression2} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                    query_value
                )
            elif page_name == 'contracts-payments-list':
                cursor.execute(
                    f"""
                    SELECT
                        t1.payment_id {order} 1 AS payment_id,
                        t1.act_id {order} 1 AS act_id,
                        t4.object_name,
                        t7.type_name,
                        t3.contract_number,
                        t8.payment_type_name,
                        t9.act_number,
                        t1.payment_number,
                        (COALESCE(t1.payment_date, NULL::date) {order} interval '1 day')::text AS payment_date,
                        t6.vat::text AS vat,
                        (t1.payment_cost / t6.contractor_value) {order} 0.01 AS payment_cost_without_vat,
                        t3.allow::text AS allow,
                        (t1.create_at {order} interval '1 microseconds')::timestamp without time zone::text AS create_at
                    {QUERY_PAYS_JOIN}
                    WHERE {where_expression2} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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
                    col_0 = all_contracts["object_id"]
                    col_1 = all_contracts["object_name"]
                    if sort_col_1_order == 'DESC':
                        col_1 = col_1 + '+'
                    else:
                        col_1 = col_1[:-1]
                    filter_col = [
                        col_0, col_1
                    ]
                elif page_name == 'contracts-list':
                    col_0 = ""
                    col_1 = all_contracts["object_name"]
                    col_2 = all_contracts["type_name"]
                    col_3 = all_contracts["contract_number"]
                    col_4 = all_contracts["date_start"]
                    col_5 = all_contracts["date_finish"]
                    col_6 = all_contracts["subcontract_number"]
                    col_7 = all_contracts["subdate_start"]
                    col_8 = all_contracts["subdate_finish"]
                    col_9 = all_contracts["contractor_name"]
                    col_10 = all_contracts["partner_name"]
                    col_11 = all_contracts["contract_description"]
                    col_12 = all_contracts["status_name"]
                    col_13 = all_contracts["allow"]
                    col_14 = all_contracts["vat"]
                    col_15 = all_contracts["contract_cost_without_vat"]
                    col_16 = all_contracts["create_at"]
                    if sort_col_1_order == 'DESC':
                        col_1 = col_1 + '+'
                        col_2 = col_2 + '+'
                        col_3 = col_3 + '+'
                        col_6 = col_6 + '+'
                        col_9 = col_9 + '+'
                        col_10 = col_10 + '+'
                        col_11 = col_11 + '+'
                        col_12 = col_12 + '+'
                        col_13 = col_13 + '+'
                        col_14 = col_14 + '+'
                    else:
                        col_1 = col_1[:-1]
                        col_2 = col_2[:-1]
                        col_3 = col_3[:-1]
                        col_6 = col_6[:-1]
                        col_9 = col_9[:-1]
                        col_10 = col_10[:-1]
                        col_11 = col_11[:-1]
                        col_12 = col_12[:-1]
                        col_13 = col_13[:-1]
                        col_14 = col_14[:-1]

                    filter_col = [
                        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12,
                        col_13, col_14, col_15, col_16
                    ]
                elif page_name == 'contracts-acts-list':
                    col_0 = ""
                    col_1 = all_contracts["object_name"]
                    col_2 = all_contracts["type_name"]
                    col_3 = all_contracts["contract_number"]
                    col_4 = all_contracts["act_number"]
                    col_5 = all_contracts["act_date"]
                    col_6 = all_contracts["status_name"]
                    col_7 = all_contracts["vat"]
                    col_8 = all_contracts["act_cost_without_vat"]
                    col_9 = all_contracts["count_tow"]
                    col_10 = all_contracts["allow"]
                    col_11 = all_contracts["create_at"]
                    if sort_col_1_order == 'DESC':
                        col_1 = col_1 + '+'
                        col_2 = col_2 + '+'
                        col_3 = col_3 + '+'
                        col_4 = col_4 + '+'
                        col_6 = col_6 + '+'
                        col_7 = col_7 + '+'
                        col_10 = col_10 + '+'
                    else:
                        col_1 = col_1[:-1]
                        col_2 = col_2[:-1]
                        col_3 = col_3[:-1]
                        col_4 = col_4[:-1]
                        col_6 = col_6[:-1]
                        col_7 = col_7[:-1]
                        col_10 = col_10[:-1]
                    filter_col = [
                        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
                    ]
                elif page_name == 'contracts-payments-list':
                    col_0 = ""
                    col_1 = all_contracts["object_name"]
                    col_2 = all_contracts["type_name"]
                    col_3 = all_contracts["contract_number"]
                    col_4 = all_contracts["payment_type_name"]
                    col_5 = all_contracts["act_number"]
                    col_6 = all_contracts["payment_number"]
                    col_7 = all_contracts["payment_date"]
                    col_8 = all_contracts["vat"]
                    col_9 = all_contracts["payment_cost_without_vat"]
                    col_10 = all_contracts["allow"]
                    col_11 = all_contracts["create_at"]
                    if sort_col_1_order == 'DESC':
                        col_1 = col_1 + '+'
                        col_2 = col_2 + '+'
                        col_3 = col_3 + '+'
                        col_4 = col_4 + '+'
                        col_5 = col_5 + '+'
                        col_6 = col_6 + '+'
                        col_8 = col_8 + '+'
                        col_10 = col_10 + '+'
                    else:
                        col_1 = col_1[:-1]
                        col_2 = col_2[:-1]
                        col_3 = col_3[:-1]
                        col_4 = col_4[:-1]
                        col_5 = col_5[:-1]
                        col_6 = col_6[:-1]
                        col_8 = col_8[:-1]
                        col_10 = col_10[:-1]
                    filter_col = [
                        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
                    ]

                if page_name in ('contracts-main', 'contracts-objects'):
                    sort_col['col_1'].append(filter_col[col_num])
                    sort_col['col_id'] = all_contracts["object_id"]
                elif page_name == 'contracts-list':
                    sort_col['col_1'].append(filter_col[col_num])
                    sort_col['col_id'] = all_contracts["contract_id"]
                elif page_name == 'contracts-acts-list':
                    sort_col['col_1'].append(filter_col[col_num])
                    sort_col['col_id'] = all_contracts["act_id"]
                elif page_name == 'contracts-payments-list':
                    sort_col['col_1'].append(filter_col[col_num])
                    sort_col['col_id'] = all_contracts["payment_id"]

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
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contracts-main'
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            col_id = 't1.object_id'
            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            user_id = app_login.current_user.get_id()

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
                query_value, sort_col, col_num, sort_sign = \
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
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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
            setting_users = {"---": None}

            # Return the updated data as a response
            return jsonify({
                'contract': all_contracts,
                'sort_col': sort_col,
                'tab_rows': tab_rows,
                'page': page_name,
                'setting_users': setting_users,
                'user_role_id': role,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


# Главная страница раздела 'Договоры' - СВОД
@contract_app_bp.route('/contracts-main', methods=['GET'])
@login_required
def get_contracts_main(link=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:

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
            header_menu = get_header_menu(role, link=link, cur_name=0)

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

            # Настройки таблицы
            setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"
            setting_users = {"---": None}
            tab_rows = 1

            return render_template('contract-main.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                                   header_menu=header_menu, tab_rows=tab_rows, objects=objects, nonce=get_nonce(),
                                   setting_users=setting_users, title="Сводная таблица договоров. Свод")
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contracts-main: {e}'], category='error')
        return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/get-contractObj-pagination', methods=['POST'])
@login_required
def get_contract_objects_pagination():
    """Постраничная выгрузка списка Объекты"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contracts-main'
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            col_id = 't1.object_id'
            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'contract': 0,
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            user_id = app_login.current_user.get_id()

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
                query_value, sort_col, col_num, sort_sign = \
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
                    {QUERY_OBJ}
                    WHERE {where_expression}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                    query_value)
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")
            try:
                cursor.execute(
                    f"""
                    {QUERY_OBJ}
                    WHERE {where_expression}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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
                    {QUERY_OBJ_JOIN}
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
            setting_users = {"---": None}

            # Return the updated data as a response
            return jsonify({
                'contract': all_contracts,
                'sort_col': sort_col,
                'tab_rows': tab_rows,
                'page': page_name,
                'setting_users': setting_users,
                'user_role_id': role,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


# 'Договоры' - Объекты
@contract_app_bp.route('/contracts-objects', methods=['GET'])
@login_required
def get_contracts_objects(link=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
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
            header_menu = get_header_menu(role, link=link, cur_name=1)

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
            # Настройки таблицы
            setting_users = "get_tab_settings(user_id=user_id, list_name=request.path[1:])"
            setting_users = {"---": None}
            tab_rows = 1

            return render_template('contract-main.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                                   header_menu=header_menu, tab_rows=tab_rows, setting_users=setting_users,
                                   objects=objects, nonce=get_nonce(), title="Сводная таблица договоров. Объекты")
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-main: {e}'], category='error')
        return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/get-contractList-pagination', methods=['POST'])
@login_required
def get_contract_list_pagination():
    """Постраничная выгрузка списка Договоров"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contracts-list'
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            col_id = 't1.contract_id'
            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            print('/get-contractList-pagination', col_id_val)

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'contract': 0,
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            user_id = app_login.current_user.get_id()

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
                query_value, sort_col, col_num, sort_sign = \
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

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")
            try:
                cursor.execute(
                    f"""
                    {WITH_CONTRACTS}
                    {SELECT_CONTRACTS},
                    (COALESCE(t1.date_start, '{sort_sign}infinity'::date))::text AS date_start,
                    (COALESCE(t1.date_finish, '{sort_sign}infinity'::date))::text AS date_finish,
                    (COALESCE(t1.subdate_start, '{sort_sign}infinity'::date))::text AS subdate_start,
                    (COALESCE(t1.subdate_finish, '{sort_sign}infinity'::date))::text AS subdate_finish
                        
                    {QUERY_CONTRACTS_JOIN}
                    WHERE {where_expression}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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

            col_0 = ""
            col_1 = all_contracts[-1]["object_name"]
            col_2 = all_contracts[-1]["type_name"]
            col_3 = all_contracts[-1]["contract_number"]
            col_4 = all_contracts[-1]["date_start"]
            col_5 = all_contracts[-1]["date_finish"]
            col_6 = all_contracts[-1]["subcontract_number"]
            col_7 = all_contracts[-1]["subdate_start"]
            col_8 = all_contracts[-1]["subdate_finish"]
            col_9 = all_contracts[-1]["contractor_name"]
            col_10 = all_contracts[-1]["partner_name"]
            col_11 = all_contracts[-1]["contract_description"]
            col_12 = all_contracts[-1]["status_name"]
            col_13 = all_contracts[-1]["allow"]
            col_14 = all_contracts[-1]["vat"]
            col_15 = all_contracts[-1]["contract_cost_without_vat"]
            col_16 = all_contracts[-1]["create_at"]
            filter_col = [
                col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
                col_14, col_15, col_16
            ]

            # Список колонок для сортировки, добавляем последние значения в столбах сортировки
            sort_col['col_1'].append(filter_col[col_num])
            sort_col['col_id'] = all_contracts[-1]["contract_id"]

            for i in range(len(all_contracts)):
                all_contracts[i] = dict(all_contracts[i])

            if where_expression2:
                where_expression2 = 'WHERE ' + where_expression2
            else:
                where_expression2 = ''

            # Число заявок
            cursor.execute(
                f"""
                    {WITH_CONTRACTS}
                    SELECT
                        COUNT(t1.contract_id)
                    {QUERY_CONTRACTS_JOIN}
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
            setting_users = {"---": None}

            # Return the updated data as a response
            return jsonify({
                'contract': all_contracts,
                'sort_col': sort_col,
                'tab_rows': tab_rows,
                'page': page_name,
                'setting_users': setting_users,
                'user_role_id': role,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


# 'Договоры' - Договоры
@contract_app_bp.route('/contracts-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contracts-list', methods=['GET'])
@login_required
def get_contracts_list(link=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            where_contracts_list = ''
            cur_name = 2  # Порядковый номер пункта в основном меню (header_menu)
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    cur_name = 1
                    where_contracts_list = f"WHERE t1.object_id = {object_id}"


            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('contracts')
            # Список договоров
            cursor.execute(
                f"""
                {WITH_CONTRACTS}
                SELECT
                    t1.contract_id - 1 AS contract_id,
                    (t1.create_at - interval '1 microseconds')::timestamp without time zone::text AS create_at
                FROM t1
                {where_contracts_list}
                ORDER BY create_at, contract_id
                LIMIT 1;
                """
            )
            objects = cursor.fetchone()
            if objects:
                objects = dict(objects)
                print(objects)
            # objects['contract_number'] = objects['contract_number'][:-1]

            app_login.conn_cursor_close(cursor, conn)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # Список основного меню
            header_menu = get_header_menu(role, link=link, cur_name=cur_name)

            # Список колонок для сортировки
            if objects:
                sort_col = {
                    'col_1': [1, 16, objects['create_at']],  # Первая колонка - ASC
                    'col_id': objects['contract_id']
                }
            else:
                sort_col = {
                    'col_1': [False, 1, False],  # Первая колонка
                    'col_id': False
                }
            # Настройки таблицы
            setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"
            setting_users = {"---": None}
            tab_rows = 1

            # Список колонок, которые скрываются для пользователя всегда
            hidden_col = []
            if not link:
                # Если проходим на странице через объект, то скрываем столбец Объект
                hidden_col.append(1)

            return render_template('contract-list.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                                   header_menu=header_menu, tab_rows=tab_rows, setting_users=setting_users,
                                   objects=objects, hidden_col=hidden_col, nonce=get_nonce(),
                                   title="Сводная таблица договоров. Договоры")
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-list: {e}'], category='error')
        return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/get-actList-pagination', methods=['POST'])
@login_required
def get_act_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contracts-acts-list'
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            col_id = 't1.act_id'
            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'contract': 0,
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    where_object_id = f"and t3.object_id = {object_id}"

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
                query_value, sort_col, col_num, sort_sign = \
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

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")
            try:
                cursor.execute(
                    f"""
                    {SELECT_ACTS},
                    (COALESCE(t1.act_date, '{sort_sign}infinity'::date))::text AS act_date
                    {QUERY_ACTS_JOIN}
                    WHERE {where_expression} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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

            col_0 = ""
            col_1 = all_contracts[-1]["object_name"]
            col_2 = all_contracts[-1]["type_name"]
            col_3 = all_contracts[-1]["contract_number"]
            col_4 = all_contracts[-1]["act_number"]
            col_5 = all_contracts[-1]["act_date"]
            col_6 = all_contracts[-1]["status_name"]
            col_7 = all_contracts[-1]["vat"]
            col_8 = all_contracts[-1]["act_cost_without_vat"]
            col_9 = all_contracts[-1]["count_tow"]
            col_10 = all_contracts[-1]["allow"]
            col_11 = all_contracts[-1]["create_at"]
            filter_col = [
                col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
            ]

            # Список колонок для сортировки, добавляем последние значения в столбах сортировки
            sort_col['col_1'].append(filter_col[col_num])
            sort_col['col_id'] = all_contracts[-1]["act_id"]

            for i in range(len(all_contracts)):
                all_contracts[i] = dict(all_contracts[i])

            if where_expression2:
                where_expression2 = f"WHERE {where_expression2} {where_object_id}"
            else:
                where_expression2 = ''
                if where_object_id:
                    where_expression2 = f"WHERE true {where_object_id}"

            # Число заявок
            cursor.execute(
                f"""
                    SELECT
                        COUNT(t1.act_id)
                    {QUERY_ACTS_JOIN}
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
            setting_users = {"---": None}

            # Return the updated data as a response
            return jsonify({
                'contract': all_contracts,
                'sort_col': sort_col,
                'tab_rows': tab_rows,
                'page': page_name,
                'setting_users': setting_users,
                'user_role_id': role,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


# 'Договоры' - Акты
@contract_app_bp.route('/contracts-acts-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contracts-acts-list', methods=['GET'])
@login_required
def get_contracts_acts_list(link=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        role = app_login.current_user.get_role()

        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            # Если зашли из проекта, то фильтруем данные с учётом объекта
            where_contracts_list = ''
            cur_name = 3  # Порядковый номер пункта в основном меню (header_menu)
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    cur_name = 2
                    where_contracts_list = f"""
                    LEFT JOIN (
                        SELECT
                            contract_id,
                            object_id
                        FROM contracts
                    ) AS t3 ON t1.contract_id = t3.contract_id
                    WHERE t3.object_id = {object_id}"""


            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('contracts')
            # Список Актов
            cursor.execute(
                f"""
                SELECT
                    t1.act_id - 1 AS act_id,
                    (t1.create_at - interval '1 microseconds')::timestamp without time zone::text AS create_at
                FROM acts as t1
                {where_contracts_list}
                ORDER BY t1.create_at, t1.act_id
                LIMIT 1;
                """
            )
            acts = cursor.fetchone()
            if acts:
                acts = dict(acts)
                print(acts)

            app_login.conn_cursor_close(cursor, conn)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # Список основного меню
            header_menu = get_header_menu(role, link=link, cur_name=cur_name)

            # Список колонок для сортировки
            if acts:
                sort_col = {
                    'col_1': [1, 11, acts['create_at']],  # Первая колонка - ASC
                    'col_id': acts['act_id']
                }
            else:
                sort_col = {
                    'col_1': [False, 1, False],  # Первая колонка
                    'col_id': False
                }
            # Настройки таблицы
            setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"
            setting_users = {"---": None}
            tab_rows = 1

            # Список колонок, которые скрываются для пользователя всегда
            hidden_col = []
            if not link:
                # Если проходим на странице через объект, то скрываем столбец Объект
                hidden_col.append(1)

            return render_template('contracts-acts-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                                   sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                                   setting_users=setting_users, nonce=get_nonce(),
                                   title="Сводная таблица договоров. Акты")
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contracts-acts-list: {e}'], category='error')
        return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/get-contractPayList-pagination', methods=['POST'])
@login_required
def get_contract_pay_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contracts-payments-list'
            limit = request.get_json()['limit']
            col_1 = request.get_json()['sort_col_1']
            col_1_val = request.get_json()['sort_col_1_val']
            col_id = 't1.payment_id'
            col_id_val = request.get_json()['sort_col_id_val']
            filter_vals_list = request.get_json()['filterValsList']

            if col_1.split('#')[0] == 'False' or not col_1:
                return jsonify({
                    'contract': 0,
                    'sort_col': 0,
                    'status': 'error',
                    'description': 'Нет данных',
                })

            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    where_object_id = f"and t3.object_id = {object_id}"

            sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2,\
                query_value, sort_col, col_num, sort_sign = \
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

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")
            try:
                cursor.execute(
                    f"""
                    {QUERY_PAYS}
                    WHERE {where_expression} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
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

            col_0 = ""
            col_1 = all_contracts[-1]["object_name"]
            col_2 = all_contracts[-1]["type_name"]
            col_3 = all_contracts[-1]["contract_number"]
            col_4 = all_contracts[-1]["payment_type_name"]
            col_5 = all_contracts[-1]["act_number"]
            col_6 = all_contracts[-1]["payment_number"]
            col_7 = all_contracts[-1]["payment_date"]
            col_8 = all_contracts[-1]["vat"]
            col_9 = all_contracts[-1]["payment_cost_without_vat"]
            col_10 = all_contracts[-1]["allow"]
            col_11 = all_contracts[-1]["create_at"]
            filter_col = [
                col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
            ]

            # Список колонок для сортировки, добавляем последние значения в столбах сортировки
            sort_col['col_1'].append(filter_col[col_num])
            sort_col['col_id'] = all_contracts[-1]["payment_id"]

            for i in range(len(all_contracts)):
                all_contracts[i] = dict(all_contracts[i])

            if where_expression2:
                where_expression2 = f"WHERE {where_expression2} {where_object_id}"
            else:
                where_expression2 = ''
                if where_object_id:
                    where_expression2 = f"WHERE true {where_object_id}"

            # Число заявок
            cursor.execute(
                f"""
                    SELECT
                        COUNT(t1.payment_id)
                    {QUERY_PAYS_JOIN}
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
            setting_users = {"---": None}

            # Return the updated data as a response
            return jsonify({
                'contract': all_contracts,
                'sort_col': sort_col,
                'tab_rows': tab_rows,
                'page': page_name,
                'setting_users': setting_users,
                'user_role_id': role,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


@contract_app_bp.route('/contracts-payments-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contracts-payments-list', methods=['GET'])
@login_required
def get_contracts_payments_list(link=''):
    try:
        global hlink_menu, hlink_profile

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            where_contracts_list = ''
            cur_name = 4  # Порядковый номер пункта в основном меню (header_menu)
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    cur_name = 3
                    where_contracts_list = f"""
                                LEFT JOIN (
                                    SELECT
                                        contract_id,
                                        object_id
                                    FROM contracts
                                ) AS t3 ON t1.contract_id = t3.contract_id
                                WHERE t3.object_id = {object_id}"""

            user_id = app_login.current_user.get_id()

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('contracts')
            # Список Актов
            cursor.execute(
                f"""
                    SELECT
                        t1.payment_id - 1 AS payment_id,
                        (t1.create_at - interval '1 microseconds')::timestamp without time zone::text AS create_at
                    FROM payments as t1
                    {where_contracts_list}
                    ORDER BY t1.create_at, t1.payment_id
                    LIMIT 1;
                    """
            )
            acts = cursor.fetchone()
            if acts:
                acts = dict(acts)
                print(acts)

            app_login.conn_cursor_close(cursor, conn)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # Список основного меню
            header_menu = get_header_menu(role, link=link, cur_name=cur_name)

            # Список колонок для сортировки
            if acts:
                sort_col = {
                    'col_1': [1, 11, acts['create_at']],  # Первая колонка - ASC
                    'col_id': acts['payment_id']
                }
            else:
                sort_col = {
                    'col_1': [False, 1, False],  # Первая колонка
                    'col_id': False
                }
            # Настройки таблицы
            setting_users = "get_tab_settings(user_id=user_id, list_name=page_name)"
            setting_users = {"---": None}
            tab_rows = 1

            # Список колонок, которые скрываются для пользователя всегда
            hidden_col = []
            if not link:
                # Если проходим на странице через объект, то скрываем столбец Объект
                hidden_col.append(1)

            return render_template('contracts-payments-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                                   sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                                   setting_users=setting_users, nonce=get_nonce(),
                                   title="Сводная таблица договоров. Платежи")
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contracts-payments-list: {e}'], category='error')
        return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/contracts-list/card/<int:contract_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contracts-list/card/<int:contract_id>', methods=['GET'])
@login_required
def get_card_contracts_contract(contract_id, link=''):
    # try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            contract_id = contract_id
            link = link

            user_id = app_login.current_user.get_id()
            if role not in (1, 7):
                return jsonify({
                    'employee': 0,
                    'status': 'error',
                    'description': 'Доступ запрещен',
                })
            else:

                # Connect to the database
                conn, cursor = app_login.conn_cursor_init_dict("contracts")

                # Находим object_id, по нему находим список tow
                cursor.execute(
                    """
                    SELECT
                        object_id
                    FROM contracts
                    WHERE contract_id = %s
                    LIMIT 1; """,
                    [contract_id]
                )
                object_id = cursor.fetchone()[0]

                print('     object_id', object_id)

                # Находим список tow (contract_tow_list)
                cursor.execute(
                    """
                    SELECT
                        tow_id,
                        tow_cost,
                        tow_cost_percent
                    FROM tows_contract
                    WHERE contract_id = %s;""",
                    [contract_id]
                )
                ct = cursor.fetchall()

                # Информация о договоре
                cursor.execute(
                    """
                    SELECT
                        t1.object_id,
                        t2.object_name,
                        t1.contract_id,
                        t1.contract_number,
                        t1.date_start,
                        COALESCE(to_char(t1.date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
                        t1.date_finish,
                        COALESCE(to_char(t1.date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,
                        t1.type_id,
                        t1.contractor_id,
                        t1.partner_id,
                        t1.contract_description,
                        t1.contract_status_id,
                        COALESCE(t1.fot_percent::text, '') AS fot_percent,
                        t1.contract_cost,
                        COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')), '') AS contract_cost_rub,
                        t1.allow,
                        t1.fot_percent,
                        COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost * t1.fot_percent / 100, '999 999 990D99 ₽')), '') AS contract_fot_cost_rub,
                        t1.create_at,
                        t4.contractor_value,
                        t4.vat,
                        0 AS undistributed_cost,
                        to_char(0, '999 999 990D99 ₽') AS undistributed_cost_rub,
                        t3.type_name
                    FROM contracts AS t1
                    LEFT JOIN (
                        SELECT
                            object_id,
                            object_name
                        FROM objects
                    ) AS t2 ON t1.object_id = t2.object_id
                    LEFT JOIN (
                        SELECT
                            type_id,
                            type_name
                        FROM contract_types
                    ) AS t3 ON t1.type_id = t3.type_id
                    LEFT JOIN (
                        SELECT
                            contractor_id,
                            vat,
                            contractor_value
                        FROM our_companies
                    ) AS t4 ON t1.contractor_id = t4.contractor_id
                    WHERE contract_id = %s;
                    """,
                    [contract_id]
                )

                contract_info = cursor.fetchone()
                contract_number = contract_info['contract_number']

                print('                       contract_info')
                if contract_info:
                    contract_info = dict(contract_info)
                pprint(contract_info)

                # Общая стоимость субподрядных договоров объекта
                cursor.execute(
                    """
                    SELECT 
                        SUM(tow_cost)
                    FROM tows_contract
                    WHERE 
                        contract_id IN
                            (SELECT
                                contract_id
                            FROM contracts
                            WHERE object_id = %s)
                        AND
                        tow_id IN 
                            (SELECT
                                tow_id
                            FROM types_of_work
                            WHERE dept_id = 1); 
                    """,
                    [object_id]
                )
                subcontractors_cost = cursor.fetchone()[0]

                # Находим project_id по object_id
                project_id = get_proj_id(object_id=object_id)['project_id']

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
                            t0.tow_id,
                            t0.child_path,
                            t0.tow_name,
                            COALESCE(t0.dept_id, null) AS dept_id,
                            COALESCE(t1.dept_short_name, '') AS dept_short_name,
                            t0.time_tracking,
                            t0.depth-1 AS depth,
                            t0.lvl,
                            CASE 
                                WHEN t0.dept_id = 1 THEN NULL
                                ELSE COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100)
                            END AS tow_cost,
                            CASE 
                                WHEN t0.dept_id = 1 THEN ''
                                ELSE COALESCE(TRIM(BOTH ' ' FROM to_char(
                                    COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100)
                                , '999 999 990D99 ₽')), '')
                            END AS tow_cost_rub,
                            CASE 
                                WHEN t2.tow_cost IS NOT NULL THEN 'manual'
                                ELSE 'calc'
                            END AS tow_cost_status,
                            CASE 
                                WHEN t0.dept_id != 1 THEN NULL
                                ELSE COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100)
                            END AS tow_subcontractor_cost,
                            CASE 
                                WHEN t0.dept_id = 1 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(
                                    COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100)
                                , '999 999 990D99 ₽')), '')
                                ELSE ''
                            END AS tow_subcontractor_cost_rub,
                            t2.tow_cost_percent,
                            COALESCE(t2.tow_cost_percent::text, '') AS tow_cost_percent_txt,
                            CASE 
                                WHEN t2.tow_cost_percent IS NOT NULL THEN 'manual'
                                ELSE 'calc'
                            END AS tow_cost_percent_status,
                            CASE 
                                WHEN t0.dept_id = 1 THEN NULL
                                ELSE COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
                            END AS tow_fot_cost,
                            CASE 
                                WHEN t0.dept_id = 1 THEN ''
                                ELSE COALESCE(TRIM(BOTH ' ' FROM to_char(
                                    COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
                                , '999 999 990D99 ₽')), '')
                            END AS tow_fot_cost_rub,
                            CASE 
                                WHEN t0.dept_id = 1 AND t3.type_id != 2 THEN 'disabled'
                                WHEN t0.dept_id != 1 AND t3.type_id = 2 THEN 'disabled'
                                ELSE ''
                            END AS disabled_row,
                            CASE 
                                WHEN t3.type_id = 1 THEN 'disabled'
                                ELSE ''
                            END AS disabled_type1,
                            CASE 
                                WHEN t3.type_id = 2 THEN 'disabled'
                                ELSE ''
                            END AS disabled_type2,
                            COALESCE(t4.tow_cnt_dept_no_matter, 0) AS tow_cnt,
                            t5.summary_subcontractor_cost,
                            COALESCE(TRIM(BOTH ' ' FROM to_char(t5.summary_subcontractor_cost, '999 999 990D99 ₽')), '') 
                                AS summary_subcontractor_cost_rub
                            
                        FROM rel_rec AS t0
                        LEFT JOIN (
                            SELECT
                                dept_id,
                                dept_short_name
                            FROM list_dept
                        ) AS t1 ON t0.dept_id = t1.dept_id
                        LEFT JOIN (
                            SELECT
                                tow_id,
                                tow_cost,
                                tow_cost_percent
                            FROM tows_contract
                            WHERE contract_id = %s
                        ) AS t2 ON t0.tow_id = t2.tow_id
                        LEFT JOIN (
                            SELECT
                                fot_percent / 100 AS fot_percent,
                                contract_cost,
                                type_id
                            FROM contracts
                            WHERE contract_id = %s
                        ) AS t3 ON true
                        LEFT JOIN (
                            SELECT
                                parent_id,
                                COUNT(*) AS tow_cnt_dept_no_matter,
                                COUNT(dept_id) AS tow_cnt
                            FROM types_of_work
                            GROUP BY parent_id
                        ) AS t4 ON t0.tow_id = t4.parent_id
                        LEFT JOIN (
                            SELECT
                                t51.tow_id,
                                SUM(COALESCE(t51.tow_cost, t51.tow_cost_percent*t52.contract_cost/100)) 
                                                AS summary_subcontractor_cost
                            FROM tows_contract AS t51
                            LEFT JOIN (
                                SELECT
                                    object_id,
                                    contract_id,
                                    contract_cost
                                FROM contracts
                                WHERE object_id = %s
                            ) AS t52 ON t51.contract_id = t52.contract_id
                            LEFT JOIN (
                                SELECT
                                    tow_id,
                                    dept_id
                                FROM types_of_work
                            ) AS t53 ON t51.tow_id = t53.tow_id
                            WHERE dept_id = 1
                            GROUP BY t51.tow_id
                        ) AS t5 ON t0.tow_id = t5.tow_id
                        
                        ORDER BY t0.child_path, t0.lvl;""",
                    [project_id, project_id, contract_id, contract_id, object_id]
                )
                tow = cursor.fetchall()

                if tow:
                    for i in range(len(tow)):
                        tow[i] = dict(tow[i])
                        # print(tow[i])
                print(tow[0])
                print(tow[1])

                # Список объектов
                cursor.execute("SELECT object_id, object_name FROM objects ORDER BY object_name")
                objects_name = cursor.fetchall()
                if objects_name:
                    for i in range(len(objects_name)):
                        objects_name[i] = dict(objects_name[i])

                # Список контрагентов
                cursor.execute("SELECT partner_id, partner_name  FROM partners ORDER BY partner_name")
                partners = cursor.fetchall()
                if partners:
                    for i in range(len(partners)):
                        partners[i] = dict(partners[i])

                # Список статусов
                cursor.execute("SELECT contract_status_id, status_name  FROM contract_statuses ORDER BY status_name")
                contract_statuses = cursor.fetchall()
                if contract_statuses:
                    for i in range(len(contract_statuses)):
                        contract_statuses[i] = dict(contract_statuses[i])

                # Список типов
                cursor.execute("SELECT type_id, type_name  FROM contract_types ORDER BY type_name")
                contract_types = cursor.fetchall()
                if contract_types:
                    for i in range(len(contract_types)):
                        contract_types[i] = dict(contract_types[i])

                # Список наших компаний из таблицы contractors
                cursor.execute("SELECT contractor_id, contractor_name FROM our_companies ORDER BY contractor_id")
                our_companies = cursor.fetchall()
                if our_companies:
                    for i in range(len(our_companies)):
                        our_companies[i] = dict(our_companies[i])

                app_login.conn_cursor_close(cursor, conn)

                # Список меню и имя пользователя
                hlink_menu, hlink_profile = app_login.func_hlink_profile()

                # print(dict(employee))

                # Return the updated data as a response
                return render_template('contract-card-contract.html', menu=hlink_menu, menu_profile=hlink_profile,
                                       contract_info=contract_info, objects_name=objects_name, partners=partners,
                                       contract_statuses=contract_statuses, tow=tow, contract_types=contract_types,
                                       our_companies=our_companies, subcontractors_cost=subcontractors_cost,
                                       nonce=get_nonce(), title=f"Договор {contract_number}")
    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
    #     flash(message=['Ошибка', f'contract-list: {e}'], category='error')
    #     return render_template('page_error.html', nonce=get_nonce())


@contract_app_bp.route('/get-towList', methods=['POST'])
@login_required
def get_tow_list():
    """Постраничная выгрузка списка Актов"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            types = request.get_json()['type']
            elem_id = request.get_json()['elem_id']
            status = request.get_json()['status']
            object_id = request.get_json()['object_id']
            focused_id = request.get_json()['focused_id']

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")

            tow = None
            if types == 'contract':
                # Находим object_id, по нему находим список tow
                cursor.execute(
                    """
                    SELECT
                        object_id
                    FROM contracts
                    WHERE contract_id = %s
                    LIMIT 1; """,
                    [elem_id]
                )
                object_id = cursor.fetchone()[0]

                # Находим project_id по object_id
                project_id = get_proj_id(object_id=object_id)['project_id']

                # Список tow
                if status == 'full':
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
                                t0.tow_id,
                                t0.child_path,
                                t0.tow_name,
                                COALESCE(t1.dept_id, null) AS dept_id,
                                COALESCE(t1.dept_short_name, '') AS dept_short_name,
                                t0.time_tracking,
                                t0.depth-1 AS depth,
                                t0.lvl,
                                t2.tow_cost,
                                TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')) AS tow_cost_rub,
                                t2.tow_cost_percent,
                                TRIM(BOTH ' ' FROM to_char(t2.tow_cost_percent, '90D90')) AS tow_cost_rub
                            FROM rel_rec AS t0
                            LEFT JOIN (
                                SELECT
                                    dept_id,
                                    dept_short_name
                                FROM list_dept
                            ) AS t1 ON t0.dept_id = t1.dept_id
                            LEFT JOIN (
                                SELECT
                                    tow_id,
                                    tow_cost,
                                    tow_cost_percent
                                FROM tows_contract
                                WHERE contract_id = %s
                            ) AS t2 ON t0.tow_id = t2.tow_id
                            ORDER BY t0.child_path, t0.lvl;""",
                        [project_id, project_id, elem_id]
                    )
                elif status == 'focus':
                    cursor.execute(
                        f"""WITH
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
                                t0.tow_id,
                                t0.child_path,
                                t0.tow_name,
                                COALESCE(t1.dept_id, null) AS dept_id,
                                COALESCE(t1.dept_short_name, '') AS dept_short_name,
                                t0.time_tracking,
                                t0.depth-1 AS depth,
                                t0.lvl,
                                t2.tow_cost,
                                TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')) AS tow_cost_rub,
                                t2.tow_cost_percent,
                                TRIM(BOTH ' ' FROM to_char(t2.tow_cost_percent, '90D99')) AS tow_percent_rub
                            FROM rel_rec AS t0
                            LEFT JOIN (
                                SELECT
                                    dept_id,
                                    dept_short_name
                                FROM list_dept
                            ) AS t1 ON t0.dept_id = t1.dept_id
                            LEFT JOIN (
                                SELECT
                                    tow_id,
                                    tow_cost,
                                    tow_cost_percent
                                FROM tows_contract
                                WHERE contract_id = %s
                            ) AS t2 ON t0.tow_id = t2.tow_id
                            WHERE 
                                t0.path <@ (SELECT CONCAT(path::text || '.%s')::ltree FROM types_of_work WHERE tow_id = %s) OR 
                                t0.tow_id = %s
                            ORDER BY t0.child_path, t0.lvl;""",
                        (project_id, project_id, elem_id, focused_id, focused_id, focused_id)
                    )
            elif types == 'act':
                if status == 'full':
                    pass
                elif status == 'main':
                    pass

            tow = cursor.fetchall()
            if tow:
                for i in range(len(tow)):
                    print(tow[i])
                    tow[i] = dict(tow[i])

            app_login.conn_cursor_close(cursor, conn)

            # Return the updated data as a response
            return jsonify({
                'tow': tow,
                'status': 'success'
            })
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


def get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, 
                         user_id, manual_type=''):
    # Колонка по которой идёт сортировка в таблице
    col_num = int(col_1.split('#')[0])
    # Направление сортировки
    sort_direction = col_1.split('#')[1]

    # Для значений дат, где может быть null заменяем на infinity с соответствующим знаком
    sort_sign = '-' if sort_direction == '1' else ''

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
    elif page_name == 'contracts-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = "to_char(t1.date_start, 'dd.mm.yyyy')"
        col_5 = "to_char(t1.date_finish, 'dd.mm.yyyy')"
        col_6 = "t1.subcontract_number"
        col_7 = "to_char(t1.subdate_start, 'dd.mm.yyyy')"
        col_8 = "to_char(t1.subdate_finish, 'dd.mm.yyyy')"
        col_9 = """CASE 
                        WHEN t1.type_id = 1 THEN t4.contractor_name
                        WHEN t1.type_id = 2 THEN t5.partner_name
                        ELSE ' '
                    END"""
        col_10 = """CASE 
                        WHEN t1.type_id = 1 THEN t5.partner_name
                        WHEN t1.type_id = 2 THEN t4.contractor_name
                        ELSE ' '
                    END"""
        col_11 = "t1.contract_description"
        col_12 = "t6.status_name"
        col_13 = "t1.allow"
        col_14 = "t4.vat"
        col_15 = "COALESCE((t1.contract_cost / t4.contractor_value), '0')"
        col_16 = "to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = f"COALESCE(t1.date_start, '{sort_sign}infinity'::date)"
        col_5 = f"COALESCE(t1.date_finish, '{sort_sign}infinity'::date)"
        col_6 = "COALESCE(t1.subcontract_number, '')"
        col_7 = f"COALESCE(t1.subdate_start, '{sort_sign}infinity'::date)"
        col_8 = f"COALESCE(t1.subdate_finish, '{sort_sign}infinity'::date)"
        col_9 = """CASE 
                                WHEN t1.type_id = 1 THEN t4.contractor_name
                                WHEN t1.type_id = 2 THEN t5.partner_name
                                ELSE ' '
                            END"""
        col_10 = """CASE 
                                WHEN t1.type_id = 1 THEN t5.partner_name
                                WHEN t1.type_id = 2 THEN t4.contractor_name
                                ELSE ' '
                            END"""
        col_11 = "COALESCE(t1.contract_description, '')"
        col_12 = "t6.status_name"
        col_13 = "t1.allow::text"
        col_14 = "t4.vat::text"
        col_15 = "COALESCE((t1.contract_cost / t4.contractor_value), 0)"
        col_16 = "t1.create_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = "t1.date_start"
        col_5 = "t1.date_finish"
        col_6 = "t1.contract_number"
        col_7 = "t1.date_start"
        col_8 = "t1.date_finish"
        col_9 = "t1.contract_number"
        col_10 = "t1.contract_number"
        col_11 = "t1.contract_description"
        col_12 = "t6.status_name"
        col_13 = "t1.contract_number"
        col_14 = "t1.contract_number"
        col_15 = "t1.contract_cost"
        col_16 = "t1.create_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16
        ]
    elif page_name == 'contracts-acts-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t1.act_number"
        col_5 = "to_char(t1.act_date, 'dd.mm.yyyy')"
        col_6 = "t2.status_name"
        col_7 = "t6.vat"
        col_8 = "COALESCE((t1.act_cost / t6.contractor_value), '0')"
        col_9 = "t5.count_tow"
        col_10 = "t3.allow"
        col_11 = "to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t1.act_number"
        col_5 = f"COALESCE(t1.act_date, '{sort_sign}infinity'::date)"
        col_6 = "t2.status_name"
        col_7 = "t6.vat::text"
        col_8 = "COALESCE((t1.act_cost / t6.contractor_value), '0')"
        col_9 = "t5.count_tow"
        col_10 = "t3.allow::text"
        col_11 = "t1.create_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t1.act_number"
        col_5 = "t1.act_date"
        col_6 = "t2.status_name"
        col_7 = "t3.contract_number"
        col_8 = "t1.act_cost"
        col_9 = "t1.act_id"
        col_10 = "t3.contract_number"
        col_11 = "t1.create_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        query_value = []
    elif page_name == 'contracts-payments-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t8.payment_type_name"
        col_5 = "t9.act_number"
        col_6 = "t1.payment_number"
        col_7 = "to_char(t1.payment_date, 'dd.mm.yyyy')"
        col_8 = "t6.vat"
        col_9 = "COALESCE((t1.act_cost / t6.contractor_value), '0')"
        col_10 = "t3.allow"
        col_11 = "to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t8.payment_type_name"
        col_5 = "t9.act_number"
        col_6 = "t1.payment_number"
        col_7 = "t1.payment_date"
        col_8 = "t6.vat::text"
        col_9 = "COALESCE((t1.act_cost / t6.contractor_value), '0')"
        col_10 = "t3.allow::text"
        col_11 = "t1.create_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t8.payment_type_name"
        col_5 = "t9.act_number"
        col_6 = "t1.payment_number"
        col_7 = "t1.payment_date"
        col_8 = "t3.contract_number"
        col_9 = "t1.act_cost"
        col_10 = "t3.contract_number"
        col_11 = "t1.create_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        query_value = []

    sort_col_1, sort_col_1_order = list_sort_col[col_num], 'DESC' if sort_direction == '1' else 'ASC'
    sort_col_id, sort_col_id_order = col_id, 'DESC' if sort_direction == '1' else 'ASC'
    sort_col_1_equal = '>' if sort_col_1_order == 'ASC' else '<'

    # Список таблиц в базе данных и их типы
    all_col_types = get_table_list()
    # Выражение для фильтрации в выражении WHERE
    print("____", col_1_val)

    if col_1_val:
        where_expression = (
            f"({sort_col_1}, {sort_col_id}) {sort_col_1_equal} "
            f"({app_payment.conv_data_to_db(list_type_col[col_num], col_1_val, all_col_types)}, "
            f"{app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)})")
    else:
        where_expression = (
            f"{sort_col_id} {sort_col_1_equal} {app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)}")

    # where_expression = (
    #     f"({sort_col_1}, {sort_col_id}) {sort_col_1_equal} "
    #     f"({app_payment.conv_data_to_db(list_type_col[col_num], col_1_val, all_col_types)}, "
    #     f"{app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)})")

    where_expression2 = []  # Вторая часть условия (пригодится для определения общего кол-ва строк)

    if filter_vals_list:
        for i in filter_vals_list:
            query_value.append('%' + i[1] + '%')
            where_expression2.append(list_filter_col[i[0]])

    where_expression2 = ' AND '.join(map(lambda x: f'{x}::text ILIKE %s', where_expression2))
    if where_expression2:
        where_expression += ' AND ' + where_expression2

    print('_________________________where_expression')
    print(where_expression)
    print('_________________________')
    return sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
        query_value, sort_col, col_num, sort_sign


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
        return render_template('page_error.html', nonce=get_nonce())


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
                {'link': f'/contracts-main', 'name': 'Свод'},
                {'link': f'/contracts-objects', 'name': 'Объекты'},
                {'link': f'/contracts-list', 'name': 'Договоры'},
                {'link': f'/contracts-acts-list', 'name': 'Акты'},
                {'link': f'/contracts-payments-list', 'name': 'Платежи'}
            ]
        else:
            header_menu = [
                {'link': f'/', 'name': 'Главная'}
            ]
    header_menu[cur_name]['class'] = 'current'
    header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu


def get_proj_id(object_id='', project_id='', link_name=''):
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        if object_id:
            # Список объектов
            cursor.execute(
                """
                SELECT
                    object_id,
                    project_id,
                    link_name
                FROM projects 

                WHERE object_id = %s 
                LIMIT 1;""",
                [object_id]
            )
        elif project_id:
            # Список объектов
            cursor.execute(
                """
                SELECT
                    object_id,
                    project_id,
                    link_name
                FROM projects 

                WHERE project_id = %s 
                LIMIT 1;""",
                [project_id]
            )
        elif link_name:
            # Список объектов
            cursor.execute(
                """
                SELECT
                    object_id,
                    project_id,
                    link_name
                FROM projects 

                WHERE link_name = %s 
                LIMIT 1;""",
                [link_name]
            )

        object_info = cursor.fetchone()
        app_login.conn_cursor_close(cursor, conn)
    except Exception as e:
        print('get_proj_id', e)
        current_app.logger.info(f"url {request.path[1:]}  -  _get_proj_id_  -  {e}")
        object_info = None
    return object_info
