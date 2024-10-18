import json
import time
import datetime
from psycopg2.extras import execute_values
from pprint import pprint
from flask import g, request, render_template, redirect, flash, url_for, abort, get_flashed_messages, \
    jsonify, Blueprint, current_app, send_file
from datetime import date, datetime
from flask_login import login_required
import error_handlers
import app_login
import app_payment
import app_project
import pandas as pd
from openpyxl import Workbook
import os
import tempfile
import requests
from decimal import *
import sys

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
        t1_2.vat,
        t1_2.vat_value,
        t1_2.created_at
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
            CASE 
                WHEN vat_value = 1 THEN false
                ELSE true
            END AS vat,
            vat_value,
            created_at
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
        t2_2.vat,
        t2_2.vat_value,
        t2_2.created_at
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
            CASE 
                WHEN vat_value = 1 THEN false
                ELSE true
            END AS vat,
            vat_value,
            created_at
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
        contractor_name
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
LEFT JOIN (
    SELECT
        DISTINCT ON (contract_id)
        contract_id,
        contract_status_date
    FROM contract_statuses_history
    ORDER BY contract_id, created_at DESC
) AS t8 ON t1.contract_id = t8.contract_id
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
    t8.contract_status_date,
    to_char(t8.contract_status_date, 'dd.mm.yyyy') AS contract_status_date_txt,
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
    t1.vat,
    ROUND(t1.contract_cost / t1.vat_value::numeric, 2) AS contract_cost,
    TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')) AS contract_cost_rub,
    t1.contract_cost AS contract_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')) AS contract_cost_with_vat_rub,
    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS created_at_txt,
    t1.created_at::timestamp without time zone::text AS created_at
"""
# ______________________________________________
QUERY_ACTS_JOIN = """
FROM acts AS t1
LEFT JOIN contract_statuses 
AS t2 ON t1.contract_status_id = t2.contract_status_id
LEFT JOIN (
    SELECT
        t1.contract_id,
        CASE
            WHEN t2.main_number IS NOT NULL THEN CONCAT(t1.contract_number, ' - (' ,t2.main_number , ')')
            ELSE t1.contract_number
        END AS contract_number,
        t1.object_id,
        t1.contractor_id,
        t1.allow,
        t1.type_id,
        CASE 
            WHEN t1.vat_value = 1 THEN false
            ELSE true
        END AS vat,
        t1.vat_value
    FROM contracts AS t1
    LEFT JOIN (
        SELECT
           t00.child_id AS contract_id, 
           t01.contract_number AS main_number
        FROM subcontract AS t00
        LEFT JOIN (
            SELECT
                contract_id,
                contract_number
            FROM contracts
        ) AS t01 ON t00.parent_id = t01.contract_id
        WHERE t00.parent_id IS NOT NULL
    ) AS t2 ON t1.contract_id = t2.contract_id
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
        type_id,
        type_name
    FROM contract_types
) AS t7 ON t3.type_id = t7.type_id

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
    t3.vat,
    ROUND(t1.act_cost / t3.vat_value::numeric, 2) AS act_cost,
    TRIM(BOTH ' ' FROM to_char(ROUND(t1.act_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')) AS act_cost_rub,
    t1.act_cost AS act_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.act_cost, '999 999 990D99 ₽')) AS act_cost_with_vat_rub,
    t5.count_tow,
    t3.vat_value,
    t3.allow,
    t1.created_at,
    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS created_at_txt
"""
# ______________________________________________
QUERY_PAYS_JOIN = """
FROM payments AS t1

LEFT JOIN (
    SELECT
        t1.contract_id,
        CASE
            WHEN t2.main_number IS NOT NULL THEN CONCAT(t1.contract_number, ' - (' ,t2.main_number , ')')
            ELSE t1.contract_number
        END AS contract_number,
        t1.object_id,
        t1.contractor_id,
        t1.allow,
        t1.type_id,
        CASE 
            WHEN t1.vat_value = 1 THEN false
            ELSE true
        END AS vat,
        t1.vat_value
    FROM contracts AS t1
    LEFT JOIN (
        SELECT
           t00.child_id AS contract_id, 
           t01.contract_number AS main_number
        FROM subcontract AS t00
        LEFT JOIN (
            SELECT
                contract_id,
                contract_number
            FROM contracts
        ) AS t01 ON t00.parent_id = t01.contract_id
        WHERE t00.parent_id IS NOT NULL
    ) AS t2 ON t1.contract_id = t2.contract_id
) AS t3 ON t1.contract_id = t3.contract_id
LEFT JOIN (
    SELECT
        object_id,
        object_name
    FROM objects
) AS t4 ON t3.object_id = t4.object_id
LEFT JOIN (
    SELECT
        type_id,
        type_name
    FROM contract_types
) AS t7 ON t3.type_id = t7.type_id
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
    t3.vat,
    ROUND(t1.payment_cost / t3.vat_value::numeric, 2) AS payment_cost,
    TRIM(BOTH ' ' FROM to_char(ROUND(t1.payment_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')) AS payment_cost_rub,
    t1.payment_cost AS payment_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.payment_cost, '999 999 990D99 ₽')) AS payment_cost_without_vat_rub,
    t3.vat_value,
    t3.allow,
    t1.created_at,
    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS created_at_txt
{QUERY_PAYS_JOIN}
"""
# ______________________________________________
# Нераспределенный остаток без учёта отделов
QUERY_CONT_INFO = """
SELECT
    t1.object_id,
    t2.object_name,
    t1.contract_id,
    t1.contract_number,
    SUBSTRING(t1.contract_number, 1,47) AS contract_number_short,
    t1.date_start,
    COALESCE(to_char(t1.date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
    t1.date_finish,
    COALESCE(to_char(t1.date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,
    t1.type_id,
    t1.contractor_id,
    t1.partner_id,
    t1.contract_description,
    t1.contract_status_id,
    t8.contract_status_date,
    COALESCE(to_char(t8.contract_status_date, 'dd.mm.yyyy'), '') AS status_date_txt,
    COALESCE(t1.fot_percent::text, '') AS fot_percent_txt,
    ROUND(t1.contract_cost / t1.vat_value::numeric, 2) AS contract_cost,
    t1.contract_cost AS contract_cost_vat,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS contract_cost_rub,
    t1.allow,
    t1.fot_percent,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost * t1.fot_percent / (t1.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '') AS contract_fot_cost_rub,
    t1.created_at,
    CASE 
        WHEN t1.vat_value = 1 THEN false
        ELSE true
    END AS vat,
    t1.vat_value,
    ROUND((t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0)), 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0), 2),
    '999 999 990D99 ₽')) AS undistributed_cost_rub,
    t3.type_name,
    t7.parent_number,
    t7.parent_id
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
        COALESCE(SUM(tow_cost), 0) AS tow_cost,
        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
    FROM tows_contract
    WHERE 
        contract_id = %s
        AND 
        tow_id IN
            (SELECT
                tow_id
            FROM types_of_work)
        ) AS t5 ON true
LEFT JOIN (
    SELECT 
        parent_id,
        child_id
    FROM subcontract
    WHERE 
        parent_id IS NOT NULL
        AND child_id = %s
    ORDER BY contract_relation_id
    LIMIT 1
        ) AS t6 ON t1.contract_id = t6.child_id
LEFT JOIN (
    SELECT 
        contract_number AS parent_number,
        contract_id AS parent_id
    FROM contracts
    ) AS t7 ON t6.parent_id = t7.parent_id
LEFT JOIN (
    SELECT
        contract_id,
        contract_status_id,
        contract_status_date
    FROM contract_statuses_history
    ORDER BY created_at DESC
) AS t8 ON t1.contract_id = t8.contract_id AND t1.contract_status_id = t8.contract_status_id
WHERE t1.contract_id = %s;
"""

QUERY_CONT_STATUS_HISTORY = """
SELECT
    t1.contract_id,
    t1.contract_status_id,
    t1.contract_status_date,
    COALESCE(to_char(t1.contract_status_date, 'dd.mm.yyyy'), '') AS contract_status_date_txt,
    t1.created_at,
    to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt,
    t2.status_name
FROM contract_statuses_history AS t1
LEFT JOIN (
    SELECT
        contract_status_id,
        status_name
    FROM contract_statuses
) AS t2 ON t1.contract_status_id = t2.contract_status_id
WHERE t1.contract_id = %s
ORDER BY t1.created_at;
"""

CONTRACT_TOW_LIST = """
WITH
RECURSIVE rel_rec AS (
        SELECT
            0 AS depth,
            t.*,
            ARRAY[t.lvl, t.tow_id] AS child_path,
            c.tow_cost,
            c.tow_cost_percent
        FROM types_of_work AS t
        LEFT JOIN (SELECT tow_id, tow_cost, tow_cost_percent FROM tows_contract WHERE contract_id = %s) c on c.tow_id = t.tow_id
        WHERE t.parent_id IS NULL AND t.project_id = %s

        UNION ALL
        SELECT
            nlevel(r.path) - 1,
            n.*,
            r.child_path || n.lvl || n.tow_id,
            cn.tow_cost,
            cn.tow_cost_percent
        FROM rel_rec AS r
        JOIN types_of_work AS n ON n.parent_id = r.tow_id
        LEFT JOIN (SELECT tow_id, tow_cost, tow_cost_percent FROM tows_contract WHERE contract_id = %s) cn on cn.tow_id = n.tow_id
        WHERE r.project_id = %s
        )
SELECT
    DISTINCT t0.tow_id,
    t0.child_path,
    t0.tow_name,
    COALESCE(t0.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    t2.tow_date_start,
    t2.tow_date_finish,
    COALESCE(to_char(t2.tow_date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
    COALESCE(to_char(t2.tow_date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,

    t2.tow_cost::float AS tow_cost_raw,
    t2.tow_cost_percent::float AS tow_cost_percent_raw,

    ROUND(CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        ELSE t3.contract_cost * t2.tow_cost_percent / 100
    END / t3.vat_value::numeric, 2) AS tow_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_rub,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        WHEN t2.tow_cost_percent != 0 THEN ROUND(t3.contract_cost * t2.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent / 100, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_with_vat_rub,
    CASE 
        WHEN t2.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,

    CASE 
        WHEN t2.tow_cost_percent != 0 THEN t2.tow_cost_percent
        ELSE ROUND(t2.tow_cost / t3.contract_cost * 100, 2)
    END AS tow_cost_percent,
    CASE 
        WHEN t2.tow_cost_percent != 0 THEN TRIM(BOTH ' ' FROM to_char(t2.tow_cost_percent, '990D99 %%'))
        WHEN t2.tow_cost != 0 THEN TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost / t3.contract_cost * 100, 2), '990D99 %%'))
        ELSE ''
    END AS tow_cost_percent_txt,
    CASE 
        WHEN t2.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
    CASE 
        WHEN t2.tow_cost != 0 THEN '₽'
        WHEN t2.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,

    ROUND(CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost * t3.fot_percent
        WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
        ELSE 0
    END / t3.vat_value::numeric, 2) AS tow_fot_cost,

    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost * t3.fot_percent / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent * t3.fot_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_fot_cost_rub,
    COALESCE(t4.tow_cnt_dept_no_matter, 0) AS tow_cnt,
    COALESCE(t4.tow_cnt, 1) AS tow_cnt2,
    CASE 
        WHEN t4.tow_cnt IS NULL OR t4.tow_cnt = 0 THEN 1
        ELSE t4.tow_cnt
    END AS tow_cnt3,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,
    ROUND(t5.summary_subcontractor_cost / t3.vat_value::numeric, 2) AS summary_subcontractor_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t5.summary_subcontractor_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '') 
        AS summary_subcontractor_cost_rub,
    CASE 
        WHEN t2.tow_id IS NOT NULL THEN 'checked'
        ELSE ''
    END AS contract_tow,
    t11.is_not_edited,
    CASE 
        WHEN t6.tow_id IS NOT NULL AND t7.tow_id IS NULL THEN 'Привязан акт'
        WHEN t6.tow_id IS NULL AND t7.tow_id IS NOT NULL THEN 'Привязан платёж'
        WHEN t6.tow_id IS NOT NULL AND t7.tow_id IS NOT NULL THEN 'Привязан акт и платёж'
        ELSE ''
    END AS tow_protect,
    COALESCE(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost)::text, '') AS tow_cost_protect_txt,

    COALESCE(ROUND(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost) / t3.vat_value::numeric, 2), 0)::float AS tow_cost_protect,

    ROUND(t6.summary_acts_cost / t3.vat_value::numeric, 2) AS summary_acts_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t6.summary_acts_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS summary_acts_cost_rub,

    ROUND(t7.summary_payments_cost / t3.vat_value::numeric, 2) AS summary_payments_cost,

    ROUND(t71.summary_payments_cost / t3.vat_value::numeric, 2) AS summary_payments_cost_without_act,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t71.summary_payments_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS summary_payments_cost_without_act_rub,

    ROUND(t72.summary_payments_cost / t3.vat_value::numeric, 2) AS summary_payments_cost_with_act,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t72.summary_payments_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS summary_payments_cost_with_act_rub,

    ROUND(COALESCE(t6.summary_acts_cost, 0) - COALESCE(t7.summary_payments_cost, 0) / t3.vat_value::numeric, 2) AS tow_remaining_cost,
    CASE 
        WHEN t6.summary_acts_cost IS NOT NULL AND t7.summary_payments_cost IS NOT NULL THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND((t6.summary_acts_cost - t7.summary_payments_cost) / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t6.summary_acts_cost IS NOT NULL AND t7.summary_payments_cost IS NULL THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t6.summary_acts_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t6.summary_acts_cost IS NULL AND t7.summary_payments_cost IS NOT NULL THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND( - t7.summary_payments_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_remaining_cost_rub,

    CASE 
        WHEN t2.tow_cost != 0 OR t2.tow_cost_percent != 0 THEN null
        ELSE ROUND(COALESCE(SUM(tr.tow_cost) OVER(PARTITION BY t0.tow_id)::numeric / t3.vat_value::numeric, 0), 2)
    END AS child_sum,

    CASE 
        WHEN t2.tow_cost != 0 OR t2.tow_cost_percent != 0 THEN ''
        ELSE COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(SUM(tr.tow_cost) OVER(PARTITION BY t0.tow_id)::numeric / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
    END AS child_sum_rub,

    CASE 
        WHEN t0.parent_id IS NOT NULL THEN 
            ROUND(
                (
                    CASE 
                        WHEN t2.tow_cost != 0 THEN t2.tow_cost
                        WHEN t2.tow_cost_percent != 0 THEN t3.contract_cost * t2.tow_cost_percent / 100
                        ELSE COALESCE(SUM(tr.tow_cost) OVER(PARTITION BY t0.tow_id), null)
                    END
                    /
                    SUM(tr.tow_cost) OVER(PARTITION BY t0.parent_id)
                )::numeric
                * 100, 
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
    SELECT
        tow_id,
        tow_cost,
        tow_cost_percent,
        tow_date_start,
        tow_date_finish
    FROM tows_contract
    WHERE contract_id = %s
) AS t2 ON t0.tow_id = t2.tow_id
LEFT JOIN (
    SELECT
        fot_percent / 100 AS fot_percent,
        contract_cost,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
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
        SUM(
            CASE 
                WHEN t51.tow_cost != 0 THEN t51.tow_cost
                WHEN t51.tow_cost_percent != 0 THEN t51.tow_cost_percent * t52.contract_cost / 100
                ELSE 0
            END
        ) AS summary_subcontractor_cost
    FROM tows_contract AS t51
    LEFT JOIN (
        SELECT
            object_id,
            contract_id,
            contract_cost,
            type_id
        FROM contracts
        WHERE object_id = %s
    ) AS t52 ON t51.contract_id = t52.contract_id
    WHERE t52.type_id = 2
    GROUP BY t51.tow_id
) AS t5 ON t0.tow_id = t5.tow_id
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
    --сумма стоимостей актов tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.act_cost / 100)
            ELSE 0
        END) AS summary_acts_cost
    FROM acts AS t51
    RIGHT JOIN (
        SELECT
            act_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_act
    ) AS t52 ON t51.act_id = t52.act_id    
    WHERE t51.act_id IN (SELECT act_id FROM acts WHERE contract_id = %s)
    GROUP BY t52.tow_id
) AS t6 ON t0.tow_id = t6.tow_id
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE contract_id = %s)
    GROUP BY t52.tow_id
) AS t7 ON t0.tow_id = t7.tow_id
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору. Только платежи привязанные к актам
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE contract_id = %s) AND t51.act_id IS NOT NULL
    GROUP BY t52.tow_id
) AS t71 ON t0.tow_id = t71.tow_id
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору. Только платежи НЕ привязанные к актам
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE contract_id = %s) AND t51.act_id IS NULL
    GROUP BY t52.tow_id
) AS t72 ON t0.tow_id = t72.tow_id

JOIN (
    SELECT
        tow_id,
        path,
        CASE 
            WHEN t0.tow_cost != 0 THEN t0.tow_cost
            WHEN t0.tow_cost_percent != 0 THEN (t0.tow_cost_percent * t1.contract_cost / 100)::float
            ELSE null
        END AS tow_cost
    FROM rel_rec AS t0
    LEFT JOIN (
        SELECT
            contract_cost
        FROM contracts
        WHERE contract_id = %s
    ) AS t1 ON true
) AS tr ON tr.path <@ t0.path

WHERE t0.tow_id IN (SELECT tow_id FROM tows_contract)
ORDER BY t0.child_path, t0.lvl;
"""

CONTRACT_TOW_LIST1 = """
WITH
RECURSIVE rel_rec AS (
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
    COALESCE(t0.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    t2.tow_date_start,
    t2.tow_date_finish,
    COALESCE(to_char(t2.tow_date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
    COALESCE(to_char(t2.tow_date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,

    t2.tow_cost::float AS tow_cost_raw,
    t2.tow_cost_percent::float AS tow_cost_percent_raw,

    ROUND(CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        ELSE t3.contract_cost * t2.tow_cost_percent / 100
    END / t3.vat_value::numeric, 2) AS tow_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_rub,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        WHEN t2.tow_cost_percent != 0 THEN ROUND(t3.contract_cost * t2.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent / 100, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_with_vat_rub,
    CASE 
        WHEN t2.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,

    CASE 
        WHEN t2.tow_cost_percent != 0 THEN t2.tow_cost_percent
        ELSE ROUND(t2.tow_cost / t3.contract_cost * 100, 2)
    END AS tow_cost_percent,
    CASE 
        WHEN t2.tow_cost_percent != 0 THEN TRIM(BOTH ' ' FROM to_char(t2.tow_cost_percent, '990D99 %%'))
        WHEN t2.tow_cost != 0 THEN TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost / t3.contract_cost * 100, 2), '990D99 %%'))
        ELSE ''
    END AS tow_cost_percent_txt,

    CASE 
        WHEN t2.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
    CASE 
        WHEN t2.tow_cost != 0 THEN '₽'
        WHEN t2.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,

    ROUND(CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost * t3.fot_percent
        WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
        ELSE 0
    END / t3.vat_value::numeric, 2) AS tow_fot_cost,

    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost * t3.fot_percent / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent * t3.fot_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_fot_cost_rub,
    COALESCE(t4.tow_cnt_dept_no_matter, 0) AS tow_cnt,
    COALESCE(t4.tow_cnt, 1) AS tow_cnt2,
    CASE 
        WHEN t4.tow_cnt IS NULL OR t4.tow_cnt = 0 THEN 1
        ELSE t4.tow_cnt
    END AS tow_cnt3,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,
    ROUND(t5.summary_subcontractor_cost / t3.vat_value::numeric, 2) AS summary_subcontractor_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t5.summary_subcontractor_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '') 
        AS summary_subcontractor_cost_rub,
    CASE 
        WHEN t2.tow_id IS NOT NULL THEN 'checked'
        ELSE ''
    END AS contract_tow,
    t11.is_not_edited,
    CASE 
        WHEN t6.tow_id IS NOT NULL AND t7.tow_id IS NULL THEN 'Привязан акт'
        WHEN t6.tow_id IS NULL AND t7.tow_id IS NOT NULL THEN 'Привязан платёж'
        WHEN t6.tow_id IS NOT NULL AND t7.tow_id IS NOT NULL THEN 'Привязан акт и платёж'
        ELSE ''
    END AS tow_protect,
    COALESCE(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost)::text, '') AS tow_cost_protect_txt,

    COALESCE(ROUND(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost) / t3.vat_value::numeric, 2), 0)::float AS tow_cost_protect,

    ROUND(t6.summary_acts_cost / t3.vat_value::numeric, 2) AS summary_acts_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t6.summary_acts_cost, '999 999 990D99 ₽')), '') AS summary_acts_cost_rub

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
        tow_cost_percent,
        tow_date_start,
        tow_date_finish
    FROM tows_contract
    WHERE contract_id = %s
) AS t2 ON t0.tow_id = t2.tow_id
LEFT JOIN (
    SELECT
        fot_percent / 100 AS fot_percent,
        contract_cost,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
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
        SUM(
            CASE 
                WHEN t51.tow_cost != 0 THEN t51.tow_cost
                WHEN t51.tow_cost_percent != 0 THEN t51.tow_cost_percent * t52.contract_cost / 100
                ELSE 0
            END
        ) AS summary_subcontractor_cost
    FROM tows_contract AS t51
    LEFT JOIN (
        SELECT
            object_id,
            contract_id,
            contract_cost,
            type_id
        FROM contracts
        WHERE object_id = %s
    ) AS t52 ON t51.contract_id = t52.contract_id
    WHERE t52.type_id = 2
    GROUP BY t51.tow_id
) AS t5 ON t0.tow_id = t5.tow_id
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
    --сумма стоимостей актов tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.act_cost / 100)
            ELSE 0
        END) AS summary_acts_cost
    FROM acts AS t51
    RIGHT JOIN (
        SELECT
            act_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_act
    ) AS t52 ON t51.act_id = t52.act_id    
    WHERE t51.act_id IN (SELECT act_id FROM acts WHERE contract_id = %s)
    GROUP BY t52.tow_id
) AS t6 ON t0.tow_id = t6.tow_id
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE contract_id = %s)
    GROUP BY t52.tow_id
) AS t7 ON t0.tow_id = t7.tow_id

WHERE t0.tow_id IN (SELECT tow_id FROM tows_contract)
ORDER BY t0.child_path, t0.lvl;
"""

CONTRACTS_LIST_WITHOUT_SUB = """
SELECT
    contract_id,
    contract_number
FROM contracts
WHERE 
    contract_id IN (
        SELECT 
            child_id
        FROM subcontract
        WHERE parent_id IS NULL)
    AND
    object_id = %s 
    AND
    type_id = %s;
"""

CONTRACTS_LIST_old = """
SELECT
    contract_id,
    contract_number
FROM contracts
WHERE 
    object_id = %s 
    AND
    type_id = %s;
"""

CONTRACTS_LIST = """
SELECT
    t1.contract_id,
    --t1.contract_number,
    --t2.main_number,
    CASE
        WHEN t2.main_number IS NOT NULL THEN CONCAT(t1.contract_number, ' - (' ,t2.main_number , ')')
        ELSE t1.contract_number
    END AS contract_number
FROM contracts AS t1
LEFT JOIN (
    SELECT
       t00.child_id AS contract_id, 
       t01.contract_number AS main_number
    FROM subcontract AS t00
    LEFT JOIN (
        SELECT
            contract_id,
            contract_number
        FROM contracts
    ) AS t01 ON t00.parent_id = t01.contract_id
    WHERE t00.parent_id IS NOT NULL
) AS t2 ON t1.contract_id = t2.contract_id
WHERE 
    t1.object_id = %s 
    AND
    t1.type_id = %s;
"""

CONTRACT_INFO = """
SELECT
    t1.contract_number,
    t1.partner_id,
    t1.contract_status_id,
    t1.allow,
    t1.contractor_id,
    t1.fot_percent::float AS fot_percent,
    ROUND(t1.contract_cost / t1.vat_value::numeric, 2)::float AS contract_cost,
    t1.auto_continue,
    t1.date_start,
    t1.date_finish,
    t1.contract_description,
    t1.vat_value::float AS vat_value,
    ROUND(COALESCE(GREATEST(t6.un_c_cost, t7.un_c_cost) / t1.vat_value::numeric, 0), 2)::float AS distributed_contract_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(COALESCE(GREATEST(t6.un_c_cost, t7.un_c_cost) / t1.vat_value::numeric, 0), 2),
    '999 999 990D99 ₽')) AS distributed_contract_cost_rub,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(COALESCE(GREATEST(t6.un_c_cost, t7.un_c_cost), 0), 2),
    '999 999 990D99 ₽')) AS distributed_contract_cost_with_vat_rub,
    ROUND((t1.contract_cost - COALESCE(GREATEST(t6.un_c_cost, t7.un_c_cost), 0)) / t1.vat_value::numeric, 2)::float AS undistributed_contract_cost
FROM contracts AS t1
LEFT JOIN (
    SELECT
        COALESCE(SUM(act_cost), 0) AS un_c_cost
    FROM acts
    WHERE contract_id = %s
) AS t6 ON true
LEFT JOIN (
    SELECT
        COALESCE(SUM(payment_cost), 0) AS un_c_cost
    FROM payments
    WHERE contract_id = %s
) AS t7 ON true
WHERE contract_id = %s;
"""

QUERY_ACT_INFO = """
SELECT
    t0.act_id,
    t0.act_number,
    SUBSTRING(t0.act_number, 1,47) AS act_number_short,
    t0.contract_status_id,
    t1.object_id,
    t2.object_name,
    t0.contract_id,
    t1.contract_number,
    t0.act_date,
    COALESCE(to_char(t0.act_date, 'dd.mm.yyyy'), '') AS act_date_txt,
    t1.type_id,

    ROUND(t1.contract_cost / t1.vat_value::numeric, 2) AS contract_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS contract_cost_rub,
    t1.contract_cost AS contract_cost_vat,

    ROUND(t0.act_cost / t1.vat_value::numeric, 2)::float AS act_cost,
    t0.act_cost::float AS act_cost_vat_raw,
    t0.act_cost AS act_cost_vat,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t0.act_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS act_cost_rub,
    t0.created_at,
    CASE 
        WHEN t1.vat_value = 1 THEN false
        ELSE true
    END AS vat,
    t1.vat_value,
    ROUND(t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0) / t1.vat_value::numeric, 2) AS undistributed_cost_vat_not_calc,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0) / t1.vat_value::numeric, 2),
    '999 999 990D99 ₽')) AS undistributed_cost_vat_not_calc_rub,

    ROUND(t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0), 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0), 2),
    '999 999 990D99 ₽')) AS undistributed_cost_rub,

    ROUND(t1.contract_cost - COALESCE(t6.un_c_cost, 0), 2) AS undistributed_contract_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t1.contract_cost - COALESCE(t6.un_c_cost, 0), 2),
    '999 999 990D99 ₽')) AS undistributed_contract_cost_rub,

    t3.type_name
FROM acts AS t0
LEFT JOIN (
    SELECT
        object_id,
        contract_id,
        contract_number,
        type_id,
        vat_value,
        contract_cost
    FROM contracts
) AS t1  ON t0.contract_id = t1.contract_id
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
        COALESCE(SUM(tow_cost), 0) AS tow_cost,
        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
    FROM tows_act
    WHERE 
        act_id = %s
        AND 
        tow_id IN
            (SELECT
                tow_id
            FROM types_of_work)
) AS t5 ON true
LEFT JOIN (
    SELECT
        COALESCE(SUM(act_cost), 0) AS un_c_cost
    FROM acts
    WHERE contract_id = %s AND act_id != %s
) AS t6 ON true

WHERE t0.act_id = %s;
"""

ACT_TOW_LIST = """
WITH
RECURSIVE rel_rec AS (
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
    COALESCE(t0.dept_id, null) AS dept_id,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.depth,
    t0.lvl,
    t31.act_date AS tow_date_start,
    COALESCE(to_char(t31.act_date, 'dd.mm.yyyy'), '') AS date_start_txt,

    ROUND(
        CASE 
            WHEN t2.tow_cost != 0 THEN t2.tow_cost
            ELSE t3.contract_cost * t2.tow_cost_percent / 100
        END / t3.vat_value::numeric
    , 2) AS tow_contract_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t2.tow_cost_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_contract_cost_rub,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        WHEN t2.tow_cost_percent != 0 THEN ROUND(t3.contract_cost * t2.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_contract_cost_with_vat,

    ROUND(
        CASE 
            WHEN t2.tow_cost != 0 THEN t2.tow_cost - COALESCE(t5.summary_acts_cost, 0)
            WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)
        END / t3.vat_value::numeric
    , 2) AS tow_remaining_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND(t2.tow_cost - COALESCE(t5.summary_acts_cost, 0), 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0), 2)
        ELSE 0
    END::float AS tow_remaining_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost - COALESCE(t5.summary_acts_cost, 0) / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(
                ROUND(((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)) / t3.vat_value::numeric, 2),
            '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_remaining_cost_rub,

    t6.tow_id AS act_tow_id,
    t6.tow_cost::float AS cost_raw, 
    ROUND(
        CASE 
            WHEN t6.tow_cost != 0 THEN t6.tow_cost
            WHEN t6.tow_cost_percent != 0 THEN t31.act_cost * t6.tow_cost_percent / 100
            ELSE 0
        END / t3.vat_value::numeric
    , 2)::float AS tow_act_cost,
    CASE 
        WHEN t6.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t6.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t6.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t31.act_cost * t6.tow_cost_percent / (t3.vat_value * 100)::numeric, 2) / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_act_cost_rub,

    CASE 
        WHEN t6.tow_cost != 0 THEN t6.tow_cost
        WHEN t6.tow_cost_percent != 0 THEN ROUND(t31.act_cost * t6.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_act_cost_with_vat,

    CASE 
        WHEN t6.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,

    CASE 
        WHEN t6.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,

    CASE 
        WHEN t2.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_contract_cost_status,

    CASE 
        WHEN t2.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_contract_cost_percent_status,
    t6.tow_cost_percent::float AS percent_raw,
    CASE 
        WHEN t6.tow_cost_percent != 0 THEN t6.tow_cost_percent
        ELSE ROUND(t6.tow_cost / t31.act_cost * 100, 2)
    END AS tow_cost_percent,
    CASE 
        WHEN t6.tow_cost_percent != 0 THEN TRIM(BOTH ' ' FROM to_char(t6.tow_cost_percent, '990D99 %%'))
        WHEN t6.tow_cost != 0 THEN TRIM(BOTH ' ' FROM to_char(ROUND(t6.tow_cost / t31.act_cost * 100, 2), '990D99 %%'))
        ELSE ''
    END AS tow_cost_percent_txt,

    CASE 
        WHEN t6.tow_cost != 0 THEN '₽'
        WHEN t6.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,

    COALESCE(t4.tow_cnt_dept_no_matter, 0) AS tow_cnt,
    COALESCE(t4.tow_cnt, 1) AS tow_cnt2,
    CASE 
        WHEN t4.tow_cnt IS NULL OR t4.tow_cnt = 0 THEN 1
        ELSE t4.tow_cnt
    END AS tow_cnt3,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,

    CASE 
        WHEN t2.tow_id IS NOT NULL THEN 'checked'
        ELSE ''
    END AS contract_tow,
    COALESCE(ROUND(t7.summary_payments_cost / t3.vat_value::numeric, 2)::text, '') AS tow_cost_protect_txt,
    COALESCE(ROUND(t7.summary_payments_cost / t3.vat_value::numeric, 2), 0) AS tow_cost_protect
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
        tow_cost_percent,
        tow_date_start,
        tow_date_finish
    FROM tows_contract
    WHERE contract_id = %s
) AS t2 ON t0.tow_id = t2.tow_id
LEFT JOIN (
    SELECT
        --fot_percent / 100 AS fot_percent,
        contract_cost,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
    FROM contracts
    WHERE contract_id = %s
) AS t3 ON true
LEFT JOIN (
    SELECT
        act_cost,
        act_date
    FROM acts
    WHERE act_id = %s
) AS t31 ON true
LEFT JOIN (
    SELECT
        parent_id,
        COUNT(*) AS tow_cnt_dept_no_matter,
        COUNT(dept_id) AS tow_cnt
    FROM types_of_work
    GROUP BY parent_id
) AS t4 ON t0.tow_id = t4.parent_id
LEFT JOIN (
    --сумма стоимостей tow по данному договору
    SELECT 
        t51.tow_id,
        SUM(CASE 
            WHEN t51.tow_cost != 0 THEN t51.tow_cost
            WHEN t51.tow_cost_percent != 0 THEN (t51.tow_cost_percent * t52.act_cost / 100)
            ELSE 0
        END) AS summary_acts_cost
    FROM tows_act AS t51
    LEFT JOIN (
        SELECT
            contract_id,
            act_id,
            act_cost
        FROM acts
        WHERE contract_id = %s
    ) AS t52 ON t51.act_id = t52.act_id    
    WHERE t51.act_id IN (SELECT act_id FROM acts WHERE contract_id = %s)
    GROUP BY t51.tow_id
) AS t5 ON t0.tow_id = t5.tow_id
LEFT JOIN (
    SELECT
        tow_id,
        tow_cost,
        tow_cost_percent
    FROM tows_act
    WHERE act_id = %s
) AS t6 ON t0.tow_id = t6.tow_id 
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE act_id = %s)
    GROUP BY t52.tow_id
) AS t7 ON t0.tow_id = t7.tow_id
WHERE t2.tow_id IS NOT NULL
ORDER BY t0.child_path, t0.lvl;
"""

QUERY_CONT_INFO_FOR_ACT = """
SELECT
    t1.*,
    ROUND(t1.contract_cost / t1.vat_value::numeric, 2) AS contract_cost,
    t1.contract_cost AS contract_cost_vat,
    t1.contract_cost - COALESCE(t6.un_c_cost, 0) AS undistributed_contract_cost,
    0 AS act_cost_vat,
    0 AS undistributed_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS contract_cost_rub
FROM contracts AS t1 
LEFT JOIN (
    SELECT
        COALESCE(SUM(act_cost), 0) AS un_c_cost
    FROM acts
    WHERE contract_id = %s AND act_id != %s
) AS t6 ON true
WHERE t1.contract_id = %s AND t1.object_id = %s AND t1.type_id = %s;
"""

FIND_OBJ_BY_ACT = """
SELECT
    t1.contract_id,
    t1.object_id
FROM acts AS t0
LEFT JOIN (
    SELECT
        contract_id,
        object_id
    FROM contracts
) AS t1  ON t0.contract_id = t1.contract_id
WHERE t0.act_id = %s
LIMIT 1;
"""

CONTRACT_TOW_LIST_FOR_PAYMENT = """
WITH
RECURSIVE rel_rec AS (
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
    t0.depth,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,
    CASE 
        WHEN t8.tow_cost != 0 THEN '₽'
        WHEN t8.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,
    t0.tow_id,
    t0.tow_name,
    COALESCE(t0.dept_id, null) AS dept_id,
    CASE 
        WHEN t9.tow_cost != 0 THEN t9.tow_cost
        WHEN t9.tow_cost_percent != 0 THEN t3.contract_cost * t9.tow_cost_percent / 100
        ELSE 0
    END AS tow_cost_with_vat,
    CASE 
        WHEN t9.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t9.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t9.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t3.contract_cost * t9.tow_cost_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_rub,
    CASE 
        WHEN t9.tow_cost != 0 THEN ROUND(t9.tow_cost - COALESCE(t7.summary_payments_cost, 0), 2)
        WHEN t9.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t9.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0), 2)
        ELSE 0
    END::float AS tow_remaining_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t9.tow_cost != 0 THEN ROUND(t9.tow_cost - COALESCE(t7.summary_payments_cost, 0), 2)
            WHEN t9.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t9.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0), 2)
            ELSE 0
        END 
    , '999 999 990D99 ₽')) AS tow_remaining_cost_rub,

    t8.tow_id AS payment_tow_id,
    t8.tow_cost::float AS cost_raw,
    t8.tow_cost_percent::float AS percent_raw, 
    CASE 
        WHEN t8.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,
    CASE 
        WHEN t8.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
    CASE 
        WHEN t8.tow_cost != 0 THEN ROUND(t8.tow_cost / t3.vat_value::numeric, 2)
        WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / (t3.vat_value * 100)::numeric, 2)
        ELSE 0
    END::float AS tow_payment_cost,
    CASE 
        WHEN t8.tow_cost != 0 THEN t8.tow_cost
        WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_payment_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t8.tow_cost != 0 THEN ROUND(t8.tow_cost / t3.vat_value::numeric, 2)
            WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / (t3.vat_value * 100)::numeric, 2)
            ELSE 0
        END
    , '999 999 990D99 ₽')) AS tow_payment_cost_rub,
    CASE 
        WHEN t8.tow_cost_percent != 0 THEN t8.tow_cost_percent
        ELSE ROUND(t8.tow_cost / t32.payment_cost * 100, 2)
    END AS tow_cost_percent,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t8.tow_cost_percent != 0 THEN t8.tow_cost_percent
            WHEN t8.tow_cost != 0 THEN  ROUND(t8.tow_cost / t32.payment_cost * 100, 2)
        ELSE 0
    END 
    , '990D99 %%')) AS tow_cost_percent_txt
FROM rel_rec AS t0

LEFT JOIN (
    SELECT
        contract_cost,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
    FROM contracts
    WHERE contract_id = %s
) AS t3 ON true
LEFT JOIN (
    SELECT
        payment_cost,
        payment_date
    FROM payments
    WHERE payment_id = %s
) AS t32 ON true
LEFT JOIN (
    SELECT
        parent_id,
        COUNT(*) AS tow_cnt_dept_no_matter,
        COUNT(dept_id) AS tow_cnt
    FROM types_of_work
    GROUP BY parent_id
) AS t4 ON t0.tow_id = t4.parent_id
LEFT JOIN (
    --сумма стоимостей tow по данному договору
    SELECT 
        t51.tow_id,
        SUM(CASE 
            WHEN t51.tow_cost != 0 THEN t51.tow_cost
            WHEN t51.tow_cost_percent != 0 THEN (t51.tow_cost_percent * t52.act_cost / 100)
            ELSE 0
        END) AS summary_acts_cost
    FROM tows_act AS t51
    LEFT JOIN (
        SELECT
            contract_id,
            act_id,
            act_cost
        FROM acts
        WHERE contract_id = %s
    ) AS t52 ON t51.act_id = t52.act_id    
    WHERE t51.act_id IN (SELECT act_id FROM acts WHERE contract_id = %s)
    GROUP BY t51.tow_id
) AS t5 ON t0.tow_id = t5.tow_id
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE contract_id = %s)
    GROUP BY t52.tow_id
) AS t7 ON t0.tow_id = t7.tow_id
LEFT JOIN (
    SELECT
        tow_id,
        tow_cost,
        tow_cost_percent
    FROM tows_payment
    WHERE payment_id = %s
) AS t8 ON t0.tow_id = t8.tow_id 
LEFT JOIN (
    SELECT
        tow_id,
        tow_cost,
        tow_cost_percent
    FROM tows_contract
    WHERE contract_id = %s
) AS t9 ON t0.tow_id = t9.tow_id 
WHERE t9.tow_id IS NOT NULL
ORDER BY t0.child_path, t0.lvl;
"""

ACT_TOW_LIST_FOR_PAYMENT = """
WITH
RECURSIVE rel_rec AS (
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
    t0.depth,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,
    CASE 
        WHEN t8.tow_cost != 0 THEN '₽'
        WHEN t8.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,
    t0.tow_id,
    t0.tow_name,
    COALESCE(t0.dept_id, null) AS dept_id,
    CASE 
        WHEN t6.tow_cost != 0 THEN t6.tow_cost
        WHEN t6.tow_cost_percent != 0 THEN ROUND(t31.act_cost * t6.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_cost_with_vat,
    CASE 
        WHEN t6.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t6.tow_cost / t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t6.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t31.act_cost * t6.tow_cost_percent / (t3.vat_value * 100)::numeric, 2), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_rub,
    CASE 
        WHEN t6.tow_cost != 0 THEN ROUND(t6.tow_cost - COALESCE(t7.summary_payments_cost, 0), 2)
        WHEN t6.tow_cost_percent != 0 THEN ROUND((t31.act_cost * t6.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0), 2)
    ELSE 0
    END::float AS tow_remaining_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t6.tow_cost != 0 THEN ROUND(t6.tow_cost - COALESCE(t7.summary_payments_cost, 0), 2)
            WHEN t6.tow_cost_percent != 0 THEN ROUND((t31.act_cost * t6.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0), 2)
            ELSE 0
        END 
    , '999 999 990D99 ₽')) AS tow_remaining_cost_rub,

    t8.tow_id AS payment_tow_id,
    t8.tow_cost::float AS cost_raw,
    t8.tow_cost_percent::float AS percent_raw, 
    CASE 
        WHEN t8.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,
    CASE 
        WHEN t8.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
    CASE 
        WHEN t8.tow_cost != 0 THEN ROUND(t8.tow_cost / t3.vat_value::numeric, 2)
        WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / (t3.vat_value * 100)::numeric, 2)
        ELSE 0
    END::float AS tow_payment_cost,
    CASE 
        WHEN t8.tow_cost != 0 THEN t8.tow_cost
        WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / 100, 2)
        ELSE 0
    END AS tow_payment_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t8.tow_cost != 0 THEN ROUND(t8.tow_cost / t3.vat_value::numeric, 2)
            WHEN t8.tow_cost_percent != 0 THEN ROUND(t32.payment_cost * t8.tow_cost_percent / (t3.vat_value * 100)::numeric, 2)
            ELSE 0
        END
    , '999 999 990D99 ₽')) AS tow_payment_cost_rub,
    CASE 
        WHEN t8.tow_cost_percent != 0 THEN t8.tow_cost_percent
        ELSE ROUND(t8.tow_cost / t32.payment_cost * 100, 2)
    END AS tow_cost_percent,
    TRIM(BOTH ' ' FROM to_char(
        CASE 
            WHEN t8.tow_cost_percent != 0 THEN t8.tow_cost_percent
            WHEN t8.tow_cost != 0 THEN  ROUND(t8.tow_cost / t32.payment_cost * 100, 2)
        ELSE 0
    END 
    , '990D99 %%')) AS tow_cost_percent_txt
FROM rel_rec AS t0

LEFT JOIN (
    SELECT
        contract_cost,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
    FROM contracts
    WHERE contract_id = %s
) AS t3 ON true
LEFT JOIN (
    SELECT
        act_cost,
        act_date
    FROM acts
    WHERE act_id = %s
) AS t31 ON true
LEFT JOIN (
    SELECT
        payment_cost,
        payment_date
    FROM payments
    WHERE payment_id = %s
) AS t32 ON true
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
        tow_id,
        tow_cost,
        tow_cost_percent
    FROM tows_act
    WHERE act_id = %s
) AS t6 ON t0.tow_id = t6.tow_id 
LEFT JOIN (
    --сумма стоимостей платежей tow по данному договору
    SELECT 
        t52.tow_id,
        SUM(CASE 
            WHEN t52.tow_cost != 0 THEN t52.tow_cost
            WHEN t52.tow_cost_percent != 0 THEN (t52.tow_cost_percent * t51.payment_cost / 100)
            ELSE 0
        END) AS summary_payments_cost
    FROM payments AS t51
    LEFT JOIN (
        SELECT
            payment_id,
            tow_id,
            tow_cost,
            tow_cost_percent
        FROM tows_payment
    ) AS t52 ON t51.payment_id = t52.payment_id    
    WHERE t52.payment_id IN (SELECT payment_id FROM payments WHERE act_id = %s)
    GROUP BY t52.tow_id
) AS t7 ON t0.tow_id = t7.tow_id
LEFT JOIN (
    SELECT
        tow_id,
        tow_cost,
        tow_cost_percent
    FROM tows_payment
    WHERE payment_id = %s
) AS t8 ON t0.tow_id = t8.tow_id 
WHERE t6.tow_id IS NOT NULL
ORDER BY t0.child_path, t0.lvl;
"""

QUERY_CONT_INFO_FOR_PAYMENT = """
SELECT
    t1.contract_id,
    t1.object_id,
    t1.type_id,
    t1.contract_number,
    ROUND(t1.contract_cost / t1.vat_value::numeric, 2) AS contract_cost,
    t1.vat_value,

    t3.payment_id,
    t3.payment_number,
    t3.payment_date,
    t3.act_id,
    ROUND(t3.payment_cost / t1.vat_value::numeric, 2)::float AS payment_cost,
    t3.payment_type_id,

    SUBSTRING(t3.payment_number, 1,47) AS act_number_short,
    to_char(t3.payment_date, 'dd.mm.yyyy') AS payment_date_txt,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS contract_cost_rub,
    TRIM(BOTH ' ' FROM to_char(ROUND(t3.payment_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')) AS payment_cost_rub,
    t1.contract_cost AS contract_cost_vat,
    ROUND(t1.contract_cost - COALESCE(t6.un_c_cost, 0), 2) AS undistributed_contract_cost,
    t3.payment_cost AS act_cost_vat,
    ROUND(t3.payment_cost - COALESCE(t5.tow_cost + t3.payment_cost * t5.tow_cost_percent / 100, 0), 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t3.payment_cost - COALESCE(t5.tow_cost + t3.payment_cost * t5.tow_cost_percent / 100, 0), 2) 
    , '999 999 990D99 ₽')) AS undistributed_cost_rub,
    ROUND(t5.tow_cost / t1.vat_value::numeric, 2) AS tow_cost,
    t5.tow_cost_percent
FROM contracts AS t1 

LEFT JOIN (
    SELECT
        *
    FROM payments
    WHERE payment_id = %s
) AS t3 ON t1.contract_id = t3.contract_id
LEFT JOIN (
    SELECT
        payment_id,
        COALESCE(SUM(tow_cost), 0) AS tow_cost,
        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
    FROM tows_payment
    GROUP BY payment_id
) AS t5 ON t3.payment_id = t5.payment_id
LEFT JOIN (
    SELECT
        COALESCE(SUM(payment_cost), 0) AS un_c_cost
    FROM payments
    WHERE contract_id = %s AND payment_id != %s
) AS t6 ON true
WHERE t1.contract_id = %s AND t1.object_id = %s AND t1.type_id = %s;
"""

QUERY_ACT_INFO_FOR_PAYMENT = """
SELECT
    t1.contract_id,
    t1.object_id,
    t1.type_id,
    t1.contract_number,
    t1.vat_value,

    t2.*,
    ROUND(t2.act_cost / t1.vat_value::numeric, 2) AS contract_cost,

    t3.*,
    ROUND(t3.payment_cost / t1.vat_value::numeric, 2)::float AS payment_cost,
    SUBSTRING(t3.payment_number, 1,47) AS act_number_short,
    to_char(t3.payment_date, 'dd.mm.yyyy') AS payment_date_txt,
    COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.act_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')), '') AS contract_cost_rub,
    TRIM(BOTH ' ' FROM to_char(ROUND(t3.payment_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')) AS payment_cost_rub,
    t2.act_cost AS contract_cost_vat,
    (t2.act_cost - COALESCE(t6.un_c_cost, 0))::float AS undistributed_contract_cost,
    t3.payment_cost AS act_cost_vat,
    ROUND(t3.payment_cost - COALESCE(t5.tow_cost + t3.payment_cost * t5.tow_cost_percent / 100, 0), 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND(t3.payment_cost - COALESCE(t5.tow_cost + t3.payment_cost * t5.tow_cost_percent / 100, 0), 2) 
    , '999 999 990D99 ₽')) AS undistributed_cost_rub
FROM contracts AS t1 
LEFT JOIN (
    SELECT
        *
    FROM acts
    WHERE act_id = %s
) AS t2 ON t1.contract_id = t2.contract_id
LEFT JOIN (
    SELECT
        *
    FROM payments
    WHERE payment_id = %s
) AS t3 ON t1.contract_id = t3.contract_id
LEFT JOIN (
    SELECT
        payment_id,
        COALESCE(SUM(tow_cost), 0) AS tow_cost,
        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
    FROM tows_payment
    GROUP BY payment_id
) AS t5 ON t3.payment_id = t5.payment_id
LEFT JOIN (
    SELECT
        COALESCE(SUM(payment_cost), 0) AS un_c_cost
    FROM payments
    WHERE act_id = %s AND payment_id != %s
) AS t6 ON true
WHERE t1.contract_id = %s AND t1.object_id = %s AND t1.type_id = %s;
"""

FIND_OBJ_BY_PAYMENT = """
SELECT
    t1.contract_id,
    t1.object_id,
    t1.type_id,
    t0.act_id,
    t0.payment_type_id
FROM payments AS t0
LEFT JOIN (
    SELECT
        contract_id,
        object_id,
        type_id
    FROM contracts
) AS t1  ON t0.contract_id = t1.contract_id
WHERE t0.payment_id = %s
LIMIT 1;
"""


# Define a function to retrieve nonce within the application context
def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@contract_app_bp.before_request
def before_request():
    app_login.before_request()


# Проверка, что пользователь не уволен
@contract_app_bp.before_request
def check_user_status():
    app_login.check_user_status()


@contract_app_bp.route('/get-first-contract', methods=['POST'])
@login_required
def get_first_contract():
    """Постраничная выгрузка списка несогласованных платежей"""
    try:
        user_id = app_login.current_user.get_id()

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = request.get_json()['page_url']
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        if page_name == 'contract-main':
            col_id = 't1.object_id'
        elif page_name == 'contract-list':
            col_id = 't1.contract_id'
        elif page_name == 'contract-objects':
            col_id = 't1.object_id'
        elif page_name == 'contract-acts-list':
            col_id = 't1.act_id'
        elif page_name == 'contract-payments-list':
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

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        link_name = request.get_json()['link']
        where_object_id = ''
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
            if object_id:
                if page_name == 'contract-list':
                    where_object_id = f"and t1.object_id = {object_id}"
                elif page_name == 'contract-acts-list':
                    where_object_id = f"and t3.object_id = {object_id}"
                elif page_name == 'contract-payments-list':
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

        if page_name == 'contract-main':
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
        elif page_name == 'contract-objects':
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
        elif page_name == 'contract-list':
            cursor.execute(
                f"""
                    {WITH_CONTRACTS}
                    SELECT
                        t1.contract_id {order} 1 AS contract_id,
                        t2.object_name,
                        t3.type_name,
                        t1.contract_number,
                        (COALESCE(t8.contract_status_date {order} interval '1 day', '{sort_sign}infinity'::date))::text AS contract_status_date,
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
                        t1.vat::text AS vat,
                        ROUND((t1.contract_cost / t1.vat_value::numeric), 2) {order} 0.01 AS contract_cost,
                        (t1.created_at {order} interval '1 day')::timestamp without time zone::text AS created_at
                    {QUERY_CONTRACTS_JOIN}
                    WHERE {where_expression2} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                query_value
            )
        elif page_name == 'contract-acts-list':
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
                        t3.vat::text AS vat,
                        (t1.act_cost / t3.vat_value::numeric) {order} 0.01 AS act_cost,
                        t5.count_tow {order} 1 AS count_tow,
                        t3.allow::text AS allow,
                        (t1.created_at {order} interval '1 microseconds')::timestamp without time zone::text AS created_at
                    {QUERY_ACTS_JOIN}
                    WHERE {where_expression2} {where_object_id}
                    ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                    LIMIT {limit};
                    """,
                query_value
            )
        elif page_name == 'contract-payments-list':
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
                        t3.vat::text AS vat,
                        (t1.payment_cost / t3.vat_value::numeric) {order} 0.01 AS payment_cost,
                        t3.allow::text AS allow,
                        (t1.created_at {order} interval '1 microseconds')::timestamp without time zone::text AS created_at
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
            if page_name == 'contract-main':
                col_0 = all_contracts["object_id"]
                col_1 = all_contracts["object_name"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+' if col_1 else col_1
                else:
                    col_1 = col_1[:-1] if col_1 else col_1
                filter_col = [
                    col_0, col_1
                ]
            elif page_name == 'contract-objects':
                col_0 = all_contracts["object_id"]
                col_1 = all_contracts["object_name"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+' if col_1 else col_1
                else:
                    col_1 = col_1[:-1] if col_1 else col_1
                filter_col = [
                    col_0, col_1
                ]
            elif page_name == 'contract-list':
                col_0 = ""
                col_1 = all_contracts["object_name"]
                col_2 = all_contracts["type_name"]
                col_3 = all_contracts["contract_number"]
                col_4 = all_contracts["date_start"]
                col_5 = all_contracts["date_finish"]
                col_6 = all_contracts["subcontract_number"]
                col_7 = all_contracts["contract_status_date"]
                col_8 = all_contracts["subdate_start"]
                col_9 = all_contracts["subdate_finish"]
                col_10 = all_contracts["partner_name"]
                col_11 = all_contracts["contractor_name"]
                col_12 = all_contracts["contract_description"]
                col_13 = all_contracts["status_name"]
                col_14 = all_contracts["allow"]
                col_15 = all_contracts["vat"]
                col_16 = all_contracts["contract_cost"]
                col_17 = all_contracts["created_at"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+' if col_1 else col_1
                    col_2 = col_2 + '+' if col_2 else col_2
                    col_3 = col_3 + '+' if col_3 else col_3
                    col_6 = col_6 + '+' if col_6 else col_6
                    col_10 = col_10 + '=' if col_10 else col_10
                    col_11 = col_11 + '+' if col_11 else col_11
                    col_12 = col_12 + '+' if col_12 else col_12
                    col_13 = col_13 + '+' if col_13 else col_13
                    col_14 = col_14 + '+' if col_14 else col_14
                    col_15 = col_15 + '+' if col_15 else col_15
                else:
                    col_1 = col_1[:-1] if col_1 else col_1
                    col_2 = col_2[:-1] if col_2 else col_2
                    col_3 = col_3[:-1] if col_3 else col_3
                    col_6 = col_6[:-1] if col_6 else col_6
                    col_10 = col_10[:-1] if col_10 else col_10
                    col_11 = col_11[:-1] if col_11 else col_11
                    col_12 = col_12[:-1] if col_12 else col_12
                    col_13 = col_13[:-1] if col_13 else col_13
                    col_14 = col_14[:-1] if col_14 else col_14
                    col_15 = col_15[:-1] if col_15 else col_15

                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12,
                    col_13, col_14, col_15, col_16, col_17
                ]
            elif page_name == 'contract-acts-list':
                col_0 = ""
                col_1 = all_contracts["object_name"]
                col_2 = all_contracts["type_name"]
                col_3 = all_contracts["contract_number"]
                col_4 = all_contracts["act_number"]
                col_5 = all_contracts["act_date"]
                col_6 = all_contracts["status_name"]
                col_7 = all_contracts["vat"]
                col_8 = all_contracts["act_cost"]
                col_9 = all_contracts["count_tow"]
                col_10 = all_contracts["allow"]
                col_11 = all_contracts["created_at"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+' if col_1 else col_1
                    col_2 = col_2 + '+' if col_2 else col_2
                    col_3 = col_3 + '+' if col_3 else col_3
                    col_4 = col_4 + '+' if col_4 else col_4
                    col_6 = col_6 + '+' if col_6 else col_6
                    col_7 = col_7 + '+' if col_7 else col_7
                    col_10 = col_10 + '+' if col_10 else col_10
                else:
                    col_1 = col_1[:-1] if col_1 else col_1
                    col_2 = col_2[:-1] if col_2 else col_2
                    col_3 = col_3[:-1] if col_3 else col_3
                    col_4 = col_4[:-1] if col_4 else col_4
                    col_6 = col_6[:-1] if col_6 else col_6
                    col_7 = col_7[:-1] if col_7 else col_7
                    col_10 = col_10[:-1] if col_10 else col_10
                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
                ]
            elif page_name == 'contract-payments-list':
                col_0 = ""
                col_1 = all_contracts["object_name"]
                col_2 = all_contracts["type_name"]
                col_3 = all_contracts["contract_number"]
                col_4 = all_contracts["payment_type_name"]
                col_5 = all_contracts["act_number"]
                col_6 = all_contracts["payment_number"]
                col_7 = all_contracts["payment_date"]
                col_8 = all_contracts["vat"]
                col_9 = all_contracts["payment_cost"]
                col_10 = all_contracts["allow"]
                col_11 = all_contracts["created_at"]
                if sort_col_1_order == 'DESC':
                    col_1 = col_1 + '+' if col_1 else col_1
                    col_2 = col_2 + '+' if col_2 else col_2
                    col_3 = col_3 + '+' if col_3 else col_3
                    col_4 = col_4 + '+' if col_4 else col_4
                    col_5 = col_5 + '+' if col_5 else col_5
                    col_6 = col_6 + '+' if col_6 else col_6
                    col_8 = col_8 + '+' if col_8 else col_8
                    col_10 = col_10 + '+' if col_10 else col_10
                else:
                    col_1 = col_1[:-1] if col_1 else col_1
                    col_2 = col_2[:-1] if col_2 else col_2
                    col_3 = col_3[:-1] if col_3 else col_3
                    col_4 = col_4[:-1] if col_4 else col_4
                    col_5 = col_5[:-1] if col_5 else col_5
                    col_6 = col_6[:-1] if col_6 else col_6
                    col_8 = col_8[:-1] if col_8 else col_8
                    col_10 = col_10[:-1] if col_10 else col_10
                filter_col = [
                    col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
                ]

            if page_name in ('contract-main', 'contract-objects'):
                sort_col['col_1'].append(filter_col[col_num])
                sort_col['col_id'] = all_contracts["object_id"]
            elif page_name == 'contract-list':
                sort_col['col_1'].append(filter_col[col_num])
                sort_col['col_id'] = all_contracts["contract_id"]
            elif page_name == 'contract-acts-list':
                sort_col['col_1'].append(filter_col[col_num])
                sort_col['col_id'] = all_contracts["act_id"]
            elif page_name == 'contract-payments-list':
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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@contract_app_bp.route('/get-contractMain-pagination', methods=['POST'])
@login_required
def get_contract_main_pagination():
    """Постраничная выгрузка списка СВОД"""
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = 'contract-main'
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

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
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
                {QUERY_MAIN}
                WHERE {where_expression}
                ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                LIMIT {limit};
                """,
                query_value
            )
            all_contracts = cursor.fetchall()

        except Exception as e:
            current_app.logger.exception(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


# Главная страница раздела 'Договоры' - СВОД
@contract_app_bp.route('/contract-main', methods=['GET'])
@login_required
def get_contracts_main(link_name=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

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
        objects['object_name'] = objects['object_name'][:-1]

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=0)

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
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/get-contractObj-pagination', methods=['POST'])
@login_required
def get_contract_objects_pagination():
    """Постраничная выгрузка списка Объекты"""
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = 'contract-main'
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

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
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
                {QUERY_OBJ}
                WHERE {where_expression}
                ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
                LIMIT {limit};
                """,
                query_value
            )
            all_contracts = cursor.fetchall()

        except Exception as e:
            current_app.logger.exception(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


# 'Договоры' - Объекты
@contract_app_bp.route('/contract-objects', methods=['GET'])
@login_required
def get_contracts_objects(link_name=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

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
        objects['object_name'] = objects['object_name'][:-1]

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=1)

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
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/get-contractList-pagination', methods=['POST'])
@login_required
def get_contract_list_pagination():
    """Постраничная выгрузка списка Договоров"""
    try:
        user_id = app_login.current_user.get_id()

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = 'contract-list'
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        col_id = 't1.contract_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']
        link_name = request.get_json()['link']

        if col_1.split('#')[0] == 'False' or not col_1:
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
            query_value, sort_col, col_num, sort_sign = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        if where_expression2:
            where_expression2 = 'WHERE ' + where_expression2
        else:
            where_expression2 = ''

        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id'] if link_name else None
            query_value.append(object_id)
            where_expression += ' AND t2.object_id = %s'
            if where_expression2:
                where_expression2 += ' AND t2.object_id = %s'
            else:
                where_expression2 = 'WHERE t2.object_id = %s'

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
                (COALESCE(t8.contract_status_date, '{sort_sign}infinity'::date))::text AS contract_status_date,
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
            current_app.logger.exception(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
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
        col_4 = all_contracts[-1]["contract_status_date"]
        col_5 = all_contracts[-1]["date_start"]
        col_6 = all_contracts[-1]["date_finish"]
        col_7 = all_contracts[-1]["subcontract_number"]
        col_8 = all_contracts[-1]["subdate_start"]
        col_9 = all_contracts[-1]["subdate_finish"]
        col_10 = all_contracts[-1]["partner_name"]
        col_11 = all_contracts[-1]["contractor_name"]
        col_12 = all_contracts[-1]["contract_description"]
        col_13 = all_contracts[-1]["status_name"]
        col_14 = all_contracts[-1]["allow"]
        col_15 = all_contracts[-1]["vat"]
        col_16 = all_contracts[-1]["contract_cost"]
        col_17 = all_contracts[-1]["created_at"]
        filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16, col_17
        ]

        # Список колонок для сортировки, добавляем последние значения в столбах сортировки
        sort_col['col_1'].append(filter_col[col_num])
        sort_col['col_id'] = all_contracts[-1]["contract_id"]
        for i in range(len(all_contracts)):
            all_contracts[i] = dict(all_contracts[i])

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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


# 'Договоры' - Договоры
@contract_app_bp.route('/contract-list', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-list', methods=['GET'])
@login_required
def get_contracts_list(link_name=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        where_contracts_list = ''
        cur_name = 2  # Порядковый номер пункта в основном меню (header_menu)
        proj = False  # Информация о проекте, если зашли из проекта
        object_id = None
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
            if object_id:
                cur_name = 1
                where_contracts_list = f"WHERE t1.object_id = {object_id}"

            project = app_project.get_proj_info(link_name)
            if project[0] == 'error':
                flash(message=project[1], category='error')
                return redirect(url_for('.objects_main'))
            elif not project[1]:
                flash(message=['ОШИБКА. Проект не найден'], category='error')
                return redirect(url_for('.objects_main'))
            proj = project[1]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('contracts')
        # Список договоров
        cursor.execute(
            f"""
            {WITH_CONTRACTS}
            SELECT
                t1.contract_id + 1 AS contract_id,
                (t1.created_at + interval '1 microseconds')::timestamp without time zone::text AS created_at
            FROM t1
            {where_contracts_list}
            ORDER BY created_at DESC, contract_id DESC
            LIMIT 1;
            """
        )
        objects = cursor.fetchone()
        if objects:
            objects = dict(objects)

        # Доступность кнопок создания допников
        new_subcontract = [False, False]
        if object_id:
            cursor.execute(
                CONTRACTS_LIST_WITHOUT_SUB,
                [object_id, 1]
            )
            new_income_contract = True if len(cursor.fetchall()) else False
            cursor.execute(
                CONTRACTS_LIST_WITHOUT_SUB,
                [object_id, 2]
            )
            new_expenditure_contract = True if len(cursor.fetchall()) else False
            new_subcontract = [new_income_contract, new_expenditure_contract]
        else:
            cursor.execute(
                """
                SELECT
                    DISTINCT(type_id)
                FROM contracts;
                """
            )
            contract_type_id = cursor.fetchall()
            if contract_type_id:
                for i in range(len(contract_type_id)):
                    new_subcontract[contract_type_id[i][0] - 1] = True
            else:
                new_subcontract = [False, False]
        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=cur_name)

        # Список колонок для сортировки
        if objects:
            sort_col = {
                'col_1': [17, 1, objects['created_at']],  # Первая колонка - DESC
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
        if not link_name:
            # Если проходим на странице через объект, то скрываем столбец Объект
            hidden_col.append(1)
            title = "Сводная таблица договоров. Договоры"
        else:
            title = "Таблица договоров объекта"

        return render_template('contract-list.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                               header_menu=header_menu, tab_rows=tab_rows, setting_users=setting_users,
                               objects=objects, hidden_col=hidden_col, nonce=get_nonce(), proj=proj,
                               new_subcontract=new_subcontract, title=title)
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/get-actList-pagination', methods=['POST'])
@login_required
def get_act_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = 'contract-acts-list'
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        col_id = 't1.act_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']
        link_name = request.get_json()['link']

        if col_1.split('#')[0] == 'False' or not col_1:
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        link_name = request.get_json()['link']
        where_object_id = ''
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
            if object_id:
                where_object_id = f"and t3.object_id = {object_id}"

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
            query_value, sort_col, col_num, sort_sign = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        if where_expression2:
            where_expression2 = 'WHERE ' + where_expression2
        else:
            where_expression2 = ''

        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id'] if link_name else None
            query_value.append(object_id)
            where_expression += ' AND t3.object_id = %s'
            if where_expression2:
                where_expression2 += ' AND t3.object_id = %s'
            else:
                where_expression2 = 'WHERE t3.object_id = %s'

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
            msg_for_user = app_login.create_traceback(info=sys.exc_info(), error_type='warning')
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': msg_for_user,
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
        col_8 = all_contracts[-1]["act_cost"]
        col_9 = all_contracts[-1]["count_tow"]
        col_10 = all_contracts[-1]["allow"]
        col_11 = all_contracts[-1]["created_at"]
        filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]

        # Список колонок для сортировки, добавляем последние значения в столбах сортировки
        sort_col['col_1'].append(filter_col[col_num])
        sort_col['col_id'] = all_contracts[-1]["act_id"]

        for i in range(len(all_contracts)):
            all_contracts[i] = dict(all_contracts[i])

        # if where_expression2:
        #     where_expression2 = f"WHERE {where_expression2} {where_object_id}"
        # else:
        #     where_expression2 = ''
        #     if where_object_id:
        #         where_expression2 = f"WHERE true {where_object_id}"

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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


# 'Договоры' - Акты
@contract_app_bp.route('/contract-acts-list', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-acts-list', methods=['GET'])
@login_required
def get_contracts_acts_list(link_name=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        where_contracts_list = ''
        cur_name = 3  # Порядковый номер пункта в основном меню (header_menu)
        proj = False  # Информация о проекте, если зашли из проекта
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
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

            project = app_project.get_proj_info(link_name)
            if project[0] == 'error':
                flash(message=project[1], category='error')
                return redirect(url_for('.objects_main'))
            elif not project[1]:
                flash(message=['ОШИБКА. Проект не найден'], category='error')
                return redirect(url_for('.objects_main'))
            proj = project[1]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('contracts')
        # Список Актов
        cursor.execute(
            f"""
            SELECT
                t1.act_id + 1 AS act_id,
                (t1.created_at + interval '1 microseconds')::timestamp without time zone::text AS created_at
            FROM acts as t1
            {where_contracts_list}
            ORDER BY t1.created_at DESC, t1.act_id DESC
            LIMIT 1;
            """
        )
        acts = cursor.fetchone()
        if acts:
            acts = dict(acts)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=cur_name)

        # Список колонок для сортировки
        if acts:
            sort_col = {
                'col_1': [11, 1, acts['created_at']],  # Первая колонка - DESC
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
        if not link_name:
            # Если проходим на странице через объект, то скрываем столбец Объект
            hidden_col.append(1)
            title = "Сводная таблица договоров. Акты"
        else:
            title = "Таблица актов объекта"

        return render_template('contract-acts-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                               sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                               setting_users=setting_users, nonce=get_nonce(), proj=proj,
                               title=title)
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/get-contractPayList-pagination', methods=['POST'])
@login_required
def get_contract_pay_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        page_name = 'contract-payments-list'
        limit = request.get_json()['limit']
        col_1 = request.get_json()['sort_col_1']
        col_1_val = request.get_json()['sort_col_1_val']
        col_id = 't1.payment_id'
        col_id_val = request.get_json()['sort_col_id_val']
        filter_vals_list = request.get_json()['filterValsList']
        link_name = request.get_json()['link']

        if col_1.split('#')[0] == 'False' or not col_1:
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': 'Нет данных',
            })

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        where_object_id = ''
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
            if object_id:
                where_object_id = f"and t3.object_id = {object_id}"

        sort_col_1, sort_col_1_order, sort_col_id, sort_col_id_order, where_expression, where_expression2, \
            query_value, sort_col, col_num, sort_sign = \
            get_sort_filter_data(page_name, limit, col_1, col_1_val, col_id, col_id_val, filter_vals_list, user_id)

        if where_expression2:
            where_expression2 = 'WHERE ' + where_expression2
        else:
            where_expression2 = ''

        if link_name:
            query_value.append(object_id)
            where_expression += ' AND t3.object_id = %s'
            if where_expression2:
                where_expression2 += ' AND t3.object_id = %s'
            else:
                where_expression2 = 'WHERE t3.object_id = %s'

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
            msg_for_user = app_login.create_traceback(info=sys.exc_info(), error_type='warning')
            return jsonify({
                'contract': 0,
                'sort_col': 0,
                'status': 'error',
                'description': msg_for_user,
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
        col_9 = all_contracts[-1]["payment_cost"]
        col_10 = all_contracts[-1]["allow"]
        col_11 = all_contracts[-1]["created_at"]
        filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]

        # Список колонок для сортировки, добавляем последние значения в столбах сортировки
        sort_col['col_1'].append(filter_col[col_num])
        sort_col['col_id'] = all_contracts[-1]["payment_id"]

        for i in range(len(all_contracts)):
            all_contracts[i] = dict(all_contracts[i])

        # if where_expression2:
        #     where_expression2 = f"WHERE {where_expression2} {where_object_id}"
        # else:
        #     where_expression2 = ''
        #     if where_object_id:
        #         where_expression2 = f"WHERE true {where_object_id}"

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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': msg_for_user,
        })


@contract_app_bp.route('/contract-payments-list', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-payments-list', methods=['GET'])
@login_required
def get_contracts_payments_list(link_name=''):
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Если зашли из проекта, то фильтруем данные с учётом объекта
        where_contracts_list = ''
        cur_name = 4  # Порядковый номер пункта в основном меню (header_menu)
        proj = False  # Информация о проекте, если зашли из проекта
        if link_name:
            object_id = get_proj_id(link_name=link_name)['object_id']
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
            project = app_project.get_proj_info(link_name)
            if project[0] == 'error':
                flash(message=project[1], category='error')
                return redirect(url_for('.objects_main'))
            elif not project[1]:
                flash(message=['ОШИБКА. Проект не найден'], category='error')
                return redirect(url_for('.objects_main'))
            proj = project[1]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('contracts')
        # Список Платежей
        cursor.execute(
            f"""
                SELECT
                    t1.payment_id + 1 AS payment_id,
                    (t1.created_at + interval '1 microseconds')::timestamp without time zone::text AS created_at
                FROM payments as t1
                {where_contracts_list}
                ORDER BY t1.created_at DESC, t1.payment_id DESC
                LIMIT 1;
                """
        )
        payments = cursor.fetchone()
        if payments:
            payments = dict(payments)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=cur_name)

        # Список колонок для сортировки
        if payments:
            sort_col = {
                'col_1': [11, 1, payments['created_at']],  # Первая колонка - ASC
                'col_id': payments['payment_id']
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
        if not link_name:
            # Если проходим на странице через объект, то скрываем столбец Объект
            hidden_col.append(1)
            title = "Сводная таблица договоров. Платежи"
        else:
            title = "Таблица платежей объекта"

        return render_template('contract-payments-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                               sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                               setting_users=setting_users, nonce=get_nonce(), proj=proj,
                               title=title)
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/contract-list/card/<int:contract_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-list/card/<int:contract_id>', methods=['GET'])
@login_required
def get_card_contracts_contract(contract_id, link_name=''):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=contract_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

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
        object_id = cursor.fetchone()
        if not object_id:
            e = 'Карточка договора: Объект или договор не найден'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())

        object_id = object_id[0]

        # Список объектов
        objects_name = get_obj_list()

        # Список договоров объекта
        cursor.execute(
            """
            SELECT
                contract_id,
                contract_number
            FROM contracts
            WHERE object_id = %s
            ; """,
            [object_id]
        )
        contracts = cursor.fetchall()
        if contracts:
            for i in range(len(contracts)):
                contracts[i] = dict(contracts[i])

        # Информация о договоре
        cursor.execute(
            QUERY_CONT_INFO,
            [contract_id, contract_id, contract_id]
        )

        contract_info = cursor.fetchone()
        contract_number = contract_info['contract_number']
        contract_number_short = contract_info['contract_number_short']

        if contract_info:
            contract_info = dict(contract_info)

        # Общая стоимость субподрядных договоров объекта
        cursor.execute(
            """
            WITH t0 AS (
                SELECT 
                    t00.contract_id,
                    (t00.tow_cost + t00.tow_cost_percent * t01.contract_cost) / t01.vat_value::numeric AS tow_cost
                FROM tows_contract AS t00
                LEFT JOIN (
                    SELECT 
                        contract_id,
                        contract_cost,
                        vat_value
                    FROM contracts
                    WHERE object_id = %s AND type_id = 2
                ) AS t01 ON t00.contract_id = t01.contract_id
            )
            SELECT 
                TRIM(BOTH ' ' FROM to_char(COALESCE(ROUND(SUM(t0.tow_cost), 2), 0), '999 999 990D99 ₽')) AS tow_cost
            FROM t0
            WHERE t0.contract_id IN (
                SELECT
                    contract_id
                FROM contracts
                WHERE object_id = %s AND type_id = 2);
            """
            ,
            [object_id, object_id]
        )

        subcontractors_cost = cursor.fetchone()[0]

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']

        # Информация об изменениях статусов договора
        cursor.execute(
            QUERY_CONT_STATUS_HISTORY,
            [contract_id, ]
        )
        contract_statuses_history = cursor.fetchall()

        if contract_statuses_history:
            for i in range(len(contract_statuses_history)):
                contract_statuses_history[i] = dict(contract_statuses_history[i])

        # Список tow
        cursor.execute(
            CONTRACT_TOW_LIST,
            [contract_id, project_id, contract_id, project_id, contract_id, contract_id, object_id, contract_id,
             contract_id, contract_id, contract_id, contract_id]
        )
        tow = cursor.fetchall()

        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

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

        # Список наших компаний из таблицы our_companies
        cursor.execute("SELECT contractor_id, contractor_name, vat FROM our_companies ORDER BY contractor_id")
        our_companies = cursor.fetchall()
        if our_companies:
            for i in range(len(our_companies)):
                our_companies[i] = dict(our_companies[i])

        app_login.conn_cursor_close(cursor, conn)

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        render_html = 'contract-card-contract.html'
        # if request.path[1:].split('/')[-2] == 'card2':
        render_html = 'contract-card-contract.html'

        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile,
                               contract_info=contract_info, objects_name=objects_name, partners=partners,
                               contract_statuses=contract_statuses, tow=tow, contract_types=contract_types,
                               our_companies=our_companies, subcontractors_cost=subcontractors_cost,
                               contracts=contracts, dept_list=dept_list,
                               contract_statuses_history=contract_statuses_history,
                               nonce=get_nonce(), title=f"Договор {contract_number_short}", title1=contract_number)
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/contract-list/card/new/<link_name>/<int:contract_type>/<int:subcontract>', methods=['GET'])
@contract_app_bp.route('/contract-list/card/new/<int:contract_type>/<int:subcontract>', methods=['GET'])
@login_required
def get_card_contracts_new_contract(contract_type, subcontract, link_name=False):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description='new', user_id=user_id)

        role = app_login.current_user.get_role()
        # Вызываем ошибку, в случае, если договор создаётся по неправильной ссылке:
        # тип договора не 1 (доходный) или не 2 (расходный) И договор/допник не (0/1)
        if contract_type not in [1, 2] or subcontract not in [0, 1]:
            e = 'Ссылка на создание нового договора некорректная, закройте страницу и создаёте договор снова.'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        object_id = get_proj_id(link_name=link_name)['object_id'] if link_name else -100
        contract_id = -100

        # Находим номера всех договоров объекта (без субподрядных)
        if link_name:
            # Если создаётся договор из объекта
            cursor.execute(
                CONTRACTS_LIST_WITHOUT_SUB,
                [object_id, contract_type]
            )
            contracts = cursor.fetchall()
            if contracts:
                for i in range(len(contracts)):
                    contracts[i] = dict(contracts[i])
            else:
                # Если договоры не найдены, а создаётся допник, вызываем ошибку
                if subcontract:
                    e = 'Для выбранного типа договора нельзя создать доп.соглашение.'
                    flash(message=['Ошибка', e], category='error')
                    return render_template('page_error.html', error=[e], nonce=get_nonce())

        else:
            # Договор создаётся из сводной таблице договоров
            # Если создаётся субподрядный договор, то список договоров не должен быть пуст
            contracts = [{'contract_id': '', 'contract_number': ''}] if subcontract else None

        # Общая стоимость субподрядных договоров объекта
        if link_name:
            cursor.execute(
                """
                    SELECT
                        TRIM(BOTH ' ' FROM to_char(COALESCE(ROUND(SUM(t1.tow_cost / t2.vat_value::numeric), 2), 0), '999 999 990D99 ₽')) AS tow_cost
                    FROM tows_contract AS t1
                    LEFT JOIN (
                        SELECT contract_id, vat_value FROM contracts
                    ) AS t2 ON t1.contract_id = t2.contract_id
                    WHERE
                        t1.contract_id IN
                            (SELECT
                                contract_id
                            FROM contracts
                            WHERE object_id = %s AND type_id = 2);
                    """,
                [object_id]
            )
            subcontractors_cost = cursor.fetchone()[0]
        else:
            subcontractors_cost = 0

        # Находим project_id по object_id и список tow
        if link_name:
            project_id = get_proj_id(object_id=object_id)['project_id']

            # Список tow
            cursor.execute(
                CONTRACT_TOW_LIST,
                [contract_id, project_id, contract_id, project_id, contract_id, contract_id, object_id, contract_id,
                 contract_id, contract_id, contract_id, contract_id]
            )
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])
        else:
            tow = None

        # в случае если создаётся допник нужен список объектов у которых уже созданы договоры, иначе допник
        # не к чему привязать. Находим список объектов (из DB objects) и оставляем то с договорами
        object_name = None
        # Список объектов
        objects_name = get_obj_list()

        # Список объектов, у которых есть договоры
        cursor.execute("SELECT object_id FROM contracts GROUP BY object_id ORDER BY object_id")
        objects_plus = cursor.fetchall()
        if objects_plus:
            objects_plus = [x[0] for x in objects_plus]

        for i in objects_name[:]:
            if i['object_id'] == object_id:
                object_name = i['object_name']
            if subcontract and i['object_id'] not in objects_plus:
                objects_name.remove(i)

        # Если создаётся допник, но список объектов пуст, значит в базе ещё не создан ни один договор
        if subcontract and not objects_name:
            e1 = 'Для создания доп.соглашения в базе должен быть создан хотя бы один договор, к которому ' \
                 'можно будет привязать дополнительное соглашение.'
            e2 = 'Создайте договор, после этого можно будет создать дополнительное соглашение'
            flash(message=['Ошибка', e1, e2], category='error')
            return render_template('page_error.html', error=[e1, e2], nonce=get_nonce())

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
        type_name = None
        if contract_types:
            for i in range(len(contract_types)):
                contract_types[i] = dict(contract_types[i])
                if contract_types[i]["type_id"] == contract_type:
                    type_name = contract_types[i]["type_name"]

        # Список наших компаний из таблицы our_companies
        cursor.execute("SELECT contractor_id, contractor_name, vat FROM our_companies ORDER BY contractor_id")
        our_companies = cursor.fetchall()
        if our_companies:
            for i in range(len(our_companies)):
                our_companies[i] = dict(our_companies[i])

        # Информация о договоре
        object_id = None if object_id == -100 else object_id
        contract_info = {
            'object_id': object_id,
            'object_name': object_name,
            'contract_id': None,
            'contract_number': '',
            'date_start': None,
            'date_start_txt': '',
            'date_finish': None,
            'date_finish_txt': '',
            'type_id': contract_type,
            'contractor_id': None,
            'partner_id': None,
            'contract_description': '',
            'contract_status_id': None,
            'fot_percent': 0,
            'contract_cost': 0,
            'contract_cost_rub': '0 ₽',
            'allow': True,
            'fot_percent_txt': '',
            'contract_fot_cost_rub': '',
            'created_at': None,
            'vat_value': None,
            'vat': None,
            'undistributed_cost': 0,
            'undistributed_cost_rub': '0 ₽',
            'type_name': type_name,
            'parent_number': 'Допник' if subcontract else '',
            'parent_id': 'Допник' if subcontract else '',
            'new_contract': 'new'
        }
        contract_number = contract_info['contract_number']

        if contract_info:
            contract_info = dict(contract_info)

        app_login.conn_cursor_close(cursor, conn)

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        render_html = 'contract-card-contract.html'
        c_type = 'доходного' if contract_type == 1 else 'расходного'
        title = f"Создание нового {c_type} договора" if not subcontract else \
            f"Создание нового {c_type} доп.соглашения"
        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile,
                               contract_info=contract_info, contract_statuses_history=list(),
                               objects_name=objects_name, partners=partners,
                               contract_statuses=contract_statuses, tow=tow, contract_types=contract_types,
                               our_companies=our_companies, subcontractors_cost=subcontractors_cost,
                               contracts=contracts, dept_list=dept_list,
                               nonce=get_nonce(), title=title)

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@login_required
def check_contract_data_for_correctness(ctr_card, contract_tow_list, role, user_id):
    try:
        if role not in (1, 4, 5):
            return {
                'status': 'error',
                'description': ["Ограничен доступ для внесения нового договора"]
            }

        data_contract = dict()

        description = list()

        ctr_card['contract_id'] = int(ctr_card['contract_id']) if ctr_card['contract_id'] != 'new' else 'new'
        ctr_card['parent_id'] = int(ctr_card['parent_id']) if ctr_card['parent_id'] else None
        ctr_card['object_id'] = int(ctr_card['object_id']) if ctr_card['object_id'] else None
        ctr_card['contractor_id'] = int(ctr_card['contractor_id']) if ctr_card['contractor_id'] else None
        # ctr_card['contract_cost'] = Decimal(str(app_payment.convert_amount(ctr_card['contract_cost']))) if \
        #     ctr_card['contract_cost'] else None
        ctr_card['contract_cost'] = app_payment.convert_amount(ctr_card['contract_cost']) if ctr_card[
            'contract_cost'] else None
        ctr_card['date_start'] = date.fromisoformat(ctr_card['date_start']) if ctr_card['date_start'] else None
        ctr_card['date_finish'] = date.fromisoformat(ctr_card['date_finish']) if ctr_card['date_finish'] else None
        ctr_card['fot_percent'] = float(ctr_card['fot_percent']) if ctr_card['fot_percent'] else 0
        ctr_card['partner_id'] = int(ctr_card['partner_id']) if ctr_card['partner_id'] else None
        ctr_card['contract_status_id'] = int(ctr_card['contract_status_id']) if ctr_card['contract_status_id'] else None
        ctr_card['status_date'] = date.fromisoformat(ctr_card['status_date']) if ctr_card['status_date'] else None
        ctr_card['vat_value'] = float(ctr_card['vat_value']) if ctr_card['vat_value'] else None
        ctr_card['project_id'] = int(ctr_card['project_id']) if ctr_card['project_id'] else None

        vat = 1.2 if ctr_card['vat'] == "С НДС" else 1
        contract_cost = ctr_card['contract_cost']

        contract_id = ctr_card['contract_id']
        object_id = ctr_card['object_id']
        project_id = ctr_card['project_id']

        # Для логирования
        change_log = {
            'cc_id': contract_id,
            'cc_type': 'contract',
            'cc_action_type': None,
            'cc_description': [ctr_card['text_comment']],
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }
        change_log['cc_description'] = change_log['cc_description'] if change_log['cc_description'] else list()

        # tow_list = request.get_json()['list_towList']
        tow_list = contract_tow_list
        tow_id_list = set()
        tow_list_to_dict = dict()
        if len(tow_list):
            for i in tow_list:
                i['id'] = int(i['id']) if i['id'].isdigit() else i['id']
                # tow_id_list.add(i['id'])
                if i['type'] == '%':
                    i['percent'] = float(i['percent']) if i['percent'] not in {'None', ''} else None
                    i['cost'] = None
                elif i['type'] == '₽':
                    i['percent'] = None
                    i['cost'] = app_payment.convert_amount(i['cost']) if i['cost'] not in {'None', ''} else None
                else:
                    i['percent'] = None
                    i['cost'] = None
                i['dept_id'] = int(i['dept_id']) if i['dept_id'] else None
                i['date_start'] = date.fromisoformat(i['date_start']) if i['date_start'] else None
                i['date_finish'] = date.fromisoformat(i['date_finish']) if i['date_finish'] else None

                del i['type']

                tow_list_to_dict[i['id']] = i
            tow_id_list = set(tow_list_to_dict.keys())

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [object_id])
        object_name = cursor.fetchone()[0]

        subquery = 'ON CONFLICT DO NOTHING'
        table_tc = 'tows_contract'

        # Если новый договор, проверяем, соотносятся ли стоимости tow и стоимость договора, если ок - запись в БД
        if contract_id == 'new':
            # check_cc = 1including_tax(contract_cost, vat)
            check_cc = contract_cost
            lst_cost_tow = None
            for i in tow_list:
                check_towc = 0
                if i['cost']:
                    # check_towc = including_tax(i['cost'], vat)
                    check_towc = i['cost']
                elif i['percent']:
                    check_towc = contract_cost * i['percent'] / 100

                lst_cost_tow = i if i['cost'] or i['percent'] else lst_cost_tow
                check_cc = round(check_cc - check_towc, 2)

            if 0 > check_cc >= -0.01 and lst_cost_tow:
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] += check_cc
                    lst_cost_tow['percent'] = None
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = contract_cost * lst_cost_tow['percent'] / 100
                    lst_cost_tow['percent'] = None
                # description.extend([
                #     f"Общая стоимость видов работ договора превышает стоимость договора ({-check_cc} ₽).",
                #     f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                #     f"к котором можно произвести корректировку стоимости"
                # ])
                # return {
                #     'status': 'error',
                #     'description': description
                # }
            elif 0 > check_cc >= -0.01 and not lst_cost_tow:
                description.extend([
                    f"Общая стоимость видов работ договора превышает стоимость договора ({-check_cc} ₽).",
                    f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                    f"к котором можно произвести корректировку стоимости"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            elif check_cc < -0.01:
                description.extend([
                    f"Общая стоимость видов работ договора превышает стоимость договора ({-check_cc} ₽).",
                    f"Отвяжите лишние виды работ от договора,или перераспределите стоимости видов работ,"
                    f" или увеличьте стоимость договора"
                ])
                return {
                    'status': 'error',
                    'description': description
                }

            if check_cc > 0.01 and ctr_card['contract_status_id'] == 1:
                description.extend([
                    f"Нельзя сохранить договор со статусом \"Подписан\" с нераспределенным остатком.",
                    f"Нераспределенный остаток: {check_cc} ₽"
                ])
                return {
                    'status': 'error',
                    'description': description
                }

            cc_description = f"Добавлен договор №: {ctr_card['contract_number']} по объекту: \"{object_name}\", " \
                             f"стоимость: ({contract_cost} ₽)"
            if change_log['cc_description'] == [False]:
                change_log['cc_description'] = [cc_description]
            else:
                change_log['cc_description'].insert(0, cc_description)
            change_log['cc_value_previous'] = contract_cost
            change_log['cc_new'] = True
            change_log['cc_action_type'] = 'create'

            action = 'INSERT INTO'
            table_nc = 'contracts'
            columns_nc = ('object_id', 'type_id', 'contract_number', 'partner_id', 'contract_status_id', 'allow',
                          'contractor_id', 'fot_percent', 'contract_cost', 'auto_continue', 'date_start', 'date_finish',
                          'contract_description', 'vat_value')
            subquery_nc = " RETURNING contract_id;"
            query_nc = app_payment.get_db_dml_query(action=action, table=table_nc, columns=columns_nc,
                                                    subquery=subquery_nc)
            values_nc = [[
                ctr_card['object_id'],
                ctr_card['type_id'],
                ctr_card['contract_number'],
                ctr_card['partner_id'],
                ctr_card['contract_status_id'],
                ctr_card['allow'],
                ctr_card['contractor_id'],
                ctr_card['fot_percent'],
                contract_cost,
                ctr_card['auto_continue'],
                ctr_card['date_start'],
                ctr_card['date_finish'],
                ctr_card['contract_description'],
                ctr_card['vat_value'],
            ]]

            table_sc = 'subcontract'
            columns_sc = ('child_id', 'parent_id')
            action = 'INSERT INTO'
            query_sc = app_payment.get_db_dml_query(action=action, table=table_sc, columns=columns_sc)
            values_sc = [[
                contract_id,
                ctr_card['parent_id']
            ]]

            action = 'INSERT INTO'
            table_ncsh = 'contract_statuses_history'
            columns_ncsh = ('contract_id', 'contract_status_id', 'contract_status_date')
            query_ncsh = app_payment.get_db_dml_query(action=action, table=table_ncsh, columns=columns_ncsh)
            values_ncsh = [[
                ctr_card['contract_id'],
                ctr_card['contract_status_id'],
                ctr_card['status_date']
            ]]

            data_contract['new_contract'] = {
                'query_nc': query_nc,
                'values_nc': values_nc,
                'query_sc': query_sc,
                'values_sc': values_sc,
                'query_ncsh': query_ncsh,
                'values_ncsh': values_ncsh,
                'change_log': change_log,
                'project_id': project_id,
                'object_id': object_id,
            }

            # ДОБАВЛЕНИЕ TOW
            columns_tc_ins = ('contract_id', 'tow_id', 'tow_cost', 'tow_cost_percent', 'tow_date_start',
                              'tow_date_finish')
            tow_id_list_ins = tow_id_list
            values_tc_ins = []
            if tow_id_list_ins:
                for i in tow_list:
                    if i['id'] in tow_id_list_ins:
                        values_tc_ins.append([
                            contract_id,
                            i['id'],
                            i['cost'],
                            i['percent'],
                            i['date_start'],
                            i['date_finish']
                        ])

            if len(values_tc_ins):
                action = 'INSERT INTO'
                query_tc_ins = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_ins,
                                                            subquery=subquery)
                data_contract['new_contract']['query_tc_ins'] = query_tc_ins
                data_contract['new_contract']['values_tc_ins'] = values_tc_ins
                data_contract['new_contract']['tow_id_list_ins'] = tow_id_list_ins

            change_log['cc_new'] = True

            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # СООБЩАМЕ ОБ УСПЕХЕ. ДОЛЖЕН БЫТЬ СТАТУС
            return {
                'status': 'success',
                'data_contract': data_contract,
                'description': description
            }

        ######################################################################################
        # Действия дня не новых договоров
        ######################################################################################
        # информация о договоре
        cursor.execute(CONTRACT_INFO, [contract_id, contract_id, contract_id])
        contract_info = cursor.fetchone()

        if contract_info:
            contract_info = dict(contract_info)
        else:
            return {
                'status': 'error',
                'description': ['Договор не найден'],
            }

        # информация о статусе договора
        cursor.execute(
            """
                SELECT 
                    * 
                FROM contract_statuses_history 
                WHERE contract_act=%s AND contract_id=%s AND contract_status_id=%s AND contract_status_date=%s
            """,
            ['contract', contract_id, ctr_card['contract_status_id'], ctr_card['status_date']])
        contract_statuses_history = cursor.fetchall()

        query_ncsh = None
        values_ncsh = None
        if not contract_statuses_history:
            action = 'INSERT INTO'
            table_ncsh = 'contract_statuses_history'
            columns_ncsh = ('contract_id', 'contract_status_id', 'contract_status_date')
            query_ncsh = app_payment.get_db_dml_query(action=action, table=table_ncsh, columns=columns_ncsh)
            values_ncsh = [[
                ctr_card['contract_id'],
                ctr_card['contract_status_id'],
                ctr_card['status_date']
            ]]

        cc_description = f"Изменен договор №: {contract_info['contract_number']} по объекту: \"{object_name}\""
        if change_log['cc_description'] == [False]:
            change_log['cc_description'] = [cc_description]
        else:
            change_log['cc_description'].insert(0, cc_description)

        # Округляем значения, иногда 1.20 превращается в 1.200006545...
        contract_info['vat_value'] = round(contract_info['vat_value'], 2)
        # # Если тип НДС был изменен, пересчитываем стоимость договора с учётом НДС
        # if ctr_card['vat_value'] != contract_info['vat_value'] or contract_cost != contract_info['contract_cost']:
        #     vat = contract_info['vat_value']
        #     # ctr_card['contract_cost'] = including_tax(ctr_card['contract_cost'], vat)
        #     ctr_card['contract_cost'] = ctr_card['contract_cost']
        #     contract_cost = including_tax(contract_cost, vat)
        if ctr_card['vat_value'] == contract_info['vat_value'] and contract_cost == contract_info['contract_cost']:
            contract_cost = including_tax_reverse(contract_cost, vat)

        # Проверяем, что стоимость договора из карточки не меньше распределенного остатка
        # (то, что заактировано или оплачено по договору)
        if contract_info['distributed_contract_cost'] > contract_cost:
            if vat == 1.2:
                description = [
                    'Ошибка изменения договора',
                    'Стоимость договора не может быть меньше заактированной/оплаченной стоимости',
                    'Мин. стоимость договора с НДС: ' + contract_info['distributed_contract_cost_with_vat_rub'],
                    f"Не хватило с НДС: {round((contract_info['distributed_contract_cost'] - contract_cost), 3)}"]
            else:
                description = [
                    'Ошибка изменения договора', contract_info['distributed_contract_cost'], contract_cost,
                    'Стоимость договора не может быть меньше заактированной/оплаченной стоимости',
                    'Мин. стоимость договора: ' + contract_info['distributed_contract_cost_rub'],
                    f"Не хватило: {round((contract_info['distributed_contract_cost'] - contract_cost), 3)}"]
            return {
                'status': 'error',
                'description': description
            }

        # Информация о допнике
        cursor.execute(
            """
                SELECT
                    t1.child_id,
                    t1.parent_id
                FROM subcontract AS t1
                WHERE child_id = %s;
                """,
            [contract_id]
        )
        subcontract_info = cursor.fetchone()

        if subcontract_info:
            subcontract_info = dict(subcontract_info)

        # Список tow
        cursor.execute(
            CONTRACT_TOW_LIST1,
            [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
        )
        tow = cursor.fetchall()
        tow_dict = dict()
        db_tow_id_list = set()

        if tow:
            for i in tow:
                i = dict(i)
                if i['contract_tow'] == 'checked':
                    db_tow_id_list.add(i['tow_id'])
                tow_dict[i['tow_id']] = i

        # Список tows_contract - для проверки и удалении из tows_contract если почему-то tow не был удалён
        # при удалении его из types_of_work
        cursor.execute(
            """
                SELECT
                    tow_id
                FROM tows_contract
                WHERE contract_id = %s;""",
            [contract_id]
        )
        tows_contract = cursor.fetchall()
        tows_contract_list_del = set()

        if tows_contract:
            # tows_contract = set(tows_contract)
            for i in range(len(tows_contract)):
                if tows_contract[i][0] not in db_tow_id_list:
                    tows_contract_list_del.add(tows_contract[i][0])

        columns_c = ['contract_id']
        values_c = [[contract_id]]

        ######################################################################################
        # Определяем изменённые поля в договоре
        ######################################################################################

        # for i in contract_info.keys():
        description_lst = ["Номер договора", "Заказчик", "Статус", "Назначение", "Контрагент", "ФОТ %", "Стоимость",
                           "Автопродление", "Дата начала", "Дата окончания", "Примечание", "НДС"]
        col_list = ('contract_number', 'partner_id', 'contract_status_id', 'allow', 'contractor_id', 'fot_percent',
                    'contract_cost', 'auto_continue', 'date_start', 'date_finish', 'contract_description', 'vat_value')

        for i in col_list:
            if i == "contract_cost":
                contract_info[i] = float(contract_info[i])
            if i == "vat_value":
                contract_info[i] = round(contract_info[i], 2)
            x = col_list.index(i)

            if ctr_card[i] != contract_info[i]:
                print('         Изменена карточка договора:', ctr_card[i])
                val_type = ''
                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка договора:')
                columns_c.append(i)
                values_c[0].append(ctr_card[i])
                if i == "contract_cost":
                    change_log['cc_value_previous'] = contract_info[i]
                    change_log['cc_value_current'] = ctr_card[i]
                    val_type = ' ₽'
                elif i == "fot_percent" or i == "vat_value":
                    val_type = ' %'

                ccdc_01_card = f"{description_lst[x]}: " \
                               f"было ({contract_info[i]}{val_type}) " \
                               f"стало ({ctr_card[i]}{val_type})"
                change_log['01_card'].append(ccdc_01_card)

        # if change_log['01_card']:
        #     change_log['cc_description'].extend(change_log['01_card'])

        columns_sc = ['child_id']
        values_sc = [[contract_id]]
        if ctr_card['parent_id'] != subcontract_info['parent_id']:
            columns_sc.append('parent_id')
            values_sc[0].append(ctr_card['parent_id'])

        ######################################################################################
        # Определяем добавляемые, изменяемые и удаляемые tow
        ######################################################################################

        # СПИСОК ДОБАВЛЕНИЯ TOW
        columns_tc_ins = ('contract_id', 'tow_id', 'tow_cost', 'tow_cost_percent', 'tow_date_start',
                          'tow_date_finish')
        tow_id_list_ins = tow_id_list - db_tow_id_list
        values_tc_ins = []

        # УДАЛЕНИЕ TOW
        columns_tc_del = 'contract_id::int, tow_id::int'
        tow_id_list_del = tows_contract_list_del | db_tow_id_list - tow_id_list
        values_tc_del = []
        if tow_id_list_del:
            for i in tow_id_list_del:
                values_tc_del.append((contract_id, i))

                # Для логирования
                if not change_log['04_tow_del']:
                    change_log['04_tow_del'].append('Удаленные виды работ:')
                cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: стоимость ({tow_dict[i]['tow_cost_rub']})"
                change_log['04_tow_del'].append(cl_02_tow_del)

        # СПИСОК ИЗМЕНЕНИЯ TOW
        columns_tc_upd = [['contract_id::integer', 'tow_id::integer'], 'tow_cost::numeric',
                          'tow_cost_percent::numeric', 'tow_date_start::date', 'tow_date_finish::date']
        tmp_tow_id_list_upd = tow_id_list - tow_id_list_del - tow_id_list_ins
        tow_id_list_upd = set()
        tow_id_set_upd = set()

        if tmp_tow_id_list_upd:
            for i in tow_list:
                if i['id'] in tmp_tow_id_list_upd and i['id'] in tow_dict.keys():
                    # Для логирования
                    if not change_log['03_tow_upd']:
                        change_log['03_tow_upd'].append('Измененные виды работ:')
                    cl_03_tow_upd = f" - {tow_dict[i['id']]['tow_name']}:"

                    # # Конвертируем стоимость tow
                    # i['cost'] = including_tax(i['cost'], vat)
                    # Проверяем были ли изменены параметры tow
                    if i['date_start'] != tow_dict[i['id']]['tow_date_start']:
                        tow_id_list_upd.add(i['id'])
                        # Если была массовая замена даты (из карточки договора)
                        # if ctr_card['date_start'] != i['date_start']:
                        cl_03_tow_upd += f" Дата начала (было:{tow_dict[i['id']]['tow_date_start']}, " \
                                         f"стало:{i['date_start']})"
                    elif i['date_finish'] != tow_dict[i['id']]['tow_date_finish']:
                        tow_id_list_upd.add(i['id'])
                        # Если была массовая замена даты (из карточки договора)
                        # if ctr_card['date_finish'] != i['date_finish']:
                        cl_03_tow_upd += f" Дата окончания (было:{tow_dict[i['id']]['tow_date_finish']}, " \
                                         f"стало:{i['date_finish']})"
                    elif i['cost'] != tow_dict[i['id']]['tow_cost_raw']:
                        tow_id_list_upd.add(i['id'])
                        if tow_dict[i['id']]['tow_cost_raw']:
                            db_cost_val = tow_dict[i['id']]['tow_cost_rub']
                        else:
                            db_cost_val = tow_dict[i['id']]['tow_cost_percent_txt']
                        cl_03_tow_upd += f" Стоимость (было:{db_cost_val}, стало:{i['cost']} ₽)"
                    elif i['percent'] != tow_dict[i['id']]['tow_cost_percent_raw']:
                        tow_id_list_upd.add(i['id'])
                        if tow_dict[i['id']]['tow_cost_percent_raw']:
                            db_cost_val = tow_dict[i['id']]['tow_cost_percent_txt']
                        else:
                            db_cost_val = tow_dict[i['id']]['tow_cost_rub']
                        cl_03_tow_upd += f" % суммы (было:{db_cost_val}, стало:{i['percent']} %)"

                    # Если в изменениях ничего нет (т.к. могла измениться дата в договоре), то не указываем изменение
                    if cl_03_tow_upd != f" - {tow_dict[i['id']]['tow_name']}:":
                        change_log['03_tow_upd'].append(cl_03_tow_upd)
            if change_log['03_tow_upd'] == ['Измененные виды работ:']:
                change_log['03_tow_upd'].pop()

        check_cc = contract_cost
        tow_list_cost = 0  # Общая стоимость видов работ договора
        check_towc = 0  # Общая стоимость видов работ договора
        lst_cost_tow = None
        # Проверка на:
        #   - превышение суммы протекции (стоимости привязанных актов/платежей)
        #   - удаляемые tow не имеют протекции
        #   - превышение общей стоимости договора суммой всех стоимостей tow
        for tow_id in tow_dict.keys():
            tow_contract_cost = 0
            check_towc = 0
            # Добавление
            if tow_id in tow_id_list_ins:
                if tow_list_to_dict[tow_id]['cost']:
                    # tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                    tow_contract_cost = tow_list_to_dict[tow_id]['cost']
                elif tow_list_to_dict[tow_id]['percent']:
                    tow_contract_cost = including_tax(tow_list_to_dict[tow_id]['percent'] * contract_cost / 100, 1)
                tow_list_cost += tow_contract_cost
                check_towc = tow_contract_cost
                lst_cost_tow = tow_list_to_dict[tow_id]
                if tow_dict[tow_id]['tow_cost_protect']:
                    description.extend([
                        f"Ошибка базы данных, обратитесь к администратору",
                        f"Вид работ: id-{tow_id}, {tow_dict[tow_id]['tow_name']}",
                        f"К виду работ не должны были, но привязаны акты/платежи на сумму: "
                        f"{tow_dict[tow_id]['tow_cost_protect']} ₽"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # Обновление
            elif tow_id in tow_id_list_upd:
                # Если указана стоимость
                if tow_list_to_dict[tow_id]['cost']:
                    # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
                    if (tow_dict[tow_id]['tow_cost_raw'] and
                            tow_dict[tow_id]['tow_cost_raw'] != tow_list_to_dict[tow_id]['cost']):
                        tow_contract_cost = tow_list_to_dict[tow_id]['cost']
                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        tow_id_set_upd.add(tow_id)
                    elif not tow_dict[tow_id]['tow_cost_raw']:
                        tow_contract_cost = tow_list_to_dict[tow_id]['cost']
                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        tow_id_set_upd.add(tow_id)
                    # Никаких изменений у tow не было
                    else:
                        tow_contract_cost = 0
                        if tow_dict[tow_id]['tow_cost_raw']:
                            tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                        elif tow_dict[tow_id]['tow_cost_percent_raw']:
                            tow_contract_cost = round(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 2)

                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost

                # Указаны проценты
                elif tow_list_to_dict[tow_id]['percent']:
                    if (tow_dict[tow_id]['tow_cost_percent_raw'] and
                            tow_dict[tow_id]['tow_cost_percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                        tow_contract_cost = round(contract_cost * tow_list_to_dict[tow_id]['percent'] / 100, 2)
                        check_towc = tow_contract_cost
                        tow_list_cost += tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        tow_id_set_upd.add(tow_id)
                    elif (tow_list_to_dict[tow_id]['percent'] and
                          tow_dict[tow_id]['tow_cost_percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                        tow_contract_cost = round(contract_cost * tow_list_to_dict[tow_id]['percent'] / 100, 2)
                        check_towc = tow_contract_cost
                        tow_list_cost += tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                    # Никаких изменений у tow не было
                    else:
                        tow_contract_cost = 0
                        if tow_dict[tow_id]['tow_cost_raw']:
                            tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                        elif tow_dict[tow_id]['tow_cost_percent_raw']:
                            tow_contract_cost = round(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 2)

                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost

                if tow_dict[tow_id]['tow_cost_protect'] > check_towc:
                    missing_amount = round(tow_dict[tow_id]['tow_cost_protect'] - check_towc, 2)
                    if missing_amount <= 0:
                        missing_amount = tow_dict[tow_id]['tow_cost_protect'] - check_towc
                    description.extend([
                        f"Вид работ: id-{tow_id}, {tow_dict[tow_id]['tow_name']}",
                        f"Стоимость вида работ договора должна быть больше:",
                        f"К виду работ привязаны акты/платежи на сумму: {tow_dict[tow_id]['tow_cost_protect']} ₽",
                        f"Стоимость по договору: {check_towc} ₽",
                        f"Недостающая сумма: {missing_amount} ₽"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # Удаление
            elif tow_id in tow_id_list_del:
                if tow_dict[tow_id]['tow_protect']:
                    description.extend([
                        "Нельзя отвязать вид работ от договора",
                        f"Вид работ: id-{tow_id}, {tow_dict[tow_id]['tow_name']}",
                        f"К удаляемому виду работ был {tow_dict[tow_id]['tow_protect'].lower()}"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # tow договора не был отредактирован
            elif tow_dict[tow_id]['contract_tow']:
                if tow_dict[tow_id]['tow_cost_raw']:
                    tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                elif tow_dict[tow_id]['tow_cost_percent_raw']:
                    tow_contract_cost = round(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 2)
                check_towc = tow_contract_cost

            check_cc = check_cc - check_towc

        if check_cc < -0.01:
            check_cc = round(check_cc, 2)
            if check_cc <= -1:
                description.extend([
                    f"1Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                    f"Скорректируйте стоимость договора или видов работ"])
                return {
                    'status': 'error',
                    'description': description
                }
            elif lst_cost_tow:
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] += check_cc
                    description.extend([
                        f"2Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = round(lst_cost_tow['percent'] * contract_cost / 100, 2) + check_cc
                    lst_cost_tow['percent'] = None
                    description.extend([
                        f"3Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                else:
                    description.extend([
                        f"4Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
            elif not lst_cost_tow:
                description.extend([
                    f"4Общая стоимость видов работ договора превышает стоимость договора на {-check_cc} ₽.",
                    f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                    f"в котором можно произвести корректировку стоимости"
                ])
                return {
                    'status': 'error',
                    'description': description
                }

        if check_cc > 0.01 and ctr_card['contract_status_id'] == 1:
            description.extend([
                f"Нельзя сохранить договор со статусом \"Подписан\" с нераспределенным остатком.",
                f"Нераспределенный остаток: {check_cc} ₽"
            ])
            return {
                'status': 'error',
                'description': description
            }

        values_tc_ins = []
        # if tow_id_list_ins:
        for tow_id in tow_id_list_ins:
            values_tc_ins.append([
                contract_id,
                tow_id,
                tow_list_to_dict[tow_id]['cost'],
                tow_list_to_dict[tow_id]['percent'],
                tow_list_to_dict[tow_id]['date_start'],
                tow_list_to_dict[tow_id]['date_finish']
            ])
            # Для логирования
            if tow_id in tow_dict.keys():
                tow_name = tow_dict[tow_id]['tow_name']

                if not change_log['02_tow_ins']:
                    change_log['02_tow_ins'].append('Добавление видов работ:')
                if tow_list_to_dict[tow_id]['cost']:
                    cl_02_tow_ins = f" !- {tow_name}: стоимость ({tow_list_to_dict[tow_id]['cost']} ₽)"
                elif tow_list_to_dict[tow_id]['percent']:
                    cl_02_tow_ins = f" !- {tow_name}: % суммы ({tow_list_to_dict[tow_id]['percent']} %)"
                else:
                    cl_02_tow_ins = f" !- {tow_name}: стоимость не указана"
                change_log['02_tow_ins'].append(cl_02_tow_ins)

        # ОБНОВЛЕНИЕ TOW
        values_tc_upd = []
        if tmp_tow_id_list_upd:
            for i in tow_list:
                if i['id'] in tow_id_list_upd:
                    values_tc_upd.append([
                        contract_id,
                        i['id'],
                        i['cost'],
                        i['percent'],
                        i['date_start'],
                        i['date_finish']
                    ])

        change_log['cc_action_type'] = 'update'

        data_contract['old_contract'] = {
            'contract_id': contract_id,
            'change_log': change_log,
            'project_id': project_id,
            'object_id': object_id,
        }

        # Для contracts
        if len(columns_c) > 1:
            query_c = app_payment.get_db_dml_query(action='UPDATE', table='contracts', columns=columns_c)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ save_contract', query_c)
            data_contract['old_contract']['columns_c'] = {
                'query_c': query_c,
                'values_c': values_c
            }
        if len(columns_sc) > 1:
            query_sc = app_payment.get_db_dml_query(action='UPDATE', table='subcontract', columns=columns_sc)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ save_contract sub', query_sc)
            data_contract['old_contract']['columns_sc'] = {
                'query_sc': query_sc,
                'values_sc': values_sc
            }
        if query_ncsh:
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ contract_statuses_history', query_ncsh)
            data_contract['old_contract']['columns_ncsh'] = {
                'query_ncsh': query_ncsh,
                'values_ncsh': values_ncsh
            }
        # Для tows_contract
        if len(values_tc_ins):
            action = 'INSERT INTO'
            query_tc_ins = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_ins,
                                                        subquery=subquery)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ INSERT INTO', query_tc_ins, values_tc_ins)
            data_contract['old_contract']['values_tc_ins'] = {
                'query_tc_ins': query_tc_ins,
                'values_tc_ins': values_tc_ins,
                'tow_id_list_ins': tow_id_list_ins,
            }

        if len(values_tc_upd):
            action = 'UPDATE DOUBLE'
            query_tc_upd = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_upd)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ UPDATE DOUBLE', query_tc_upd)
            pprint(values_tc_upd)
            data_contract['old_contract']['values_tc_upd'] = {
                'query_tc_upd': query_tc_upd,
                'values_tc_upd': values_tc_upd
            }

        if len(values_tc_del):
            action = 'DELETE'
            query_tc_del = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_del,
                                                        subquery=subquery)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ DELETE', query_tc_del, values_tc_del)
            data_contract['old_contract']['values_tc_del'] = {
                'query_tc_del': query_tc_del,
                'values_tc_del': values_tc_del
            }

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # СООБЩАМЕ ОБ УСПЕХЕ. ДОЛЖЕН БЫТЬ СТАТУС
        return {
            'status': 'success',
            'data_contract': data_contract,
            'description': description,
        }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': 'error',
            'description': [msg_for_user],
        }


@login_required
def save_contract(new_contract=None, old_contract=None):
    try:
        if new_contract:
            contract_id = 'new'
            try:
                user_id = new_contract['user_id']
            except:
                user_id = None
        else:
            try:
                contract_id = old_contract['contract_id']
            except:
                contract_id = None
            try:
                user_id = old_contract['user_id']
            except:
                user_id = None

        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=contract_id, user_id=user_id)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        description = list()
        ######################################################################################
        # НОВЫЙ ДОГОВОР
        ######################################################################################
        if new_contract:
            query_nc = new_contract['query_nc']
            values_nc = new_contract['values_nc']
            query_sc = new_contract['query_sc']
            values_sc = new_contract['values_sc']
            query_ncsh = new_contract['query_ncsh']
            values_ncsh = new_contract['values_ncsh']
            query_tc_ins = None
            values_tc_ins = None
            # tow_id_list_ins = new_contract['tow_id_list_ins']

            object_id = new_contract['object_id']
            project_id = new_contract['project_id']
            change_log = new_contract['change_log']

            user_id = new_contract['user_id']

            if 'query_tc_ins' in new_contract.keys():
                query_tc_ins = new_contract['query_tc_ins']
                values_tc_ins = new_contract['values_tc_ins']

            # Добавляем новый договор в таблицу 'contracts'
            execute_values(cursor, query_nc, values_nc)
            contract_id = cursor.fetchone()[0]
            conn.commit()
            new_contract = True

            # Добавляем запись в таблицу 'subcontract'
            values_sc[0][0] = contract_id
            execute_values(cursor, query_sc, values_sc)
            conn.commit()

            # Добавляем новый договор в таблицу 'contract_statuses_history'
            values_ncsh[0][0] = contract_id
            execute_values(cursor, query_ncsh, values_ncsh)
            conn.commit()

            # Добавляем лог
            change_log['cc_id'] = contract_id

            # ДОБАВЛЕНИЕ TOW
            if values_tc_ins:
                for i in values_tc_ins:
                    i[0] = contract_id

                execute_values(cursor, query_tc_ins, values_tc_ins)
                conn.commit()

                if not change_log['02_tow_ins']:
                    cursor.execute(
                        CONTRACT_TOW_LIST1,
                        [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
                    )
                    tow = cursor.fetchall()
                    tow_dict = dict()
                    db_tow_id_list = set()
                    if tow:
                        for i in tow:
                            i = dict(i)
                            if i['contract_tow'] == 'checked':
                                db_tow_id_list.add(i['tow_id'])
                            tow_dict[i['tow_id']] = i
                    for i in values_tc_ins:
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        if tow_dict[i[1]]['tow_cost_raw']:
                            cl_02_tow_ins = f" - {tow_dict[i[1]]['tow_name']}: стоимость " \
                                            f"({tow_dict[i[1]]['tow_cost_raw']} ₽)"
                        elif tow_dict[i[1]]['tow_cost_percent_raw']:
                            cl_02_tow_ins = f" - {tow_dict[i[1]]['tow_name']}: стоимость " \
                                            f"({tow_dict[i[1]]['tow_cost_percent_raw']} %)"
                        else:
                            cl_02_tow_ins = f" - {tow_dict[i[1]]['tow_name']}: стоимость не указана"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)
            app_login.conn_cursor_close(cursor, conn)

            change_log['user_id'] = user_id
            add_contracts_change_log(change_log)

            description.append('Договор: Сохранён в базе данных')
            # Return the updated data as a response
            return {
                'status': 'success',
                'description': description,
                'contract_id': contract_id
            }

        ######################################################################################
        # СТАРЫЙ ДОГОВОР
        ######################################################################################
        elif old_contract:
            contract_id = old_contract['contract_id']
            query_nc = None
            values_nc = None
            query_sc = None
            values_sc = None
            query_c = None
            values_c = None
            query_ncsh = None
            values_ncsh = None
            query_tc_ins = None
            values_tc_ins = None
            query_tc_upd = None
            values_tc_upd = None
            query_tc_del = None
            values_tc_del = None
            c_keys = set(old_contract.keys())

            object_id = old_contract['object_id']
            project_id = old_contract['project_id']
            change_log = old_contract['change_log']

            user_id = old_contract['user_id']

            # Для contracts UPDATE
            if 'columns_c' in c_keys:
                query_c = old_contract['columns_c']['query_c']
                values_c = old_contract['columns_c']['values_c']
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^ save_contract', query_c)
                execute_values(cursor, query_c, values_c)
                conn.commit()
            # Для subcontract UPDATE
            if 'columns_sc' in c_keys:
                query_sc = old_contract['columns_sc']['query_sc']
                values_sc = old_contract['columns_sc']['values_sc']
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^ save_contract sub', query_sc)
                execute_values(cursor, query_sc, values_sc)
                conn.commit()
            # Для contract_statuses_history INSERT INTO
            if 'columns_ncsh' in c_keys:
                query_ncsh = old_contract['columns_ncsh']['query_ncsh']
                values_ncsh = old_contract['columns_ncsh']['values_ncsh']
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^ contract_statuses_history', query_ncsh)
                execute_values(cursor, query_ncsh, values_ncsh)
                conn.commit()
            # Для tows_contract INSERT INTO
            if 'values_tc_ins' in c_keys:
                query_tc_ins = old_contract['values_tc_ins']['query_tc_ins']
                values_tc_ins = old_contract['values_tc_ins']['values_tc_ins']
                execute_values(cursor, query_tc_ins, values_tc_ins)

                # Список tow
                if values_tc_ins:
                    if not change_log['02_tow_ins']:
                        cursor.execute(
                            CONTRACT_TOW_LIST1,
                            [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
                        )
                        tow = cursor.fetchall()
                        tow_dict = dict()
                        db_tow_id_list = set()
                        if tow:
                            for i in tow:
                                i = dict(i)
                                if i['contract_tow'] == 'checked':
                                    db_tow_id_list.add(i['tow_id'])
                                tow_dict[i['tow_id']] = i
                        for i in values_tc_ins:
                            if not change_log['02_tow_ins']:
                                change_log['02_tow_ins'].append('Добавление видов работ:')
                            if tow_dict[i[1]]['tow_cost_raw']:
                                cl_02_tow_ins = (f" - {tow_dict[i[1]]['tow_name']}: стоимость "
                                                 f"({tow_dict[i[1]]['tow_cost_raw']} ₽)")
                            elif tow_dict[i[1]]['tow_cost_percent_raw']:
                                cl_02_tow_ins = (f" - {tow_dict[i[1]]['tow_name']}: стоимость "
                                                 f"({tow_dict[i[1]]['tow_cost_percent_raw']} %)")
                            else:
                                cl_02_tow_ins = f" - {tow_dict[i[1]]['tow_name']}: стоимость не указана"
                            change_log['02_tow_ins'].append(cl_02_tow_ins)

            # Для tows_contract UPDATE DOUBLE
            if 'values_tc_upd' in c_keys:
                query_tc_upd = old_contract['values_tc_upd']['query_tc_upd']
                values_tc_upd = old_contract['values_tc_upd']['values_tc_upd']
                execute_values(cursor, query_tc_upd, values_tc_upd)
            # Для tows_contract DELETE
            if 'values_tc_del' in c_keys:
                query_tc_del = old_contract['values_tc_del']['query_tc_del']
                values_tc_del = old_contract['values_tc_del']['values_tc_del']
                execute_values(cursor, query_tc_del, (values_tc_del,))
            if 'values_tc_ins' in c_keys or 'values_tc_upd' in c_keys or 'values_tc_del' in c_keys:
                conn.commit()

            app_login.conn_cursor_close(cursor, conn)

            # Если не было данных
            if {'columns_c', 'columns_sc', 'values_tc_ins', 'values_tc_upd', 'values_tc_del'}.isdisjoint(c_keys):
                status = 'success'
                description.append('Договор: Договор и виды работ договора не были изменены')
            else:
                status = 'success'
                description.append('Договор: Изменения сохранены')

            # # добавляем запись в change log
            # cc_description = list()
            # cc_value_previous = 100
            # cc_value_current = 120

            # if 'columns_c' in c_keys:
            #     cc_description.extend(['auto: Обновлён договор'])
            # if 'columns_sc' in c_keys:
            #     cc_description.extend(['auto: Изменен subcontract'])
            # if 'values_tc_ins' in c_keys:
            #     cc_description.extend(['auto: Добавлены виды работ в договор'])
            # if 'values_tc_upd' in c_keys:
            #     cc_description.extend(['auto: Обновлены виды работ договора'])
            # if 'values_tc_del' in c_keys:
            #     cc_description.extend(['auto: Удалены виды работ из договор'])
            # cc_description.extend([])
            # data_ccl = {
            #     'cc_id': contract_id,
            #     'cc_type': 'contract',
            #     'cc_description': cc_description,
            #     'cc_value_previous': cc_value_previous,
            #     'cc_value_current': cc_value_current
            # }
            change_log['user_id'] = user_id
            add_contracts_change_log(change_log)

            # Return the updated data as a response
            return {
                'status': status,
                'description': description,
                'contract_id': contract_id
            }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': 'error',
            'description': [msg_for_user],
        }


@contract_app_bp.route('/contract-acts-list/card/<int:act_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-acts-list/card/<int:act_id>', methods=['GET'])
@login_required
def get_card_contracts_act(act_id, link_name=''):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=act_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        act_id = act_id
        link_name = link_name

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Находим object_id, по нему находим список tow
        cursor.execute(FIND_OBJ_BY_ACT, [act_id])
        object_id = cursor.fetchone()

        if not object_id:
            e = 'Карточка акта: Объект или договор не найден'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())

        contract_id, object_id = object_id[0], object_id[1]

        # Список объектов
        objects_name = get_obj_list()

        # Список id проектов у которых есть договоры
        cursor.execute(
            """
                SELECT
                    object_id
                FROM contracts
                GROUP BY object_id
                ORDER BY object_id;
                """
        )
        proj_list = cursor.fetchall()
        proj_list = set([x[0] for x in proj_list])

        # Объекты, у которых есть договоры
        objects = list()

        if objects_name:
            for i in objects_name:
                if i['object_id'] in proj_list:
                    objects.append(i)

        # Список договоров объекта
        # Доходные договоры
        cursor.execute(
            CONTRACTS_LIST,
            [object_id, 1]
        )
        contracts_income = cursor.fetchall()
        if contracts_income:
            for i in range(len(contracts_income)):
                contracts_income[i] = dict(contracts_income[i])

        # Расходные договоры
        cursor.execute(
            CONTRACTS_LIST,
            [object_id, 2]
        )
        contracts_expenditure = cursor.fetchall()
        if contracts_expenditure:
            for i in range(len(contracts_expenditure)):
                contracts_expenditure[i] = dict(contracts_expenditure[i])

        # Информация об акте
        cursor.execute(
            QUERY_ACT_INFO,
            [act_id, contract_id, act_id, act_id]
        )
        act_info = cursor.fetchone()
        contract_number = act_info['contract_number']
        act_number = act_info['act_number']
        act_number_short = act_info['act_number_short']

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']

        # Список tow акта
        cursor.execute(
            ACT_TOW_LIST,
            [project_id, project_id, contract_id, contract_id, act_id, contract_id, contract_id, act_id, act_id]
        )
        tow = cursor.fetchall()

        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

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

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        render_html = 'contract-card-act.html'

        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile, act_info=act_info,
                               objects_name=objects_name, act_statuses=contract_statuses, tow=tow,
                               act_types=contract_types,
                               contracts_income=contracts_income, contracts_expenditure=contracts_expenditure,
                               nonce=get_nonce(), dept_list=dept_list,
                               title=f"Акт № {act_number_short} по договору: {contract_number}", title1=act_number)

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/contract-acts-list/card/new/<link_name>', methods=['GET'])
@contract_app_bp.route('/contract-acts-list/card/new', methods=['GET'])
@login_required
def get_card_contracts_new_act(link_name=False):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description='new', user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        object_id = get_proj_id(link_name=link_name)['object_id'] if link_name else -100
        contract_id = -100
        act_id = -100

        # Находим номера всех договоров объекта (без субподрядных)
        if link_name:
            # Если создаётся договор из объекта
            # Доходные договоры
            cursor.execute(
                CONTRACTS_LIST,
                [object_id, 1]
            )
            contracts_income = cursor.fetchall()
            if contracts_income:
                for i in range(len(contracts_income)):
                    contracts_income[i] = dict(contracts_income[i])

            # Расходные договоры
            cursor.execute(
                CONTRACTS_LIST,
                [object_id, 2]
            )
            contracts_expenditure = cursor.fetchall()
            if contracts_expenditure:
                for i in range(len(contracts_expenditure)):
                    contracts_expenditure[i] = dict(contracts_expenditure[i])

        else:
            # Договор создаётся из сводной таблице договоров
            contracts_income = []
            contracts_expenditure = []

        tow = None
        object_name = None
        objects_name = get_obj_list()

        # Список объектов, у которых есть договоры
        cursor.execute("SELECT object_id FROM contracts GROUP BY object_id ORDER BY object_id")
        objects_plus = cursor.fetchall()
        if objects_plus:
            objects_plus = [x[0] for x in objects_plus]
        for i in objects_name[:]:
            if i['object_id'] == object_id:
                object_name = i['object_name']
            if i['object_id'] not in objects_plus:
                objects_name.remove(i)

        # Список статусов
        cursor.execute("SELECT contract_status_id, status_name  FROM contract_statuses ORDER BY status_name")
        contract_statuses = cursor.fetchall()
        if contract_statuses:
            for i in range(len(contract_statuses)):
                contract_statuses[i] = dict(contract_statuses[i])

        # Список типов
        if link_name:
            cursor.execute(
                """
                    SELECT 
                        DISTINCT t1.type_id, t2.type_name
                    FROM contracts AS t1
                    LEFT JOIN contract_types AS t2 ON t1.type_id = t2.type_id
                    WHERE t1.object_id = %s
                    ORDER BY t2.type_name;
                """,
                [object_id]
            )
            contract_types = cursor.fetchall()
        else:
            cursor.execute("SELECT type_id, type_name  FROM contract_types ORDER BY type_name")
            contract_types = cursor.fetchall()
        if contract_types:
            for i in range(len(contract_types)):
                contract_types[i] = dict(contract_types[i])
        type_name = None

        # Информация о договоре
        object_id = None if object_id == -100 else object_id
        act_info = {
            'object_id': object_id,
            'object_name': object_name,
            'contract_id': None,
            'contract_number': '',
            'date_start': None,
            'date_start_txt': '',
            'date_finish': None,
            'date_finish_txt': '',
            'type_id': None,
            'contractor_id': None,
            'partner_id': None,
            'contract_description': '',
            'contract_status_id': None,
            'fot_percent': 0,
            'act_cost': 0,
            'act_cost_rub': '0 ₽',
            'act_cost_vat': 0,
            'contract_cost_vat': 0,
            'contract_cost': 0,
            'contract_cost_rub': '0 ₽',
            'undistributed_contract_cost': 0,
            'allow': True,
            'fot_percent_txt': '',
            'contract_fot_cost_rub': '',
            'created_at': None,
            'vat_value': None,
            'vat': None,
            'undistributed_cost': 0,
            'undistributed_cost_rub': '0 ₽',
            'type_name': type_name,
            'parent_number': '',
            'parent_id': '',
            'new_act': 'new'
        }
        act_number = act_info['contract_number']

        if act_info:
            act_info = dict(act_info)

        app_login.conn_cursor_close(cursor, conn)

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # if request.path[1:].split('/')[-2] == 'card2':
        render_html = 'contract-card-act.html'
        title = "Создание нового акта"

        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile, act_info=act_info,
                               objects_name=objects_name, act_statuses=contract_statuses, tow=tow,
                               act_types=contract_types,
                               contracts_income=contracts_income, contracts_expenditure=contracts_expenditure,
                               dept_list=dept_list, nonce=get_nonce(), title=title)

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/change-object-from-act/<int:object_id>', methods=['POST'])
@login_required
def change_object_from_act(object_id):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Доходные договоры
        cursor.execute(
            CONTRACTS_LIST,
            [object_id, 1]
        )
        contracts_income = cursor.fetchall()
        if contracts_income:
            for i in range(len(contracts_income)):
                contracts_income[i] = dict(contracts_income[i])

        # Расходные договоры
        cursor.execute(
            CONTRACTS_LIST,
            [object_id, 2]
        )
        contracts_expenditure = cursor.fetchall()
        if contracts_expenditure:
            for i in range(len(contracts_expenditure)):
                contracts_expenditure[i] = dict(contracts_expenditure[i])

        # Список типов
        cursor.execute("""
                SELECT 
                    DISTINCT t1.type_id, t2.type_name
                FROM contracts AS t1
                LEFT JOIN contract_types AS t2 ON t1.type_id = t2.type_id
                WHERE t1.object_id = %s
                ORDER BY t2.type_name
                ;""",
                       [object_id]
                       )
        act_types = cursor.fetchall()
        if act_types:
            for i in range(len(act_types)):
                act_types[i] = dict(act_types[i])

        # Return the data as a response
        return jsonify({
            'contracts_income': contracts_income,
            'contracts_expenditure': contracts_expenditure,
            'act_types': act_types,
            'status': 'success'
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/change-contract-from-act/<int:object_id>/<int:type_id>/<int:contract_id>', methods=['POST'])
@login_required
def change_contract_from_act(object_id: int, type_id: int, contract_id: int):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        act_id = -1

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Проверка, что объект, тип договора и договор указаны правильно
        cursor.execute(
            QUERY_CONT_INFO_FOR_ACT,
            [contract_id, act_id, contract_id, object_id, type_id]
        )
        check_con_info = cursor.fetchall()
        if check_con_info:
            if len(check_con_info) == 1:
                check_con_info = dict(check_con_info[0])
            else:
                return jsonify({
                    'status': 'error',
                    'description': ['Проверка договора не пройдена. rev-1'],
                })
        else:
            app_login.conn_cursor_close(cursor, conn)
            return jsonify({
                'status': 'error',
                'description': ['Проверка договора не пройдена. rev-2'],
            })
        # Список tow акта
        cursor.execute(
            ACT_TOW_LIST,
            [project_id, project_id, contract_id, contract_id, act_id, contract_id, contract_id, act_id, act_id]
        )
        tow = cursor.fetchall()

        app_login.conn_cursor_close(cursor, conn)

        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Return the data as a response
        return jsonify({
            'check_con_info': check_con_info,
            'tow': tow,
            'dept_list': dept_list,
            'status': 'success'
        })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/save_act', methods=['POST'])
@login_required
def save_act():
    try:
        try:
            user_id = app_login.current_user.get_id()
        except:
            user_id = None
        try:
            act_id = request.get_json()['act_id']
        except:
            act_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=act_id, user_id=user_id)

        description = list()

        object_id = request.get_json()['object_id']
        type_id = request.get_json()['act_type']
        contract_id = request.get_json()['contract_id']
        act_number = request.get_json()['act_number']
        date_start = request.get_json()['date_start']
        status_id = request.get_json()['status_id']
        act_cost = request.get_json()['act_cost']
        tow_list = request.get_json()['list_towList']
        text_comment = request.get_json()['text_comment']

        act_id = int(act_id) if act_id != 'new' else 'new'
        object_id = int(object_id) if object_id else None
        type_id = int(type_id) if type_id else None
        contract_id = int(contract_id) if contract_id else None
        date_start = date.fromisoformat(date_start) if date_start else None
        act_cost = app_payment.convert_amount(act_cost) if act_cost else None
        status_id = int(status_id) if status_id else None

        # Для логирования
        change_log = {
            'cc_id': act_id,
            'cc_type': 'act',
            'cc_action_type': None,
            'cc_description': [text_comment],
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }
        change_log['cc_description'] = change_log['cc_description'] if change_log['cc_description'] else list()

        if not object_id or not type_id or not contract_id or not date_start or not act_cost or not status_id:
            description.extend(['В данных акта не хватает информации'])

            not_enough_lst = ['Объект', 'Тип акта', 'Договор', 'Дата акта', 'Стоимость акта', 'Статус акта']
            tmp = [not object_id, not type_id, not contract_id, not date_start, not act_cost, not status_id]
            not_enough = '('
            for i in range(len(tmp)):
                if tmp[i]:
                    not_enough += f'{not_enough_lst[i]}, '
            not_enough = not_enough[:-2]
            not_enough += ')'

            description.append(not_enough)

            return jsonify({
                'status': 'error',
                'description': description,
            })

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [object_id])
        object_name = cursor.fetchone()[0]

        tmp_act_id = act_id if act_id != 'new' else -1
        cursor.execute(
            QUERY_CONT_INFO_FOR_ACT,
            [contract_id, tmp_act_id, contract_id, object_id, type_id]
        )
        check_con_info = cursor.fetchall()
        if check_con_info:
            if len(check_con_info) == 1:
                check_con_info = dict(check_con_info[0])
            else:
                description.extend(['Проверка договора не пройдена. rev-1'])
                return jsonify({
                    'status': 'error',
                    'description': description,
                })
        else:
            description.extend(['Проверка договора не пройдена. rev-2'])
            return jsonify({
                'status': 'error',
                'description': description,
            })

        vat = check_con_info['vat_value']

        check_con_info['undistributed_contract_cost'] = float(check_con_info['undistributed_contract_cost']) if (
            check_con_info)['undistributed_contract_cost'] else check_con_info['undistributed_contract_cost']

        tow_id_list = set()
        tow_list_to_dict = dict()
        if len(tow_list):
            for i in tow_list:
                i['id'] = int(i['id']) if i['id'] else None
                # tow_id_list.add(i['id'])
                if i['type'] == '%':
                    i['percent'] = float(i['percent']) if i['percent'] != 'None' else None
                    i['cost'] = None
                elif i['type'] == '₽':
                    i['percent'] = None
                    i['cost'] = app_payment.convert_amount(i['cost']) if i['cost'] != 'None' else None
                else:
                    i['percent'] = None
                    i['cost'] = None

                del i['type']

                tow_list_to_dict[i['id']] = i
            tow_id_list = set(tow_list_to_dict.keys())

        # Проверка, что стоимость акта не была изменена
        act_info = None
        if act_id != 'new':
            # Информация об акте
            cursor.execute(
                QUERY_ACT_INFO,
                [act_id, contract_id, act_id, act_id]
            )
            act_info = cursor.fetchone()
            if not act_info:
                return jsonify({
                    'status': 'error',
                    'description': ['Акт не найден'],
                })
            # if act_info['act_cost'] != act_cost:
            #     act_cost = including_tax(act_cost, check_con_info['vat_value'])
        # else:
        #     act_cost = including_tax(act_cost, check_con_info['vat_value'])

        # Проверяем что незаактированный остаток договора не меньше стоимости акта
        if check_con_info['undistributed_contract_cost'] < act_cost:
            is_vat = ' с НДС' if vat == 1.2 else ''
            check_ac = round(act_cost - check_con_info['undistributed_contract_cost'], 2)
            description.extend([
                "Незаактированный остаток договора меньше стоимости акта",
                f"Остаток{is_vat}: {check_con_info['undistributed_contract_cost']} ₽",
                f"Стоимость акта{is_vat}: {act_cost} ₽",
                f"Не хватает: {check_ac} ₽"
            ])
            return jsonify({
                'status': 'error',
                'description': description,
            })

        contract_cost = float(check_con_info['contract_cost'])
        tmp_act_id = -1 if act_id == 'new' else act_id
        # Список tow акта
        cursor.execute(
            ACT_TOW_LIST,
            [project_id, project_id, contract_id, contract_id, tmp_act_id, contract_id, contract_id, tmp_act_id,
             tmp_act_id]
        )
        tow = cursor.fetchall()
        tow_dict = dict()

        # Проверяем, незаактированный остаток договора не меньше стоимости акта, а так же проверяем актуальность списка tow
        db_tow_id_list = set()
        if tow:
            for i in tow:
                tow_list_cost = 0  # Общая стоимость видов работ акта
                i = dict(i)
                if i['act_tow_id']:
                    db_tow_id_list.add(i['tow_id'])

                # Если к акту привязали tow (указали стоимость tow)
                if len(tow_list_to_dict):
                    tow_dict[i['tow_id']] = i
                    if i['tow_id'] in tow_list_to_dict.keys():
                        tow_act_cost = tow_list_to_dict[i['tow_id']]['cost'] if tow_list_to_dict[i['tow_id']]['cost'] \
                            else round(tow_list_to_dict[i['tow_id']]['percent'] * act_cost / 100, 2)
                        tow_list_cost += tow_act_cost

                        tmp_tow_remaining_cost = round(i['tow_remaining_cost_with_vat'] + i['tow_act_cost'] -
                                                       tow_act_cost, 2)

                        if tmp_tow_remaining_cost < 0:
                            x = round(tow_act_cost - i['tow_remaining_cost_with_vat'], 2)
                            description.extend([
                                f"id:{i['tow_id']} - \"{i['tow_name']}\"",
                                "Незаактированный остаток вида работ договора меньше стоимости вида работ акта",
                                f"Остаток вида работ: {i['tow_remaining_cost_with_vat']} ₽",
                                f"Стоимость вида работ: {tow_act_cost} ₽",
                                f"Не хватает:  {x} ₽"
                            ])
                            return jsonify({
                                'status': 'error',
                                'description': description,
                            })
            else:
                for i in tow:
                    i = dict(i)
                    tow_dict[i['tow_id']] = i

        if tow_list_to_dict.keys() - tow_dict.keys():
            description.extend([
                "Список видов работ не актуален",
                "За время работы с актом изменился список видов работ договора.",
                "Обновите страницу и повторите попытку снова"
            ])
            return {
                'status': 'error',
                'description': description
            }

        subquery = 'ON CONFLICT DO NOTHING'
        table_ta = 'tows_act'

        # Если новый акт, проверяем, соотносятся ли стоимости tow и стоимость акта, если ок - запись в БД
        if act_id == 'new':
            check_ac = act_cost
            lst_cost_tow = None

            values_ac_ins = []
            if len(tow_list):
                for i in tow_list:
                    check_towc = 0
                    if i['cost']:
                        check_towc = i['cost']
                    elif i['percent']:
                        check_towc = round(act_cost * i['percent'] / 100, 2)

                    lst_cost_tow = i if i['cost'] or i['percent'] else lst_cost_tow
                    check_ac = round(check_ac - check_towc, 2)

                    values_ac_ins.append([
                        act_id,
                        i['id'],
                        i['cost'],
                        i['percent']
                    ])

                if 0 > check_ac >= -0.01 and lst_cost_tow:
                    if lst_cost_tow['cost']:
                        lst_cost_tow['cost'] += check_ac
                    elif lst_cost_tow['percent']:
                        lst_cost_tow['cost'] = round(act_cost * lst_cost_tow['percent'] / 100, 2)
                        lst_cost_tow['percent'] = None
                    description.extend([
                        f"Общая стоимость видов работ акта превышает стоимость акта ({check_ac} ₽).",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif 0 > check_ac >= -0.01 and not lst_cost_tow:
                    description.extend([
                        f"Общая стоимость видов работ акта превышает стоимость акта ({check_ac} ₽).",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif check_ac < -0.01:
                    description.extend([
                        f"Общая стоимость видов работ акта превышает стоимость акта ({check_ac} ₽).",
                        f"Отвяжите лишние виды работ от договора,или перераспределите стоимости видов работ,"
                        f" или увеличьте стоимость акта"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # Добавляем новый акт
            action = 'INSERT INTO'
            table_na = 'acts'
            columns_na = ('contract_id', 'act_number', 'contract_status_id', 'act_cost', 'act_date')
            subquery_na = " RETURNING act_id;"
            print(action)
            query_na = app_payment.get_db_dml_query(action=action, table=table_na, columns=columns_na,
                                                    subquery=subquery_na)
            print(query_na)
            values_na = [[
                contract_id,
                act_number,
                status_id,
                act_cost,
                date_start
            ]]
            print(values_na)
            execute_values(cursor, query_na, values_na)
            new_act_id = cursor.fetchone()[0]
            conn.commit()

            # Добавляем tow в tow_acts
            if len(values_ac_ins):
                for i in values_ac_ins:
                    i[0] = new_act_id
                action = 'INSERT INTO'
                columns_ac_ins = ('act_id', 'tow_id', 'tow_cost', 'tow_cost_percent')
                query_ac_ins = app_payment.get_db_dml_query(action=action, table=table_ta, columns=columns_ac_ins,
                                                            subquery=subquery)
                print(action)
                print(query_ac_ins)
                print(values_ac_ins)
                execute_values(cursor, query_ac_ins, values_ac_ins)

                conn.commit()

            app_login.conn_cursor_close(cursor, conn)

            # Для логирования
            cc_description = f"Добавлен акт №: {act_number} по объекту: \"{object_name}\", " \
                             f"стоимость: ({act_cost} ₽)"
            if change_log['cc_description'] == [False]:
                change_log['cc_description'] = [cc_description]
            else:
                change_log['cc_description'].insert(0, cc_description)
            change_log['cc_id'] = new_act_id
            change_log['cc_value_previous'] = 0
            change_log['cc_value_current'] = act_cost
            change_log['cc_new'] = True
            change_log['cc_action_type'] = 'create'

            add_contracts_change_log(change_log)

            flash(message=[f"Акт №: {act_number} создан", ], category='success')
            description.append('Акт сохранен')
            return jsonify({
                'status': 'success',
                'act_id': new_act_id,
                'description': description,
            })
        else:
            ######################################################################################
            # Определяем изменённые поля в акте
            ######################################################################################
            columns_a = ['act_id']
            values_a = [[act_id]]

            if object_id != act_info['object_id']:
                description.extend([
                    "Нельзя сменить объект для акта",
                    "Удалите акт и создайте новый для выбранного объекта"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if type_id != act_info['type_id']:
                description.extend([
                    "Нельзя сменить тип акта",
                    "Удалите акт и создайте новый, выбрав нужный тип акта"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if contract_id != act_info['contract_id']:
                description.extend([
                    "Нельзя сменить договор для акта",
                    "Удалите акт и создайте новый, выбрав нужный договор"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if act_number != act_info['act_number']:
                columns_a.append('act_number')
                values_a[0].append(act_number)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка акта:')
                change_log['01_card'].append(f"Номер акта: было ({act_info['act_number']}) стало ({act_number})")

            if date_start != act_info['act_date']:
                columns_a.append('act_date')
                values_a[0].append(date_start)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка акта:')
                change_log['01_card'].append(f"Дата акта: было ({act_info['act_date']}) стало ({date_start})")

            if status_id != act_info['contract_status_id']:
                columns_a.append('contract_status_id')
                values_a[0].append(status_id)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка акта:')
                change_log['01_card'].append(f"Статус: было ({act_info['contract_status_id']}) стало ({status_id})")

            if act_cost != act_info['act_cost']:
                columns_a.append('act_cost')

                values_a[0].append(act_cost)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка акта:')
                change_log['01_card'].append(f"Стоимость: было ({act_info['act_cost']} ₽) стало ({act_cost} ₽)")

            ######################################################################################
            # Определяем добавляемые, изменяемые и удаляемые tow
            #
            # Проверяем, не превышает ли сумма tow стоимость договора, формируем список добавляемых и редактируемых tow
            ######################################################################################

            columns_ta_ins = ('act_id', 'tow_id', 'tow_cost', 'tow_cost_percent')
            tow_id_list_ins = tow_id_list - db_tow_id_list  # СПИСОК ДОБАВЛЕНИЯ TOW
            tow_id_list_del = db_tow_id_list - tow_id_list  # СПИСОК УДАЛЕНИЯ TOW
            tow_id_list_upd = tow_id_list - tow_id_list_del - tow_id_list_ins  # СПИСОК ИЗМЕНЕНИЯ TOW

            check_ac = act_cost
            lst_cost_tow = None
            values_ta_ins = []
            values_ta_del = []
            values_ta_upd = []
            tow_id_set_upd = set()

            for tow_id in tow_id_list - tow_id_list_del:
                check_towc = 0
                if tow_id in tow_id_list_ins:
                    if tow_list_to_dict[tow_id]['cost']:
                        check_towc = tow_list_to_dict[tow_id]['cost']
                        lst_cost_tow = tow_list_to_dict[tow_id]

                        # Для логирования
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        cl_02_tow_ins = f" - {tow_dict[tow_id]['tow_name']}: " \
                                        f"стоимость ({tow_list_to_dict[tow_id]['cost']} ₽)"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)

                    elif tow_list_to_dict[tow_id]['percent']:
                        check_towc = round(act_cost * tow_list_to_dict[tow_id]['percent'] / 100, 2)
                        lst_cost_tow = tow_list_to_dict[tow_id]

                        # Для логирования
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        cl_02_tow_ins = f" - {tow_dict[tow_id]['tow_name']}: " \
                                        f"стоимость ({tow_list_to_dict[tow_id]['percent']} %)"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)

                elif tow_id in tow_id_list_upd:
                    # Для логирования
                    cl_03_tow_upd = f" - {tow_dict[tow_id]['tow_name']}:"

                    # Если указана стоимость
                    if tow_list_to_dict[tow_id]['cost']:
                        # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
                        if tow_dict[tow_id]['cost_raw'] and \
                                tow_dict[tow_id]['cost_raw'] != tow_list_to_dict[tow_id]['cost']:
                            check_towc = tow_list_to_dict[tow_id]['cost']
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" Стоимость (было:{tow_dict[tow_id]['cost_raw']} ₽, " \
                                             f"стало:{tow_list_to_dict[tow_id]['cost']} ₽)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)

                        elif not tow_dict[tow_id]['cost_raw']:
                            check_towc = tow_list_to_dict[tow_id]['cost']
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" Стоимость (было: - , " \
                                             f"стало:{tow_list_to_dict[tow_id]['cost']} ₽)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)
                        # Никаких изменений у tow не было
                        else:
                            check_towc = 0
                            if tow_dict[tow_id]['cost_raw']:
                                check_towc = tow_dict[tow_id]['cost_raw']
                            elif tow_dict[tow_id]['percent_raw']:
                                check_towc = act_cost * tow_dict[tow_id]['percent_raw'] / 100

                    # Указаны проценты
                    elif tow_list_to_dict[tow_id]['percent']:
                        if (tow_dict[tow_id]['percent_raw'] and
                                tow_dict[tow_id]['percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                            check_towc = act_cost * tow_list_to_dict[tow_id]['percent'] / 100
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" % суммы (было:{tow_dict[tow_id]['percent_raw']} %, " \
                                             f"стало:{tow_list_to_dict[tow_id]['percent']} %)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)

                        elif (tow_list_to_dict[tow_id]['percent'] and
                              tow_dict[tow_id]['percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                            check_towc = act_cost * tow_list_to_dict[tow_id]['percent'] / 100
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" % суммы (было:{tow_dict[tow_id]['percent_raw']} %, " \
                                             f"стало:{tow_list_to_dict[tow_id]['percent']} %)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)
                        # Никаких изменений у tow не было
                        else:
                            check_towc = 0
                            if tow_dict[tow_id]['cost_raw']:
                                check_towc = tow_dict[tow_id]['cost_raw']
                            elif tow_dict[tow_id]['percent_raw']:
                                check_towc = act_cost * tow_dict[tow_id]['percent_raw'] / 100

                else:
                    if tow_dict[tow_id]['cost_raw']:
                        check_towc = tow_dict[tow_id]['cost_raw']
                    elif tow_dict[tow_id]['percent_raw']:
                        check_towc = act_cost * tow_dict[tow_id]['percent_raw'] / 100

                check_ac = check_ac - check_towc

            if check_ac < -0.01:
                check_ac = round(check_ac, 2)
                if check_ac <= -1:
                    description.extend([
                        f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                        f"Скорректируйте стоимость акта или видов работ"])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif lst_cost_tow:
                    if lst_cost_tow['cost']:
                        lst_cost_tow['cost'] += check_ac
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                            f"У последнего созданного/измененного вида работ была изменена стоимость:",
                            f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                        ])
                    elif lst_cost_tow['percent']:
                        lst_cost_tow['cost'] = round((act_cost * lst_cost_tow['percent'] / 100) + check_ac, 2)
                        lst_cost_tow['percent'] = None
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                            f"У последнего созданного/измененного вида работ была изменена стоимость:",
                            f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                        ])
                    else:
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                            f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                            f"в котором можно произвести корректировку стоимости"
                        ])
                        return {
                            'status': 'error',
                            'description': description
                        }
                elif not lst_cost_tow:
                    description.extend([
                        f"Общая стоимость видов работ акта превышает стоимость акта на {-check_ac} ₽.",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # ДОБАВЛЕНИЕ TOW
            if tow_id_list_ins:
                for tow_id in tow_id_list_ins:
                    values_ta_ins.append([
                        act_id,
                        tow_list_to_dict[tow_id]['id'],
                        tow_list_to_dict[tow_id]['cost'],
                        tow_list_to_dict[tow_id]['percent']
                    ])

            # УДАЛЕНИЕ TOW
            columns_ta_del = 'act_id::int, tow_id::int'
            values_ta_del = []
            if tow_id_list_del:
                for i in tow_id_list_del:
                    values_ta_del.append((act_id, i))

                    # Для логирования
                    if not change_log['04_tow_del']:
                        change_log['04_tow_del'].append('Удаленные виды работ:')
                    if tow_dict[i]['cost_raw']:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: стоимость ({tow_dict[i]['cost_raw']} ₽)"
                    elif tow_dict[i]['percent_raw']:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: % суммы ({tow_dict[i]['percent_raw']} %)"
                    else:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: стоимость не указана"
                    change_log['04_tow_del'].append(cl_02_tow_del)

            # ОБНОВЛЕНИЕ TOW
            columns_ta_upd = [['act_id::integer', 'tow_id::integer'], 'tow_cost::numeric', 'tow_cost_percent::numeric']
            if tow_id_set_upd:
                for tow_id in tow_id_set_upd:
                    values_ta_upd.append([
                        act_id,
                        tow_list_to_dict[tow_id]['id'],
                        tow_list_to_dict[tow_id]['cost'],
                        tow_list_to_dict[tow_id]['percent']
                    ])

            # Для acts
            if len(columns_a) > 1:
                print('columns_a', columns_a)
                query_a = app_payment.get_db_dml_query(action='UPDATE', table='acts', columns=columns_a)
                execute_values(cursor, query_a, values_a)
            # Для tows_act
            if len(values_ta_ins):
                action = 'INSERT INTO'
                query_ta_ins = app_payment.get_db_dml_query(action=action, table=table_ta, columns=columns_ta_ins,
                                                            subquery=subquery)
                print(action)
                print(query_ta_ins)
                print(values_ta_ins)
                execute_values(cursor, query_ta_ins, values_ta_ins)

            if len(values_ta_upd):
                action = 'UPDATE DOUBLE'
                query_ta_upd = app_payment.get_db_dml_query(action=action, table=table_ta, columns=columns_ta_upd)
                print(action)
                print(query_ta_upd)
                pprint(values_ta_upd)
                execute_values(cursor, query_ta_upd, values_ta_upd)

            if len(values_ta_del):
                action = 'DELETE'
                query_tc_del = app_payment.get_db_dml_query(action=action, table=table_ta, columns=columns_ta_del,
                                                            subquery=subquery)
                print(action)
                print(query_tc_del)
                print(values_ta_del)
                execute_values(cursor, query_tc_del, (values_ta_del,))

            if len(columns_a) > 1 or len(values_ta_ins) or len(values_ta_upd) or len(values_ta_del):
                conn.commit()
                status = 'success'
                description.append('Изменения в акте сохранены')
                flash(message=[f"Акт №: {act_number} сохранён", ], category='success')
            else:
                status = 'success'
                description.append('В акте не найдено изменений')
                flash(message=[f"В акте №: {act_number} не найдено изменений", ], category='success')
            print('description')
            print(description)

            # Для логирования
            cc_description = f"Изменен акт №: {act_number} по объекту: \"{object_name}\""
            if change_log['cc_description'] == [False]:
                change_log['cc_description'] = [cc_description]
            else:
                change_log['cc_description'].insert(0, cc_description)
            change_log['cc_action_type'] = 'update'

            add_contracts_change_log(change_log)

            return jsonify({
                'status': status,
                'description': description,
            })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/contract-payments-list/card/<int:payment_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link_name>/contract-payments-list/card/<int:payment_id>', methods=['GET'])
@login_required
def get_card_contracts_payment(payment_id, link_name=''):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=payment_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        payment_id = payment_id
        link_name = link_name

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Находим object_id, по нему находим список tow
        cursor.execute(FIND_OBJ_BY_PAYMENT, [payment_id])
        object_info = cursor.fetchone()

        if not object_info:
            e = 'Карточка платежа: Информация о платеже не найдена'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())

        object_info = dict(object_info)

        contract_id = object_info['contract_id']
        object_id = object_info['object_id']
        project_id = get_proj_id(object_id=object_id)['project_id']
        act_id = object_info['act_id']
        type_id = object_info['type_id']
        payment_type_id = object_info['payment_type_id']

        # Списки объектов - оставляем только объект платежа, т.к. объекты мы менять не можем
        cursor.execute("""SELECT contract_id, contract_number FROM contracts WHERE contract_id = %s;""", [contract_id])
        contracts_income = cursor.fetchone()
        contracts_income = [dict(contracts_income)]
        contracts_expenditure = contracts_income

        tmp_act_id = act_id if act_id else -1
        tmp_payment_id = payment_id
        ######################################################################################
        # ВИД ПЛАТЕЖА - АВАНС
        ######################################################################################
        if payment_type_id == 1:
            # Информация о договоре платежа
            cursor.execute(
                QUERY_CONT_INFO_FOR_PAYMENT,
                [tmp_payment_id, contract_id, tmp_payment_id, contract_id, object_id, type_id]
            )
            payment_info = cursor.fetchall()
            # Список актов пуст
            act_list = list()
            # tow list
            cursor.execute(CONTRACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, payment_id, contract_id, contract_id, contract_id,
                            payment_id, contract_id])
            tow = cursor.fetchall()
        else:
            # Информация об акте платежа
            cursor.execute(
                QUERY_ACT_INFO_FOR_PAYMENT,
                [tmp_act_id, tmp_payment_id, tmp_act_id, tmp_payment_id, contract_id, object_id, type_id]
            )
            payment_info = cursor.fetchall()

            # Список актов
            cursor.execute(
                """
                SELECT
                    t1.act_id,
                    t1.act_number
                FROM acts AS t1
                WHERE t1.contract_id = %s
                """,
                [contract_id]
            )
            act_list = cursor.fetchall()
            if act_list:
                for i in range(len(act_list)):
                    act_list[i] = dict(act_list[i])

            # tow list
            cursor.execute(ACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, act_id, payment_id, act_id, act_id, payment_id])
            tow = cursor.fetchall()

        if payment_info:
            if len(payment_info) == 1:
                payment_info = dict(payment_info[0])
            else:
                return jsonify({
                    'status': 'error',
                    'description': ['Проверка договора не пройдена. rev-1'],
                })
        else:
            return jsonify({
                'status': 'error',
                'description': ['Проверка договора не пройдена. rev-2'],
            })

        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

        objects_name = get_obj_list()

        # Вид платежа
        cursor.execute("SELECT payment_type_id, payment_type_name  FROM payment_types ORDER BY payment_type_name")
        payment_types = cursor.fetchall()
        if payment_types:
            for i in range(len(payment_types)):
                payment_types[i] = dict(payment_types[i])
        print('payment_types:  ', payment_types)

        # Список типов
        if link_name:
            cursor.execute("""
                    SELECT 
                        DISTINCT t1.type_id, t2.type_name
                    FROM contracts AS t1
                    LEFT JOIN contract_types AS t2 ON t1.type_id = t2.type_id
                    WHERE t1.object_id = %s
                    ORDER BY t2.type_name
                    ;""",
                           [object_id]
                           )
            contract_types = cursor.fetchall()
        else:
            cursor.execute("SELECT type_id, type_name  FROM contract_types ORDER BY type_name")
            contract_types = cursor.fetchall()
        if contract_types:
            for i in range(len(contract_types)):
                contract_types[i] = dict(contract_types[i])

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        render_html = 'contract-card-payment.html'
        title = f"Платеж № {payment_info['act_number_short']} по договору: {payment_info['contract_number']}"

        print('payment_info:    ', payment_info)
        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile, payment_info=payment_info,
                               objects_name=objects_name, payment_types=payment_types, tow=tow, acts=act_list,
                               act_types=contract_types,
                               contracts_income=contracts_income, contracts_expenditure=contracts_expenditure,
                               dept_list=dept_list, nonce=get_nonce(),
                               title=title, title1=payment_info['payment_number'])
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/contract-payments-list/card/new/<link_name>', methods=['GET'])
@contract_app_bp.route('/contract-payments-list/card/new', methods=['GET'])
@login_required
def get_card_contracts_new_payment(link_name=False):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description='new', user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        print('get_card_contracts_new_payment', link_name)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        object_id = get_proj_id(link_name=link_name)['object_id'] if link_name else -100
        contract_id = -100
        act_id = -100
        payment_id = -100

        # Находим номера всех договоров объекта (без субподрядных)
        if link_name:
            # Если создаётся договор из объекта
            # Доходные договоры
            cursor.execute(
                CONTRACTS_LIST,
                [object_id, 1]
            )
            contracts_income = cursor.fetchall()
            if contracts_income:
                for i in range(len(contracts_income)):
                    contracts_income[i] = dict(contracts_income[i])

            # Расходные договоры
            cursor.execute(
                CONTRACTS_LIST,
                [object_id, 2]
            )
            contracts_expenditure = cursor.fetchall()
            if contracts_expenditure:
                for i in range(len(contracts_expenditure)):
                    contracts_expenditure[i] = dict(contracts_expenditure[i])

        else:
            # Договор создаётся из сводной таблице договоров
            contracts_income = []
            contracts_expenditure = []
        print('contracts_income')
        print(contracts_income)
        print('contracts_expenditure')
        print(contracts_expenditure)
        tow = None
        object_name = None
        objects_name = get_obj_list()

        print(' ___2')
        # Список объектов, у которых есть договоры
        cursor.execute("SELECT object_id FROM contracts GROUP BY object_id ORDER BY object_id")
        objects_plus = cursor.fetchall()
        if objects_plus:
            objects_plus = [x[0] for x in objects_plus]
        print(' Список объектов, у которых есть договоры', objects_plus)
        for i in objects_name[:]:
            if i['object_id'] == object_id:
                object_name = i['object_name']
            if i['object_id'] not in objects_plus:
                objects_name.remove(i)
        print(' __objects__', objects_name)

        # Вид платежа
        cursor.execute("SELECT payment_type_id, payment_type_name  FROM payment_types ORDER BY payment_type_name")
        payment_types = cursor.fetchall()
        if payment_types:
            for i in range(len(payment_types)):
                payment_types[i] = dict(payment_types[i])
        print('# Вид платежа')
        print(payment_types)

        # Список типов
        if link_name:
            cursor.execute("""
                    SELECT 
                        DISTINCT t1.type_id, t2.type_name
                    FROM contracts AS t1
                    LEFT JOIN contract_types AS t2 ON t1.type_id = t2.type_id
                    WHERE t1.object_id = %s
                    ORDER BY t2.type_name
                    ;""",
                           [object_id]
                           )
            contract_types = cursor.fetchall()
        else:
            cursor.execute("SELECT type_id, type_name  FROM contract_types ORDER BY type_name")
            contract_types = cursor.fetchall()
        if contract_types:
            for i in range(len(contract_types)):
                contract_types[i] = dict(contract_types[i])
        type_name = None
        print('# Список типов')
        print(contract_types)
        # Информация о договоре
        object_id = None if object_id == -100 else object_id
        payment_info = {
            'object_id': object_id,
            'object_name': object_name,
            'contract_id': None,
            'contract_number': '',
            'act_id': None,
            'payment_id': None,
            'payment_number': '',
            'act_number': '',
            'date_start': None,
            'date_start_txt': '',
            'payment_date': None,
            'payment_date_txt': '',
            'type_id': None,
            'payment_type_id': None,
            'contractor_id': None,
            'new_payment': 'new',
            'payment_cost_rub': '0 ₽',
            'contract_cost_rub': '0 ₽',
            'vat_value': None,
            'vat': None,
            'contract_cost_vat': 0,
            'contract_cost': 0,
            'payment_cost_vat': 0,
            'payment_cost': 0,
            'undistributed_contract_cost': 0,
            'allow': True,
            'created_at': None,
            'undistributed_cost': 0,
            'undistributed_cost_rub': '0 ₽'
        }
        payment_number = payment_info['payment_number']

        print('                       payment_info')
        if payment_info:
            payment_info = dict(payment_info)

        print('     payment_info', payment_info)

        app_login.conn_cursor_close(cursor, conn)
        print('app_login.conn_cursor_close(cursor, conn)')

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # print(dict(employee))
        # if request.path[1:].split('/')[-2] == 'card2':
        render_html = 'contract-card-payment.html'
        title = "Создание нового платежа"

        # Return the updated data as a response
        return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile, payment_info=payment_info,
                               objects_name=objects_name, payment_types=payment_types, tow=tow, acts=list(),
                               act_types=contract_types,
                               contracts_income=contracts_income, contracts_expenditure=contracts_expenditure,
                               dept_list=dept_list, nonce=get_nonce(), title=title)

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@contract_app_bp.route('/change-contract-from-payment/<int:contract_id>', methods=['POST'])
@login_required
def change_contract_from_payment(contract_id: int):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        print(contract_id)
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Список актов и виды платежей
        cursor.execute(
            """
            SELECT
                t1.act_id,
                t1.act_number
            FROM acts AS t1
            WHERE t1.contract_id = %s
            """,
            [contract_id]
        )
        act_list = cursor.fetchall()
        if act_list:
            for i in range(len(act_list)):
                act_list[i] = dict(act_list[i])

            cursor.execute("SELECT payment_type_id, payment_type_name  FROM payment_types ORDER BY payment_type_name")
            payment_types = cursor.fetchall()
        else:
            cursor.execute("""
            SELECT 
                payment_type_id, 
                payment_type_name
            FROM payment_types 
            WHERE payment_type_id = 1
            ORDER BY payment_type_name""")
            payment_types = cursor.fetchall()
        if payment_types:
            for i in range(len(payment_types)):
                payment_types[i] = dict(payment_types[i])

        # Информация о договоре
        cursor.execute("SELECT * FROM contracts WHERE contract_id = %s", [contract_id])
        check_con_info = cursor.fetchone()
        if check_con_info:
            check_con_info = dict(check_con_info)
        else:
            return jsonify({
                'status': 'error',
                'description': ['Договор не пройден. rev-3'],
            })

        app_login.conn_cursor_close(cursor, conn)

        # Return the data as a response
        return jsonify({
            'payment_types': payment_types,
            'act_list': act_list,
            'check_con_info': check_con_info,
            'status': 'success'
        })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/change-payment_types-from-payment/<int:payment_types_id>/<int:some_id>', methods=['POST'])
@login_required
def change_payment_types_from_payment(payment_types_id: int, some_id: int):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        print(payment_types_id, some_id)
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        payment_id = -1
        tow = None

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        ######################################################################################
        # Вид платежа - АВАНС, подгружаем данные о tow договора
        ######################################################################################
        if payment_types_id == 1:
            contract_id = some_id
            cursor.execute(
                """
                SELECT
                    object_id
                FROM contracts
                WHERE contract_id = %s
                LIMIT 1;""",
                [contract_id]
            )
            object_id = cursor.fetchone()
            if not object_id:
                app_login.conn_cursor_close(cursor, conn)
                return jsonify({
                    'status': 'error',
                    'description': ['Объект или договор не найден'],
                })
            object_id = object_id[0]
            proj_info = get_proj_id(object_id=object_id)
            object_id = proj_info['object_id']
            project_id = proj_info['project_id']
            link_name = proj_info['link_name']
            cursor.execute(CONTRACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, payment_id, contract_id, contract_id, contract_id,
                            payment_id, contract_id])
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])

            cursor.execute(
                """
                SELECT 
                    t1.contract_cost AS contract_cost_vat,
                    TRIM(BOTH ' ' FROM to_char(ROUND(t1.contract_cost / t1.vat_value::numeric, 2), '999 999 990D99 ₽')) AS contract_cost_rub,
                    t1.contract_cost - COALESCE(t6.un_c_cost, 0) AS undistributed_contract_cost,
                    ROUND(COALESCE(t0.payment_cost, 0) - COALESCE(t5.tow_cost + COALESCE(t0.payment_cost, 0) * t5.tow_cost_percent / 100, 0), 2) AS undistributed_cost,
                    TRIM(BOTH ' ' FROM to_char(
                        ROUND(COALESCE(t0.payment_cost, 0) - COALESCE(t5.tow_cost + COALESCE(t0.payment_cost, 0) * t5.tow_cost_percent / 100, 0), 2),
                    '999 999 990D99 ₽')) AS undistributed_cost_rub,
                    COALESCE(t0.payment_cost, 0) AS act_cost_vat
                FROM contracts AS t1
                LEFT JOIN (
                    SELECT
                        payment_cost
                FROM payments
                WHERE payment_id = %s
                ) AS t0 ON true
                LEFT JOIN (
                    SELECT 
                        COALESCE(SUM(tow_cost), 0) AS tow_cost,
                        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
                    FROM tows_payment
                    WHERE 
                        payment_id = %s
                        AND 
                        tow_id IN
                            (SELECT
                                tow_id
                            FROM types_of_work)
                ) AS t5 ON true
                LEFT JOIN (
                    SELECT 
                        contract_id,
                        COALESCE(SUM(payment_cost), 0) AS un_c_cost
                    FROM payments
                    GROUP BY contract_id
                ) AS t6 ON t1.contract_id = t6.contract_id
                WHERE t1.contract_id = %s;
                """,
                [payment_id, payment_id, contract_id]
            )
            info = cursor.fetchone()
        ######################################################################################
        # Вид платежа - АКТ, подгружаем данные о tow акта
        ######################################################################################
        elif payment_types_id == 2:
            # Находим object_id, по нему находим список tow
            act_id = some_id
            cursor.execute(FIND_OBJ_BY_ACT, [act_id])
            object_id = cursor.fetchone()
            contract_id = object_id['contract_id']
            proj_info = get_proj_id(object_id=object_id['object_id'])
            object_id = proj_info['object_id']
            project_id = proj_info['project_id']
            link_name = proj_info['link_name']
            print(object_id)
            if not object_id:
                app_login.conn_cursor_close(cursor, conn)
                return jsonify({
                    'status': 'error',
                    'description': ['Объект или договор не найден'],
                })
            cursor.execute(ACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, act_id, payment_id, act_id, act_id, payment_id])
            tow = cursor.fetchall()

            if tow:
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])

            cursor.execute(
                """
                SELECT 
                    t0.act_cost AS contract_cost_vat,
                    TRIM(BOTH ' ' FROM to_char(ROUND(t0.act_cost / t2.vat_value::numeric, 2), '999 999 990D99 ₽')) AS contract_cost_rub,
                    t0.act_cost - COALESCE(t6.un_c_cost, 0) AS undistributed_contract_cost,
                    ROUND(COALESCE(t1.payment_cost, 0) - COALESCE(t5.tow_cost + COALESCE(t1.payment_cost, 0) * t5.tow_cost_percent / 100, 0), 2) AS undistributed_cost,
                    TRIM(BOTH ' ' FROM to_char(
                        ROUND(COALESCE(t1.payment_cost, 0) - COALESCE(t5.tow_cost + COALESCE(t1.payment_cost, 0) * t5.tow_cost_percent / 100, 0), 2),
                    '999 999 990D99 ₽')) AS undistributed_cost_rub,
                    COALESCE(t1.payment_cost, 0) AS act_cost_vat
                FROM acts AS t0
                LEFT JOIN (
                    SELECT
                        payment_cost
                FROM payments
                WHERE payment_id = %s
                ) AS t1 ON true
                LEFT JOIN (
                    SELECT
                        contract_id,
                        vat_value
                    FROM contracts
                ) AS t2 ON t0.contract_id = t0.contract_id
                LEFT JOIN (
                    SELECT 
                        COALESCE(SUM(tow_cost), 0) AS tow_cost,
                        COALESCE(SUM(tow_cost_percent), 0) AS tow_cost_percent
                    FROM tows_payment
                    WHERE 
                        payment_id = %s
                        AND 
                        tow_id IN
                            (SELECT
                                tow_id
                            FROM types_of_work)
                ) AS t5 ON true
                LEFT JOIN (
                    SELECT 
                        act_id,
                        COALESCE(SUM(payment_cost), 0) AS un_c_cost
                    FROM payments
                    GROUP BY act_id
                ) AS t6 ON t0.act_id = t6.act_id
                WHERE t0.act_id = %s;
                """,
                [payment_id, payment_id, act_id]
            )
            info = cursor.fetchone()

        else:
            return jsonify({
                'status': 'error',
                'description': ['Ошибка определения вида платежа'],
            })
        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        app_login.conn_cursor_close(cursor, conn)
        if info:
            info = dict(info)
        print(info)
        # Return the data as a response
        return jsonify({
            'tow': tow,
            'dept_list': dept_list,
            'info': info,
            'status': 'success'
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/save_contracts_payment', methods=['POST'])
@login_required
def save_contracts_payment():
    try:
        try:
            user_id = app_login.current_user.get_id()
        except:
            user_id = None
        try:
            payment_id = request.get_json()['payment_id']
        except:
            payment_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=payment_id, user_id=user_id)

        print(request.get_json())

        description = list()

        object_id = request.get_json()['object_id']
        type_id = request.get_json()['act_type']
        contract_id = request.get_json()['contract_id']
        payment_type_id = request.get_json()['payment_types']
        act_id = request.get_json()['act_number'] if payment_type_id == '2' else False
        payment_number = request.get_json()['payment_number']
        date_start = request.get_json()['date_start']
        payment_cost = request.get_json()['payment_cost']
        tow_list = request.get_json()['list_towList']
        text_comment = request.get_json()['text_comment']

        payment_id = int(payment_id) if payment_id != 'new' else 'new'
        object_id = int(object_id) if object_id else None
        type_id = int(type_id) if type_id else None
        contract_id = int(contract_id) if contract_id else None
        payment_type_id = int(payment_type_id) if payment_type_id else None
        act_id = int(act_id) if act_id else None
        date_start = date.fromisoformat(date_start) if date_start else None
        payment_cost = app_payment.convert_amount(payment_cost) if payment_cost else None

        # Для логирования
        change_log = {
            'cc_id': payment_id,
            'cc_type': 'payment',
            'cc_action_type': None,
            'cc_description': [text_comment],
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }
        change_log['cc_description'] = change_log['cc_description'] if change_log['cc_description'] else list()

        if not object_id or not type_id or not contract_id or not payment_type_id or not payment_id or not date_start \
                or not payment_cost or payment_type_id == 2 and not act_id:
            print('not object_id:', not object_id,
                  '\nnot type_id:', not type_id,
                  '\nnot contract_id:', not contract_id,
                  '\nnot payment_type_id:', not payment_type_id,
                  '\nnot payment_id:', not payment_id,
                  '\nnot date_start:', not date_start,
                  '\nnot payment_cost:', not payment_cost,
                  '\npayment_type_id == 2 and not act_id:', payment_type_id == 2 and not act_id)
            description.extend(['В данных платежа не хватаем информации'])
            return jsonify({
                'status': 'error',
                'description': description,
            })

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [object_id])
        object_name = cursor.fetchone()[0]

        tmp_payment_id = -1 if payment_id == 'new' else payment_id
        tmp_act_id = act_id if act_id else -1
        if payment_type_id == 1:
            cursor.execute(
                QUERY_CONT_INFO_FOR_PAYMENT,
                [tmp_payment_id, contract_id, tmp_payment_id, contract_id, object_id, type_id]
            )
        else:
            cursor.execute(
                QUERY_ACT_INFO_FOR_PAYMENT,
                [tmp_act_id, tmp_payment_id, tmp_act_id, tmp_payment_id, contract_id, object_id, type_id]
            )
        check_con_info = cursor.fetchall()
        if check_con_info:
            if len(check_con_info) == 1:
                check_con_info = dict(check_con_info[0])
            else:
                description.extend(['Проверка договора не пройдена. rev-1'])
                return jsonify({
                    'status': 'error',
                    'description': description,
                })
        else:
            description.extend(['Проверка договора не пройдена. rev-2'])
            return jsonify({
                'status': 'error',
                'description': description,
            })

        vat = check_con_info['vat_value']

        # print('       check_con_info')
        # print(check_con_info)

        tow_id_list = set()
        tow_list_to_dict = dict()
        if len(tow_list):
            for i in tow_list:
                i['id'] = int(i['id']) if i['id'] else None
                # tow_id_list.add(i['id'])
                if i['type'] == '%':
                    i['percent'] = float(i['percent']) if i['percent'] != 'None' else None
                    i['cost'] = None
                elif i['type'] == '₽':
                    i['percent'] = None
                    i['cost'] = app_payment.convert_amount(i['cost']) if i['cost'] != 'None' else None
                else:
                    i['percent'] = None
                    i['cost'] = None

                del i['type']

                tow_list_to_dict[i['id']] = i
            tow_id_list = set(tow_list_to_dict.keys())
        # print('------------------------------     tow_list_to_dict')
        # for k, v in tow_list_to_dict.items():
        #     print(k, v)

        if payment_type_id == 1:
            name_pt = 'договора'
        else:
            name_pt = 'акта'

        payment_info = check_con_info
        # # Проверка, что стоимость акта не была изменена
        # if payment_id != 'new':
        #     if payment_info['payment_cost'] != payment_cost:
        #         payment_cost = including_tax(payment_cost, check_con_info['vat_value'])
        # else:
        #     payment_cost = including_tax(payment_cost, check_con_info['vat_value'])

        # Проверяем что неоплаченный остаток договора не меньше стоимости платежа
        if check_con_info['undistributed_contract_cost'] < payment_cost:
            check_pc = payment_cost - check_con_info['undistributed_contract_cost']
            description.extend([
                f"Неоплаченный остаток {name_pt} меньше стоимости платежа",
                f"Остаток: {check_con_info['undistributed_contract_cost']} ₽",
                f"Стоимость платежа без НДС: {payment_cost} ₽",
                f"Не хватает: {check_pc} ₽"
            ])
            return jsonify({
                'status': 'error',
                'description': description,
            })

        contract_cost = float(check_con_info['contract_cost'])

        # Список tow платежа
        if payment_type_id == 1:
            cursor.execute(CONTRACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, tmp_payment_id, contract_id, contract_id, contract_id,
                            tmp_payment_id, contract_id])
        else:
            cursor.execute(ACT_TOW_LIST_FOR_PAYMENT,
                           [project_id, project_id, contract_id, tmp_act_id, tmp_payment_id, tmp_act_id, tmp_act_id,
                            tmp_payment_id])
        tow = cursor.fetchall()
        tow_dict = dict()

        # print(payment_cost)
        # if payment_info:
        #     pprint(dict(payment_info))
        # print('------------------------------     tow')
        # print(tow)
        # print('-----------------------------__')

        # Проверяем, неоплаченный остаток договора не меньше стоимости платежа, а так же проверяем актуальность списка tow
        db_tow_id_list = set()
        if tow:
            for i in tow:
                tow_list_cost = 0  # Общая стоимость видов работ платежа
                i = dict(i)
                if i['payment_tow_id']:
                    db_tow_id_list.add(i['tow_id'])

                # Если к платежу привязали tow (указали стоимость tow)
                if len(tow_list_to_dict):
                    tow_dict[i['tow_id']] = i
                    # print(i)
                    if i['tow_id'] in tow_list_to_dict.keys():

                        tow_payment_cost = tow_list_to_dict[i['tow_id']]['cost']
                        if not tow_list_to_dict[i['tow_id']]['cost']:
                            tow_payment_cost = round(tow_list_to_dict[i['tow_id']]['percent'] * payment_cost / 100, 2)

                        tow_list_cost += tow_payment_cost

                        tmp_tow_remaining_cost = round(i['tow_remaining_cost_with_vat'] + i['tow_payment_cost'] -
                                                       tow_payment_cost, 2)

                        if tmp_tow_remaining_cost < 0:
                            if payment_type_id == 1:
                                name_pt = 'договора'
                            else:
                                name_pt = 'акта'
                            x = tow_payment_cost - i['tow_remaining_cost_with_vat']
                            description.extend([
                                f"id:{i['tow_id']} - \"{i['tow_name']}\"",
                                f"Неоплаченный остаток вида работ {name_pt} меньше стоимости вида работ платежа",
                                f"Остаток вида работ: {i['tow_remaining_cost_with_vat']} ₽",
                                f"Стоимость вида работ: {tow_payment_cost} ₽",
                                f"Не хватает:  {x} ₽"
                            ])
                            return jsonify({
                                'status': 'error',
                                'description': description,
                            })
                        # print('________________________ ')
            else:
                for i in tow:
                    i = dict(i)
                    tow_dict[i['tow_id']] = i

        if tow_list_to_dict.keys() - tow_dict.keys():
            description.extend([
                "Список видов работ не актуален",
                "За время работы с платежом изменился список видов работ договора.",
                "Обновите страницу и повторите попытку снова"
            ])
            return {
                'status': 'error',
                'description': description
            }

        subquery = 'ON CONFLICT DO NOTHING'
        table_tp = 'tows_payment'

        # Если новый платеж, проверяем, соотносятся ли стоимости tow и стоимость платежа, если ок - запись в БД
        if payment_id == 'new':
            check_pc = payment_cost
            lst_cost_tow = None

            values_pc_ins = []
            if len(tow_list):
                for i in tow_list:
                    check_towc = 0
                    if i['cost']:
                        check_towc = i['cost']
                    elif i['percent']:
                        check_towc = round(payment_cost * i['percent'] / 100, 2)

                    lst_cost_tow = i if i['cost'] or i['percent'] else lst_cost_tow
                    check_pc = round(check_pc - check_towc, 2)

                    values_pc_ins.append([
                        payment_id,
                        i['id'],
                        i['cost'],
                        i['percent']
                    ])

                if 0 > check_pc >= -0.01 and lst_cost_tow:
                    if lst_cost_tow['cost']:
                        lst_cost_tow['cost'] += check_pc
                    elif lst_cost_tow['percent']:
                        lst_cost_tow['cost'] = round(payment_cost * lst_cost_tow['percent'] / 100, 2)
                        lst_cost_tow['percent'] = None
                    description.extend([
                        f"Общая стоимость видов работ платежа превышает стоимость платежа ({check_pc} ₽).",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif 0 > check_pc >= -0.01 and not lst_cost_tow:
                    description.extend([
                        f"Общая стоимость видов работ платежа превышает стоимость платежа ({check_pc} ₽).",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif check_pc < -0.01:
                    description.extend([
                        f"Общая стоимость видов работ платежа превышает стоимость платежа ({check_pc} ₽).",
                        f"Отвяжите лишние виды работ от договора,или перераспределите стоимости видов работ,"
                        f" или увеличьте стоимость акта"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # Добавляем новый платеж
            action = 'INSERT INTO'
            table_np = 'payments'
            columns_np = ('contract_id', 'payment_number', 'payment_date', 'act_id', 'payment_cost', 'payment_type_id')
            subquery_np = " RETURNING payment_id;"
            print(action)
            query_np = app_payment.get_db_dml_query(action=action, table=table_np, columns=columns_np,
                                                    subquery=subquery_np)
            print(query_np)
            values_np = [[
                contract_id,
                payment_number,
                date_start,
                act_id if act_id else None,
                payment_cost,
                payment_type_id
            ]]
            print(values_np)
            execute_values(cursor, query_np, values_np)
            new_payment_id = cursor.fetchone()[0]
            conn.commit()

            # Добавляем tow в tow_acts
            if len(values_pc_ins):
                for i in values_pc_ins:
                    i[0] = new_payment_id
                action = 'INSERT INTO'
                columns_pc_ins = ('payment_id', 'tow_id', 'tow_cost', 'tow_cost_percent')
                query_pc_ins = app_payment.get_db_dml_query(action=action, table=table_tp, columns=columns_pc_ins,
                                                            subquery=subquery)
                print(action)
                print(query_pc_ins)
                print(values_pc_ins)
                execute_values(cursor, query_pc_ins, values_pc_ins)

                conn.commit()

            app_login.conn_cursor_close(cursor, conn)

            # Для логирования
            cc_description = ''
            if payment_type_id == 1:
                cc_description = f"Добавлен платеж №: {payment_number} договора №: {payment_info['contract_number']} " \
                                 f"по объекту: \"{object_name}\", стоимость: ({payment_cost} ₽)"
            else:
                cc_description = f"Добавлен платеж №: {payment_number} акта №: {payment_info['act_number']}" \
                                 f"договора №: {payment_info['contract_number']} по объекту: \"{object_name}\", " \
                                 f"стоимость: ({payment_cost} ₽)"
            if change_log['cc_description'] == [False]:
                change_log['cc_description'] = [cc_description]
            else:
                change_log['cc_description'].insert(0, cc_description)
            change_log['cc_id'] = new_payment_id
            change_log['cc_value_previous'] = 0
            change_log['cc_value_current'] = payment_cost
            change_log['cc_new'] = True
            change_log['cc_action_type'] = 'create'

            add_contracts_change_log(change_log)

            flash(message=[f"Платеж №: {payment_number} создан", ], category='success')
            description.append('Платеж сохранен')
            return jsonify({
                'status': 'success',
                'payment_id': new_payment_id,
                'description': description,
            })
        else:
            ######################################################################################
            # Определяем изменённые поля в платеже
            ######################################################################################
            columns_p = ['payment_id']
            values_p = [[payment_id]]

            print('payment_info')
            print(payment_info)

            if not payment_info['payment_id']:
                return {
                    'status': 'error',
                    'description': ['Платеж не найден'],
                }
            if object_id != payment_info['object_id']:
                description.extend([
                    "Нельзя сменить объект для платежа",
                    "Удалите платеж и создайте новый для выбранного объекта"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if type_id != payment_info['type_id']:
                description.extend([
                    "Нельзя сменить тип платежа",
                    "Удалите платеж и создайте новый, выбрав нужный тип платежа"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if contract_id != payment_info['contract_id']:
                description.extend([
                    "Нельзя сменить договор для платежа",
                    "Удалите платеж и создайте новый, выбрав нужный договор"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if payment_type_id != payment_info['payment_type_id']:
                description.extend([
                    "Нельзя сменить вид платежа",
                    "Удалите платеж и создайте новый, выбрав нужный вид платежа"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
            if act_id != payment_info['act_id']:
                description.extend([
                    "Нельзя сменить акт для платежа",
                    "Удалите платеж и создайте новый, выбрав нужный акт"
                ])
                return {
                    'status': 'error',
                    'description': description
                }

            if payment_number != payment_info['payment_number']:
                columns_p.append('payment_number')
                values_p[0].append(payment_number)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка платежа:')
                change_log['01_card'].append(f"Номер платежа: было ({payment_info['payment_number']}) "
                                             f"стало ({payment_number})")

            if date_start != payment_info['payment_date']:
                columns_p.append('payment_date')
                values_p[0].append(date_start)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка платежа:')
                change_log['01_card'].append(f"Дата платежа: было ({payment_info['payment_date']}) "
                                             f"стало ({date_start})")

            if payment_cost != payment_info['payment_cost']:
                columns_p.append('payment_cost')
                values_p[0].append(payment_cost)

                if not change_log['01_card']:
                    change_log['01_card'].append('Изменена карточка платежа:')
                change_log['01_card'].append(f"Стоимость: было ({payment_info['payment_cost']} ₽) "
                                             f"стало ({payment_cost} ₽)")

            print('columns_p:', columns_p)
            print('values_p:', values_p)

            ######################################################################################
            # Определяем добавляемые, изменяемые и удаляемые tow
            #
            # Проверяем, не превышает ли сумма tow стоимость договора, формируем список добавляемых и редактируемых tow
            ######################################################################################

            columns_tp_ins = ('payment_id', 'tow_id', 'tow_cost', 'tow_cost_percent')
            tow_id_list_ins = tow_id_list - db_tow_id_list  # СПИСОК ДОБАВЛЕНИЯ TOW
            tow_id_list_del = db_tow_id_list - tow_id_list  # СПИСОК УДАЛЕНИЯ TOW
            tow_id_list_upd = tow_id_list - tow_id_list_del - tow_id_list_ins  # СПИСОК ИЗМЕНЕНИЯ TOW
            print('____tow_id_list_ins____', tow_id_list_ins)
            print('____tow_id_list_del____', tow_id_list_del)
            print('____tow_id_list_upd____', tow_id_list_upd)

            check_pc = payment_cost
            lst_cost_tow = None
            values_tp_ins = []
            values_tp_del = []
            values_tp_upd = []
            tow_id_set_upd = set()
            for tow_id in tow_id_list - tow_id_list_del:
                check_towc = 0
                if tow_id in tow_id_list_ins:
                    if tow_list_to_dict[tow_id]['cost']:
                        check_towc = tow_list_to_dict[tow_id]['cost']
                        lst_cost_tow = tow_list_to_dict[tow_id]

                        # Для логирования
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        cl_02_tow_ins = f" - {tow_dict[tow_id]['tow_name']}: " \
                                        f"стоимость ({tow_list_to_dict[tow_id]['cost']} ₽)"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)

                    elif tow_list_to_dict[tow_id]['percent']:
                        check_towc = payment_cost * tow_list_to_dict[tow_id]['percent'] / 100
                        lst_cost_tow = tow_list_to_dict[tow_id]

                        # Для логирования
                        if not change_log['02_tow_ins']:
                            change_log['02_tow_ins'].append('Добавление видов работ:')
                        cl_02_tow_ins = f" - {tow_dict[tow_id]['tow_name']}: " \
                                        f"стоимость ({tow_list_to_dict[tow_id]['percent']} %)"
                        change_log['02_tow_ins'].append(cl_02_tow_ins)

                elif tow_id in tow_id_list_upd:
                    # Для логирования
                    cl_03_tow_upd = f" - {tow_dict[tow_id]['tow_name']}:"

                    # print('      upd')
                    # Если указана стоимость
                    if tow_list_to_dict[tow_id]['cost']:
                        # print('cost')
                        # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
                        if tow_dict[tow_id]['cost_raw'] and \
                                tow_dict[tow_id]['cost_raw'] != tow_list_to_dict[tow_id]['cost']:
                            if tow_dict[tow_id]['cost_raw'] != tow_list_to_dict[tow_id]['cost']:
                                check_towc = tow_list_to_dict[tow_id]['cost']
                                lst_cost_tow = tow_list_to_dict[tow_id]
                                # print('    == 1 ==', tow_dict[tow_id]['cost_raw'], tow_list_to_dict[tow_id]['cost'], type(tow_dict[tow_id]['cost_raw']), type(tow_list_to_dict[tow_id]['cost']))
                                tow_id_set_upd.add(tow_id)

                                # Для логирования
                                if not change_log['03_tow_upd']:
                                    change_log['03_tow_upd'].append('Измененные виды работ:')
                                cl_03_tow_upd += f" Стоимость (было:{tow_dict[tow_id]['cost_raw']} ₽, " \
                                                 f"стало:{tow_list_to_dict[tow_id]['cost']} ₽)"
                                change_log['03_tow_upd'].append(cl_03_tow_upd)

                            else:
                                check_towc = tow_dict[tow_id]['cost_raw']
                                # print('    == 1 0 ==', tow_dict[tow_id]['cost_raw'])
                        elif not tow_dict[tow_id]['cost_raw']:
                            check_towc = tow_list_to_dict[tow_id]['cost']
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            # print('    == 2 ==', tow_dict[tow_id]['cost_raw'], tow_list_to_dict[tow_id]['cost'])
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" Стоимость (было: - , " \
                                             f"стало:{tow_list_to_dict[tow_id]['cost']} ₽)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)
                        # Никаких изменений у tow не было
                        else:
                            check_towc = 0
                            if tow_dict[tow_id]['cost_raw']:
                                check_towc = tow_dict[tow_id]['cost_raw']
                            elif tow_dict[tow_id]['percent_raw']:
                                check_towc = payment_cost * tow_dict[tow_id]['percent_raw'] / 100

                    # Указаны проценты
                    elif tow_list_to_dict[tow_id]['percent']:
                        # print('percent')
                        if (tow_dict[tow_id]['percent_raw'] and
                                tow_dict[tow_id]['percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                            check_towc = payment_cost * tow_list_to_dict[tow_id]['percent'] / 100
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" % суммы (было:{tow_dict[tow_id]['percent_raw']} %, " \
                                             f"стало:{tow_list_to_dict[tow_id]['percent']} %)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)

                        elif (tow_list_to_dict[tow_id]['percent'] and
                              tow_dict[tow_id]['percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                            check_towc = payment_cost * tow_list_to_dict[tow_id]['percent'] / 100
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            tow_id_set_upd.add(tow_id)

                            # Для логирования
                            if not change_log['03_tow_upd']:
                                change_log['03_tow_upd'].append('Измененные виды работ:')
                            cl_03_tow_upd += f" % суммы (было:{tow_dict[tow_id]['percent_raw']} %, " \
                                             f"стало:{tow_list_to_dict[tow_id]['percent']} %)"
                            change_log['03_tow_upd'].append(cl_03_tow_upd)
                        # Никаких изменений у tow не было
                        else:
                            check_towc = 0
                            if tow_dict[tow_id]['cost_raw']:
                                check_towc = tow_dict[tow_id]['cost_raw']
                            elif tow_dict[tow_id]['percent_raw']:
                                check_towc = payment_cost * tow_dict[tow_id]['percent_raw'] / 100

                else:
                    # print('      else')
                    if tow_dict[tow_id]['cost_raw']:
                        check_towc = tow_dict[tow_id]['cost_raw']
                    elif tow_dict[tow_id]['percent_raw']:
                        check_towc = payment_cost * tow_dict[tow_id]['percent_raw'] / 100

                check_pc = check_pc - check_towc

            if check_pc < -0.01:
                check_pc = round(check_pc, 2)
                if check_pc <= -1:
                    description.extend([
                        f"Общая стоимость видов работ акта превысила стоимость акта на {-check_pc} ₽.",
                        f"Скорректируйте стоимость акта или видов работ"])
                    return {
                        'status': 'error',
                        'description': description
                    }
                elif lst_cost_tow:
                    if lst_cost_tow['cost']:
                        lst_cost_tow['cost'] += check_pc
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_pc} ₽.",
                            f"У последнего созданного/измененного вида работ была изменена стоимость:",
                            f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                        ])
                    elif lst_cost_tow['percent']:
                        lst_cost_tow['cost'] = round((payment_cost * lst_cost_tow['percent'] / 100) + check_pc, 2)
                        lst_cost_tow['percent'] = None
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_pc} ₽.",
                            f"У последнего созданного/измененного вида работ была изменена стоимость:",
                            f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                        ])
                    else:
                        description.extend([
                            f"Общая стоимость видов работ акта превысила стоимость акта на {-check_pc} ₽.",
                            f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                            f"в котором можно произвести корректировку стоимости"
                        ])
                        return {
                            'status': 'error',
                            'description': description
                        }
                elif not lst_cost_tow:
                    description.extend([
                        f"Общая стоимость видов работ акта превышает стоимость акта на {-check_pc} ₽.",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # ДОБАВЛЕНИЕ TOW
            if tow_id_list_ins:
                for tow_id in tow_id_list_ins:
                    values_tp_ins.append([
                        payment_id,
                        tow_list_to_dict[tow_id]['id'],
                        tow_list_to_dict[tow_id]['cost'],
                        tow_list_to_dict[tow_id]['percent']
                    ])

            # УДАЛЕНИЕ TOW
            columns_tp_del = 'payment_id::int, tow_id::int'
            values_tp_del = []
            if tow_id_list_del:
                for i in tow_id_list_del:
                    values_tp_del.append((payment_id, i))

                    # Для логирования
                    if not change_log['04_tow_del']:
                        change_log['04_tow_del'].append('Удаленные виды работ:')
                    if tow_dict[i]['cost_raw']:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: стоимость ({tow_dict[i]['cost_raw']} ₽)"
                    elif tow_dict[i]['percent_raw']:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: % суммы ({tow_dict[i]['percent_raw']} %)"
                    else:
                        cl_02_tow_del = f" - {tow_dict[i]['tow_name']}: стоимость не указана"
                    change_log['04_tow_del'].append(cl_02_tow_del)

            # ОБНОВЛЕНИЕ TOW
            columns_tp_upd = [['payment_id::integer', 'tow_id::integer'], 'tow_cost::numeric',
                              'tow_cost_percent::numeric']
            if tow_id_set_upd:
                for tow_id in tow_id_set_upd:
                    values_tp_upd.append([
                        payment_id,
                        tow_list_to_dict[tow_id]['id'],
                        tow_list_to_dict[tow_id]['cost'],
                        tow_list_to_dict[tow_id]['percent']
                    ])

            # Для payments
            if len(columns_p) > 1:
                query_p = app_payment.get_db_dml_query(action='UPDATE', table='payments', columns=columns_p)
                execute_values(cursor, query_p, values_p)
            # Для tows_act
            if len(values_tp_ins):
                action = 'INSERT INTO'
                query_tp_ins = app_payment.get_db_dml_query(action=action, table=table_tp, columns=columns_tp_ins,
                                                            subquery=subquery)
                execute_values(cursor, query_tp_ins, values_tp_ins)

            if len(values_tp_upd):
                action = 'UPDATE DOUBLE'
                query_tp_upd = app_payment.get_db_dml_query(action=action, table=table_tp, columns=columns_tp_upd)
                execute_values(cursor, query_tp_upd, values_tp_upd)

            if len(values_tp_del):
                action = 'DELETE'
                query_tc_del = app_payment.get_db_dml_query(action=action, table=table_tp, columns=columns_tp_del,
                                                            subquery=subquery)
                execute_values(cursor, query_tc_del, (values_tp_del,))

            if len(columns_p) > 1 or len(values_tp_ins) or len(values_tp_upd) or len(values_tp_del):
                conn.commit()
                status = 'success'
                description.append('Изменения в платеже сохранены')
                flash(message=[f"Платеж №: {payment_number} сохранён", ], category='success')
            else:
                status = 'success'
                description.append('В платеже не найдено изменений')
                flash(message=[f"В платеже №: {payment_number} не найдено изменений", ], category='success')

            # Для логирования
            # Для логирования
            cc_description = ''
            if payment_type_id == 1:
                cc_description = f"Изменен платеж №: {payment_number} договора №: {payment_info['contract_number']} " \
                                 f"по объекту: \"{object_name}\""
            else:
                cc_description = f"Изменен платеж №: {payment_number} акта №: {payment_info['act_number']}" \
                                 f"договора №: {payment_info['contract_number']} по объекту: \"{object_name}\""
            if change_log['cc_description'] == [False]:
                change_log['cc_description'] = [cc_description]
            else:
                change_log['cc_description'].insert(0, cc_description)
            change_log['cc_action_type'] = 'update'

            add_contracts_change_log(change_log)

            return jsonify({
                'status': status,
                'description': description,
            })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


def including_tax(cost: float, vat: [int, float]) -> float:
    try:
        cost = float(cost) if cost else 0
        return round(cost / vat, 2)

    except Exception as e:
        current_app.logger.exception(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return cost


def including_tax_reverse(cost: float, vat: [int, float]) -> float:
    try:
        cost = float(cost) if cost else 0
        return round(cost * vat, 2)

    except Exception as e:
        current_app.logger.exception(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return cost


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

    if page_name == 'contract-main':
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
    elif page_name == 'contract-objects':
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
    elif page_name == 'contract-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = "to_char(t8.contract_status_date, 'dd.mm.yyyy')"
        col_5 = "to_char(t1.date_start, 'dd.mm.yyyy')"
        col_6 = "to_char(t1.date_finish, 'dd.mm.yyyy')"
        col_7 = "t1.subcontract_number"
        col_8 = "to_char(t1.subdate_start, 'dd.mm.yyyy')"
        col_9 = "to_char(t1.subdate_finish, 'dd.mm.yyyy')"
        col_10 = """CASE 
                    WHEN t1.type_id = 1 THEN t5.partner_name
                    WHEN t1.type_id = 2 THEN t4.contractor_name
                    ELSE ' '
                END"""
        col_11 = """CASE 
                    WHEN t1.type_id = 1 THEN t4.contractor_name
                    WHEN t1.type_id = 2 THEN t5.partner_name
                    ELSE ' '
                END"""
        col_12 = "t1.contract_description"
        col_13 = "t6.status_name"
        col_14 = "t1.allow"
        col_15 = "t1.vat"
        col_16 = "COALESCE(ROUND(t1.contract_cost / t1.vat::numeric, 2), '0')"
        col_17 = "to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
        list_filter_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16, col_17
        ]
        # столбцы сортировки
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = f"COALESCE(t8.contract_status_date, '{sort_sign}infinity'::date)"
        col_5 = f"COALESCE(t1.date_start, '{sort_sign}infinity'::date)"
        col_6 = f"COALESCE(t1.date_finish, '{sort_sign}infinity'::date)"
        col_7 = "t1.subcontract_number"
        col_8 = f"COALESCE(t1.subdate_start, '{sort_sign}infinity'::date)"
        col_9 = f"COALESCE(t1.subdate_finish, '{sort_sign}infinity'::date)"
        col_10 = """CASE 
                    WHEN t1.type_id = 1 THEN t5.partner_name
                    WHEN t1.type_id = 2 THEN t4.contractor_name
                    ELSE ' '
                END"""
        col_11 = """CASE 
                    WHEN t1.type_id = 1 THEN t4.contractor_name
                    WHEN t1.type_id = 2 THEN t5.partner_name
                    ELSE ' '
                END"""
        col_12 = "COALESCE(t1.contract_description, '')"
        col_13 = "t6.status_name"
        col_14 = "t1.allow::text"
        col_15 = "t1.vat::text"
        col_16 = "COALESCE(ROUND(t1.contract_cost / t1.vat::numeric, 2), '0')"
        col_17 = "t1.created_at"
        list_sort_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16, col_17
        ]
        # типы данных столбцов
        col_0 = ""
        col_1 = "t2.object_name"
        col_2 = "t3.type_name"
        col_3 = "t1.contract_number"
        col_4 = "t8.contract_status_date"
        col_5 = "t1.date_start"
        col_6 = "t1.date_finish"
        col_7 = "t1.contract_number"
        col_8 = "t1.date_start"
        col_9 = "t1.date_finish"
        col_10 = "t1.contract_number"
        col_11 = "t1.contract_number"
        col_12 = "t1.contract_description"
        col_13 = "t6.status_name"
        col_14 = "t1.contract_number"
        col_15 = "t1.contract_number"
        col_16 = "t1.contract_cost"
        col_17 = "t1.created_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
            col_14, col_15, col_16, col_17
        ]
    elif page_name == 'contract-acts-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t1.act_number"
        col_5 = "to_char(t1.act_date, 'dd.mm.yyyy')"
        col_6 = "t2.status_name"
        col_7 = "t3.vat"
        col_8 = "COALESCE(ROUND(t1.act_cost / t3.vat::numeric, 2), '0')"
        col_9 = "t5.count_tow"
        col_10 = "t3.allow"
        col_11 = "to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
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
        col_7 = "t3.vat::text"
        col_8 = "COALESCE(ROUND(t1.act_cost / t3.vat::numeric, 2), '0')"
        col_9 = "t5.count_tow"
        col_10 = "t3.allow::text"
        col_11 = "t1.created_at"
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
        col_11 = "t1.created_at"
        list_type_col = [
            col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11
        ]
        query_value = []
    elif page_name == 'contract-payments-list':
        # столбцы фильтров
        col_0 = ""
        col_1 = "t4.object_name"
        col_2 = "t7.type_name"
        col_3 = "t3.contract_number"
        col_4 = "t8.payment_type_name"
        col_5 = "t9.act_number"
        col_6 = "t1.payment_number"
        col_7 = "to_char(t1.payment_date, 'dd.mm.yyyy')"
        col_8 = "t3.vat"
        col_9 = "COALESCE(ROUND(t1.payment_cost / t3.vat_value::numeric, 2), '0')"
        col_10 = "t3.allow"
        col_11 = "to_char(t1.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')"
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
        col_8 = "t3.vat::text"
        col_9 = "COALESCE(ROUND(t1.payment_cost / t3.vat_value::numeric, 2), '0')"
        col_10 = "t3.allow::text"
        col_11 = "t1.created_at"
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
        col_9 = "t1.payment_cost"
        col_10 = "t3.contract_number"
        col_11 = "t1.created_at"
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

    # if col_1_val:
    #     where_expression = (
    #         f"({sort_col_1}, {sort_col_id}) {sort_col_1_equal} "
    #         f"({app_payment.conv_data_to_db(list_type_col[col_num], col_1_val, all_col_types)}, "
    #         f"{app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)})")
    # else:
    #     where_expression = (
    #         f"{sort_col_id} {sort_col_1_equal} {app_payment.conv_data_to_db(sort_col_id, col_id_val, all_col_types)}")

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
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return None


def get_header_menu(role: int = 0, link: str = '', cur_name: int = 0):
    # Если указана страница проекта
    if link:
        # Админ и директор, юрист
        if role in (1, 4, 5):
            header_menu = [
                {'link': f'/objects/{link}', 'name': 'В проект'},
                {'link': f'/objects/{link}/contract-list', 'name': 'Договоры'},
                {'link': f'/objects/{link}/contract-acts-list', 'name': 'Акты'},
                {'link': f'/objects/{link}/contract-payments-list', 'name': 'Платежи'}
            ]
        else:
            header_menu = [
                {'link': f'/objects/{link}', 'name': 'В проект'}
            ]
    else:
        # Админ и директор
        if role in (1, 4, 5):
            header_menu = [
                {'link': f'/contract-main', 'name': 'Свод'},
                {'link': f'/contract-objects', 'name': 'Объекты'},
                {'link': f'/contract-list', 'name': 'Договоры'},
                {'link': f'/contract-acts-list', 'name': 'Акты'},
                {'link': f'/contract-payments-list', 'name': 'Платежи'}
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
                    link_name,
                    project_full_name
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
                    link_name,
                    project_full_name
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
                    link_name,
                    project_full_name
                FROM projects 

                WHERE link_name = %s 
                LIMIT 1;""",
                [link_name]
            )

        object_info = cursor.fetchone()
        app_login.conn_cursor_close(cursor, conn)
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        object_info = None
    return object_info


def get_obj_list():
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Список объектов по которым созданы проекты
        cursor.execute(
            """
            SELECT
                t1.project_id,
                t2.object_id,
                t2.object_name
            FROM projects as t1
            LEFT JOIN objects as t2 ON t1.object_id=t2.object_id
            ORDER BY t2.object_name;
            """
        )
        obj_list = cursor.fetchall()
        if obj_list:
            for i in range(len(obj_list)):
                obj_list[i] = dict(obj_list[i])
        app_login.conn_cursor_close(cursor, conn)
    except Exception as e:
        current_app.logger.exception(f"url {request.path[1:]}  -  _get_proj_id_  -  {e}")
        obj_list = None
    return obj_list


@contract_app_bp.route('/tow-list-for-object/<int:object_id>/<int:type_id>/<contract_id>', methods=['POST'])
@login_required
def tow_list_for_object(object_id, type_id, contract_id=''):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']
        # Указываем id, который точно не может быть в БД
        contract_id = -100 if contract_id == 'new' else int(contract_id)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")
        # Список tow
        cursor.execute(
            CONTRACT_TOW_LIST1,
            [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
        )
        tow = cursor.fetchall()
        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

        # Находим номера всех договоров объекта (без субподрядных)
        cursor.execute(
            CONTRACTS_LIST_WITHOUT_SUB,
            [object_id, type_id]
        )
        contracts = cursor.fetchall()
        if contracts:
            for i in range(len(contracts)):
                contracts[i] = dict(contracts[i])

        # Общая стоимость субподрядных договоров объекта
        cursor.execute(
            """
                SELECT 
                    TRIM(BOTH ' ' FROM to_char(COALESCE(SUM(tow_cost), 0), '999 999 990D99 ₽')) AS tow_cost
                FROM tows_contract
                WHERE 
                    contract_id IN
                        (SELECT
                            contract_id
                        FROM contracts
                        WHERE object_id = %s AND type_id = 2)
                    AND 
                    tow_id IN
                        (SELECT
                            tow_id
                        FROM types_of_work
                        --Для Кати нужен любой tow, даже без отдела
                        --WHERE dept_id IS NOT NULL
                        ); 
                """,
            [object_id]
        )
        subcontractors_cost = cursor.fetchone()[0]

        # Список отделов
        dept_list = app_project.get_main_dept_list(user_id)

        # Return the updated data as a response
        return jsonify({
            'status': 'success',
            'tow': tow,
            'dept_list': dept_list,
            'contracts': contracts,
            'subcontractors_cost': subcontractors_cost,
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


@contract_app_bp.route('/save_new_partner', methods=['POST'])
@login_required
def save_new_partner():
    try:
        try:
            user_id = app_login.current_user.get_id()
        except:
            user_id = None
        try:
            short_name = request.get_json()['short_name']
        except:
            short_name = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=short_name, user_id=user_id)

        full_name = request.get_json()['full_name']

        conn, cursor = app_login.conn_cursor_init_dict('contracts')

        action = 'INSERT INTO'
        table = 'partners'
        columns = ('partner_name', 'partner_short_name')
        subquery = " ON CONFLICT DO NOTHING RETURNING partner_id;"
        query = app_payment.get_db_dml_query(action=action, table=table, columns=columns, subquery=subquery)
        values = [[full_name, short_name]]
        execute_values(cursor, query, values)
        partner_id = cursor.fetchall()

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        if partner_id:
            return jsonify({
                'status': 'success',
                'id': partner_id,
            })

        return jsonify({
            'status': 'error',
            'description': ["Контрагент с полным или коротким именем уже существует в базе данных"],
        })
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [str(e)],
        })


@contract_app_bp.route('/delete_contract', methods=['POST'])
@login_required
def delete_contract():
    try:
        user_id = app_login.current_user.get_id()
        try:
            contract_id = request.get_json()['contract_id']
        except:
            contract_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=contract_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        text_comment = request.get_json()['text_comment']

        conn, cursor = app_login.conn_cursor_init_dict('contracts')

        # Ищем причины не удалять договор:)
        description = ["Договор нельзя удалить, т.к. к нему привязано "]
        flag_act = False
        cnt_act = 0
        flag_payment = False
        cnt_payment = 0

        # Находим id
        cursor.execute(
            """
                    SELECT
                        object_id,
                        contract_number
                    FROM contracts
                    WHERE contract_id = %s
                    """,
            [contract_id, ]
        )
        object_id = cursor.fetchone()
        if not object_id:
            return jsonify({
                'status': 'error',
                'description': ["Договор не найден "],
            })
        proj_info = get_proj_id(object_id=object_id["object_id"])

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [object_id["object_id"]])
        object_name = cursor.fetchone()[0]

        # Проверяем, есть ли допники у договора
        cursor.execute(
            """
                    SELECT
                        t2.contract_number,
                        to_char(t2.created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at
                    FROM subcontract AS t1
                    LEFT JOIN
                        (SELECT 
                            contract_id,
                            contract_number,
                            created_at
                        FROM contracts) 
                    AS t2 ON t1.child_id = t2.contract_id
                    WHERE t1.parent_id = %s
                    """,
            [contract_id, ]
        )
        subcontracts = cursor.fetchall()
        if subcontracts:
            description.append("Список дополнительных соглашений:")
            for i in range(len(subcontracts)):
                subcontracts[i] = dict(subcontracts[i])
                description.append(f"Доп.согл. №: {subcontracts[i]['contract_number']}. "
                                   f"Создан: {subcontracts[i]['created_at']}")

        # Проверяем, есть ли платежи и акты по договору
        cursor.execute(
            """
                    SELECT
                        act_id AS id,
                        'Акт' AS type,
                        act_number AS name,
                        to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at
                    FROM acts
                    WHERE contract_id = %s
                    UNION ALL
                    SELECT
                        payment_id AS id,
                        'Платеж' AS type,
                        payment_number AS name,
                        to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at
                    FROM payments
                    WHERE contract_id = %s
                    ORDER BY type, id;
                    """,
            [contract_id, contract_id]
        )
        acts_payments_of_contract = cursor.fetchall()
        if acts_payments_of_contract:
            for i in range(len(acts_payments_of_contract)):
                acts_payments_of_contract[i] = dict(acts_payments_of_contract[i])

                if acts_payments_of_contract[i]['type'] == 'Акт':
                    cnt_act += 1
                    if not flag_act:
                        flag_act = True
                        description.append("Список привязанных актов:")
                elif acts_payments_of_contract[i]['type'] == 'Платеж':
                    cnt_payment += 1
                    if not flag_payment:
                        flag_payment = True
                        description.append("Список привязанных платежей:")

                description.append(f"{acts_payments_of_contract[i]['type']} №: {acts_payments_of_contract[i]['name']}. "
                                   f"Создан: {acts_payments_of_contract[i]['created_at']}")

        # Конструктор для описания первой строки с причинами для ошибки
        if subcontracts or acts_payments_of_contract:
            if subcontracts:
                description[0] += f"{len(subcontracts)} договоров, "
            if flag_act:
                description[0] += f"{cnt_act} актов, "
            if flag_payment:
                description[0] += f"{cnt_payment} платежей, "
            description[0] = description[0][:-2]

            return jsonify({
                'status': 'error',
                'description': description,
            })

        # Удаляем все виды работ договора из таблицы tows_contract
        subquery = 'ON CONFLICT DO NOTHING'

        query_c_del = app_payment.get_db_dml_query(action='DELETE', table='contracts', columns='contract_id::int')
        values_c_del = (contract_id,)

        execute_values(cursor, query_c_del, (values_c_del,))

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        # Для логирования
        cc_description = \
            [f"Удален договор №: {object_id['contract_number']} по объекту: \"{object_name}\"", text_comment]
        change_log = {
            'cc_id': contract_id,
            'cc_type': 'contract',
            'cc_action_type': 'delete',
            'cc_description': cc_description,
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }

        add_contracts_change_log(change_log)

        flash(message=[f"Договор №: {object_id['contract_number']} удалён", ], category='success')
        return jsonify({
            'status': 'success',
            'description': ['Договор удалён'],
            'link': proj_info['link_name'],
        })


    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@contract_app_bp.route('/delete_act', methods=['POST'])
@login_required
def delete_act():
    try:
        user_id = app_login.current_user.get_id()

        try:
            act_id = request.get_json()['act_id']
        except:
            act_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=act_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        text_comment = request.get_json()['text_comment']

        conn, cursor = app_login.conn_cursor_init_dict('contracts')

        # Ищем причины не удалять акт:)
        description = ["Акт нельзя удалить, т.к. к нему привязаны платежи "]
        flag_act = False
        cnt_act = 0
        flag_payment = False
        cnt_payment = 0

        # Находим id
        cursor.execute(
            """
                SELECT
                    t2.object_id,
                    t1.act_number,
                    t2.contract_number
                FROM acts AS t1
                LEFT JOIN (
                    SELECT 
                        object_id,
                        contract_id,
                        contract_number
                    FROM contracts
                ) AS t2 ON t1.contract_id = t2.contract_id
                WHERE t1.act_id = %s
                """,
            [act_id, ]
        )
        object_id = cursor.fetchone()

        if not object_id:
            return jsonify({
                'status': 'error',
                'description': ["Акт не найден "],
            })
        proj_info = get_proj_id(object_id=object_id["object_id"])

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [object_id["object_id"]])
        object_name = cursor.fetchone()[0]

        # Проверяем, есть ли платежи и акты по договору
        cursor.execute(
            """
                SELECT
                    payment_id AS id,
                    'Платеж' AS type,
                    payment_number AS name,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at
                FROM payments
                WHERE act_id = %s
                ORDER BY type, id;
                """,
            [act_id]
        )
        payments_of_act = cursor.fetchall()
        if payments_of_act:
            for i in range(len(payments_of_act)):
                payments_of_act[i] = dict(payments_of_act[i])

                cnt_payment += 1
                if not flag_payment:
                    flag_payment = True
                    description.append("Список привязанных платежей:")

                description.append(f"{payments_of_act[i]['type']} №: {payments_of_act[i]['name']}. "
                                   f"Создан: {payments_of_act[i]['created_at']}")

        # Конструктор для описания первой строки с причинами для ошибки
        if payments_of_act:
            if flag_payment:
                description[0] += f"{cnt_payment} платежей, "
            description[0] = description[0][:-2]

            return jsonify({
                'status': 'error',
                'description': description,
            })

        # Удаляем все виды работ акта из таблицы tows_act
        subquery = 'ON CONFLICT DO NOTHING'

        query_a_del = app_payment.get_db_dml_query(action='DELETE', table='acts', columns='act_id::int')
        values_a_del = (act_id,)
        execute_values(cursor, query_a_del, (values_a_del,))

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        # Для логирования
        cc_description = \
            [f"Удален акт №: {object_id['act_number']} договора №: {object_id['contract_number']} "
             f"по объекту: \"{object_name}\"", text_comment]
        change_log = {
            'cc_id': act_id,
            'cc_type': 'act',
            'cc_action_type': 'delete',
            'cc_description': cc_description,
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }

        add_contracts_change_log(change_log)

        flash(message=[f"Акт №: {object_id['act_number']} удалён", ], category='success')
        return jsonify({
            'status': 'success',
            'description': ['Акт удалён'],
            'link': proj_info['link_name'],
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@contract_app_bp.route('/delete_contract_payment', methods=['POST'])
@login_required
def delete_contract_payment():
    try:
        user_id = app_login.current_user.get_id()
        try:
            payment_id = request.get_json()['payment_id']
        except:
            payment_id = None
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=payment_id, user_id=user_id)

        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        text_comment = request.get_json()['text_comment']

        conn, cursor = app_login.conn_cursor_init_dict('contracts')

        # Ищем причины не удалять платеж :)
        description = ["Платеж не найден "]
        # Ищем, есть ли платеж в БД
        cursor.execute(
            """
                    SELECT
                        t1.*,
                        t2.object_id,
                        t1.payment_type_id,
                        t2.contract_number,
                        t3.act_number
                    FROM payments AS t1
                    LEFT JOIN (
                        SELECT 
                            object_id,
                            contract_id,
                            contract_number
                        FROM contracts
                    ) AS t2 ON t1.contract_id = t2.contract_id
                    LEFT JOIN (
                        SELECT 
                            act_id,
                            act_number
                        FROM acts
                    ) AS t3 ON t1.act_id = t3.act_id
                    WHERE t1.payment_id = %s
                    """,
            [payment_id, ]
        )
        payment_info = cursor.fetchone()
        if payment_info:
            payment_info = dict(payment_info)
        else:
            return jsonify({
                'status': 'error',
                'description': description,
            })

            # Удаляем все виды работ договора из таблицы tows_contract
        subquery = 'ON CONFLICT DO NOTHING'

        query_p_del = app_payment.get_db_dml_query(action='DELETE', table='payments', columns='payment_id::int')
        values_p_del = (payment_id,)
        execute_values(cursor, query_p_del, (values_p_del,))

        query_p_del = app_payment.get_db_dml_query(action='DELETE', table='payments', columns='payment_id::int')
        values_p_del = (payment_id,)
        execute_values(cursor, query_p_del, (values_p_del,))

        conn.commit()

        proj_info = get_proj_id(object_id=payment_info["object_id"])

        cursor.execute("SELECT object_name FROM objects WHERE object_id = %s;", [payment_info["object_id"]])
        object_name = cursor.fetchone()[0]

        app_login.conn_cursor_close(cursor, conn)

        # Для логирования
        cc_description = [text_comment]
        if payment_info['payment_type_id'] == 1:
            cc_description = \
                [f"Удален платеж №: {payment_id} договора №: {payment_info['contract_number']} "
                 f"по объекту: \"{object_name}\"", text_comment]
        elif payment_info['payment_type_id'] == 2:
            cc_description = \
                [f"Удален платеж №: {payment_id} акта №: {payment_info['act_number']} "
                 f"договора №: {payment_info['contract_number']} по объекту: \"{object_name}\"", text_comment]
        change_log = {
            'cc_id': payment_id,
            'cc_type': 'payment',
            'cc_action_type': 'delete',
            'cc_description': cc_description,
            'cc_value_previous': None,
            'cc_value_current': None,
            'cc_new': False,
            '01_card': [],
            '02_tow_ins': [],
            '03_tow_upd': [],
            '04_tow_del': [],
            'user_id': user_id,
        }

        add_contracts_change_log(change_log)

        flash(message=[f"Платеж №: {payment_info['payment_number']} удалён", ], category='success')
        return jsonify({
            'status': 'success',
            'description': ['Платеж удалён'],
            'link': proj_info['link_name'],
        })


    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


def add_contracts_change_log(data):
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        conn, cursor = app_login.conn_cursor_init_dict('contracts')
        cc_id = data['cc_id']
        cc_type = data['cc_type']
        cc_action_type = data['cc_action_type']
        cc_description = data['cc_description']
        cc_value_previous = data['cc_value_previous']
        cc_value_current = data['cc_value_current']
        cc_new = data['cc_new']
        user_id = data['user_id']
        cc_01_card = data['01_card']
        cc_02_tow_ins = data['02_tow_ins']
        cc_03_tow_upd = data['03_tow_upd']
        cc_04_tow_del = data['04_tow_del']

        if cc_01_card:
            cc_description.extend(cc_01_card)
        if cc_02_tow_ins:
            cc_description.extend(cc_02_tow_ins)
        if cc_03_tow_upd:
            cc_description.extend(cc_03_tow_upd)
        if cc_04_tow_del:
            cc_description.extend(cc_04_tow_del)
        query_ccl = """
            INSERT INTO contracts_change_log (
                cc_id,
                cc_type,
                cc_action_type,
                cc_description,
                cc_value_previous,
                cc_value_current,
                cc_owner_id,
                cc_new
            )
            VALUES %s;
            """
        values_ccl = [
            (cc_id, cc_type, cc_action_type, cc_description, cc_value_previous, cc_value_current, user_id, cc_new)]

        execute_values(cursor, query_ccl, values_ccl)
        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


@contract_app_bp.route('/merge_tow_row/<int:contract_tow_id>/<int:raw_tow_id>', methods=['POST'])
@login_required
def merge_tow_row(contract_tow_id: int = None, raw_tow_id: int = None):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name,
                               log_description=f"raw_tow_id: {raw_tow_id}, contract_tow_id: {contract_tow_id}",
                               user_id=user_id)

        conn, cursor = app_login.conn_cursor_init_dict('objects')
        # Проверяем, что виды работ из одного проекта
        cursor.execute(
            """
            SELECT
                tow_id,
                project_id,
                nlevel(path) - 1 AS nlevel,
                path,
                lvl
            FROM types_of_work 

            WHERE tow_id IN %s;""",
            [(contract_tow_id, raw_tow_id)]
        )

        tmp_check_same_proj = cursor.fetchall()
        check_same_proj = None
        if tmp_check_same_proj:
            check_same_proj = dict()
            for i in range(len(tmp_check_same_proj)):
                check_same_proj[tmp_check_same_proj[i]['tow_id']] = dict(tmp_check_same_proj[i])

            if check_same_proj[contract_tow_id]['project_id'] != check_same_proj[raw_tow_id]['project_id']:
                return jsonify({'status': 'error', 'description': ['Ошибка', 'Ошибка проверки видов работ rev.1']})
            proj_info = get_proj_id(project_id=check_same_proj[contract_tow_id]['project_id'])
        elif not check_same_proj or len(check_same_proj) != 2:
            return jsonify({'status': 'error', 'description': ['Ошибка', 'Ошибка проверки видов работ rev.2']})

        link_name = proj_info['link_name']
        project_id = proj_info['project_id']
        # Проверяем, что lvl самого дальнего ребенка при слиянии не превысит lvl 10/*
        cursor.execute(
            """
            SELECT
                tow_id,
                path,
                lvl,
                nlevel(path) - 1 AS path
            FROM types_of_work
            WHERE project_id = %s AND path <@ %s
            ORDER BY nlevel(path) - 1 DESC, lvl;""",
            [project_id, check_same_proj[raw_tow_id]['path']]
        )
        lst_child = cursor.fetchone()

        lst_child_lvl = lst_child['lvl']
        contract_lvl = check_same_proj[contract_tow_id]['lvl']
        raw_lvl = check_same_proj[raw_tow_id]['lvl']
        new_lst_child_lvl = contract_lvl - raw_lvl + lst_child_lvl
        if new_lst_child_lvl > 9:
            return jsonify({'status': 'error',
                            'description': [
                                'Ошибка', 'Объединение не возможно',
                                f'Уровень вложенности у дочернего объекта превышает 10 ({new_lst_child_lvl} ур.)']})

        # Переводим все связанные с raw_tow_id данные к contract_tow_id
        query_upd = "UPDATE types_of_work SET parent_id = %s WHERE parent_id = %s;"
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^ types_of_work', query_upd, [(raw_tow_id, contract_tow_id)])
        cursor.execute(query_upd, [contract_tow_id, raw_tow_id])

        # Удаляем raw_tow
        query_del = "DELETE FROM types_of_work WHERE tow_id = %s;"
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^ types_of_work', query_del, (raw_tow_id,))
        execute_values(cursor, query_del, ((raw_tow_id,),))

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        flash(message=['Виды работ объединены'], category='success')

        return jsonify(
            {'status': 'success', 'url': f'/objects/{link_name}/tow', 'description': ['Виды работ объединены']})


    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info())
        return jsonify({'status': 'error',
                        'description': msg_for_user,
                        })
