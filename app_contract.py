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
            CASE 
                WHEN vat_value = 1 THEN false
                ELSE true
            END AS vat,
            vat_value,
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
        t2_2.vat,
        t2_2.vat_value,
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
            CASE 
                WHEN vat_value = 1 THEN false
                ELSE true
            END AS vat,
            vat_value,
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
    t1.vat,
    t1.contract_cost,
    TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')) AS contract_cost_rub,
    t1.contract_cost * t1.vat_value AS contract_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.contract_cost * t1.vat_value, '999 999 990D99 ₽')) AS contract_cost_with_vat_rub,
    to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS create_at_txt,
    t1.create_at::timestamp without time zone::text AS create_at
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
        allow,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
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
    t1.act_cost,
    TRIM(BOTH ' ' FROM to_char(t1.act_cost, '999 999 990D99 ₽')) AS act_cost_rub,
    t1.act_cost * t3.vat_value AS act_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.act_cost * t3.vat_value, '999 999 990D99 ₽')) AS act_cost_with_vat_rub,
    t5.count_tow,
    t3.vat_value,
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
        allow,
        type_id,
        CASE 
            WHEN vat_value = 1 THEN false
            ELSE true
        END AS vat,
        vat_value
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
    t1.payment_cost,
    TRIM(BOTH ' ' FROM to_char(t1.payment_cost, '999 999 990D99 ₽')) AS payment_cost_rub,
    t1.payment_cost * t3.vat_value AS payment_cost_with_vat,
    TRIM(BOTH ' ' FROM to_char(t1.payment_cost * t3.vat_value, '999 999 990D99 ₽')) AS payment_cost_without_vat_rub,
    t3.vat_value,
    t3.allow,
    t1.create_at,
    to_char(t1.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS')  AS create_at_txt
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
    COALESCE(t1.fot_percent::text, '') AS fot_percent_txt,
    t1.contract_cost,
    ROUND(t1.contract_cost * t1.vat_value::numeric, 2) AS contract_cost_vat,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')), '') AS contract_cost_rub,
    t1.allow,
    t1.fot_percent,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost * t1.fot_percent / 100, '999 999 990D99 ₽')), '') AS contract_fot_cost_rub,
    t1.create_at,
    CASE 
        WHEN t1.vat_value = 1 THEN false
        ELSE true
    END AS vat,
    t1.vat_value,
    t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0) AS undistributed_cost_vat_not_calc,
    TRIM(BOTH ' ' FROM to_char(
        t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0),
    '999 999 990D99 ₽')) AS undistributed_cost_vat_not_calc_rub,
    
    ROUND((t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0)) * t1.vat_value::numeric, 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND((t1.contract_cost - COALESCE(t5.tow_cost + t1.contract_cost * t5.tow_cost_percent / 100, 0)) * t1.vat_value::numeric, 2),
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
WHERE t1.contract_id = %s;
"""

CONTRACT_TOW_LIST = """
WITH
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
    t2.tow_date_start,
    t2.tow_date_finish,
    COALESCE(to_char(t2.tow_date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
    COALESCE(to_char(t2.tow_date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,
    
    t2.tow_cost::float AS tow_cost_raw,
    t2.tow_cost_percent::float AS tow_cost_percent_raw,
        
    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        ELSE t3.contract_cost * t2.tow_cost_percent / 100
    END AS tow_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t3.contract_cost * t2.tow_cost_percent / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_cost_rub,
    
    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND(t2.tow_cost * t3.vat_value::numeric, 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t2.tow_cost_percent / 100) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND(t2.tow_cost * t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(ROUND((t3.contract_cost * t2.tow_cost_percent / 100) * t3.vat_value::numeric, 2), '999 999 990D99 ₽')), '')
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
    
    t2.tow_cost_percent AS tow_cost_percent2,
    COALESCE(t2.tow_cost_percent::text, '') AS tow_cost_percent2_txt,
    
    CASE 
        WHEN t2.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
    CASE 
        WHEN t2.tow_cost != 0 THEN '₽'
        WHEN t2.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,
    --COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent AS tow_fot_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost * t3.fot_percent
        WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
        ELSE 0
    END AS tow_fot_cost,
    /*COALESCE(TRIM(BOTH ' ' FROM to_char(
            COALESCE(t2.tow_cost, t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent
        , '999 999 990D99 ₽')), '') AS tow_fot_cost_rub,*/
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost * t3.fot_percent, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char((t3.contract_cost * t2.tow_cost_percent / 100) * t3.fot_percent, '999 999 990D99 ₽')), '')
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
    t5.summary_subcontractor_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t5.summary_subcontractor_cost, '999 999 990D99 ₽')), '') 
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
    
    COALESCE(
    ROUND(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost) * t3.vat_value::numeric, 2)
    ::text, '') AS tow_cost_protect_txt,
    
    
    COALESCE(GREATEST(t6.summary_acts_cost, t7.summary_payments_cost), 0)::float AS tow_cost_protect,
    t6.summary_acts_cost,
    t7.summary_payments_cost
        
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
        SUM(COALESCE(t51.tow_cost, t51.tow_cost_percent*t52.contract_cost/100)) 
                        AS summary_subcontractor_cost
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

CONTRACTS_LIST = """
SELECT
    contract_id,
    contract_number
FROM contracts
WHERE 
    object_id = %s 
    AND
    type_id = %s;
"""

CONTRACT_INFO = """
SELECT
    t1.contract_number,
    t1.partner_id,
    t1.contract_status_id,
    t1.allow,
    t1.contractor_id,
    t1.fot_percent::float AS fot_percent,
    t1.contract_cost::float AS contract_cost,
    t1.auto_continue,
    t1.date_start,
    t1.date_finish,
    t1.contract_description,
    t1.vat_value::float AS vat_value,
    t1.contract_cost::float AS contract_cost
FROM contracts AS t1
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
    
    t1.contract_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')), '') AS contract_cost_rub,
    ROUND(t1.contract_cost * t1.vat_value::numeric, 2) AS contract_cost_vat,
    ROUND((t1.contract_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0)) * t1.vat_value::numeric, 2) AS undistributed_cost,
    
    
    t0.act_cost::float AS act_cost,
    ROUND(t0.act_cost * t1.vat_value::numeric, 2)::float AS act_cost_vat_raw,
    ROUND(t0.act_cost * t1.vat_value::numeric, 2) AS act_cost_vat,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t0.act_cost, '999 999 990D99 ₽')), '') AS act_cost_rub,
    t0.create_at,
    CASE 
        WHEN t1.vat_value = 1 THEN false
        ELSE true
    END AS vat,
    t1.vat_value,
    t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0) AS undistributed_cost_vat_not_calc,
    TRIM(BOTH ' ' FROM to_char(
        t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0),
    '999 999 990D99 ₽')) AS undistributed_cost_vat_not_calc_rub,

    ROUND((t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0)) * t1.vat_value::numeric, 2) AS undistributed_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND((t0.act_cost - COALESCE(t5.tow_cost + t0.act_cost * t5.tow_cost_percent / 100, 0)) * t1.vat_value::numeric, 2),
    '999 999 990D99 ₽')) AS undistributed_cost_rub,
    
    ROUND((t1.contract_cost - COALESCE(t6.un_c_cost, 0)) * t1.vat_value::numeric, 2) AS undistributed_contract_cost,
    TRIM(BOTH ' ' FROM to_char(
        ROUND((t1.contract_cost - COALESCE(t6.un_c_cost, 0)) * t1.vat_value::numeric, 2),
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
    WHERE contract_id = %s
) AS t6 ON true
        
WHERE t0.act_id = %s;
"""

ACT_TOW_LIST = """
WITH
RECURSIVE rel_rec AS (
        SELECT
            1 AS depth,
            *,
            ARRAY[lvl] AS child_path
        FROM types_of_work
        WHERE parent_id IS NULL AND project_id = %s

        UNION ALL
        SELECT
            nlevel(r.path) + 1,
            n.*,
            r.child_path || n.lvl
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
    t0.depth-1 AS depth,
    t0.lvl,
    t31.act_date AS tow_date_start,
    COALESCE(to_char(t31.act_date, 'dd.mm.yyyy'), '') AS date_start_txt,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        ELSE t3.contract_cost * t2.tow_cost_percent / 100
    END AS tow_contract_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t3.contract_cost * t2.tow_cost_percent / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_contract_cost_rub,
    
    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND(t2.tow_cost * t3.vat_value::numeric, 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t2.tow_cost_percent / 100) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_contract_cost_with_vat,
    
    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost - COALESCE(t5.summary_acts_cost, 0)
        WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)
    END AS tow_remaining_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND((t2.tow_cost - COALESCE(t5.summary_acts_cost, 0)) * t3.vat_value::numeric, 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND(((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_remaining_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost - COALESCE(t5.summary_acts_cost, 0), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_remaining_cost_rub,
        
    CASE 
        WHEN t6.tow_cost != 0 THEN t6.tow_cost
        WHEN t6.tow_cost_percent != 0 THEN t31.act_cost * t6.tow_cost_percent / 100
        ELSE 0
    END AS tow_act_cost,
    CASE 
        WHEN t6.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t6.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t6.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t31.act_cost * t6.tow_cost_percent / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_act_cost_rub,
    
    CASE 
        WHEN t6.tow_cost != 0 THEN ROUND(t6.tow_cost * t3.vat_value::numeric, 2)
        WHEN t6.tow_cost_percent != 0 THEN ROUND((t31.act_cost * t6.tow_cost_percent / 100) * t3.vat_value::numeric, 2)
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
    COALESCE(t7.summary_payments_cost::text, '') AS tow_cost_protect_txt,
    COALESCE(t7.summary_payments_cost, 0) AS tow_cost_protect/*,
    t11.is_not_edited*/
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
    ROUND(t1.contract_cost * t1.vat_value::numeric, 2) AS contract_cost_vat,
    ROUND((t1.contract_cost - COALESCE(t6.un_c_cost, 0)) * t1.vat_value::numeric, 2) AS undistributed_contract_cost,
    0 AS act_cost_vat,
    0 AS undistributed_cost,
    COALESCE(TRIM(BOTH ' ' FROM to_char(t1.contract_cost, '999 999 990D99 ₽')), '') AS contract_cost_rub
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

ACT_TOW_LIST_FOR_PAYMENT = """
WITH
RECURSIVE rel_rec AS (
        SELECT
            1 AS depth,
            *,
            ARRAY[lvl] AS child_path
        FROM types_of_work
        WHERE parent_id IS NULL AND project_id = %s

        UNION ALL
        SELECT
            nlevel(r.path) + 1,
            n.*,
            r.child_path || n.lvl
        FROM rel_rec AS r
        JOIN types_of_work AS n ON n.parent_id = r.tow_id
        WHERE r.project_id = %s
        )
SELECT
    t0.depth-1 AS depth,
    COALESCE(
        CASE 
            WHEN t4.tow_cnt = 0 THEN t4.tow_cnt_dept_no_matter
            WHEN t4.tow_cnt_dept_no_matter = 0 THEN 1
            ELSE t4.tow_cnt
        END, 1) AS tow_cnt4,
    CASE 
        WHEN t6.tow_cost != 0 THEN '₽'
        WHEN t6.tow_cost_percent != 0 THEN '%%'
        ELSE ''
    END AS value_type,
    t0.tow_id,
    t0.tow_name,
    COALESCE(t0.dept_id, null) AS dept_id,
    CASE 
        WHEN t6.tow_cost != 0 THEN ROUND(t6.tow_cost * t3.vat_value::numeric, 2)
        WHEN t6.tow_cost_percent != 0 THEN ROUND((t31.act_cost * t6.tow_cost_percent / 100) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_act_cost_with_vat,
    CASE 
        WHEN t6.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t6.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t6.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t31.act_cost * t6.tow_cost_percent / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_act_cost_rub,
    CASE 
        WHEN t6.tow_cost != 0 THEN t6.tow_cost - COALESCE(t7.summary_payments_cost, 0)
        WHEN t6.tow_cost_percent != 0 THEN (t31.act_cost * t6.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0)
    END AS tow_remaining_cost,
        CASE 
        WHEN t6.tow_cost != 0 THEN ROUND((t6.tow_cost - COALESCE(t7.summary_payments_cost, 0)) * t3.vat_value::numeric, 2)
        WHEN t6.tow_cost_percent != 0 THEN ROUND(((t31.act_cost * t6.tow_cost_percent / 100) - COALESCE(t7.summary_payments_cost, 0)) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_remaining_cost_with_vat,
    CASE 
        WHEN t8.tow_cost != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_status,
    CASE 
        WHEN t8.tow_cost_percent != 0 THEN 'manual'
        ELSE 'calc'
    END AS tow_cost_percent_status,
        
        
        
        
    
    
    
    

    t0.child_path,
    COALESCE(t1.dept_short_name, '') AS dept_short_name,
    t0.time_tracking,
    t0.lvl,
    t31.act_date AS tow_date_start,
    COALESCE(to_char(t31.act_date, 'dd.mm.yyyy'), '') AS date_start_txt,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost
        ELSE t3.contract_cost * t2.tow_cost_percent / 100
    END AS tow_contract_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost, '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t3.contract_cost * t2.tow_cost_percent / 100, '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_contract_cost_rub,

    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND(t2.tow_cost * t3.vat_value::numeric, 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND((t3.contract_cost * t2.tow_cost_percent / 100) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_contract_cost_with_vat,

    CASE 
        WHEN t2.tow_cost != 0 THEN t2.tow_cost - COALESCE(t5.summary_acts_cost, 0)
        WHEN t2.tow_cost_percent != 0 THEN (t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)
    END AS tow_remaining_cost,
    CASE 
        WHEN t2.tow_cost != 0 THEN ROUND((t2.tow_cost - COALESCE(t5.summary_acts_cost, 0)) * t3.vat_value::numeric, 2)
        WHEN t2.tow_cost_percent != 0 THEN ROUND(((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0)) * t3.vat_value::numeric, 2)
        ELSE 0
    END AS tow_remaining_cost_with_vat,
    CASE 
        WHEN t2.tow_cost != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char(t2.tow_cost - COALESCE(t5.summary_acts_cost, 0), '999 999 990D99 ₽')), '')
        WHEN t2.tow_cost_percent != 0 THEN COALESCE(TRIM(BOTH ' ' FROM to_char((t3.contract_cost * t2.tow_cost_percent / 100) - COALESCE(t5.summary_acts_cost, 0), '999 999 990D99 ₽')), '')
        ELSE ''
    END AS tow_remaining_cost_rub,

    CASE 
        WHEN t6.tow_cost != 0 THEN t6.tow_cost
        WHEN t6.tow_cost_percent != 0 THEN t31.act_cost * t6.tow_cost_percent / 100
        ELSE 0
    END AS tow_act_cost,

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

    CASE 
        WHEN t6.tow_cost_percent != 0 THEN t6.tow_cost_percent
        ELSE ROUND(t6.tow_cost / t31.act_cost * 100, 2)
    END AS tow_cost_percent,
    CASE 
        WHEN t6.tow_cost_percent != 0 THEN TRIM(BOTH ' ' FROM to_char(t6.tow_cost_percent, '990D99 %%'))
        WHEN t6.tow_cost != 0 THEN TRIM(BOTH ' ' FROM to_char(ROUND(t6.tow_cost / t31.act_cost * 100, 2), '990D99 %%'))
        ELSE ''
    END AS tow_cost_percent_txt,


    COALESCE(t4.tow_cnt_dept_no_matter, 0) AS tow_cnt,
    COALESCE(t4.tow_cnt, 1) AS tow_cnt2,
    CASE 
        WHEN t4.tow_cnt IS NULL OR t4.tow_cnt = 0 THEN 1
        ELSE t4.tow_cnt
    END AS tow_cnt3,

    CASE 
        WHEN t2.tow_id IS NOT NULL THEN 'checked'
        ELSE ''
    END AS contract_tow,
    COALESCE(t7.summary_payments_cost::text, '') AS tow_cost_protect_txt,
    COALESCE(t7.summary_payments_cost, 0) AS tow_cost_protect/*,
    t11.is_not_edited*/
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
            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
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
            # pprint(request.get_json())
            # print(f"""/get-first-contract\\n                WHERE {where_expression2} {where_object_id}
            #         ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
            #         LIMIT {limit}""")
            # print('query_value', query_value)

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
                            (t1.contract_cost * t1.vat_value) {order} 0.01 AS contract_cost,
                            (t1.create_at {order} interval '1 day')::timestamp without time zone::text AS create_at
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
                            (t1.act_cost * t3.vat_value) {order} 0.01 AS act_cost,
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
                            (t1.payment_cost * t3.vat_value) {order} 0.01 AS payment_cost,
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
                    col_7 = all_contracts["subdate_start"]
                    col_8 = all_contracts["subdate_finish"]
                    col_9 = all_contracts["contractor_name"]
                    col_10 = all_contracts["partner_name"]
                    col_11 = all_contracts["contract_description"]
                    col_12 = all_contracts["status_name"]
                    col_13 = all_contracts["allow"]
                    col_14 = all_contracts["vat"]
                    col_15 = all_contracts["contract_cost"]
                    col_16 = all_contracts["create_at"]
                    if sort_col_1_order == 'DESC':
                        col_1 = col_1 + '+' if col_1 else col_1
                        col_2 = col_2 + '+' if col_2 else col_2
                        col_3 = col_3 + '+' if col_3 else col_3
                        col_6 = col_6 + '+' if col_6 else col_6
                        col_9 = col_9 + '=' if col_9 else col_9
                        col_10 = col_10 + '=' if col_10 else col_10
                        col_11 = col_11 + '+' if col_11 else col_11
                        col_12 = col_12 + '+' if col_12 else col_12
                        col_13 = col_13 + '+' if col_13 else col_13
                        col_14 = col_14 + '+' if col_14 else col_14
                    else:
                        col_1 = col_1[:-1] if col_1 else col_1
                        col_2 = col_2[:-1] if col_2 else col_2
                        col_3 = col_3[:-1] if col_3 else col_3
                        col_6 = col_6[:-1] if col_6 else col_6
                        col_9 = col_9[:-1] if col_9 else col_9
                        col_10 = col_10[:-1] if col_10 else col_10
                        col_11 = col_11[:-1] if col_11 else col_11
                        col_12 = col_12[:-1] if col_12 else col_12
                        col_13 = col_13[:-1] if col_13 else col_13
                        col_14 = col_14[:-1] if col_14 else col_14

                    filter_col = [
                        col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12,
                        col_13, col_14, col_15, col_16
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
                    col_11 = all_contracts["create_at"]
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
                elif page_name == 'contract-acts-list':
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
                    col_11 = all_contracts["create_at"]
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
                elif page_name == 'contract-acts-list':
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

            user_id = app_login.current_user.get_id()

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
@contract_app_bp.route('/contract-main', methods=['GET'])
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
        flash(message=['Ошибка', f'contract-main: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/get-contractObj-pagination', methods=['POST'])
@login_required
def get_contract_objects_pagination():
    """Постраничная выгрузка списка Объекты"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
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

            user_id = app_login.current_user.get_id()

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
@contract_app_bp.route('/contract-objects', methods=['GET'])
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
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/get-contractList-pagination', methods=['POST'])
@login_required
def get_contract_list_pagination():
    """Постраничная выгрузка списка Договоров"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
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

            user_id = app_login.current_user.get_id()

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
            # print('/get-contractList-pagination\n', '= - ' * 20, f"""WHERE {where_expression}
            #         ORDER BY {sort_col_1} {sort_col_1_order} NULLS LAST, {sort_col_id} {sort_col_id_order} NULLS LAST
            #         LIMIT {limit};""")
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
            col_15 = all_contracts[-1]["contract_cost"]
            col_16 = all_contracts[-1]["create_at"]
            filter_col = [
                col_0, col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10, col_11, col_12, col_13,
                col_14, col_15, col_16
            ]

            # Список колонок для сортировки, добавляем последние значения в столбах сортировки
            sort_col['col_1'].append(filter_col[col_num])
            sort_col['col_id'] = all_contracts[-1]["contract_id"]
            print('sort_col')
            print(sort_col)
            for i in range(len(all_contracts)):
                all_contracts[i] = dict(all_contracts[i])

            # if where_expression2:
            #     where_expression2 = 'WHERE ' + where_expression2
            # else:
            #     where_expression2 = ''

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
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'contract': 0,
            'sort_col': 0,
            'status': 'error',
            'description': str(e),
        })


# 'Договоры' - Договоры
@contract_app_bp.route('/contract-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contract-list', methods=['GET'])
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
            proj = False  # Информация о проекте, если зашли из проекта
            object_id = None
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
                if object_id:
                    cur_name = 1
                    where_contracts_list = f"WHERE t1.object_id = {object_id}"

                project = app_project.get_proj_info(link)
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
            print('            new_subcontract', new_subcontract)
            app_login.conn_cursor_close(cursor, conn)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # Список основного меню
            header_menu = get_header_menu(role, link=link, cur_name=cur_name)

            # Список колонок для сортировки
            if objects:
                sort_col = {
                    'col_1': [16, 0, objects['create_at']],  # Первая колонка - ASC
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
                title = "Сводная таблица договоров. Договоры"
            else:
                title = "Таблица договоров объекта"

            return render_template('contract-list.html', menu=hlink_menu, menu_profile=hlink_profile, sort_col=sort_col,
                                   header_menu=header_menu, tab_rows=tab_rows, setting_users=setting_users,
                                   objects=objects, hidden_col=hidden_col, nonce=get_nonce(), proj=proj,
                                   new_subcontract=new_subcontract, title=title)
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-list: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/get-actList-pagination', methods=['POST'])
@login_required
def get_act_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
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

            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
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
            col_8 = all_contracts[-1]["act_cost"]
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
@contract_app_bp.route('/contract-acts-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contract-acts-list', methods=['GET'])
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
            proj = False  # Информация о проекте, если зашли из проекта
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

                project = app_project.get_proj_info(link)
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
                    'col_1': [11, 0, acts['create_at']],  # Первая колонка - ASC
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
                title = "Сводная таблица договоров. Акты"
            else:
                title = "Таблица актов объекта"

            return render_template('contract-acts-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                                   sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                                   setting_users=setting_users, nonce=get_nonce(), proj=proj,
                                   title=title)
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-acts-list: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/get-contractPayList-pagination', methods=['POST'])
@login_required
def get_contract_pay_list_pagination():
    """Постраничная выгрузка списка Актов"""
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            page_name = 'contract-acts-list'
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

            user_id = app_login.current_user.get_id()

            # Если зашли из проекта, то фильтруем данные с учётом объекта
            link = request.get_json()['link']
            where_object_id = ''
            if link:
                object_id = get_proj_id(link_name=link)['object_id']
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
            col_9 = all_contracts[-1]["payment_cost"]
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


@contract_app_bp.route('/contract-payments-list', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contract-payments-list', methods=['GET'])
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
            proj = False  # Информация о проекте, если зашли из проекта
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
                project = app_project.get_proj_info(link)
                if project[0] == 'error':
                    flash(message=project[1], category='error')
                    return redirect(url_for('.objects_main'))
                elif not project[1]:
                    flash(message=['ОШИБКА. Проект не найден'], category='error')
                    return redirect(url_for('.objects_main'))
                proj = project[1]

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
                    'col_1': [11, 0, acts['create_at']],  # Первая колонка - ASC
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
                title = "Сводная таблица договоров. Платежи"
            else:
                title = "Таблица платежей объекта"

            return render_template('contract-payments-list.html', menu=hlink_menu, menu_profile=hlink_profile,
                                   sort_col=sort_col, header_menu=header_menu, tab_rows=tab_rows,
                                   setting_users=setting_users, nonce=get_nonce(), proj=proj,
                                   title=title)
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-acts-list: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/contract-list/card/<int:contract_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contract-list/card/<int:contract_id>', methods=['GET'])
@login_required
def get_card_contracts_contract(contract_id, link=''):
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            user_id = app_login.current_user.get_id()
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
            print('     object_id', object_id)

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
            print('     contracts', contracts)

            # Информация о договоре
            cursor.execute(
                QUERY_CONT_INFO,
                [contract_id, contract_id, contract_id]
            )

            contract_info = cursor.fetchone()
            contract_number = contract_info['contract_number']
            contract_number_short = contract_info['contract_number_short']

            print('                       contract_info')
            if contract_info:
                contract_info = dict(contract_info)

            print('     contract_info', contract_info)

            # Общая стоимость субподрядных договоров объекта
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
            """
            cursor.execute(
                """
                WITH t0 AS (
                    SELECT 
                        t00.contract_id,
                        t00.tow_cost + t00.tow_cost_percent * t01.contract_cost AS tow_cost
                    FROM tows_contract AS t00
                    LEFT JOIN (
                        SELECT 
                            contract_id,
                            contract_cost
                        FROM contracts
                        WHERE object_id = %s AND type_id = 2
                    ) AS t01 ON t00.contract_id = t01.contract_id
                )
                SELECT 
                    TRIM(BOTH ' ' FROM to_char(COALESCE(SUM(t0.tow_cost), 0), '999 999 990D99 ₽')) AS tow_cost
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
            print('     subcontractors_cost', subcontractors_cost)

            # Находим project_id по object_id
            project_id = get_proj_id(object_id=object_id)['project_id']

            # Список tow
            cursor.execute(
                CONTRACT_TOW_LIST,
                [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
            )
            tow = cursor.fetchall()

            if tow:
                # print('     tow_list')
                for i in range(len(tow)):
                    tow[i] = dict(tow[i])
                    # if tow[i]['contract_tow']:
                    #     print('     ', tow[i])
            # print(tow[0])
            # print(tow[1])

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
            print(our_companies)

            app_login.conn_cursor_close(cursor, conn)

            # Список отделов
            dept_list = app_project.get_dept_list(user_id)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # print(dict(employee))
            render_html = 'contract-card-contract.html'
            # if request.path[1:].split('/')[-2] == 'card2':
            render_html = 'contract-card-contract.html'

            # Return the updated data as a response
            return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile,
                                   contract_info=contract_info, objects_name=objects_name, partners=partners,
                                   contract_statuses=contract_statuses, tow=tow, contract_types=contract_types,
                                   our_companies=our_companies, subcontractors_cost=subcontractors_cost,
                                   contracts=contracts, dept_list=dept_list,
                                   nonce=get_nonce(), title=f"Договор {contract_number_short}", title1=contract_number)
    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'contract-list/card/: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


# @contract_app_bp.route('/contract-list/card2/new/<link>/<int:contract_type>/<int:subcontract>', methods=['GET'])
# @contract_app_bp.route('/contract-list/card2/new/<int:contract_type>/<int:subcontract>', methods=['GET'])
@contract_app_bp.route('/contract-list/card/new/<link>/<int:contract_type>/<int:subcontract>', methods=['GET'])
@contract_app_bp.route('/contract-list/card/new/<int:contract_type>/<int:subcontract>', methods=['GET'])
@login_required
def get_card_contracts_new_contract(contract_type, subcontract, link=False):
    try:
        role = app_login.current_user.get_role()
        # Вызываем ошибку, в случае, если договор создаётся по неправильной ссылке:
        # тип договора не 1 (доходный) или не 2 (расходный) И договор/допник не (0/1)
        if contract_type not in [1, 2] or subcontract not in [0, 1]:
            e = 'Ссылка на создание нового договора некорректная, закройте страницу и создаёте договор снова.'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)
        else:
            print('get_card_contracts_new_contract_', contract_type, subcontract, link)
            user_id = app_login.current_user.get_id()

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict("contracts")

            object_id = get_proj_id(link_name=link)['object_id'] if link else -100
            contract_id = -100

            print('     object_id', object_id)

            # Находим номера всех договоров объекта (без субподрядных)
            if link:
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
            if link:
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
                                WHERE dept_id IS NOT NULL);
                        """,
                    [object_id]
                )
                subcontractors_cost = cursor.fetchone()[0]
            else:
                subcontractors_cost = 0

            # Находим project_id по object_id и список tow
            if link:
                project_id = get_proj_id(object_id=object_id)['project_id']

                # Список tow
                cursor.execute(
                    CONTRACT_TOW_LIST,
                    [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
                )
                tow = cursor.fetchall()

                if tow:
                    for i in range(len(tow)):
                        tow[i] = dict(tow[i])
                    print(tow[i])
            else:
                tow = None

            print(' ___')
            # в случае если создаётся допник нужен список объектов у которых уже созданы договоры, иначе допник
            # не к чему привязать. Находим список объектов (из DB objects) и оставляем то с договорами
            object_name = None
            # Список объектов
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
                if subcontract and i['object_id'] not in objects_plus:
                    objects_name.remove(i)
            print(' __objects__', objects_name)
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
            print(our_companies)

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
                'create_at': None,
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

            print('                       contract_info')
            if contract_info:
                contract_info = dict(contract_info)

            print('     contract_info', contract_info)

            app_login.conn_cursor_close(cursor, conn)
            print('app_login.conn_cursor_close(cursor, conn)')

            # Список отделов
            dept_list = app_project.get_dept_list(user_id)

            # Список меню и имя пользователя
            hlink_menu, hlink_profile = app_login.func_hlink_profile()

            # print(dict(employee))
            # if request.path[1:].split('/')[-2] == 'card2':
            render_html = 'contract-card-contract.html'
            c_type = 'доходного' if contract_type == 1 else 'расходного'
            title = f"Создание нового {c_type} договора" if not subcontract else \
                f"Создание нового {c_type} доп.соглашения"
            # Return the updated data as a response
            return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile,
                                   contract_info=contract_info, objects_name=objects_name, partners=partners,
                                   contract_statuses=contract_statuses, tow=tow, contract_types=contract_types,
                                   our_companies=our_companies, subcontractors_cost=subcontractors_cost,
                                   contracts=contracts, dept_list=dept_list,
                                   nonce=get_nonce(), title=title)

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
        flash(message=['Ошибка', f'/contract-list/card/new: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())



def check_contract_data_for_correctness(ctr_card, contract_tow_list, role):
    # try:
        if role not in (1, 4, 5):
            return {
                'status': 'error',
                'description': ["Ограничен доступ для внесения нового договора"]
            }
        print('             def check_contract_data_for_correctness')

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
        ctr_card['fot_percent'] = float(ctr_card['fot_percent']) if ctr_card['fot_percent'] else None
        ctr_card['partner_id'] = int(ctr_card['partner_id']) if ctr_card['partner_id'] else None
        ctr_card['contract_status_id'] = int(ctr_card['contract_status_id']) if ctr_card['contract_status_id'] else None
        ctr_card['vat_value'] = float(ctr_card['vat_value']) if ctr_card['vat_value'] else None

        vat = 1.2 if ctr_card['vat'] == "С НДС" else 1
        contract_cost = ctr_card['contract_cost']

        print('-' * 30, '    ctr_card')
        print(ctr_card)

        contract_id = ctr_card['contract_id']
        object_id = ctr_card['object_id']
        project_id = get_proj_id(object_id=object_id)['project_id']
        print('-' * 30, '    contract_id, object_id, project_id')
        print(contract_id, object_id, project_id)

        # tow_list = request.get_json()['list_towList']
        tow_list = contract_tow_list
        tow_id_list = set()
        tow_list_to_dict = dict()
        print('------------------------------     tow_list')
        print(tow_list)
        if len(tow_list):
            for i in tow_list:
                print(' ' * 10, i)
                i['id'] = int(i['id']) if i['id'].isdigit() else i['id']
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
                i['dept_id'] = int(i['dept_id']) if i['dept_id'] else None
                i['date_start'] = date.fromisoformat(i['date_start']) if i['date_start'] else None
                i['date_finish'] = date.fromisoformat(i['date_finish']) if i['date_finish'] else None

                del i['type']

                tow_list_to_dict[i['id']] = i
            tow_id_list = set(tow_list_to_dict.keys())
        print(' /-|-\ /' * 30)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")
        new_contract = False

        subquery = 'ON CONFLICT DO NOTHING'
        table_tc = 'tows_contract'

        # Если новый договор, проверяем, соотносятся ли стоимости tow и стоимость договора, если ок - запись в БД
        if contract_id == 'new':
            check_cc = including_tax(contract_cost, vat)
            lst_cost_tow = None
            for i in tow_list:
                check_towc = 0
                if i['cost']:
                    check_towc = including_tax(i['cost'], vat)
                elif i['percent']:
                    check_towc = including_tax(contract_cost * i['percent'] / 100, vat)

                # del i['type']

                lst_cost_tow = i if i['cost'] or i['percent'] else lst_cost_tow
                check_cc = round(check_cc - check_towc, 2)

            if 0 > check_cc >= -0.01 and lst_cost_tow:
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] += check_cc
                    lst_cost_tow['percent'] = None
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = including_tax(contract_cost * lst_cost_tow['percent'] / 100, vat)
                    lst_cost_tow['percent'] = None
                description.extend([
                    f"Общая стоимость видов работ договора превышает стоимость договора ({-check_cc} ₽).",
                    f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                    f"к котором можно произвести корректировку стоимости"
                ])
                return {
                    'status': 'error',
                    'description': description
                }
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

            action = 'INSERT INTO'
            table_nc = 'contracts'
            columns_nc = ('object_id', 'type_id', 'contract_number', 'partner_id', 'contract_status_id', 'allow',
                          'contractor_id', 'fot_percent', 'contract_cost', 'auto_continue', 'date_start', 'date_finish',
                          'contract_description', 'vat_value')
            subquery_nc = " RETURNING contract_id;"
            print(action)
            query_nc = app_payment.get_db_dml_query(action=action, table=table_nc, columns=columns_nc,
                                                    subquery=subquery_nc)
            print(query_nc)
            values_nc = [[
                ctr_card['object_id'],
                ctr_card['type_id'],
                ctr_card['contract_number'],
                ctr_card['partner_id'],
                ctr_card['contract_status_id'],
                ctr_card['allow'],
                ctr_card['contractor_id'],
                ctr_card['fot_percent'],
                including_tax(contract_cost, vat),
                ctr_card['auto_continue'],
                ctr_card['date_start'],
                ctr_card['date_finish'],
                ctr_card['contract_description'],
                ctr_card['vat_value']
            ]]
            print(values_nc)

            table_sc = 'subcontract'
            columns_sc = ('child_id', 'parent_id')
            action = 'INSERT INTO'
            print(action)
            query_sc = app_payment.get_db_dml_query(action=action, table=table_sc, columns=columns_sc)
            print(query_sc)
            values_sc = [[
                contract_id,
                ctr_card['parent_id']
            ]]
            print(values_sc)


            data_contract['new_contract'] = {
                'query_nc': query_nc,
                'values_nc': values_nc,
                'query_sc': query_sc,
                'values_sc': values_sc
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
                            including_tax(i['cost'], vat),
                            i['percent'],
                            i['date_start'],
                            i['date_finish']
                        ])

            if len(values_tc_ins):
                action = 'INSERT INTO'
                print(action)
                query_tc_ins = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_ins,
                                                            subquery=subquery)
                print(query_tc_ins)
                print(values_tc_ins)
                data_contract['new_contract']['query_tc_ins'] = query_tc_ins
                data_contract['new_contract']['values_tc_ins'] = values_tc_ins

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
        cursor.execute(CONTRACT_INFO, [contract_id])
        contract_info = cursor.fetchone()

        if contract_info:
            contract_info = dict(contract_info)

        # Округляем значения, иногда 1.20 превращается в 1.200006545...
        contract_info['vat_value'] = round(contract_info['vat_value'], 2)
        # Если тип НДС был изменен, пересчитываем стоимость договора с учётом НДС
        if ctr_card['vat_value'] != contract_info['vat_value'] or \
                contract_cost != contract_info['contract_cost']:
            vat = contract_info['vat_value']
            ctr_card['contract_cost'] = including_tax(ctr_card['contract_cost'], vat)
            contract_cost = including_tax(contract_cost, vat)

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

        print('                       subcontract_info columns_c')
        if subcontract_info:
            subcontract_info = dict(subcontract_info)
        pprint(subcontract_info)

        # Список tow
        cursor.execute(
            CONTRACT_TOW_LIST,
            [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
        )
        tow = cursor.fetchall()
        tow_dict = dict()
        db_tow_id_list = set()
        print('____ 4610 ____')
        if tow:
            for i in tow:
                i = dict(i)
                if i['contract_tow'] == 'checked':
                    db_tow_id_list.add(i['tow_id'])
                tow_dict[i['tow_id']] = i
                # print({i['tow_id']: i})

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
            print(tows_contract)
            # tows_contract = set(tows_contract)
            for i in range(len(tows_contract)):
                if tows_contract[i][0] not in db_tow_id_list:
                    tows_contract_list_del.add(tows_contract[i][0])
                    print(tows_contract[i])

            print('             tows_contract_list_del')
            print(tows_contract_list_del)
            print(' ^ ^ ^' * 20)
        columns_c = ['contract_id']
        values_c = [[contract_id]]

        ######################################################################################
        # Определяем изменённые поля в договоре
        ######################################################################################

        for i in contract_info.keys():
            if i == "contract_cost":
                contract_info[i] = float(contract_info[i])
            if i == "vat_value":
                contract_info[i] = round(contract_info[i], 2)
            # print('___', i, ctr_card[i], '___', contract_info[i], '___', ctr_card[i] == contract_info[i], '___',
            #       type(ctr_card[i]), '/', type(contract_info[i]))
            if ctr_card[i] != contract_info[i]:
                columns_c.append(i)
                values_c[0].append(ctr_card[i])

        print('columns_c:', columns_c)
        print('values_c:', values_c)

        columns_sc = ['child_id']
        values_sc = [[contract_id]]
        if ctr_card['parent_id'] != subcontract_info['parent_id']:
            print('___ parent_id', ctr_card['parent_id'], '___', subcontract_info['parent_id'])
            columns_sc.append('parent_id')
            values_sc[0].append(ctr_card['parent_id'])
        print('columns_sc:', columns_sc)
        print('values_sc:', values_sc)

        ######################################################################################
        # Определяем добавляемые, изменяемые и удаляемые tow
        ######################################################################################

        # СПИСОК ДОБАВЛЕНИЯ TOW
        columns_tc_ins = ('contract_id', 'tow_id', 'tow_cost', 'tow_cost_percent', 'tow_date_start',
                          'tow_date_finish')
        tow_id_list_ins = tow_id_list - db_tow_id_list
        values_tc_ins = []
        # if tow_id_list_ins:
        #     for i in tow_list:
        #         if i['id'] in tow_id_list_ins:
        #             i['cost'] = including_tax(i['cost'], vat)

        # УДАЛЕНИЕ TOW
        columns_tc_del = 'contract_id::int, tow_id::int'
        tow_id_list_del = tows_contract_list_del | db_tow_id_list - tow_id_list
        values_tc_del = []
        if tow_id_list_del:
            values_tc_del = [(contract_id, i) for i in tow_id_list_del]

        # СПИСОК ИЗМЕНЕНИЯ TOW
        columns_tc_upd = [['contract_id::integer', 'tow_id::integer'], 'tow_cost::numeric',
                          'tow_cost_percent::numeric', 'tow_date_start::date', 'tow_date_finish::date']
        # tmp_tow_id_list_upd = tow_id_list & db_tow_id_list
        tmp_tow_id_list_upd = tow_id_list - tow_id_list_del - tow_id_list_ins
        tow_id_list_upd = set()
        tow_id_set_upd = set()
        values_tc_upd = []

        if tmp_tow_id_list_upd:
            for i in tow_list:
                if i['id'] in tmp_tow_id_list_upd and i['id'] in tow_dict.keys():
                    # Конвертируем стоимость tow
                    i['cost'] = including_tax(i['cost'], vat)
                    # Проверяем были ли изменены параметры tow
                    if i['date_start'] != tow_dict[i['id']]['tow_date_start']:
                        tow_id_list_upd.add(i['id'])
                    elif i['date_finish'] != tow_dict[i['id']]['tow_date_finish']:
                        tow_id_list_upd.add(i['id'])
                    elif i['cost'] != tow_dict[i['id']]['tow_cost_raw']:
                        tow_id_list_upd.add(i['id'])
                    elif i['percent'] != tow_dict[i['id']]['tow_cost_percent_raw']:
                        tow_id_list_upd.add(i['id'])

        print('____tmp_tow_id_list_upd____')
        print(tmp_tow_id_list_upd, '\n', tow_id_list_upd)

        check_cc = contract_cost
        tow_list_cost = 0  # Общая стоимость видов работ договора
        check_towc = 0  # Общая стоимость видов работ договора
        lst_cost_tow = None
        # Проверка на:
        #   - превышение суммы протекции (стоимости привязанных актов/платежей)
        #   - удаляемые tow не имеют протекции
        #   - превышение общей стоимости договора суммой всех стоимостей tow
        for tow_id in tow_dict.keys():
            print('for tow_id in tow_dict.keys() ', tow_id)
            tow_contract_cost = 0
            check_towc = 0
            # Добавление
            if tow_id in tow_id_list_ins:
                print('       Добавление')
                if tow_list_to_dict[tow_id]['cost']:
                    tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
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
                        f"К виду работ привязаны не должны были, но привязаны акты/платежи на сумму: "
                        f"{tow_dict[tow_id]['tow_cost_protect']} ₽"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }

            # Обновление
            elif tow_id in tow_id_list_upd:
                print('       Обновление', tow_list_to_dict[tow_id])
                # Если указана стоимость
                if tow_list_to_dict[tow_id]['cost']:
                    print('cost')
                    # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
                    if (tow_dict[tow_id]['tow_cost_raw'] and
                            tow_dict[tow_id]['tow_cost_raw'] != tow_list_to_dict[tow_id]['cost']):
                        # tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                        # if tow_dict[tow_id]['tow_cost_raw'] != tow_list_to_dict[tow_id]['cost']:
                        tow_contract_cost = tow_list_to_dict[tow_id]['cost']
                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 1 ==', tow_dict[tow_id]['tow_cost_raw'], tow_list_to_dict[tow_id]['cost'])
                        tow_id_set_upd.add(tow_id)
                    elif not tow_dict[tow_id]['tow_cost_raw']:
                        # tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                        tow_contract_cost = tow_list_to_dict[tow_id]['cost']
                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 2 ==', tow_dict[tow_id]['tow_cost_raw'], tow_list_to_dict[tow_id]['cost'])
                        tow_id_set_upd.add(tow_id)
                    # Никаких изменений у tow не было
                    else:
                        tow_contract_cost = 0
                        if tow_dict[tow_id]['tow_cost_raw']:
                            tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                        elif tow_dict[tow_id]['tow_cost_percent_raw']:
                            tow_contract_cost = (
                                including_tax(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 1))

                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost

                # Указаны проценты
                elif tow_list_to_dict[tow_id]['percent']:
                    print('percent', tow_list_to_dict[tow_id])
                    if (tow_dict[tow_id]['tow_cost_percent_raw'] and
                            tow_dict[tow_id]['tow_cost_percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                        tow_contract_cost = including_tax(contract_cost * tow_list_to_dict[tow_id]['percent'] / 100,
                                                          1)
                        check_towc = tow_contract_cost
                        tow_list_cost += tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 3 ==', tow_dict[tow_id]['tow_cost_raw'], tow_list_to_dict[tow_id]['cost'])
                        tow_id_set_upd.add(tow_id)
                    elif (tow_list_to_dict[tow_id]['percent'] and
                          tow_dict[tow_id]['tow_cost_percent_raw'] != tow_list_to_dict[tow_id]['percent']):
                        tow_contract_cost = including_tax(contract_cost * tow_list_to_dict[tow_id]['percent'] / 100,
                                                          1)
                        check_towc = tow_contract_cost
                        tow_list_cost += tow_contract_cost
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 4 ==', contract_cost, tow_list_to_dict[tow_id]['cost'])
                    # Никаких изменений у tow не было
                    else:
                        tow_contract_cost = 0
                        if tow_dict[tow_id]['tow_cost_raw']:
                            tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                        elif tow_dict[tow_id]['tow_cost_percent_raw']:
                            tow_contract_cost = (
                                including_tax(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 1))

                        tow_list_cost += tow_contract_cost
                        check_towc = tow_contract_cost

                if tow_dict[tow_id]['tow_cost_protect'] > check_towc:
                    print(')_)_)_)_)   ', tow_dict[tow_id]['tow_cost_protect'] - check_towc)
                    missing_amount = including_tax(tow_dict[tow_id]['tow_cost_protect'] - check_towc, 1)
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
                print('       Удаление', tow_list_to_dict[tow_id])
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
                print('       не был отредактирован', tow_list_to_dict[tow_id])
                if tow_dict[tow_id]['tow_cost_raw']:
                    print()
                    tow_contract_cost = tow_dict[tow_id]['tow_cost_raw']
                elif tow_dict[tow_id]['tow_cost_percent_raw']:
                    tow_contract_cost = including_tax(contract_cost * tow_dict[tow_id]['tow_cost_percent_raw'] / 100, 1)
                check_towc = tow_contract_cost
                print(check_towc, tow_dict[tow_id])


            check_cc = check_cc - check_towc

        print('____check_cc____')
        print(check_cc)
        print(lst_cost_tow)

        if check_cc < 0:
            print(' check_cc 1')
            check_cc = round(check_cc, 2)
            if check_cc <= -1:
                description.extend([
                    f"Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                    f"Скорректируйте стоимость договора или видов работ"])
                print(' check_cc 2', description)
                return {
                    'status': 'error',
                    'description': description
                }
            elif lst_cost_tow:
                print(' check_cc 3')
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] -= check_cc
                    description.extend([
                        f"Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                    print(111111111)
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = (
                            including_tax(lst_cost_tow['percent'] * contract_cost / 100, vat) + check_cc)
                    lst_cost_tow['percent'] = None
                    description.extend([
                        f"Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                    print(22222222)
                else:
                    description.extend([
                        f"Общая стоимость видов работ договора превысила стоимость договора на {-check_cc} ₽.",
                        f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                        f"в котором можно произвести корректировку стоимости"
                    ])
                    return {
                        'status': 'error',
                        'description': description
                    }
            elif not lst_cost_tow:
                description.extend([
                    f"Общая стоимость видов работ договора превышает стоимость договора на {-check_cc} ₽.",
                    f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
                    f"в котором можно произвести корректировку стоимости"
                ])
                print(' check_cc 4', description)
                return {
                    'status': 'error',
                    'description': description
                }


        print('____tow_id_list_ins____')
        print(tow_id_list_ins)
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

        print('\n____tow_id_list_upd____')
        print(tow_id_list_upd, '\n')
        print('____values_tc_upd____')
        print(values_tc_upd, '\n')

        print(lst_cost_tow)
        print(tow_list)

        data_contract['old_contract'] = {
            'contract_id': contract_id
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
            # Для tows_contract
        if len(values_tc_ins):
            action = 'INSERT INTO'
            query_tc_ins = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_ins,
                                                        subquery=subquery)
            print(action)
            print(query_tc_ins)
            print(values_tc_ins)
            data_contract['old_contract']['values_tc_ins'] = {
                'query_tc_ins': query_tc_ins,
                'values_tc_ins': values_tc_ins
            }

        if len(values_tc_upd):
            action = 'UPDATE DOUBLE'
            query_tc_upd = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_upd)
            print(action)
            print(query_tc_upd)
            pprint(values_tc_upd)
            data_contract['old_contract']['values_tc_upd'] = {
                'query_tc_upd': query_tc_upd,
                'values_tc_upd': values_tc_upd
            }

        if len(values_tc_del):
            action = 'DELETE'
            query_tc_del = app_payment.get_db_dml_query(action=action, table=table_tc, columns=columns_tc_del,
                                                        subquery=subquery)
            print(action)
            print(query_tc_del)
            print(values_tc_del)
            data_contract['old_contract']['values_tc_del'] = {
                'query_tc_del': query_tc_del,
                'values_tc_del': values_tc_del
            }


        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # СООБЩАМЕ ОБ УСПЕХЕ. ДОЛЖЕН БЫТЬ СТАТУС
        return {
            'status': 'success',
            'data_contract': data_contract,
            'description': description
        }

    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #     return {
    #         'status': 'error',
    #         'description': [str(e)],
    #     }




def save_contract(new_contract=None, old_contract=None):
    # try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")
        print('  def save_contract')
        print(new_contract)


        print(old_contract)
        description = list()
        ######################################################################################
        # НОВЫЙ ДОГОВОР
        ######################################################################################
        if new_contract:
            query_nc = new_contract['query_nc']
            values_nc = new_contract['values_nc']
            query_sc = new_contract['query_sc']
            values_sc = new_contract['values_sc']
            query_tc_ins = None
            values_tc_ins = None
            if 'query_tc_ins' in new_contract.keys():
                query_tc_ins = new_contract['query_tc_ins']
                values_tc_ins = new_contract['values_tc_ins']

            # Добавляем новый договор в таблицу 'contracts'
            execute_values(cursor, query_nc, values_nc)
            contract_id = cursor.fetchone()[0]
            conn.commit()
            new_contract = True
            print('contract_id:', contract_id)

            # Добавляем запись в таблицу 'subcontract'
            values_sc[0][0] = contract_id
            execute_values(cursor, query_sc, values_sc)
            conn.commit()

            # ДОБАВЛЕНИЕ TOW
            if values_tc_ins:
                for i in values_tc_ins:
                    i[0] = contract_id

                execute_values(cursor, query_tc_ins, values_tc_ins)
                conn.commit()
            app_login.conn_cursor_close(cursor, conn)

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
            query_sc = None
            values_sc = None
            query_tc_ins = None
            values_tc_ins = None
            query_tc_upd = None
            values_tc_upd = None
            query_tc_del = None
            values_tc_del = None
            c_keys = set(old_contract.keys())

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
            # Для tows_contract INSERT INTO
            if 'values_tc_ins' in c_keys:
                query_tc_ins = old_contract['values_tc_ins']['query_tc_ins']
                values_tc_ins = old_contract['values_tc_ins']['values_tc_ins']
                execute_values(cursor, query_tc_ins, values_tc_ins)
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

            # Return the updated data as a response
            return {
                'status': status,
                'description': description,
                'contract_id': contract_id
            }

    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #     return {
    #         'status': 'error',
    #         'description': [str(e)],
    #     }



@contract_app_bp.route('/contract-acts-list/card/<int:act_id>', methods=['GET'])
@contract_app_bp.route('/objects/<link>/contract-acts-list/card/<int:act_id>', methods=['GET'])
@login_required
def get_card_contracts_act(act_id, link=''):
    # try:
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)
    else:
        act_id = act_id
        link = link

        user_id = app_login.current_user.get_id()
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")

        # Находим object_id, по нему находим список tow
        cursor.execute(FIND_OBJ_BY_ACT, [act_id])
        object_id = cursor.fetchone()
        print(object_id)
        if not object_id:
            e = 'Карточка акта: Объект или договор не найден'
            flash(message=['Ошибка', e], category='error')
            return render_template('page_error.html', error=[e], nonce=get_nonce())

        contract_id, object_id = object_id[0], object_id[1]
        print('     object_id', object_id, '     contract_id', contract_id)

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
        print('     objects', objects)

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
            [act_id, contract_id, act_id]
        )
        act_info = cursor.fetchone()
        print([act_id, contract_id, act_id])
        print('act_info', act_info)
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
            # print('     tow_list')
            for i in range(len(tow)):
                tow[i] = dict(tow[i])

        # Список статусов
        cursor.execute(
            "SELECT contract_status_id, status_name  FROM contract_statuses ORDER BY status_name")
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
        dept_list = app_project.get_dept_list(user_id)

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


# except Exception as e:
#     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
#     flash(message=['Ошибка', f'contract-list: {e}'], category='error')
#     return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/contract-acts-list/card/new/<link>', methods=['GET'])
@contract_app_bp.route('/contract-acts-list/card/new', methods=['GET'])
@login_required
def get_card_contracts_new_act(link=False):
    # try:
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    print('get_card_contracts_new_act_', link)
    user_id = app_login.current_user.get_id()

    # Connect to the database
    conn, cursor = app_login.conn_cursor_init_dict("contracts")

    object_id = get_proj_id(link_name=link)['object_id'] if link else -100
    contract_id = -100
    act_id = -100

    print('     act_id', act_id)

    # Находим номера всех договоров объекта (без субподрядных)
    if link:
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

    # Список статусов
    cursor.execute("SELECT contract_status_id, status_name  FROM contract_statuses ORDER BY status_name")
    contract_statuses = cursor.fetchall()
    if contract_statuses:
        for i in range(len(contract_statuses)):
            contract_statuses[i] = dict(contract_statuses[i])
    print('# Список статусов')
    print(contract_statuses)

    # Список типов
    if link:
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
        'create_at': None,
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

    print('                       act_info')
    if act_info:
        act_info = dict(act_info)

    print('     act_info', act_info)

    app_login.conn_cursor_close(cursor, conn)
    print('app_login.conn_cursor_close(cursor, conn)')

    # Список отделов
    dept_list = app_project.get_dept_list(user_id)

    # Список меню и имя пользователя
    hlink_menu, hlink_profile = app_login.func_hlink_profile()

    # print(dict(employee))
    # if request.path[1:].split('/')[-2] == 'card2':
    render_html = 'contract-card-act.html'
    title = "Создание нового акта"

    # Return the updated data as a response
    return render_template(render_html, menu=hlink_menu, menu_profile=hlink_profile, act_info=act_info,
                           objects_name=objects_name, act_statuses=contract_statuses, tow=tow,
                           act_types=contract_types,
                           contracts_income=contracts_income, contracts_expenditure=contracts_expenditure,
                           dept_list=dept_list, nonce=get_nonce(), title=title)


# except Exception as e:
#     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
#     flash(message=['Ошибка', f'/contract-acts-list/card/new: {e}'], category='error')
#     return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/change-object-from-act/<int:object_id>', methods=['POST'])
@login_required
def change_object_from_act(object_id):
    # try:
    print('        change_object_from_act', type(object_id), object_id)

    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    user_id = app_login.current_user.get_id()

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

    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #         return jsonify({
    #             'status': 'error',
    #             'description': [str(e)],
    #         })


@contract_app_bp.route('/change-contract-from-act/<int:object_id>/<int:type_id>/<int:contract_id>', methods=['POST'])
@login_required
def change_contract_from_act(object_id: int, type_id: int, contract_id: int):
    # try:
    print(object_id, type_id, contract_id)
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    user_id = app_login.current_user.get_id()

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
    print('________')
    print([project_id, project_id, contract_id, contract_id, act_id, contract_id, contract_id, act_id])
    # Список tow акта
    cursor.execute(
        ACT_TOW_LIST,
        [project_id, project_id, contract_id, contract_id, act_id, contract_id, contract_id, act_id, act_id]
    )
    tow = cursor.fetchall()

    app_login.conn_cursor_close(cursor, conn)

    if tow:
        # print('     tow_list')
        for i in range(len(tow)):
            tow[i] = dict(tow[i])
            print(tow[i])

    # Список отделов
    dept_list = app_project.get_dept_list(user_id)

    # Return the data as a response
    return jsonify({
        'check_con_info': check_con_info,
        'tow': tow,
        'dept_list': dept_list,
        'status': 'success'
    })
    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #         return jsonify({
    #             'status': 'error',
    #             'description': [str(e)],
    #         })


@contract_app_bp.route('/save_act', methods=['POST'])
@login_required
def save_act():
    # try:
    print(request.get_json())

    description = list()

    act_id = request.get_json()['act_id']
    object_id = request.get_json()['object_id']
    type_id = request.get_json()['act_type']
    contract_id = request.get_json()['contract_id']
    act_number = request.get_json()['act_number']
    date_start = request.get_json()['date_start']
    status_id = request.get_json()['status_id']
    act_cost = request.get_json()['act_cost']
    tow_list = request.get_json()['list_towList']

    act_id = int(act_id) if act_id != 'new' else 'new'
    object_id = int(object_id) if object_id else None
    type_id = int(type_id) if type_id else None
    contract_id = int(contract_id) if contract_id else None
    date_start = date.fromisoformat(date_start) if date_start else None
    act_cost = app_payment.convert_amount(act_cost) if act_cost else None
    status_id = int(status_id) if status_id else None

    if not object_id or not type_id or not contract_id or not date_start or not act_cost or not status_id:
        description.extend(['В данных акта не хватаем информации'])
        return jsonify({
            'status': 'error',
            'description': description,
        })

    # Находим project_id по object_id
    project_id = get_proj_id(object_id=object_id)['project_id']

    # Connect to the database
    conn, cursor = app_login.conn_cursor_init_dict("contracts")
    cursor.execute(
        QUERY_CONT_INFO_FOR_ACT,
        [contract_id, -1 if act_id == 'new' else act_id, contract_id, object_id, type_id]
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

    print('       check_con_info')
    print(check_con_info)

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
    print('------------------------------     tow_list_to_dict')
    for k, v in tow_list_to_dict.items():
        print(k, v)

    # Проверка, что стоимость акта не была изменена
    act_info = None
    if act_id != 'new':
        # Информация об акте
        cursor.execute(
            QUERY_ACT_INFO,
            [act_id, contract_id, act_id]
        )
        act_info = cursor.fetchone()
        if act_info['act_cost'] != act_cost:
            act_cost = including_tax(act_cost, check_con_info['vat_value'])
    else:
        act_cost = including_tax(act_cost, check_con_info['vat_value'])

    # Проверяем что незаактированный остаток договора не меньше стоимости акта
    if check_con_info['undistributed_contract_cost'] < act_cost:
        check_ac = act_cost - including_tax(check_con_info['undistributed_contract_cost'], 1)
        description.extend([
            "Незаактированный остаток договора меньше стоимости акта",
            f"Остаток: {check_con_info['undistributed_contract_cost']} ₽",
            f"Стоимость акта без НДС: {act_cost} ₽",
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
        [project_id, project_id, contract_id, contract_id, tmp_act_id, contract_id, contract_id, tmp_act_id, tmp_act_id]
    )
    tow = cursor.fetchall()
    tow_dict = dict()

    print(act_cost)
    pprint(dict(act_info))
    print('------------------------------     tow')
    print(tow)
    print('-----------------------------__')

    # Проверяем, незаактированный остаток договора не меньше стоимости акта, а так же проверяем актуальность списка tow
    if tow:
        # Если к акту привязали (указали стоимость)
        if len(tow_list_to_dict):
            tow_list_cost = 0  # Общая стоимость видов работ акта

            for i in tow:
                i = dict(i)
                tow_dict[i['tow_id']] = i
                print(i)
                if i['tow_id'] in tow_list_to_dict.keys():
                    tow_act_cost = tow_list_to_dict[i['tow_id']]['cost'] if tow_list_to_dict[i['tow_id']]['cost'] else (
                        including_tax(tow_list_to_dict[i['tow_id']]['percent'] * act_cost / 100, 1))
                    tow_list_cost += tow_act_cost

                    tmp_tow_remaining_cost = \
                        including_tax(i['tow_remaining_cost_with_vat'] + i['tow_act_cost'], 1) - tow_act_cost

                    print(i['tow_id'],
                          '\n', tmp_tow_remaining_cost, i['tow_remaining_cost_with_vat'], i['tow_act_cost'],
                          '\n', including_tax(i['tow_remaining_cost_with_vat'] + i['tow_act_cost'], 1), tow_act_cost)

                    if tmp_tow_remaining_cost < 0:
                        x = including_tax(tow_act_cost - including_tax(i['tow_remaining_cost_with_vat'], 1), 1)
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
                    print('________________________ ')
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

    new_contract = False

    subquery = 'ON CONFLICT DO NOTHING'
    table_ta = 'tows_act'

    # Если новый договор, проверяем, соотносятся ли стоимости tow и стоимость договора, если ок - запись в БД
    if act_id == 'new':
        check_ac = including_tax(contract_cost, vat)
        lst_cost_tow = None

        values_ac_ins = []
        if len(tow_list):
            for i in tow_list:
                check_towc = 0
                if i['cost']:
                    check_towc = including_tax(i['cost'], vat)
                elif i['percent']:
                    check_towc = including_tax(contract_cost * i['percent'] / 100, vat)

                # del i['type']

                lst_cost_tow = i if i['cost'] or i['percent'] else lst_cost_tow
                check_ac = round(check_ac - check_towc, 2)

                values_ac_ins.append([
                    act_id,
                    i['id'],
                    including_tax(i['cost'], vat),
                    i['percent']
                ])

            if 0 > check_ac >= -0.01 and lst_cost_tow:
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] -= check_ac
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = including_tax(contract_cost * lst_cost_tow['percent'] / 100, vat)
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
                "Удалите акт и создайте новый для выбранного договора"
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
        if date_start != act_info['act_date']:
            columns_a.append('act_date')
            values_a[0].append(date_start)
        if status_id != act_info['contract_status_id']:
            columns_a.append('contract_status_id')
            values_a[0].append(status_id)
        if act_cost != act_info['act_cost']:
            columns_a.append('act_cost')
            values_a[0].append(act_cost)

        print('columns_a:', columns_a)
        print('values_a:', values_a)

        ######################################################################################
        # Определяем добавляемые, изменяемые и удаляемые tow
        ######################################################################################

        # Список tow акта
        cursor.execute("""
        SELECT 
            tow_id, 
            tow_cost AS cost, 
            tow_cost_percent AS percent,
            tow_cost::float AS cost_raw, 
            tow_cost_percent::float AS percent_raw
        FROM tows_act
        WHERE act_id = %s;
        """, [act_id])
        db_tow = cursor.fetchall()

        db_tow_dict = dict()
        if db_tow:
            for i in db_tow:
                i = dict(i)
                print(i)
                db_tow_dict[i['tow_id']] = i

        db_tow_id_list = set(db_tow_dict.keys())

        ######################################################################################
        # Проверяем, не превышает ли сумма tow стоимость договора, формируем список добавляемых и редактируемых tow
        ######################################################################################

        columns_ta_ins = ('act_id', 'tow_id', 'tow_cost', 'tow_cost_percent')
        tow_id_list_ins = tow_id_list - db_tow_id_list  # СПИСОК ДОБАВЛЕНИЯ TOW
        tow_id_list_del = db_tow_id_list - tow_id_list  # СПИСОК УДАЛЕНИЯ TOW
        tow_id_list_upd = tow_id_list - tow_id_list_del - tow_id_list_ins  # СПИСОК ИЗМЕНЕНИЯ TOW
        print('____tow_id_list_ins____', tow_id_list_ins)
        print('____tow_id_list_del____', tow_id_list_del)
        print('____tow_id_list_upd____', tow_id_list_upd)

        check_ac = act_cost
        lst_cost_tow = None
        values_ta_ins = []
        values_ta_del = []
        values_ta_upd = []
        tow_id_set_upd = set()
        for tow_id in tow_id_list - tow_id_list_del:
            print(' _ ' * 5, tow_id , tow_list_to_dict[tow_id])
            check_towc = 0
            if tow_id in tow_id_list_ins:
                print('   ins')
                if tow_list_to_dict[tow_id]['cost']:
                    tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                    check_towc = tow_list_to_dict[tow_id]['cost']
                    lst_cost_tow = tow_list_to_dict[tow_id]
                elif tow_list_to_dict[tow_id]['percent']:
                    # check_towc = including_tax(act_cost * tow_list_to_dict[tow_id]['percent'] / 100, 1)
                    check_towc = act_cost * tow_list_to_dict[tow_id]['percent'] / 100
                    lst_cost_tow = tow_list_to_dict[tow_id]
            elif tow_id in tow_id_list_upd:
                print('      upd')
                # Если указана стоимость
                if tow_list_to_dict[tow_id]['cost']:
                    print('cost')
                    # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
                    if db_tow_dict[tow_id]['cost'] and db_tow_dict[tow_id]['cost'] != tow_list_to_dict[tow_id]['cost']:
                        tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                        if db_tow_dict[tow_id]['cost'] != tow_list_to_dict[tow_id]['cost']:
                            check_towc = tow_list_to_dict[tow_id]['cost']
                            lst_cost_tow = tow_list_to_dict[tow_id]
                            print('    == 1 ==', db_tow_dict[tow_id]['cost'], tow_list_to_dict[tow_id]['cost'])
                            tow_id_set_upd.add(tow_id)
                        else:
                            check_towc = db_tow_dict[tow_id]['cost_raw']
                            print('    == 1 0 ==', db_tow_dict[tow_id]['cost'])
                    elif not db_tow_dict[tow_id]['cost']:
                        tow_list_to_dict[tow_id]['cost'] = including_tax(tow_list_to_dict[tow_id]['cost'], vat)
                        check_towc = tow_list_to_dict[tow_id]['cost']
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 2 ==', db_tow_dict[tow_id]['cost'], tow_list_to_dict[tow_id]['cost'])
                        tow_id_set_upd.add(tow_id)
                    # Никаких изменений у tow не было
                    else:
                        check_towc = 0
                        print('    == 0 0 ==', db_tow_dict[tow_id]['cost'], db_tow_dict[tow_id]['percent'])
                        if db_tow_dict[tow_id]['cost']:
                            check_towc = db_tow_dict[tow_id]['cost_raw']
                        elif db_tow_dict[tow_id]['percent']:
                            # check_towc = including_tax(act_cost * db_tow_dict[tow_id]['percent'] / 100, 1)
                            check_towc = act_cost * db_tow_dict[tow_id]['percent_raw'] / 100
                # Указаны проценты
                elif tow_list_to_dict[tow_id]['percent']:
                    print('percent')
                    if (db_tow_dict[tow_id]['percent'] and
                            db_tow_dict[tow_id]['percent'] != tow_list_to_dict[tow_id]['percent']):
                        # check_towc = including_tax(act_cost * tow_list_to_dict[tow_id]['percent'] / 100, 1)
                        check_towc = act_cost * tow_list_to_dict[tow_id]['percent'] / 100
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 3 ==', db_tow_dict[tow_id]['cost'], tow_list_to_dict[tow_id]['cost'])
                        tow_id_set_upd.add(tow_id)
                    elif (tow_list_to_dict[tow_id]['percent'] and
                          db_tow_dict[tow_id]['percent'] != tow_list_to_dict[tow_id]['percent']):
                        # check_towc = including_tax(act_cost * tow_list_to_dict[tow_id]['percent'] / 100, 1)
                        check_towc = act_cost * tow_list_to_dict[tow_id]['percent'] / 100
                        lst_cost_tow = tow_list_to_dict[tow_id]
                        print('    == 4 ==', db_tow_dict[tow_id]['cost'], tow_list_to_dict[tow_id]['cost'])
                    # Никаких изменений у tow не было
                    else:
                        check_towc = 0
                        if db_tow_dict[tow_id]['cost_raw']:
                            check_towc = db_tow_dict[tow_id]['cost_raw']
                        elif db_tow_dict[tow_id]['percent_raw']:
                            # check_towc = including_tax(act_cost * db_tow_dict[tow_id]['percent_raw'] / 100, 1)
                            check_towc = act_cost * db_tow_dict[tow_id]['percent_raw'] / 100

            else:
                print('      else')
                if db_tow_dict[tow_id]['cost_raw']:
                    check_towc = db_tow_dict[tow_id]['cost_raw']
                elif db_tow_dict[tow_id]['percent_raw']:
                    # check_towc = including_tax(act_cost * db_tow_dict[tow_id]['percent_raw'] / 100, 1)
                    check_towc = act_cost * db_tow_dict[tow_id]['percent_raw'] / 100

            print('        check_ac', check_ac, check_towc)
            # check_ac = round(check_ac - check_towc, 2)
            check_ac = check_ac - check_towc
        print('____check_ac____')
        print(check_ac)
        print(lst_cost_tow)

        if check_ac < 0:
            check_ac = round(check_ac, 2)
            if check_ac <= -1:
                description.extend([
                    f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                    f"Скорректируйте стоимость акта или видов работ"])
                print(' check_ac 2', description)
                return {
                    'status': 'error',
                    'description': description
                }
            elif lst_cost_tow:
                if lst_cost_tow['cost']:
                    lst_cost_tow['cost'] -= check_ac
                    description.extend([
                        f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                    print(111111111)
                elif lst_cost_tow['percent']:
                    lst_cost_tow['cost'] = (
                            including_tax(act_cost * lst_cost_tow['percent'] / 100, 1) + check_ac)
                    lst_cost_tow['percent'] = None
                    description.extend([
                        f"Общая стоимость видов работ акта превысила стоимость акта на {-check_ac} ₽.",
                        f"У последнего созданного/измененного вида работ была изменена стоимость:",
                        f"id-{lst_cost_tow['id']}, стоимость: {lst_cost_tow['cost']} ₽"
                    ])
                    print(22222222)
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

        # if 0 > check_ac >= -0.01 and lst_cost_tow:
        #     print('____check_ac____   01')
        #     if lst_cost_tow['cost']:
        #         print('____check_ac____   02', lst_cost_tow['cost'])
        #         lst_cost_tow['cost'] += check_ac
        #         lst_cost_tow['percent'] = None
        #         print(lst_cost_tow)
        #         print(tow_list)
        #     elif lst_cost_tow['percent']:
        #         print('____check_ac____   03', lst_cost_tow['percent'])
        #         lst_cost_tow['cost'] = including_tax(act_cost * lst_cost_tow['percent'] / 100, 1)
        #         lst_cost_tow['percent'] = None
        #     else:
        #         return {
        #             'status': 'error',
        #             'description': description.extend([
        #                 f"Общая стоимость видов работ акта превышает стоимость акта ({-check_ac} ₽).",
        #                 f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
        #                 f"к котором можно произвести корректировку стоимости"
        #             ])
        #         }
        # elif 0 > check_ac >= -0.01 and not lst_cost_tow:
        #     return {
        #         'status': 'error',
        #         'description': description.extend([
        #             f"Общая стоимость видов работ акта превышает стоимость акта ({-check_ac} ₽).",
        #             f"Не удалось перераспределить этот остаток, т.к. не был найден вид работ, "
        #             f"к котором можно произвести корректировку стоимости"
        #         ])
        #     }
        # elif check_ac < -0.01:
        #     return {
        #         'status': 'error',
        #         'description': description.extend([
        #             f"Общая стоимость видов работ акта превышает стоимость акта ({-check_ac} ₽).",
        #             f"Перераспределите стоимости видов работ, или увеличьте стоимость акта"
        #         ])
        #     }

        # ДОБАВЛЕНИЕ TOW
        if tow_id_list_ins:
            for tow_id in tow_id_list_ins:
                values_ta_ins.append([
                    act_id,
                    tow_list_to_dict[tow_id]['id'],
                    tow_list_to_dict[tow_id]['cost'],
                    tow_list_to_dict[tow_id]['percent']
                ])

            # for k, v in tow_list_to_dict.items():
            #     if k in tow_id_list_ins:
            #         v['cost'] = including_tax(v['cost'], vat)
            #         print('=====', k, v)
            #         values_ta_ins.append([
            #             act_id,
            #             v['id'],
            #             v['cost'],
            #             v['percent']
            #         ])

        # УДАЛЕНИЕ TOW
        columns_ta_del = 'act_id::int, tow_id::int'
        if tow_id_list_del:
            values_ta_del = [(act_id, i) for i in tow_id_list_del]

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

        # values_ta_upd = []
        # print(' ОБНОВЛЕНИЕ TOW', (tow_id_list - tow_id_list_del).intersection(db_tow_id_list))
        # for i in (tow_id_list - tow_id_list_del).intersection(db_tow_id_list):
        #     print('   **', i, tow_list_to_dict[i])
        #     # Если указана стоимость
        #     if tow_list_to_dict[i]['cost']:
        #         print('cost')
        #         # Проверяем, что стоимость равна стоимости из БД, если нет, добавляем в список для обновления
        #         if db_tow_dict[i]['cost'] and db_tow_dict[i]['cost'] != tow_list_to_dict[i]['cost']:
        #             print('    if', db_tow_dict[i]['cost'], )
        #             tow_list_to_dict[i]['cost'] = including_tax(tow_list_to_dict[i]['cost'], vat)
        #             if db_tow_dict[i]['cost'] != tow_list_to_dict[i]['cost']:
        #                 # tow_id_list_upd.add(tow_list_to_dict[i]['id'])
        #                 print('        1___', db_tow_dict[i]['cost'], tow_list_to_dict[i]['cost'])
        #                 # values_ta_upd.append([
        #                 #     act_id,
        #                 #     tow_list_to_dict[i]['id'],
        #                 #     tow_list_to_dict[i]['cost'],
        #                 #     tow_list_to_dict[i]['percent']
        #                 # ])
        #         elif not db_tow_dict[i]['cost']:
        #             # tow_id_list_upd.add(tow_list_to_dict[i]['id'])
        #             tow_list_to_dict[i]['cost'] = including_tax(tow_list_to_dict[i]['cost'], vat)
        #             print('        2______ not ', db_tow_dict[i]['cost'])
        #             # values_ta_upd.append([
        #             #     act_id,
        #             #     tow_list_to_dict[i]['id'],
        #             #     tow_list_to_dict[i]['cost'],
        #             #     tow_list_to_dict[i]['percent']
        #             # ])
        #     elif tow_list_to_dict[i]['percent']:
        #         print('percent')
        #         if db_tow_dict[i]['percent'] and db_tow_dict[i]['percent'] != tow_list_to_dict[i]['percent']:
        #             print('        3___ percent __', db_tow_dict[i]['percent'], tow_list_to_dict[i]['percent'])
        #             # tow_id_list_upd.add(tow_list_to_dict[i]['id'])
        #             # values_ta_upd.append([
        #             #     act_id,
        #             #     tow_list_to_dict[i]['id'],
        #             #     tow_list_to_dict[i]['cost'],
        #             #     tow_list_to_dict[i]['percent']
        #             # ])
        # if tow_id_list_upd:
        #     for i in tow_id_list_upd:
        #         values_ta_upd.append([
        #             act_id,
        #             tow_list_to_dict[i]['id'],
        #             tow_list_to_dict[i]['cost'],
        #             tow_list_to_dict[i]['percent']
        #         ])

        # Для acts
        if len(columns_a) > 1:
            query_a = app_payment.get_db_dml_query(action='UPDATE', table='acts', columns=columns_a)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^ save_act', query_a)
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
        return jsonify({
            'status': status,
            'description': description,
        })
    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
    #         return jsonify({
    #             'status': 'error',
    #             'description': [str(e)],
    #         })


@contract_app_bp.route('/contract-payments-list/card/new/<link>', methods=['GET'])
@contract_app_bp.route('/contract-payments-list/card/new', methods=['GET'])
@login_required
def get_card_contracts_new_payment(link=False):
    # try:
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    print('get_card_contracts_new_payment', link)
    user_id = app_login.current_user.get_id()

    # Connect to the database
    conn, cursor = app_login.conn_cursor_init_dict("contracts")

    object_id = get_proj_id(link_name=link)['object_id'] if link else -100
    contract_id = -100
    act_id = -100
    payment_id = -100

    # Находим номера всех договоров объекта (без субподрядных)
    if link:
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
    if link:
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
        'create_at': None,
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
    dept_list = app_project.get_dept_list(user_id)

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


# except Exception as e:
#     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
#     flash(message=['Ошибка', f'/contract-acts-list/card/new: {e}'], category='error')
#     return render_template('page_error.html', error=[e], nonce=get_nonce())


@contract_app_bp.route('/change-contract-from-payment/<int:contract_id>', methods=['POST'])
@login_required
def change_contract_from_payment(contract_id: int):
    # try:
    print(contract_id)
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    user_id = app_login.current_user.get_id()

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
    # except Exception as e:
    #     current_app.logger.info(f"url {request.path[1:]}  -  id {user_id}  -  {e}")
    #         return jsonify({
    #             'status': 'error',
    #             'description': [str(e)],
    #         })


@contract_app_bp.route('/change-payment_types-from-payment/<int:payment_types_id>/<int:some_id>', methods=['POST'])
@login_required
def change_payment_types_from_payment(payment_types: int, some_id: int):
    # try:
    print(payment_types, some_id)
    role = app_login.current_user.get_role()
    if role not in (1, 4, 5):
        return error_handlers.handle403(403)

    user_id = app_login.current_user.get_id()

    # Connect to the database
    conn, cursor = app_login.conn_cursor_init_dict("contracts")

    ######################################################################################
    # Вид платежа - АВАНС, подгружаем данные о tow договора
    ######################################################################################
    if payment_types == 1:
        pass
    ######################################################################################
    # Вид платежа - АКТ, подгружаем данные о tow акта
    ######################################################################################
    elif payment_types == 2:
        # Находим object_id, по нему находим список tow
        cursor.execute(FIND_OBJ_BY_ACT, [some_id])
        object_id = cursor.fetchone()
        print(object_id)
        if not object_id:
            return jsonify({
                'status': 'error',
                'description': ['Объект или договор не найден'],
            })

        contract_id, object_id = object_id[0], object_id[1]
        print('     object_id', object_id, '     contract_id', contract_id)
    else:
        return jsonify({
            'status': 'error',
            'description': ['Ошибка определения вида платежа'],
        })



def including_tax(cost: float, vat: [int, float]) -> float:
    try:
        cost = float(cost) if cost else 0
        # print(cost, vat, round(cost / vat, 2))
        return round(cost / vat, 2)

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return cost


@contract_app_bp.route('/get-towList', methods=['POST'])
@login_required
def get_tow_list():
    """Вызрузка сфокусированного tow list"""
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
                        CONTRACT_TOW_LIST,
                        [project_id, project_id, elem_id, elem_id, object_id, elem_id, elem_id]
                    )
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
                                t2.tow_date_start,
                                t2.tow_date_finish,
                                COALESCE(to_char(t2.tow_date_start, 'dd.mm.yyyy'), '') AS date_start_txt,
                                COALESCE(to_char(t2.tow_date_finish, 'dd.mm.yyyy'), '') AS date_finish_txt,
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
                                    tow_cost_percent,
                                    tow_date_start,
                                    tow_date_finish
                                FROM tows_contract
                                WHERE contract_id = %s
                            ) AS t2 ON t0.tow_id = t2.tow_id
                            ORDER BY t0.child_path, t0.lvl;""",
                        [project_id, project_id, elem_id]
                    )
                elif status == 'focus':
                    cursor.execute(
                        """
                        SELECT
                            path
                        FROM types_of_work
                        WHERE tow_id = %s
                        LIMIT 1;
                        """,
                        [elem_id]
                    )
                    focused_path = cursor.fetchone()[0]

                    focused_tow_list = CONTRACT_TOW_LIST
                    # Условие, когда путь (path) мы генерируем
                    # where_condition = """
                    # WHERE
                    #     t0.path <@ (SELECT CONCAT(path::text || '.%s')::ltree FROM types_of_work WHERE tow_id = %s) OR
                    #     t0.tow_id = %s
                    # ORDER BY t0.child_path, t0.lvl;
                    # """
                    # [project_id, project_id, elem_id, elem_id, object_id, focused_path, focused_id, focused_id]

                    # Условие, когда путь (path) мы находим
                    where_condition = """
                    WHERE 
                        t0.path <@ (SELECT CONCAT(path::text || '.%s')::ltree FROM types_of_work WHERE tow_id = %s) OR 
                        t0.tow_id = %s
                    ORDER BY t0.child_path, t0.lvl;
                    """
                    focused_tow_list = focused_tow_list.replace('ORDER BY t0.child_path, t0.lvl;', where_condition)
                    cursor.execute(
                        focused_tow_list,
                        [project_id, project_id, elem_id, elem_id, object_id, elem_id, elem_id,
                         focused_path, focused_id, focused_id]
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
        col_14 = "t1.vat"
        col_15 = "COALESCE((t1.contract_cost / t1.vat_value), '0')"
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
        col_6 = "t1.subcontract_number"
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
        col_14 = "t1.vat::text"
        col_15 = "COALESCE((t1.contract_cost / t1.vat_value), 0)"
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
        col_8 = "COALESCE((t1.act_cost / t3.vat_value), '0')"
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
        col_7 = "t3.vat::text"
        col_8 = "COALESCE((t1.act_cost / t3.vat_value), '0')"
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
    elif page_name == 'contract-acts-list':
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
        col_9 = "COALESCE((t1.act_cost / t3.vat_value), '0')"
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
        col_8 = "t3.vat::text"
        col_9 = "COALESCE((t1.act_cost / t3.vat_value), '0')"
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
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'get_table_list: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


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
        print('get_proj_id', e)
        current_app.logger.info(f"url {request.path[1:]}  -  _get_proj_id_  -  {e}")
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
        print('get_obj_list', e)
        current_app.logger.info(f"url {request.path[1:]}  -  _get_proj_id_  -  {e}")
        obj_list = None
    print(obj_list)
    return obj_list


@contract_app_bp.route('/tow-list-for-object/<int:object_id>/<int:type_id>/<contract_id>', methods=['POST'])
@login_required
def tow_list_for_object(object_id, type_id, contract_id=''):
    try:
        print('        tow_list_for_object', type(object_id), object_id, contract_id)

        user_id = app_login.current_user.get_id()

        # Находим project_id по object_id
        project_id = get_proj_id(object_id=object_id)['project_id']
        # Указываем id, который точно не может быть в БД
        contract_id = -100 if contract_id == 'new' else int(contract_id)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict("contracts")
        # Список tow
        cursor.execute(
            CONTRACT_TOW_LIST,
            [project_id, project_id, contract_id, contract_id, object_id, contract_id, contract_id]
        )
        tow = cursor.fetchall()
        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])
                # print(tow[i])
        print('tow', type(tow), len(tow), object_id, type_id, type_id)

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
        dept_list = app_project.get_dept_list(user_id)

        # Return the updated data as a response
        return jsonify({
            'status': 'success',
            'tow': tow,
            'dept_list': dept_list,
            'contracts': contracts,
            'subcontractors_cost': subcontractors_cost,
        })

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': [str(e)],
        })


@contract_app_bp.route('/save_new_partner', methods=['POST'])
@login_required
def save_new_partner():
    try:
        full_name = request.get_json()['full_name']
        short_name = request.get_json()['short_name']

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

        print('partner_id', partner_id)
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
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': [str(e)],
        })


@contract_app_bp.route('/delete_contract', methods=['POST'])
@login_required
def delete_contract():
    try:
        role = app_login.current_user.get_role()
        if role not in (1, 4, 5):
            return error_handlers.handle403(403)

        contract_id = request.get_json()['contract_id']
        # contract_id = 10

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
        print(object_id)
        proj_info = get_proj_id(object_id=object_id["object_id"])

        # Проверяем, есть ли допники у договора
        cursor.execute(
            """
                SELECT
                    t2.contract_number,
                    to_char(t2.create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS create_at
                FROM subcontract AS t1
                LEFT JOIN
                    (SELECT 
                        contract_id,
                        contract_number,
                        create_at
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
                                   f"Создан: {subcontracts[i]['create_at']}")

        # Проверяем, есть ли платежи и акты по договору
        cursor.execute(
            """
                SELECT
                    act_id AS id,
                    'Акт' AS type,
                    act_number AS name,
                    to_char(create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS create_at
                FROM acts
                WHERE contract_id = %s
                UNION ALL
                SELECT
                    payment_id AS id,
                    'Платеж' AS type,
                    payment_number AS name,
                    to_char(create_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS create_at
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
                print(acts_payments_of_contract[i])
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
                                   f"Создан: {acts_payments_of_contract[i]['create_at']}")

        # Конструктор для описания первой строки с причинами для ошибки
        if subcontracts or acts_payments_of_contract:
            description_0 = []
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
        query_tc_del = app_payment.get_db_dml_query(action='DELETE', table='tows_contract', columns='contract_id::int')
        values_tc_del = (contract_id,)
        print(query_tc_del, values_tc_del)
        execute_values(cursor, query_tc_del, (values_tc_del,))

        query_sc_del = app_payment.get_db_dml_query(action='DELETE', table='subcontract', columns='child_id::int')
        values_sc_del = (contract_id,)
        print(query_sc_del, values_sc_del)
        execute_values(cursor, query_sc_del, (values_sc_del,))

        query_c_del = app_payment.get_db_dml_query(action='DELETE', table='contracts', columns='contract_id::int')
        values_c_del = (contract_id,)
        print(query_c_del, values_c_del)
        execute_values(cursor, query_c_del, (values_c_del,))

        conn.commit()

        app_login.conn_cursor_close(cursor, conn)

        flash(message=[f"Договор №: {object_id['contract_number']} удалён", ], category='success')
        return jsonify({
            'status': 'success',
            'description': ['Договор удалён'],
            'link': proj_info['link_name'],
        })

    except Exception as e:
        current_app.logger.info(f"url {request.path[1:]}  -  id {app_login.current_user.get_id()}  -  {e}")
        return jsonify({
            'status': 'error',
            'description': str(e),
        })


@contract_app_bp.route('/delete_act', methods=['POST'])
@login_required
def delete_act():
    return jsonify({
        'status': 'error',
        'description': ['Удаление акта ещё не разработано'],
    })


def del_con_payment():
    pass
