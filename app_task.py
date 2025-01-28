import json
import time
from dataclasses import asdict

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
from dateutil.relativedelta import relativedelta

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
        path,
        tow_id,
        tow_name,
        dept_id,
        time_tracking,
        lvl,
        project_id,
        ARRAY[lvl, tow_id] AS child_path
    FROM types_of_work
    WHERE parent_id IS NULL AND project_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.path,
        n.tow_id,
        n.tow_name,
        n.dept_id,
        n.time_tracking,
        n.lvl,
        n.project_id,
        r.child_path || n.lvl || n.tow_id
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.parent_id = r.tow_id
    WHERE r.project_id = %s
)
SELECT
    t0.tow_id,
    t0.child_path,
    t0.tow_name,
    CASE
        WHEN length(t0.tow_name) > 120 - depth * 2 THEN SUBSTRING(t0.tow_name, 1, 117 - depth * 2) || '...'
        ELSE t0.tow_name
    END AS tow_short_name,
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

# Список tasks
TASK_LIST_old_WITHOUL_last_row = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        path,
        task_id,
        tow_id,
        CASE 
            WHEN main_task IS TRUE THEN 'main_task'
            ELSE 'task'
        END AS class,
        main_task,
        task_number,
        task_name,
        lvl,
        ARRAY[lvl, task_id] AS child_path
    FROM tasks
    WHERE parent_id IS NULL AND tow_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.path,
        n.task_id,
        n.tow_id,
        CASE 
            WHEN n.main_task IS TRUE THEN 'main_task'
            ELSE 'task'
        END AS class,
        n.main_task,
        n.task_number,
        n.task_name,
        n.lvl,
        r.child_path || n.lvl || n.task_id
    FROM rel_rec AS r
    JOIN tasks AS n ON n.parent_id = r.task_id
    WHERE r.tow_id = %s
),
--Для суммарных данных ТОМов
hotr AS (
    SELECT
        t3.main_task_id AS task_id,
        t1.hotr_date,
        SUM(hotr_value) AS hotr_value
    FROM hours_of_task_responsible AS t1
    LEFT JOIN (SELECT task_responsible_id, task_id FROM task_responsible) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
    LEFT JOIN (SELECT task_id, subltree(path,2,3)::text::int AS main_task_id, tow_id FROM tasks) AS t3 ON t2.task_id = t3.task_id
    WHERE t3.tow_id = %s
    GROUP BY t3.main_task_id, t1.hotr_date
)
SELECT
    t0.task_id,
    t0.tow_id,
    t0.child_path,
    t0.main_task,
    t0.class,
    COALESCE(t0.task_number, '') AS task_number,
    t0.task_name,
    t0.depth,
    t0.lvl,
    t1.task_responsible_id,
    t6.task_status_name,
    COALESCE(t1.task_responsible_comment, '') AS task_responsible_comment,
    t1.task_status_id,
    t1.user_id,
    t5.short_full_name,
    t1.rowspan,
    t4.task_cnt,
    
    CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '📅' || ROUND(COALESCE(t2.task_sum_fact, t3.task_sum_fact)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
    COALESCE(t2.task_sum_fact, t3.task_sum_fact) AS task_sum_fact,
    
    CASE WHEN COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) IS NOT NULL THEN '📅' || COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) ELSE '' END AS task_sum_previous_fact_txt,
    COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
    --text format
    CASE WHEN COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣' || COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) ELSE '' END AS input_task_sum_week_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_1 IS NOT NULL THEN t2.input_task_week_1_day_1::text ELSE '📅' || t3.input_task_week_1_day_1 END
        ELSE '' END AS input_task_week_1_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_2 IS NOT NULL THEN t2.input_task_week_1_day_2::text ELSE '📅' || t3.input_task_week_1_day_2 END
        ELSE '' END AS input_task_week_1_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_3 IS NOT NULL THEN t2.input_task_week_1_day_3::text ELSE '📅' || t3.input_task_week_1_day_3 END 
        ELSE '' END AS input_task_week_1_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_4 IS NOT NULL THEN t2.input_task_week_1_day_4::text ELSE '📅' || t3.input_task_week_1_day_4 END 
        ELSE '' END AS input_task_week_1_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_5 IS NOT NULL THEN t2.input_task_week_1_day_5::text ELSE '📅' || t3.input_task_week_1_day_5 END 
        ELSE '' END AS input_task_week_1_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_6 IS NOT NULL THEN t2.input_task_week_1_day_6::text ELSE '📅' || t3.input_task_week_1_day_6 END 
        ELSE '' END AS input_task_week_1_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_7 IS NOT NULL THEN t2.input_task_week_1_day_7::text ELSE '📅' || t3.input_task_week_1_day_7 END 
        ELSE '' END AS input_task_week_1_day_7_txt,
    
    CASE WHEN COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣' || COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) ELSE '' END AS input_task_sum_week_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_1 IS NOT NULL THEN t2.input_task_week_2_day_1::text ELSE '📅' || t3.input_task_week_2_day_1 END
        ELSE '' END AS input_task_week_2_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_2 IS NOT NULL THEN t2.input_task_week_2_day_2::text ELSE '📅' || t3.input_task_week_2_day_2 END
        ELSE '' END AS input_task_week_2_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_3 IS NOT NULL THEN t2.input_task_week_2_day_3::text ELSE '📅' || t3.input_task_week_2_day_3 END 
        ELSE '' END AS input_task_week_2_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_4 IS NOT NULL THEN t2.input_task_week_2_day_4::text ELSE '📅' || t3.input_task_week_2_day_4 END 
        ELSE '' END AS input_task_week_2_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_5 IS NOT NULL THEN t2.input_task_week_2_day_5::text ELSE '📅' || t3.input_task_week_2_day_5 END 
        ELSE '' END AS input_task_week_2_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_6 IS NOT NULL THEN t2.input_task_week_2_day_6::text ELSE '📅' || t3.input_task_week_2_day_6 END 
        ELSE '' END AS input_task_week_2_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_7 IS NOT NULL THEN t2.input_task_week_2_day_7::text ELSE '📅' || t3.input_task_week_2_day_7 END 
        ELSE '' END AS input_task_week_2_day_7_txt,

    CASE WHEN COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣' || COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) ELSE '' END AS input_task_sum_week_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_1 IS NOT NULL THEN t2.input_task_week_3_day_1::text ELSE '📅' || t3.input_task_week_3_day_1 END
        ELSE '' END AS input_task_week_3_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_2 IS NOT NULL THEN t2.input_task_week_3_day_2::text ELSE '📅' || t3.input_task_week_3_day_2 END
        ELSE '' END AS input_task_week_3_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_3 IS NOT NULL THEN t2.input_task_week_3_day_3::text ELSE '📅' || t3.input_task_week_3_day_3 END 
        ELSE '' END AS input_task_week_3_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_4 IS NOT NULL THEN t2.input_task_week_3_day_4::text ELSE '📅' || t3.input_task_week_3_day_4 END 
        ELSE '' END AS input_task_week_3_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_5 IS NOT NULL THEN t2.input_task_week_3_day_5::text ELSE '📅' || t3.input_task_week_3_day_5 END 
        ELSE '' END AS input_task_week_3_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_6 IS NOT NULL THEN t2.input_task_week_3_day_6::text ELSE '📅' || t3.input_task_week_3_day_6 END 
        ELSE '' END AS input_task_week_3_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_7 IS NOT NULL THEN t2.input_task_week_3_day_7::text ELSE '📅' || t3.input_task_week_3_day_7 END 
        ELSE '' END AS input_task_week_3_day_7_txt,

    CASE WHEN COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣' || COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) ELSE '' END AS input_task_sum_week_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_1 IS NOT NULL THEN t2.input_task_week_4_day_1::text ELSE '📅' || t3.input_task_week_4_day_1 END
        ELSE '' END AS input_task_week_4_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_2 IS NOT NULL THEN t2.input_task_week_4_day_2::text ELSE '📅' || t3.input_task_week_4_day_2 END
        ELSE '' END AS input_task_week_4_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_3 IS NOT NULL THEN t2.input_task_week_4_day_3::text ELSE '📅' || t3.input_task_week_4_day_3 END 
        ELSE '' END AS input_task_week_4_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_4 IS NOT NULL THEN t2.input_task_week_4_day_4::text ELSE '📅' || t3.input_task_week_4_day_4 END 
        ELSE '' END AS input_task_week_4_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_5 IS NOT NULL THEN t2.input_task_week_4_day_5::text ELSE '📅' || t3.input_task_week_4_day_5 END 
        ELSE '' END AS input_task_week_4_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_6 IS NOT NULL THEN t2.input_task_week_4_day_6::text ELSE '📅' || t3.input_task_week_4_day_6 END 
        ELSE '' END AS input_task_week_4_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_7 IS NOT NULL THEN t2.input_task_week_4_day_7::text ELSE '📅' || t3.input_task_week_4_day_7 END 
        ELSE '' END AS input_task_week_4_day_7_txt,
    
    --numeric format
    COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) AS input_task_sum_week_1,
    COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) AS input_task_week_1_day_1,
    COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) AS input_task_week_1_day_2,
    COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) AS input_task_week_1_day_3,
    COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) AS input_task_week_1_day_4,
    COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) AS input_task_week_1_day_5,
    COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) AS input_task_week_1_day_6,
    COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) AS input_task_week_1_day_7,
    
    COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) AS input_task_sum_week_2,
    COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) AS input_task_week_2_day_1,
    COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) AS input_task_week_2_day_2,
    COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) AS input_task_week_2_day_3,
    COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) AS input_task_week_2_day_4,
    COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) AS input_task_week_2_day_5,
    COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) AS input_task_week_2_day_6,
    COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) AS input_task_week_2_day_7,
    
    COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) AS input_task_sum_week_3,
    COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) AS input_task_week_3_day_1,
    COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) AS input_task_week_3_day_2,
    COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) AS input_task_week_3_day_3,
    COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) AS input_task_week_3_day_4,
    COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) AS input_task_week_3_day_5,
    COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) AS input_task_week_3_day_6,
    COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) AS input_task_week_3_day_7,
    
    COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) AS input_task_sum_week_4,
    COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) AS input_task_week_4_day_1,
    COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) AS input_task_week_4_day_2,
    COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) AS input_task_week_4_day_3,
    COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) AS input_task_week_4_day_4,
    COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) AS input_task_week_4_day_5,
    COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) AS input_task_week_4_day_6,
    COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) AS input_task_week_4_day_7,
    
    CASE WHEN COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) IS NOT NULL THEN '📅' || COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) ELSE '' END AS task_sum_future_fact_txt,
    COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) AS task_sum_future_fact


FROM rel_rec AS t0
FULL JOIN (
    SELECT
        task_responsible_id,
        task_id,
        user_id,
        task_status_id,
        task_responsible_comment,
        CASE
            WHEN ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY task_responsible_id ASC) = 1
            THEN ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY task_responsible_id DESC)
            ELSE -1
        END AS rowspan
    FROM public.task_responsible
    WHERE task_id IN (SELECT task_id FROM tasks WHERE tow_id = %s)
) AS t1 ON t0.task_id = t1.task_id

LEFT JOIN (
    SELECT
        --SUM(CASE WHEN hotr_date <= (CURRENT_DATE - EXTRACT(DOW FROM CURRENT_DATE)::INTEGER - 7)::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
        task_responsible_id,
        SUM(hotr_value) AS task_sum_fact,
        
        SUM(CASE WHEN hotr_date < (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
        
        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE AND hotr_date < (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE))::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_7,
            
        SUM(CASE WHEN hotr_date > (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_future_fact
            
    FROM public.hours_of_task_responsible
    GROUP BY task_responsible_id
) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
LEFT JOIN (
    SELECT
        --SUM(CASE WHEN hotr_date <= (CURRENT_DATE - EXTRACT(DOW FROM CURRENT_DATE)::INTEGER - 7)::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
        task_id,
        SUM(hotr_value) AS task_sum_fact,
        
        SUM(CASE WHEN hotr_date < (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
        
        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE AND hotr_date < (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE))::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_7,
            
        SUM(CASE WHEN hotr_date > (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_future_fact
            
    FROM hotr
    GROUP BY task_id
) AS t3 ON t0.task_id = t3.task_id AND t0.main_task IS TRUE
LEFT JOIN (
    SELECT
        parent_id,
        COUNT(*) task_cnt
    FROM tasks
    GROUP BY parent_id
) AS t4 ON t0.task_id = t4.parent_id
LEFT JOIN (
    SELECT
        user_id,
        concat_ws(' ', 
            last_name, 
            LEFT(first_name, 1) || '.', 
            CASE
                WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
            END) AS short_full_name
    FROM public.users
) AS t5 ON t1.user_id = t5.user_id
LEFT JOIN (
    SELECT 
        task_status_id,
        task_status_name
    FROM public.task_statuses
) AS t6 ON t1.task_status_id = t6.task_status_id

ORDER BY t0.child_path, t0.lvl, t1.task_responsible_id;


"""

TASK_LIST = """
WITH RECURSIVE rel_rec AS (
    SELECT
        0 AS depth,
        path,
        task_id,
        tow_id,
        CASE 
            WHEN main_task IS TRUE THEN 'main_task'
            ELSE 'task'
        END AS class,
        main_task,
        task_number,
        task_name,
        lvl,
        ARRAY[lvl, task_id] AS child_path
    FROM tasks
    WHERE parent_id IS NULL AND tow_id = %s

    UNION ALL
    SELECT
        nlevel(r.path) - 2,
        n.path,
        n.task_id,
        n.tow_id,
        CASE 
            WHEN n.main_task IS TRUE THEN 'main_task'
            ELSE 'task'
        END AS class,
        n.main_task,
        n.task_number,
        n.task_name,
        n.lvl,
        r.child_path || n.lvl || n.task_id
    FROM rel_rec AS r
    JOIN tasks AS n ON n.parent_id = r.task_id
    WHERE r.tow_id = %s
),
--Для суммарных данных ТОМов
hotr AS (
    SELECT
        t3.main_task_id AS task_id,
        t1.hotr_date,
        SUM(hotr_value) AS hotr_value,
        
        SUM(CASE WHEN hotr_date < (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
        
        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE AND hotr_date < (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE))::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_7,

        SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_1,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_2,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_3,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_4,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_5,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_6,
            SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_7,

        SUM(CASE WHEN hotr_date > (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_future_fact
        
    FROM hours_of_task_responsible AS t1
    LEFT JOIN (SELECT task_responsible_id, task_id FROM task_responsible) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
    LEFT JOIN (SELECT task_id, subltree(path,2,3)::text::int AS main_task_id, tow_id FROM tasks) AS t3 ON t2.task_id = t3.task_id
    WHERE t3.tow_id = %s
    GROUP BY t3.main_task_id, t1.hotr_date
),
--Для суммарных данных ТОМов task_plan_labor_cost
tplc AS (
	SELECT
        t3.main_task_id AS task_id,
        SUM(t2.task_plan_labor_cost) AS task_plan_labor_cost
        
	FROM task_responsible AS t2
    LEFT JOIN (SELECT task_id, subltree(path,2,3)::text::int AS main_task_id, tow_id FROM tasks) AS t3 ON t2.task_id = t3.task_id
    WHERE t3.tow_id = %s
    GROUP BY t3.main_task_id
)
    (SELECT
        CASE 
            WHEN t1.task_responsible_id IS NULL THEN 'tom-' || t0.task_id 
            ELSE 'task-' || t1.task_responsible_id 
        END AS row_id,

        COALESCE(t1.task_plan_labor_cost, t31.task_plan_labor_cost) AS task_plan_labor_cost,
		COALESCE(TRIM(TRAILING '.' FROM TRIM(TRAILING '0' FROM ROUND(COALESCE(t1.task_plan_labor_cost, t31.task_plan_labor_cost), 4)::text)), '') AS task_plan_labor_cost_txt,

        CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact, NULL) IS NULL THEN FALSE ELSE TRUE END AS is_not_edited,
        t0.task_id,
        t0.tow_id,
        t0.child_path,
        t0.main_task,
        t0.class,
        COALESCE(t0.task_number, '') AS task_number,
        t0.task_name,
        t0.depth,
        t0.lvl,
        t1.task_responsible_id,
        COALESCE(t6.task_status_name, '...') AS task_status_name,
        COALESCE(t1.task_responsible_comment, '') AS task_responsible_comment,
        t1.task_status_id,
        t1.user_id,
        COALESCE(t5.short_full_name, '...') AS short_full_name,
        t1.rowspan,
        t4.task_cnt,
    
        CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '📅' || ROUND(COALESCE(t2.task_sum_fact, t3.task_sum_fact)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
        COALESCE(t2.task_sum_fact, t3.task_sum_fact) AS task_sum_fact,
    
        CASE WHEN COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) IS NOT NULL THEN '📅' || ROUND(COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact)/8::numeric, 2) ELSE '' END AS task_sum_previous_fact_txt,
        COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
        --text format
        CASE WHEN COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣' || TO_CHAR((INTERVAL '1 minute' * COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) * 60), 'HH24:MI') ELSE '' END AS input_task_sum_week_1_txt,
            
        CASE WHEN COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_1 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_1 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_1 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_1_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_2 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_2 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_2 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_1_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_3 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_3 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_3 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_1_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_4 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_4 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_4 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_1_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_5 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_5 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_5 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_1_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_6 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_6 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_6 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_1_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) IS NOT NULL THEN 
            CASE 
                WHEN t2.input_task_week_1_day_7 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_1_day_7 * 60), 'HH24:MI') 
                ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_1_day_7 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_1_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣' || TO_CHAR((INTERVAL '1 minute' * COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) * 60), 'HH24:MI') ELSE '' END AS input_task_sum_week_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_1 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_1 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_1 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_2_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_2 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_2 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_2 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_2_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_3 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_3 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_3 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_2_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_4 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_4 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_4 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_2_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_5 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_5 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_5 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_2_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_6 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_6 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_6 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_2_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_7 IS NOT NULL THEN TO_CHAR((INTERVAL '1 minute' * t2.input_task_week_2_day_7 * 60), 'HH24:MI') ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_2_day_7 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_2_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣' || TO_CHAR((INTERVAL '1 minute' * COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) * 60), 'HH24:MI') ELSE '' END AS input_task_sum_week_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_1 IS NOT NULL THEN t2.input_task_week_3_day_1::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_1 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_3_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_2 IS NOT NULL THEN t2.input_task_week_3_day_2::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_2 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_3_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_3 IS NOT NULL THEN t2.input_task_week_3_day_3::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_3 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_3_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_4 IS NOT NULL THEN t2.input_task_week_3_day_4::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_4 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_3_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_5 IS NOT NULL THEN t2.input_task_week_3_day_5::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_5 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_3_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_6 IS NOT NULL THEN t2.input_task_week_3_day_6::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_6 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_3_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_7 IS NOT NULL THEN t2.input_task_week_3_day_7::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_3_day_7 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_3_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣' || TO_CHAR((INTERVAL '1 minute' * COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) * 60), 'HH24:MI') ELSE '' END AS input_task_sum_week_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_1 IS NOT NULL THEN t2.input_task_week_4_day_1::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_1 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_4_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_2 IS NOT NULL THEN t2.input_task_week_4_day_2::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_2 * 60), 'HH24:MI') END
            ELSE '' END AS input_task_week_4_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_3 IS NOT NULL THEN t2.input_task_week_4_day_3::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_3 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_4_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_4 IS NOT NULL THEN t2.input_task_week_4_day_4::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_4 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_4_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_5 IS NOT NULL THEN t2.input_task_week_4_day_5::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_5 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_4_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_6 IS NOT NULL THEN t2.input_task_week_4_day_6::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_6 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_4_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_7 IS NOT NULL THEN t2.input_task_week_4_day_7::text ELSE '📅' || TO_CHAR((INTERVAL '1 minute' * t3.input_task_week_4_day_7 * 60), 'HH24:MI') END 
            ELSE '' END AS input_task_week_4_day_7_txt,
    
        --numeric format
        COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) AS input_task_sum_week_1,
        COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) AS input_task_week_1_day_1,
        COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) AS input_task_week_1_day_2,
        COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) AS input_task_week_1_day_3,
        COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) AS input_task_week_1_day_4,
        COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) AS input_task_week_1_day_5,
        COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) AS input_task_week_1_day_6,
        COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) AS input_task_week_1_day_7,
    
        COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) AS input_task_sum_week_2,
        COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) AS input_task_week_2_day_1,
        COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) AS input_task_week_2_day_2,
        COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) AS input_task_week_2_day_3,
        COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) AS input_task_week_2_day_4,
        COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) AS input_task_week_2_day_5,
        COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) AS input_task_week_2_day_6,
        COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) AS input_task_week_2_day_7,
    
        COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) AS input_task_sum_week_3,
        COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) AS input_task_week_3_day_1,
        COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) AS input_task_week_3_day_2,
        COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) AS input_task_week_3_day_3,
        COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) AS input_task_week_3_day_4,
        COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) AS input_task_week_3_day_5,
        COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) AS input_task_week_3_day_6,
        COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) AS input_task_week_3_day_7,
    
        COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) AS input_task_sum_week_4,
        COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) AS input_task_week_4_day_1,
        COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) AS input_task_week_4_day_2,
        COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) AS input_task_week_4_day_3,
        COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) AS input_task_week_4_day_4,
        COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) AS input_task_week_4_day_5,
        COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) AS input_task_week_4_day_6,
        COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) AS input_task_week_4_day_7,
    
        CASE WHEN COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) IS NOT NULL THEN '📅' || ROUND(COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact)/8::numeric, 2) ELSE '' END AS task_sum_future_fact_txt,
        COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) AS task_sum_future_fact
    
    
    FROM rel_rec AS t0
    FULL JOIN (
        SELECT
            task_responsible_id,
            task_id,
            user_id,
            task_status_id,
            task_responsible_comment,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY task_responsible_id ASC) = 1
                THEN ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY task_responsible_id DESC)
                ELSE -1
            END AS rowspan,
            task_plan_labor_cost
        FROM public.task_responsible
        WHERE task_id IN (SELECT task_id FROM tasks WHERE tow_id = %s)
    ) AS t1 ON t0.task_id = t1.task_id
    
    LEFT JOIN (
        SELECT
            --SUM(CASE WHEN hotr_date <= (CURRENT_DATE - EXTRACT(DOW FROM CURRENT_DATE)::INTEGER - 7)::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
            task_responsible_id,
            SUM(hotr_value) AS task_sum_fact,
    
            SUM(CASE WHEN hotr_date < (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
    
            SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE AND hotr_date < (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_1,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '7 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) - interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,
    
            SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE))::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_2,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_1,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_2,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_3,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_4,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_5,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_6,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_2_day_7,
    
            SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_3,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_1,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_2,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_3,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_4,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_5,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_6,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_3_day_7,
    
            SUM(CASE WHEN hotr_date >= (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE AND hotr_date <= (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_sum_week_4,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_1,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_2,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_3,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_4,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_5,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_6,
                SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_4_day_7,
    
            SUM(CASE WHEN hotr_date > (date_trunc('week', CURRENT_DATE) + interval '2 week' + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS task_sum_future_fact
    
        FROM public.hours_of_task_responsible
        GROUP BY task_responsible_id
    ) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
    LEFT JOIN (
        SELECT
            --SUM(CASE WHEN hotr_date <= (CURRENT_DATE - EXTRACT(DOW FROM CURRENT_DATE)::INTEGER - 7)::DATE THEN hotr_value ELSE NULL END) AS task_sum_previous_fact,
            task_id,
            SUM(hotr_value) AS task_sum_fact,
    
            SUM(task_sum_previous_fact) AS task_sum_previous_fact,
    
            SUM(input_task_sum_week_1) AS input_task_sum_week_1,
                SUM(input_task_week_1_day_1) AS input_task_week_1_day_1,
                SUM(input_task_week_1_day_2) AS input_task_week_1_day_2,
                SUM(input_task_week_1_day_3) AS input_task_week_1_day_3,
                SUM(input_task_week_1_day_4) AS input_task_week_1_day_4,
                SUM(input_task_week_1_day_5) AS input_task_week_1_day_5,
                SUM(input_task_week_1_day_6) AS input_task_week_1_day_6,
                SUM(input_task_week_1_day_7) AS input_task_week_1_day_7,
                
            SUM(input_task_sum_week_2) AS input_task_sum_week_2,
                SUM(input_task_week_2_day_1) AS input_task_week_2_day_1,
                SUM(input_task_week_2_day_2) AS input_task_week_2_day_2,
                SUM(input_task_week_2_day_3) AS input_task_week_2_day_3,
                SUM(input_task_week_2_day_4) AS input_task_week_2_day_4,
                SUM(input_task_week_2_day_5) AS input_task_week_2_day_5,
                SUM(input_task_week_2_day_6) AS input_task_week_2_day_6,
                SUM(input_task_week_2_day_7) AS input_task_week_2_day_7,
                
            SUM(input_task_sum_week_3) AS input_task_sum_week_3,
                SUM(input_task_week_3_day_1) AS input_task_week_3_day_1,
                SUM(input_task_week_3_day_2) AS input_task_week_3_day_2,
                SUM(input_task_week_3_day_3) AS input_task_week_3_day_3,
                SUM(input_task_week_3_day_4) AS input_task_week_3_day_4,
                SUM(input_task_week_3_day_5) AS input_task_week_3_day_5,
                SUM(input_task_week_3_day_6) AS input_task_week_3_day_6,
                SUM(input_task_week_3_day_7) AS input_task_week_3_day_7,
            
            SUM(input_task_sum_week_4) AS input_task_sum_week_4,
                SUM(input_task_week_4_day_1) AS input_task_week_4_day_1,
                SUM(input_task_week_4_day_2) AS input_task_week_4_day_2,
                SUM(input_task_week_4_day_3) AS input_task_week_4_day_3,
                SUM(input_task_week_4_day_4) AS input_task_week_4_day_4,
                SUM(input_task_week_4_day_5) AS input_task_week_4_day_5,
                SUM(input_task_week_4_day_6) AS input_task_week_4_day_6,
                SUM(input_task_week_4_day_7) AS input_task_week_4_day_7,
                
            SUM(task_sum_future_fact) AS task_sum_future_fact
    
        FROM hotr
        GROUP BY task_id
    ) AS t3 ON t0.task_id = t3.task_id AND t0.main_task IS TRUE
	LEFT JOIN tplc AS t31 ON t0.task_id = t31.task_id AND t0.main_task IS TRUE
    LEFT JOIN (
        SELECT
            parent_id,
            COUNT(*) task_cnt
        FROM tasks
        GROUP BY parent_id
    ) AS t4 ON t0.task_id = t4.parent_id
    LEFT JOIN (
        SELECT
            user_id,
            concat_ws(' ', 
                last_name, 
                LEFT(first_name, 1) || '.', 
                CASE
                    WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
                END) AS short_full_name
        FROM public.users
    ) AS t5 ON t1.user_id = t5.user_id
    LEFT JOIN (
        SELECT 
            task_status_id,
            task_status_name
        FROM public.task_statuses
    ) AS t6 ON t1.task_status_id = t6.task_status_id
    ORDER BY t0.child_path, t0.lvl, t1.task_responsible_id)

UNION ALL

    SELECT
        'itogo-row' AS row_id,
        (SELECT SUM(task_plan_labor_cost) AS task_plan_labor_cost FROM tplc) AS task_plan_labor_cost,
 		TRIM(TRAILING '.' FROM TRIM(TRAILING '0' FROM (SELECT SUM(task_plan_labor_cost) AS task_plan_labor_cost FROM tplc)::text)) AS task_plan_labor_cost_txt,
        TRUE AS is_not_edited,
        NULL AS task_id,
        NULL AS tow_id,
        ARRAY[NULL::int] AS child_path,
        TRUE AS main_task,
        'last_row' AS class,
        '' AS task_number,
        'ИТОГО (в днях)' AS task_name,
        NULL AS depth,
        NULL AS lvl,
        NULL AS task_responsible_id,
        '' AS task_status_name,
        '' AS task_responsible_comment,
        NULL AS task_status_id,
        NULL AS user_id,
        NULL AS short_full_name,
        1 AS rowspan,
        NULL AS task_cnt,
    
        CASE WHEN SUM(t3.hotr_value) IS NOT NULL THEN '📅' || ROUND(SUM(t3.hotr_value)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
        SUM(t3.hotr_value) AS task_sum_fact,
    
        CASE WHEN SUM(t3.task_sum_previous_fact) IS NOT NULL THEN '📅' || ROUND(SUM(t3.task_sum_previous_fact)/8::numeric, 2) ELSE '' END AS task_sum_previous_fact_txt,
        SUM(t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
        --text format
        CASE WHEN SUM(t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣' || ROUND(SUM(t3.input_task_sum_week_1)/8::numeric, 2) ELSE '' END AS input_task_sum_week_1_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_1) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_2) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_3) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_4) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_5) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_6) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_7) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_1_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣' || ROUND(SUM(t3.input_task_sum_week_2)/8::numeric, 2) ELSE '' END AS input_task_sum_week_2_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_1) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_2) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_3) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_4) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_5) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_6) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_7) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_2_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣' || ROUND(SUM(t3.input_task_sum_week_3)/8::numeric, 2) ELSE '' END AS input_task_sum_week_3_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_1) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_2) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_3) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_4) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_5) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_6) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_7) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_3_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣' || ROUND(SUM(t3.input_task_sum_week_4)/8::numeric, 2) ELSE '' END AS input_task_sum_week_4_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_1) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_2) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_3) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_4) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_5) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_6) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_7) IS NOT NULL THEN '📅' || ROUND(SUM(t3.input_task_week_4_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_7_txt,
        
        --numeric format
        SUM(t3.input_task_sum_week_1) AS input_task_sum_week_1,
        SUM(t3.input_task_week_1_day_1) AS input_task_week_1_day_1,
        SUM(t3.input_task_week_1_day_2) AS input_task_week_1_day_2,
        SUM(t3.input_task_week_1_day_3) AS input_task_week_1_day_3,
        SUM(t3.input_task_week_1_day_4) AS input_task_week_1_day_4,
        SUM(t3.input_task_week_1_day_5) AS input_task_week_1_day_5,
        SUM(t3.input_task_week_1_day_6) AS input_task_week_1_day_6,
        SUM(t3.input_task_week_1_day_7) AS input_task_week_1_day_7,
        
        SUM(t3.input_task_sum_week_2) AS input_task_sum_week_2,
        SUM(t3.input_task_week_2_day_1) AS input_task_week_2_day_1,
        SUM(t3.input_task_week_2_day_2) AS input_task_week_2_day_2,
        SUM(t3.input_task_week_2_day_3) AS input_task_week_2_day_3,
        SUM(t3.input_task_week_2_day_4) AS input_task_week_2_day_4,
        SUM(t3.input_task_week_2_day_5) AS input_task_week_2_day_5,
        SUM(t3.input_task_week_2_day_6) AS input_task_week_2_day_6,
        SUM(t3.input_task_week_2_day_7) AS input_task_week_2_day_7,
        
        SUM(t3.input_task_sum_week_3) AS input_task_sum_week_3,
        SUM(t3.input_task_week_3_day_1) AS input_task_week_3_day_1,
        SUM(t3.input_task_week_3_day_2) AS input_task_week_3_day_2,
        SUM(t3.input_task_week_3_day_3) AS input_task_week_3_day_3,
        SUM(t3.input_task_week_3_day_4) AS input_task_week_3_day_4,
        SUM(t3.input_task_week_3_day_5) AS input_task_week_3_day_5,
        SUM(t3.input_task_week_3_day_6) AS input_task_week_3_day_6,
        SUM(t3.input_task_week_3_day_7) AS input_task_week_3_day_7,
        
        SUM(t3.input_task_sum_week_4) AS input_task_sum_week_4,
        SUM(t3.input_task_week_4_day_1) AS input_task_week_4_day_1,
        SUM(t3.input_task_week_4_day_2) AS input_task_week_4_day_2,
        SUM(t3.input_task_week_4_day_3) AS input_task_week_4_day_3,
        SUM(t3.input_task_week_4_day_4) AS input_task_week_4_day_4,
        SUM(t3.input_task_week_4_day_5) AS input_task_week_4_day_5,
        SUM(t3.input_task_week_4_day_6) AS input_task_week_4_day_6,
        SUM(t3.input_task_week_4_day_7) AS input_task_week_4_day_7,
        
        CASE WHEN SUM(t3.task_sum_future_fact) IS NOT NULL THEN '📅' || SUM(t3.task_sum_future_fact) ELSE '' END AS task_sum_future_fact_txt,
        SUM(t3.task_sum_future_fact) AS task_sum_future_fact
    
    FROM hotr AS t3"""

# Список сотрудников с их текущим отделом и родительским отделом (АР=> АМ-2)
EMPLOYEES_LIST = """
SELECT
    t1.user_id,
    concat_ws(' ', 
        t1.last_name, 
        LEFT(t1.first_name, 1) || '.', 
        CASE
            WHEN t1.surname<>'' THEN LEFT(t1.surname, 1) || '.' ELSE ''
        END) AS short_full_name,
    t3.*
FROM public.users AS t1
LEFT JOIN (
    SELECT
        DISTINCT ON (user_id)
        user_id,
        dept_id,
        date_promotion
    FROM public.empl_dept
    WHERE date_promotion <= now()
    ORDER BY user_id, date_promotion DESC
) AS t2 ON t1.user_id = t2.user_id
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
        dept_id,
        dept_short_name,
        group_id,
        group_name,
        group_short_name
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
        dr2.child_id AS dept_id,
        lg2.dept_short_name,
        dr2.child_id AS group_id,
        lg2.dept_name AS group_name,
        lg2.dept_short_name AS group_short_name
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
    
    ORDER BY group_id
) AS t3 ON t2.dept_id = t3.group_id
"""

# Список отделов и родительские отделы
DEPT_LIST_WITH_PARENT_part_1 = """
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
    ld.dept_id,
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
WHERE ph.parent_id IS NULL """

DEPT_LIST_WITH_PARENT_part_2 = """
UNION

SELECT 
    dr2.child_id AS dept_id,
    lg2.dept_short_name,
    dr2.child_id AS group_id,
    lg2.dept_name AS group_name,
    lg2.dept_short_name AS group_short_name
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
"""

DAYS_OF_THE_WEEK = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']  # Дни недели
DAYS_OF_THE_WEEK_FULL = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

# Список задач без орг работ
MY_TASKS_LIST = f"""
                WITH RECURSIVE rel_task_resp AS (
                    SELECT
                        10000 AS depth,
                        task_responsible_id,
                        task_id,
                        task_id AS parent_id,
                        0 AS tow_id,
                        task_status_id,
                        ARRAY[''] AS name_path,
                        ARRAY[''] AS short_name_path,
                        ARRAY[task_id] AS child_path,
                        '' AS task_name,
						ARRAY['tr'] AS tow_task,
						ARRAY['Текущая задача: '] AS tow_task_title
                    FROM task_responsible
                    WHERE user_id = %s
                    
                    UNION ALL
                    
                    SELECT
                        r.depth - 1,
                        r.task_responsible_id,
                        n.task_id,
                        n.parent_id,
                        n.tow_id,
                        r.task_status_id,
                        n.task_name || r.name_path,
                        
                        CASE
                            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
                            ELSE n.task_name
                        END || r.short_name_path,
          
                        r.child_path || n.task_id || n.lvl::int,
                        n.task_name,
						ARRAY['task'] || r.tow_task,
						ARRAY['Задача: '] || r.tow_task_title
                    FROM rel_task_resp AS r
                    JOIN tasks AS n ON n.task_id = r.parent_id
                ),
                rel_rec AS (
                    SELECT
						depth,
                        task_responsible_id,
                        task_id,
                        tow_id AS parent_id,
                        tow_id,
                        task_status_id,
                        name_path,
                        short_name_path,
                        child_path,
                        task_name,
						tow_task,
						tow_task_title
                    FROM rel_task_resp
                    WHERE parent_id IS NULL
                
                    UNION ALL
                
                    SELECT
                        r.depth - 1,
                        r.task_responsible_id,
                        r.task_id,
                        n.parent_id,
                        n.tow_id,
                        r.task_status_id,
                        n.tow_name || r.name_path,

                        CASE
                            WHEN length(n.tow_name) > 20 THEN SUBSTRING(n.tow_name, 1, 17) || '...'
                            ELSE n.tow_name
                        END || r.short_name_path,
                                        
                        r.child_path || n.tow_id || n.lvl::int,
                        n.tow_name,
						ARRAY['tow'] || r.tow_task,
						ARRAY['Вид работ: '] || r.tow_task_title
                    FROM rel_rec AS r
                    JOIN types_of_work AS n ON n.tow_id = r.parent_id
                )
                SELECT
                    CASE
                        WHEN t1.task_status_id = 4 THEN 'tr_task_status_closed'
                        ELSE 'tr_task_status_not_closed'
                    END AS task_class,
                    t1.child_path[1] AS task_id,
                    t1.task_responsible_id,
                    '' as task_number,
                    t1.task_status_id,
                    t1.tow_task,
                    t1.tow_task_title,
                    t4.project_id,
                    t5.task_status_name,
					t6.hotr_value,
					t2.task_plan_labor_cost,
					COALESCE(t6.hotr_value::text, '-') AS hotr_value_txt,
					COALESCE(t2.task_plan_labor_cost::text, '-') AS task_plan_labor_cost_txt,
                    CASE
                        WHEN t1.task_status_id = 4 THEN TRUE
                        ELSE FALSE
                    END AS editing_is_prohibited,
                    t3.tow_id,
                    COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,
                    t6.input_task_week_1_day_1,
                    t6.input_task_week_1_day_2,
                    t6.input_task_week_1_day_3,
                    t6.input_task_week_1_day_4,
                    t6.input_task_week_1_day_5,
                    t6.input_task_week_1_day_6,
                    t6.input_task_week_1_day_7,
                    
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt,
                    /*depth,
                    task_responsible_id,
                    task_id,
                    name_path[1:array_length(name_path, 1) - 1] AS name_path*/
                    
                    t1.name_path[array_length(t1.name_path, 1) - 1] AS task_name,
                    t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,

                    t1.short_name_path[array_length(t1.short_name_path, 1) - 1] AS short_task_name,
                    t1.short_name_path[1:array_length(t1.short_name_path, 1) - 2] AS short_name_path

                    
                FROM rel_rec AS t1
                LEFT JOIN (
                    SELECT 
                        task_id,
                        task_responsible_id,
                        task_status_id,
                        task_responsible_comment,
                        task_plan_labor_cost
                    FROM public.task_responsible
                ) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
                LEFT JOIN (
                    SELECT 
                        task_id,
                        tow_id
                    FROM public.tasks
                ) AS t3 ON t1.child_path[1] = t3.task_id
                LEFT JOIN (
                    SELECT 
                        tow_id,
                        project_id
                    FROM public.types_of_work
                ) AS t4 ON t1.tow_id = t4.tow_id
                LEFT JOIN (
                    SELECT 
                        task_status_id,
                        task_status_name
                    FROM public.task_statuses
                ) AS t5 ON t1.task_status_id = t5.task_status_id
                LEFT JOIN (
                    SELECT
                        task_responsible_id,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                        SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,
                        SUM(hotr_value) AS hotr_value,
                        MAX(hotr_date) AS max_date
                    FROM public.hours_of_task_responsible
                    GROUP BY task_responsible_id
                ) AS t6 ON t1.task_responsible_id = t6.task_responsible_id
                WHERE parent_id IS NULL
                ORDER BY t6.max_date DESC NULLS LAST, t4.project_id, t1.child_path[1], t1.task_responsible_id;"""

# Список дней по которым нужно отправить часы и статусы почасовой оплаты
USER_LABOR_DATE_LIST = """
--СПИСОК ДАТ ПОДАЧИ ЧАСОВ И СТАТУС ПОЧАСОВОЙ ОПЛАТЫ ДЛЯ ЛЮБОГО КОЛИЧЕСТВА СОТРУДНИКОВ
--EXPLAIN ANALYZE
--Статус отправки часов
WITH labor_changes AS (
    SELECT 
        user_id,
        empl_labor_date,
        empl_labor_status,
        LEAD(empl_labor_date) OVER (PARTITION BY user_id ORDER BY empl_labor_date) AS next_date
    FROM public.labor_status
),
labor_dates AS (
    SELECT 
        user_id,
        generate_series(empl_labor_date, COALESCE(next_date - INTERVAL '1 day', CURRENT_DATE), '1 day'::interval)::date AS labor_date
    FROM labor_changes
    WHERE empl_labor_status = true
),
--Статус почасовой оплаты
hours_changes AS (
    SELECT 
        user_id,
        empl_hours_date,
        full_day_status,
        LEAD(empl_hours_date) OVER (PARTITION BY user_id ORDER BY empl_hours_date) AS next_date
    FROM public.hour_per_day_norm
),
hours_dates AS (
    SELECT 
        user_id,
        generate_series(empl_hours_date, COALESCE(next_date - INTERVAL '1 day', CURRENT_DATE), '1 day'::interval)::date AS labor_date
    FROM hours_changes
    WHERE full_day_status = true
),

--Статус увольнения
hire_and_fire_changes AS (
    SELECT 
        user_id,
        haf_date,
        haf_type,
        LEAD(haf_date) OVER (PARTITION BY user_id ORDER BY haf_date) AS next_date
    FROM public.hire_and_fire
),
hire_and_fire_dates AS (
    SELECT 
        user_id,
        generate_series(haf_date, COALESCE(next_date - INTERVAL '1 day', CURRENT_DATE), '1 day'::interval)::date AS haf_date
    FROM hire_and_fire_changes
    WHERE haf_type = 'hire'
),

--Список сотрудников выбранных отделов
user_list AS (
	SELECT
		t1.user_id
	FROM public.empl_dept AS t1
	JOIN (
		SELECT
			user_id,
			MAX(date_promotion) AS date_promotion
		FROM public.empl_dept
		WHERE date_promotion <= now()::date
		GROUP BY user_id
	) AS t2 ON t1.user_id=t2.user_id AND t1.date_promotion=t2.date_promotion
	WHERE t1.dept_id IN %s
),
user_dept_list AS (
	SELECT
		t1.user_id,
		t1.dept_id
	FROM public.empl_dept AS t1
	JOIN (
		SELECT
			user_id,
			MAX(date_promotion) AS date_promotion
		FROM public.empl_dept
		WHERE date_promotion <= now()::date
		GROUP BY user_id
	) AS t2 ON t1.user_id=t2.user_id AND t1.date_promotion=t2.date_promotion
	--WHERE t1.dept_id = 27
),
labor_date_list AS (
	SELECT 
	    t1.user_id, 
	    t1.labor_date,
		CASE 
			WHEN t2.labor_date IS NOT NULL THEN FALSE ELSE TRUE 
		END AS full_day_status
	FROM labor_dates AS t1
	LEFT JOIN hours_dates AS t2 ON t1.user_id=t2.user_id AND t1.labor_date=t2.labor_date
	LEFT JOIN hire_and_fire_dates AS t3 ON t1.user_id=t3.user_id AND t1.labor_date=t3.haf_date
	WHERE t1.user_id IN (SELECT * FROM user_list)
		AND (
				(
				EXTRACT(dow FROM t1.labor_date) NOT IN (0,6) AND 
				t1.labor_date NOT IN (SELECT holiday_date FROM public.list_holidays WHERE holiday_status = TRUE)
				)
				OR
				(
				EXTRACT(dow FROM t1.labor_date) IN (0,6) AND 
				t1.labor_date IN (SELECT holiday_date FROM public.list_holidays WHERE holiday_status = FALSE)
				)
			)
		AND t1.labor_date >= '2024-09-09'
		AND t3.haf_date IS NOT NULL
),
hotr_group_by_day AS (
	SELECT 
	    t1.user_id, 
		t1.labor_date,
		t1.full_day_status,
	    SUM(t2.hotr_value) AS total_hotr,
		SUM(CASE WHEN t2.approved_status = FALSE AND t2.sent_status = FALSE THEN t2.hotr_value ELSE 0 END) AS unapproved_hotr,
		SUM(CASE WHEN t2.approved_status = TRUE AND t2.sent_status = FALSE THEN t2.hotr_value ELSE 0 END) AS unsent_hotr
	FROM labor_date_list AS t1
	LEFT JOIN (
		SELECT
			t22.user_id,
			t21.hotr_date,
			t21.hotr_value,
			t21.sent_status,
			t21.approved_status
		FROM public.hours_of_task_responsible AS t21
		LEFT JOIN (
			SELECT 
				user_id,
				task_responsible_id
			FROM public.task_responsible
		) AS t22 ON t21.task_responsible_id=t22.task_responsible_id

		UNION ALL

		SELECT
			t24.user_id,
			t23.hotr_date,
			t23.hotr_value,
			t23.sent_status,
			t23.approved_status
		FROM public.org_work_hours_of_task_responsible AS t23
		LEFT JOIN (
			SELECT 
				user_id,
				task_responsible_id
			FROM public.org_work_responsible
		) AS t24 ON t23.task_responsible_id=t24.task_responsible_id
	) AS t2 ON t1.user_id=t2.user_id AND t1.labor_date=t2.hotr_date
	GROUP BY t1.user_id, t1.labor_date, t1.full_day_status	
)
SELECT
	t5.short_full_name,
	t2.dept_id,
	t1.*
FROM hotr_group_by_day AS t1
LEFT JOIN user_dept_list AS t2 ON t1.user_id = t2.user_id
LEFT JOIN (
	SELECT
		user_id,
		concat_ws(' ', 
			last_name, 
			LEFT(first_name, 1) || '.', 
			CASE
				WHEN surname<>'' THEN LEFT(surname, 1) || '.' ELSE ''
			END) AS short_full_name
	FROM public.users
) AS t5 ON t1.user_id = t5.user_id
ORDER BY t1.labor_date, t1.user_id
;

"""

# Список задач сотрудников, которые не отправил ГАП
UNAPPROVED_HOTR_LIST = """
--EXPLAIN ANALYZE
WITH RECURSIVE rel_task_resp AS (
    SELECT
        user_id,
        10000 AS depth,
        task_responsible_id,
        task_id,
        task_id AS parent_id,
        0 AS tow_id,
        task_status_id,
        ARRAY[''] AS name_path,
        ARRAY[''] AS short_name_path,
        ARRAY[task_id] AS child_path,
        '' AS task_name,
        ARRAY['tr'] AS tow_task,
        ARRAY['Текущая задача: '] AS tow_task_title
    FROM public.task_responsible
    WHERE user_id IN %s 
        AND task_responsible_id IN (SELECT task_responsible_id FROM public.hours_of_task_responsible WHERE approved_status = FALSE)
    
    UNION ALL

    SELECT
        r.user_id,
        r.depth - 1,
        r.task_responsible_id,
        n.task_id,
        n.parent_id,
        n.tow_id,
        r.task_status_id,
        n.task_name || r.name_path,

        CASE
            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
            ELSE n.task_name
        END || r.short_name_path,

        r.child_path || n.task_id || n.lvl::int,
        n.task_name,
        ARRAY['task'] || r.tow_task,
        ARRAY['Задача: '] || r.tow_task_title
    FROM rel_task_resp AS r
    JOIN tasks AS n ON n.task_id = r.parent_id
),
rel_rec AS (
    SELECT
        user_id,
        depth,
        task_responsible_id,
        task_id,
        tow_id AS parent_id,
        tow_id,
        task_status_id,
        name_path,
        short_name_path,
        child_path,
        task_name,
        tow_task,
        tow_task_title
    FROM rel_task_resp
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        r.user_id,
        r.depth - 1,
        r.task_responsible_id,
        r.task_id,
        n.parent_id,
        n.tow_id,
        r.task_status_id,
        n.tow_name || r.name_path,

        CASE
            WHEN length(n.tow_name) > 20 THEN SUBSTRING(n.tow_name, 1, 17) || '...'
            ELSE n.tow_name
        END || r.short_name_path,

        r.child_path || n.tow_id || n.lvl::int,
        n.tow_name,
        ARRAY['tow'] || r.tow_task,
        ARRAY['Вид работ: '] || r.tow_task_title
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.tow_id = r.parent_id
),
rel_rec_org_works AS (
    SELECT
        0 AS depth,
        o.*,
        ARRAY[o.lvl, o.task_id] AS child_path,
        ARRAY[task_name] AS name_path,
        ARRAY[CASE
            WHEN length(task_name) > 20 THEN SUBSTRING(task_name, 1, 17) || '...'
            ELSE task_name
        END] AS short_name_path,
        ARRAY[CASE
                WHEN main_task THEN 'tr'
                ELSE 'task'
        END] AS tow_task,
        ARRAY[CASE
                WHEN main_task THEN 'Базовая задача:'
                ELSE 'Задача:'
        END] AS tow_task_title
    FROM public.org_works AS o
    WHERE parent_id IS NULL

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.*,
        r.child_path || n.lvl || n.task_id,
        r.name_path || n.task_name,
        r.short_name_path || CASE
            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
            ELSE n.task_name
        END,
        ARRAY[CASE
                WHEN n.main_task THEN 'tr'
                ELSE 'task'
        END] || r.tow_task AS tow_task,
        ARRAY[CASE
                WHEN n.main_task THEN 'Базовая задача:'
                ELSE 'Задача:'
        END] || r.tow_task_title AS tow_task_title
    FROM rel_rec_org_works AS r
    JOIN public.org_works AS n ON n.parent_id = r.task_id
)
(
    SELECT
        t1.user_id,
        'task' AS row_type,
        CASE
            WHEN t1.task_status_id = 4 THEN 'tr_task_status_closed'
            ELSE 'tr_task_status_not_closed'
        END AS task_class,
        t1.child_path[1] AS task_id,
        t1.task_responsible_id::text,
        '' as task_number,
        t1.task_status_id,
        t1.tow_task,
        t1.tow_task_title,
        t4.project_id,
        t5.task_status_name,
        t2.task_plan_labor_cost,
        COALESCE(t2.task_plan_labor_cost::text, '-') AS task_plan_labor_cost_txt,
        CASE
            WHEN t1.task_status_id = 4 THEN TRUE
            ELSE FALSE
        END AS editing_is_prohibited,
        t3.tow_id,
        COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,
        t6.input_task_week_1_day_1,
    
        COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
        t6.max_date,
    
        t1.name_path[array_length(t1.name_path, 1) - 1] AS task_name,
        t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,
    
        t1.short_name_path[array_length(t1.short_name_path, 1) - 1] AS short_task_name,
        t1.short_name_path[1:array_length(t1.short_name_path, 1) - 2] AS short_name_path
    FROM rel_rec AS t1
    LEFT JOIN (
        SELECT 
            task_id,
            task_responsible_id,
            task_status_id,
            task_responsible_comment,
            task_plan_labor_cost
        FROM public.task_responsible
    ) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
    LEFT JOIN (
        SELECT 
            task_id,
            tow_id
        FROM public.tasks
    ) AS t3 ON t1.child_path[1] = t3.task_id
    LEFT JOIN (
        SELECT 
            tow_id,
            project_id
        FROM public.types_of_work
    ) AS t4 ON t1.tow_id = t4.tow_id
    LEFT JOIN (
        SELECT 
            task_status_id,
            task_status_name
        FROM public.task_statuses
    ) AS t5 ON t1.task_status_id = t5.task_status_id
    LEFT JOIN (
        SELECT
            task_responsible_id,
            SUM(CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            MAX(hotr_date) AS max_date
        FROM public.hours_of_task_responsible
        WHERE approved_status = FALSE
        GROUP BY task_responsible_id
    ) AS t6 ON t1.task_responsible_id = t6.task_responsible_id
    WHERE parent_id IS NULL AND t6.input_task_week_1_day_1 IS NOT NULL
)

UNION ALL
(
    SELECT
        t2.user_id,
        'org_work' AS row_type,
        'tr_task_status_not_closed' AS task_class,
        t1.task_id,
        COALESCE(t2.task_responsible_id::text, MD5(t1.task_id::text)) AS task_responsible_id,
        '' as task_number,
        NULL AS task_status_id,
        t1.tow_task,
        t1.tow_task_title,
        NULL AS project_id,
        '' AS task_status_name,
        0 AS task_plan_labor_cost,
        '-' AS task_plan_labor_cost_txt,
        TRUE AS editing_is_prohibited,
        NULL AS tow_id,
        COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,
    
        t6.input_task_week_1_day_1,
    
        COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
        t6.max_date,
    
        t1.name_path[array_length(t1.name_path, 1)] AS task_name,
        t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,
    
        t1.short_name_path[array_length(t1.short_name_path, 1)] AS short_task_name,
        t1.short_name_path[1:array_length(t1.short_name_path, 1) - 1] AS short_name_path
    FROM rel_rec_org_works AS t1
    LEFT JOIN (
        SELECT
            user_id,
            task_id,
            task_responsible_id,
            task_responsible_comment
        FROM public.org_work_responsible
        WHERE user_id IN %s
    ) AS t2 ON t1.task_id = t2.task_id
    LEFT JOIN (
        SELECT
            task_responsible_id,
            SUM(CASE WHEN hotr_date = %s::DATE  THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            MAX(hotr_date) AS max_date
        FROM public.org_work_hours_of_task_responsible
        WHERE approved_status = FALSE
        GROUP BY task_responsible_id
    ) AS t6 ON t2.task_responsible_id = t6.task_responsible_id
    WHERE NOT t1.main_task 
    AND t2.task_responsible_id IN (SELECT task_responsible_id  FROM public.org_work_hours_of_task_responsible WHERE approved_status = FALSE)
    AND t6.input_task_week_1_day_1 IS NOT NULL
)

ORDER BY max_date DESC NULLS LAST, project_id, task_id, task_responsible_id;
"""

# Список задач сотрудников, которые не согласованы Рукотделом
UNSENT_HOTR_LIST = """
--EXPLAIN ANALYZE
WITH RECURSIVE rel_task_resp AS (
    SELECT
        user_id,
        10000 AS depth,
        task_responsible_id,
        task_id,
        task_id AS parent_id,
        0 AS tow_id,
        task_status_id,
        ARRAY[''] AS name_path,
        ARRAY[''] AS short_name_path,
        ARRAY[task_id] AS child_path,
        '' AS task_name,
        ARRAY['tr'] AS tow_task,
        ARRAY['Текущая задача: '] AS tow_task_title
    FROM task_responsible
    WHERE user_id IN %s AND 
                task_responsible_id IN (SELECT task_responsible_id FROM public.hours_of_task_responsible WHERE approved_status = TRUE AND sent_status = FALSE)
    
    UNION ALL

    SELECT
        r.user_id,
        r.depth - 1,
        r.task_responsible_id,
        n.task_id,
        n.parent_id,
        n.tow_id,
        r.task_status_id,
        n.task_name || r.name_path,

        CASE
            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
            ELSE n.task_name
        END || r.short_name_path,

        r.child_path || n.task_id || n.lvl::int,
        n.task_name,
        ARRAY['task'] || r.tow_task,
        ARRAY['Задача: '] || r.tow_task_title
    FROM rel_task_resp AS r
    JOIN tasks AS n ON n.task_id = r.parent_id
),
rel_rec AS (
    SELECT
        user_id,
        depth,
        task_responsible_id,
        task_id,
        tow_id AS parent_id,
        tow_id,
        task_status_id,
        name_path,
        short_name_path,
        child_path,
        task_name,
        tow_task,
        tow_task_title
    FROM rel_task_resp
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        r.user_id,
        r.depth - 1,
        r.task_responsible_id,
        r.task_id,
        n.parent_id,
        n.tow_id,
        r.task_status_id,
        n.tow_name || r.name_path,

        CASE
            WHEN length(n.tow_name) > 20 THEN SUBSTRING(n.tow_name, 1, 17) || '...'
            ELSE n.tow_name
        END || r.short_name_path,

        r.child_path || n.tow_id || n.lvl::int,
        n.tow_name,
        ARRAY['tow'] || r.tow_task,
        ARRAY['Вид работ: '] || r.tow_task_title
    FROM rel_rec AS r
    JOIN types_of_work AS n ON n.tow_id = r.parent_id
),
rel_rec_org_works AS (
    SELECT
        0 AS depth,
        o.*,
        ARRAY[o.lvl, o.task_id] AS child_path,
        ARRAY[task_name] AS name_path,
        ARRAY[CASE
            WHEN length(task_name) > 20 THEN SUBSTRING(task_name, 1, 17) || '...'
            ELSE task_name
        END] AS short_name_path,
        ARRAY[CASE
                WHEN main_task THEN 'tr'
                ELSE 'task'
        END] AS tow_task,
        ARRAY[CASE
                WHEN main_task THEN 'Базовая задача:'
                ELSE 'Задача:'
        END] AS tow_task_title
    FROM public.org_works AS o
    WHERE parent_id IS NULL

    UNION ALL
    SELECT
        nlevel(r.path) - 1,
        n.*,
        r.child_path || n.lvl || n.task_id,
        r.name_path || n.task_name,
        r.short_name_path || CASE
            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
            ELSE n.task_name
        END,
        ARRAY[CASE
                WHEN n.main_task THEN 'tr'
                ELSE 'task'
        END] || r.tow_task AS tow_task,
        ARRAY[CASE
                WHEN n.main_task THEN 'Базовая задача:'
                ELSE 'Задача:'
        END] || r.tow_task_title AS tow_task_title
    FROM rel_rec_org_works AS r
    JOIN public.org_works AS n ON n.parent_id = r.task_id
)
(SELECT
    t1.user_id,
    'task' AS row_type,
    CASE
        WHEN t1.task_status_id = 4 THEN 'tr_task_status_closed'
        ELSE 'tr_task_status_not_closed'
    END AS task_class,
    t1.child_path[1] AS task_id,
    t1.task_responsible_id::text,
    '' as task_number,
    t1.task_status_id,
    t1.tow_task,
    t1.tow_task_title,
    t4.project_id,
    t5.task_status_name,
    t6.hotr_value,
    t2.task_plan_labor_cost,
    COALESCE(t6.hotr_value::text, '-') AS hotr_value_txt,
    COALESCE(t2.task_plan_labor_cost::text, '-') AS task_plan_labor_cost_txt,
    CASE
        WHEN t1.task_status_id = 4 THEN TRUE
        ELSE FALSE
    END AS editing_is_prohibited,
    t3.tow_id,
    COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,
    t6.input_task_week_1_day_1,

    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
    t6.max_date,

    t1.name_path[array_length(t1.name_path, 1) - 1] AS task_name,
    t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,

    t1.short_name_path[array_length(t1.short_name_path, 1) - 1] AS short_task_name,
    t1.short_name_path[1:array_length(t1.short_name_path, 1) - 2] AS short_name_path
FROM rel_rec AS t1
LEFT JOIN (
    SELECT 
        task_id,
        task_responsible_id,
        task_status_id,
        task_responsible_comment,
        task_plan_labor_cost
    FROM public.task_responsible
) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
LEFT JOIN (
    SELECT 
        task_id,
        tow_id
    FROM public.tasks
) AS t3 ON t1.child_path[1] = t3.task_id
LEFT JOIN (
    SELECT 
        tow_id,
        project_id
    FROM public.types_of_work
) AS t4 ON t1.tow_id = t4.tow_id
LEFT JOIN (
    SELECT 
        task_status_id,
        task_status_name
    FROM public.task_statuses
) AS t5 ON t1.task_status_id = t5.task_status_id
LEFT JOIN (
    SELECT
        task_responsible_id,
        SUM(CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
        SUM(hotr_value) AS hotr_value,
        MAX(hotr_date) AS max_date
    FROM public.hours_of_task_responsible
    WHERE approved_status = TRUE AND sent_status = FALSE
    GROUP BY task_responsible_id
) AS t6 ON t1.task_responsible_id = t6.task_responsible_id
WHERE parent_id IS NULL
AND t2.task_responsible_id IN (SELECT task_responsible_id  FROM public.hours_of_task_responsible WHERE  approved_status = TRUE AND sent_status = FALSE)
AND t6.input_task_week_1_day_1 IS NOT NULL
)

UNION ALL
(SELECT
    t2.user_id,
    'org_work' AS row_type,
    'tr_task_status_not_closed' AS task_class,
    t1.task_id,
    COALESCE(t2.task_responsible_id::text, MD5(t1.task_id::text)) AS task_responsible_id,
    '' as task_number,
    NULL AS task_status_id,
    t1.tow_task,
    t1.tow_task_title,
    NULL AS project_id,
    '' AS task_status_name,
    t6.hotr_value,
    0 AS task_plan_labor_cost,
    COALESCE(t6.hotr_value::text, '-') AS hotr_value_txt,
    '-' AS task_plan_labor_cost_txt,
    TRUE AS editing_is_prohibited,
    NULL AS tow_id,
    COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,

    t6.input_task_week_1_day_1,

    COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
    t6.max_date,

    t1.name_path[array_length(t1.name_path, 1)] AS task_name,
    t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,

    t1.short_name_path[array_length(t1.short_name_path, 1)] AS short_task_name,
    t1.short_name_path[1:array_length(t1.short_name_path, 1) - 1] AS short_name_path
FROM rel_rec_org_works AS t1
LEFT JOIN (
    SELECT
        user_id,
        task_id,
        task_responsible_id,
        task_responsible_comment
    FROM public.org_work_responsible
    WHERE user_id IN %s
) AS t2 ON t1.task_id = t2.task_id
LEFT JOIN (
    SELECT
        task_responsible_id,
        SUM(CASE WHEN hotr_date = %s::DATE  THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
        SUM(hotr_value) AS hotr_value,
        MAX(hotr_date) AS max_date
    FROM public.org_work_hours_of_task_responsible
    WHERE approved_status = TRUE AND sent_status = FALSE
    GROUP BY task_responsible_id
) AS t6 ON t2.task_responsible_id = t6.task_responsible_id
WHERE NOT t1.main_task 
AND t2.task_responsible_id IN (SELECT task_responsible_id  FROM public.org_work_hours_of_task_responsible WHERE  approved_status = TRUE AND sent_status = FALSE)
AND input_task_week_1_day_1 IS NOT NULL
)
ORDER BY max_date DESC NULLS LAST, project_id, task_id, task_responsible_id;
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


# Проверка, что ip адрес не забанен
@task_app_bp.before_request
def is_ip_banned():
    app_login.is_ip_banned()


# Страница раздела 'Задачи' проекта
@task_app_bp.route('/objects/<link_name>/tasks', methods=['GET'])
@login_required
def get_all_tasks(link_name):
    """Страница раздела 'Задачи' проекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())

        project = app_project.get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        project = project[1]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')
        # текущий id отдела сотрудника
        user_dept_id = FDataBase(conn).user_dept_id(user_id)

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = app_login.current_user.is_head_of_dept()

        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        role = app_login.current_user.get_role()

        # Список tow
        cursor.execute(
            TOW_LIST,
            [project['project_id'], project['project_id']]
        )
        tow = cursor.fetchall()

        if tow:
            for i in range(len(tow)):
                tow[i] = dict(tow[i])
                # Ссылка для перехода в раздел задачи tow
                if tow[i]['dept_id'] is not None and tow[i]['time_tracking']:
                    if project['gip_id'] == user_id or role in (1, 4) or is_head_of_dept:
                        tow[i]['link'] = f"/objects/{link_name}/tasks/{tow[i]['tow_id']}"
                    elif tow[i]['dept_id'] == user_dept_id:
                        tow[i]['link'] = f"/objects/{link_name}/tasks/{tow[i]['tow_id']}"

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=1, is_head_of_dept=is_head_of_dept)

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        if role in (1, 4):
            pass
        elif role in (5, 6):
            pass
        else:
            if is_head_of_dept:
                pass
            pass

        tep_info = True
        project = app_project.get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('.objects_main'))
        proj = project[1]

        return render_template('task-main.html', menu=hlink_menu, menu_profile=hlink_profile, tow=tow,
                               header_menu=header_menu,  nonce=get_nonce(), tep_info=tep_info,
                               proj=proj, title='Задачи, главная страница')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Страница раздела 'Задачи с подзадачами' проекта
@task_app_bp.route('/tasks/<int:tow_id>', methods=['GET'])
@task_app_bp.route('/objects/<link_name>/tasks/<int:tow_id>', methods=['GET'])
@login_required
def get_tasks_on_tow_id(tow_id, link_name=False):
    """Страница раздела 'Задачи с подзадачами' проекта"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id, ip_address=app_login.get_client_ip())

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('objects')

        # Информация для tow cart
        cursor.execute("""
                SELECT
                    t0.tow_id,
                    t0.tow_name,
                    CASE
                        WHEN length(t0.tow_name) > 30 THEN SUBSTRING(t0.tow_name, 1, 27) || '...'
                        ELSE t0.tow_name
                    END AS tow_short_name,
                    t1.project_img_middle,
                    t1.link_name,
                    t2.object_name,
                    CASE
                        WHEN length(t2.object_name) > 30 THEN SUBSTRING(t2.object_name, 1, 27) || '...'
                        ELSE t2.object_name
                    END AS object_short_name,
                    t3.dept_short_name,
                    t0.time_tracking
                FROM types_of_work AS t0
                LEFT JOIN (
                    SELECT
                        project_id,
                        object_id,
                        project_img_middle,
                        link_name
                    FROM projects
                ) AS t1 ON t0.project_id=t1.project_id
                LEFT JOIN objects AS t2 ON t1.object_id=t2.object_id
                LEFT JOIN (
                    SELECT
                        dept_id,
                        dept_short_name
                    FROM list_dept
                ) AS t3 ON t0.dept_id=t3.dept_id
                WHERE t0.tow_id = %s ;
                """,
                       [tow_id])
        tow_cart = cursor.fetchone()
        if not tow_cart:
            flash(message=['Ошибка', 'Информация о виде работ не найдена'], category='error')
            return redirect(url_for('app_project.objects_main'))
        tow_cart = dict(tow_cart)

        # Если tow имеет статус False для параметра отправка часов (time_tracking) значит нельзя создать структуру
        if not tow_cart['time_tracking']:
            full_link = request.url.split('/')
            full_link = f"{full_link[0]}//{full_link[2]}/objects/{tow_cart['link_name']}/tasks"
            flash(message=[
                'Ошибка',
                'Отключён учёт рабочего времени для данного вида работ',
                'Перейдите на страницу "Задачи.Главная" и включите статус "Учёт часов"',
                full_link], category='error')
            return redirect(url_for('app_project.objects_main'))

        tow_cart = {
            'link_name': tow_cart['link_name'],
            'project_img_middle': tow_cart['project_img_middle'],
            'tow_info': {
                'Объект': ['Наименование объект', tow_cart['object_name'], tow_cart['object_short_name']],
                'Вид работ': ['Название вида работ', tow_cart['tow_name'], tow_cart['tow_short_name']],
                'id': ['id вида работ', '', tow_cart['tow_id']],
                'Отдел': ['Отдел, к которому привязан вид работ', '', tow_cart['dept_short_name']],
            }
        }

        # Информация о tow
        cursor.execute("""
                        SELECT
                            *,
                            CASE
                                WHEN length(tow_name) > 200 THEN SUBSTRING(tow_name, 1, 197) || '...'
                                ELSE tow_name
                            END AS short_tow_name
                        FROM types_of_work 
                        WHERE tow_id = %s ;
                        """,
                       [tow_id])
        tow_info = cursor.fetchone()

        # tow_id не найден - ошибка + переход на главную страницу
        if not tow_info:
            flash(message=['Ошибка', 'Вид работ не найден'], category='error')
            return redirect(url_for('app_project.objects_main'))
        tow_info = dict(tow_info)

        dept_id = tow_info['dept_id']
        # tow без отдела - нельзя создавать задачи - ошибка + переход на главную страницу
        if not dept_id:
            flash(message=['Ошибка', 'К виду работ не привязан отдел', 'Работа с задачами ограничена'],
                  category='error')
            return redirect(url_for('app_project.objects_main'))

        project_id = tow_info['project_id']

        link_info = dict(app_contract.get_proj_id(project_id=project_id))

        project = app_project.get_proj_info(link_info['link_name'])
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('app_project.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('app_project.objects_main'))
        proj = project[1]

        # Проверяем, что link_name и tow_id принадлежат к общему project_id
        if link_name:
            if link_name != tow_cart['link_name']:
                return redirect(f"/tasks/{tow_id}", code=302)

        link_name = link_info['link_name']

        tep_info = False

        role = app_login.current_user.get_role()

        # Если объект закрыт и юзер не админ - ошибка. В закрытый проект пройти нельзя
        if proj['project_close_status'] and role not in (11, 4):
            flash(message=['Ошибка', proj['project_full_name'],'Проект закрыт', 'Ошибка доступа'], category='error')
            return redirect(url_for('app_project.objects_main'))

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = app_login.current_user.is_head_of_dept()

        # Список основного меню
        header_menu = get_header_menu(role, link=link_name, cur_name=None, is_head_of_dept=is_head_of_dept)

        # Список дат 4-х недель
        th_week_list = False

        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # Список статусов задач
        cursor.execute("""
                        SELECT 
                            * 
                        FROM public.task_statuses
                        ORDER BY task_status_name ASC;
                        """)
        task_statuses = cursor.fetchall()

        if task_statuses:
            for i in range(len(task_statuses)):
                task_statuses[i] = dict(task_statuses[i])
        else:
            flash(message=['Ошибка', 'Не найдены статусы задач', 'Создание задач невозможна'], category='error')
            return redirect(url_for('app_project.objects_main'))

        # Список задач вида работ
        cursor.execute(
            TASK_LIST,
            [tow_id, tow_id, tow_id, tow_id, tow_id])
        tasks = cursor.fetchall()

        if len(tasks):
            for i in range(len(tasks)):
                tasks[i] = dict(tasks[i])
        else:
            tasks = False

        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        # Родительский отдел текущей tow
        cursor.execute(
            f'{DEPT_LIST_WITH_PARENT_part_1} AND lg.group_id = {dept_id}'
            f'{DEPT_LIST_WITH_PARENT_part_2} AND dr2.child_id = {dept_id}')
        parent_dept_id = cursor.fetchone()
        if not parent_dept_id:
            flash(message=['Не найден родительский отдел выбранного вида работ', 'Создание задач невозможна'],
                  category='error')
            return redirect(url_for('app_project.objects_main'))
        parent_dept_id = parent_dept_id[0]

        # Список ФИО сотрудников отделов
        cursor.execute(
            f'''
            {EMPLOYEES_LIST} 
            WHERE t3.dept_id = {parent_dept_id} AND t1.is_fired = FALSE 
            ORDER BY t1.last_name, t1.first_name, t1.surname
            ''')
        responsible = cursor.fetchall()

        app_login.conn_cursor_close(cursor, conn)

        user_from_parent_dept = False  # Статус, что пользователь привязан к тому же отделу, что и tow
        user_from_parent_dept = True if role == 1 else user_from_parent_dept
        if responsible:
            for i in range(len(responsible)):
                responsible[i] = dict(responsible[i])
                if responsible[i]['user_id'] == user_id:
                    user_from_parent_dept = True
        tow_info['user_from_parent_dept'] = user_from_parent_dept
        # tow_info['user_from_parent_dept'] = False

        # Список дней 4-х недель
        today = date.today()
        current_week_monday = today - timedelta(days=today.weekday())  # Дата текущего дня

        th_week_list = []  # Список дат 4-х недель
        for i in range(0, 4):
            week_start = current_week_monday + timedelta(weeks=i - 1)
            week_dates = [
                {
                    'name': (week_start + timedelta(days=j)).strftime('%d.%m.%y'),
                    'class': "th_task_labor_1_day th_week_day" if j==0 else "th_task_labor th_week_day",
                    'day_week': DAYS_OF_THE_WEEK[j]
                }
                for j in range(7)]
            th_week_list.append({'name': "№ " + str(i + 1), 'class': "th_task_labor th_sum_week"})
            th_week_list.extend(week_dates)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        if role in (1, 4):
            tep_info = True
        elif role in (5, 6):
            tep_info = True
        else:
            if is_head_of_dept:
                tep_info = True
        tow_cart['tep_info'] = tep_info
        title = f"Задачи раздела (id:{tow_id}) - {tow_info['tow_name']}"
        return render_template('task-tasks.html', menu=hlink_menu, menu_profile=hlink_profile,
                               header_menu=header_menu, nonce=get_nonce(), tep_info=tep_info, tow_info=tow_info,
                               th_week_list=th_week_list, tasks=tasks, responsible=responsible, proj=proj,
                               tow_cart=tow_cart, task_statuses=task_statuses, title=title)

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Сохранение измененных данных на листе 'Задачи с подзадачами' проекта
@task_app_bp.route('/save_tasks_changes/<int:tow_id>', methods=['POST'])
@login_required
def save_tasks_changes(tow_id:int):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name,
                               log_description=f"tow_id: {tow_id}", user_id=user_id, ip_address=app_login.get_client_ip())

        user_changes = request.get_json()['userChanges']
        new_tow = request.get_json()['list_newRowList']
        deleted_tow = request.get_json()['list_deletedRowList']
        reserves_changes = request.get_json()['reservesChanges']

        description = 'Изменения не найдены. Ничего не произошло'

        # Меняем типы данных, isdigit()->int, isnumeric() -> float, 'None'->None
        for task_id in list(user_changes.keys())[:]:
            v = user_changes[task_id]

            for tr_id in list(v.keys())[:]:
                vv = v[tr_id]

                for kkk, vvv in vv.items():
                    if vvv == 'None':
                        user_changes[task_id][tr_id][kkk] = None

                    elif kkk in ('parent_id', 'lvl', 'td_task_responsible_user', 'td_tow_task_statuses'):
                        if str_to_int(vvv):
                        # if isinstance(vvv, str) and vvv.isdigit():
                            user_changes[task_id][tr_id][kkk] = int(vvv)
                        if kkk == 'td_task_responsible_user' and user_changes[task_id][tr_id][kkk] in (' ', ''):
                            user_changes[task_id][tr_id][kkk] = None
                        elif kkk == 'td_tow_task_statuses' and user_changes[task_id][tr_id][kkk] == 0:
                            user_changes[task_id][tr_id][kkk] = 1  # по умолчанию id-1 не в работе

                    elif kkk == 'input_task_plan_labor_cost':
                        if str_to_float(vvv):
                            user_changes[task_id][tr_id][kkk] = float(vvv)
                        else:
                            user_changes[task_id][tr_id][kkk] = None

                if isinstance(tr_id, str):
                    if str_to_int(tr_id):
                        user_changes[task_id][int(tr_id)] = user_changes[task_id].pop(tr_id)
                    elif tr_id == 'None':
                        user_changes[task_id][None] = user_changes[task_id].pop(tr_id)

            if str_to_int(task_id):
                user_changes[int(task_id)] = user_changes.pop(task_id)

        for task_id in list(new_tow.keys())[:]:
            v = new_tow[task_id]

            for tr_id in list(v.keys())[:]:
                if isinstance(tr_id, str):
                    if str_to_int(tr_id):
                        new_tow[task_id][int(tr_id)] = new_tow[task_id].pop(tr_id)
                    elif tr_id == 'None':
                        new_tow[task_id][None] = new_tow[task_id].pop(tr_id)

            if str_to_int(task_id):
                new_tow[int(task_id)] = new_tow.pop(task_id)

        # 1 преобразование полученных данных
        # 2 получение данных с сервера для проверки валидности новых изменений
        # 3 Запись изменений в базу данных

        #############################################################################################
        # преобразование полученных данных
        #############################################################################################
        if True:
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('objects')

            # Информация о tow
            cursor.execute("""
                            SELECT
                                *,
                                SUBSTRING(tow_name, 1,200) AS short_tow_name
                            FROM types_of_work 
                            WHERE tow_id = %s ;
                            """,
                           [tow_id])
            tow_info = cursor.fetchone()

            # tow_id не найден - ошибка + переход на главную страницу
            if not tow_info:
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name, log_description=f'tow_id:{tow_id}. Вид работ не найден',
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=['Ошибка', 'Вид работ не найден'], category='error')
                return jsonify({
                    'status': 'error',
                    'description': [['Вид работ не найден']],
                })
            tow_info = dict(tow_info)

            dept_id = tow_info['dept_id']
            # tow без отдела - нельзя создавать задачи - ошибка + переход на главную страницу
            if not dept_id:
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'tow_id:{tow_id}. К виду работ не привязан отдел. Работа с задачами ограничена',
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=['Ошибка', 'К виду работ не привязан отдел', 'Работа с задачами ограничена'],
                      category='error')
                return jsonify({
                    'status': 'error',
                    'description': [['К виду работ не привязан отдел', 'Работа с задачами ограничена']],
                })

            project_id = tow_info['project_id']

            link_name = app_contract.get_proj_id(project_id=project_id)
            link_name = dict(link_name)['link_name']

            project = app_project.get_proj_info(link_name)
            if project[0] == 'error':
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'tow_id:{tow_id}. {project[1]}',
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=project[1], category='error')
                return jsonify({
                    'status': 'error',
                    'description': [[project[1]]],
                })
            elif not project[1]:
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'tow_id:{tow_id}. Проект не найден',
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=['ОШИБКА. Проект не найден'], category='error')
                return jsonify({
                    'status': 'error',
                    'description': [['Проект не найден']],
                })
            proj = project[1]
            tep_info = False

            role = app_login.current_user.get_role()

            # Если объект закрыт и юзер не админ - ошибка. В закрытый проект пройти нельзя
            if proj['project_close_status'] and role not in (11, 4):
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'tow_id:{tow_id}. Проект закрыт. Ошибка доступа',
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=['Ошибка', proj['project_full_name'], 'Проект закрыт', 'Ошибка доступа'], category='error')
                return jsonify({
                    'status': 'error',
                    'description': [[proj['project_full_name'], 'Проект закрыт', 'Ошибка доступа']],
                })

            # Статус, является ли пользователь руководителем отдела
            is_head_of_dept = app_login.current_user.is_head_of_dept()

            app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # # Список задач, у которых плановые трудозатраты обнулены. Этим списком проверяем, что все
        # # удалячемые задачи не имеют плановых трудозатрат, т.к. плановые трудозатраты удалили в этом же сохранении
        # recheck_list_plan_labor_cost = set()

        # Список для удаления
        if len(deleted_tow):
            valued_del_task = []
            valued_del_tr = []
            valued_del = []
            # for task_id,v in deleted_tow.items():
            for task_id in list(deleted_tow.keys())[:]:
                v = deleted_tow[task_id]
                # Если tr_id = 'None', то заменяем на NoneType
                if 'None' in v.keys():
                    deleted_tow[task_id][None] = deleted_tow[task_id].pop('None')

                for tr_id in v.keys():
                    valued_del.append((task_id, tr_id))
                    if tr_id is None:
                        valued_del_task.append((int(task_id),))
                    else:
                        valued_del_tr.append((int(tr_id),))
            # Проверяем список удаляемых данных на валидность
            task_is_actual = task_list_is_actual(checked_list=set(valued_del), tow_id=tow_id, is_task=False)

            # Если после проверки был прислан список задач у которых есть плановые трудозатраты, проверяем,
            # что у такого списка так же в текущем сохранении удалялись и плановые трудозатраты. Иначе ошибка
            if task_is_actual['status'] and 'recheck_list' in task_is_actual.keys():
                for i in task_is_actual['recheck_list']:
                    if i[0] in user_changes.keys():
                        if i[1] in user_changes[i[0]].keys():
                            if 'input_task_plan_labor_cost' in user_changes[i[0]][i[1]].keys():
                                if user_changes[i[0]][i[1]]['input_task_plan_labor_cost'] != 0:
                                    description = 'У задачи есть плановые трудозатраты (v.1)'
                                    flash(message=['Ошибка',
                                                   description,
                                                   f"task_id: {i[0]}"
                                                   ], category='error')
                                    return jsonify({
                                        'status': 'error',
                                        'description': [description,
                                                        f"task_id: {i[0]}"
                                                        ],
                                    })
                                # else:
                                #     recheck_list_plan_labor_cost.add((i[0], i[1]))
                                #     # Только для новой задачи. Удаляем запись в user_changes
                                #     user_changes[i[0]][i[1]] = user_changes[task_id].pop(tr_id)
                        else:
                            tr_info = get_tr_info(i[1])
                            description = 'У задачи есть плановые трудозатраты (v.2)'
                            flash(message=['Ошибка',
                                           description,
                                           f"Задача: {tr_info['short_task_name']}",
                                           f"Исполнитель: {tr_info['short_full_name']}"
                                           ], category='error')
                            return jsonify({
                                'status': 'error',
                                'description': [description,
                                                f"Задача: {tr_info['short_task_name']}",
                                                f"Исполнитель: {tr_info['short_full_name']}"
                                                ],
                            })
                    else:
                        description = 'У задачи есть плановые трудозатраты (v.3)'
                        flash(message=['Ошибка',
                                       description,
                                       f"task_id: {i[0]}"
                                       ], category='error')
                        return jsonify({
                            'status': 'error',
                            'description': [description,
                                            f"task_id: {i[0]}"
                                            ],
                        })

            elif not task_is_actual['status']:
                if 'tr_id' in task_is_actual.keys():
                    tr_info = get_tr_info(task_is_actual['tr_id'])
                    app_login.set_warning_log(
                        log_url=sys._getframe().f_code.co_name,
                        log_description=f"tow_id:{tow_id}. {task_is_actual['description']}. "
                                        f"Задача: {tr_info['short_task_name']}. "
                                        f"Исполнитель: {tr_info['short_full_name']}",
                        user_id=user_id, ip_address=app_login.get_client_ip()
                    )
                    flash(message=['Ошибка',
                                   task_is_actual['description'],
                                   f"Задача: {tr_info['short_task_name']}",
                                   f"Исполнитель: {tr_info['short_full_name']}"
                                   ], category='error')
                    return jsonify({
                        'status': 'error',
                        'description': [task_is_actual['description'],
                                        f"Задача: {tr_info['short_task_name']}",
                                        f"Исполнитель: {tr_info['short_full_name']}"
                                        ],
                    })
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f"tow_id:{tow_id}. {task_is_actual['description']}",
                    user_id=user_id, ip_address=app_login.get_client_ip()
                )
                flash(message=['Ошибка', task_is_actual['description']], category='error')
                return jsonify({
                    'status': 'error',
                    'description': [task_is_actual['description']],
                })

        ######################################################################################
        # НОВОЕ. Список для добавления
        ######################################################################################
        values_new_task = []
        values_new_tr = []
        sorted_new_task = []
        sorted_new_tr = []
        new_task_dict = {}
        new_tr_dict = {}
        values_upd_task = []
        values_upd_tr = []

        # Список вновь созданных task_id и tr_id для проверки, что user_changes не останется не учтённых текстовых id
        new_task_set = set()
        new_tr_set = set()

        if len(new_tow):
            # Список новых tow value
            columns_task = ('main_task', 'tow_id', 'parent_id', 'task_number', 'task_name', 'lvl', 'owner', 'last_editor')
            columns_upd_task = ('task_id', 'parent_id::integer')
            columns_tr = ('task_id', 'user_id', 'task_status_id', 'task_responsible_comment', 'owner', 'last_editor',
                          'task_plan_labor_cost')

            # Добавляем все новые task_id в список
            new_task_set = set(new_tow.keys())

            # for task_id, tr in new_tow.items():
            for task_id in list(new_tow.keys())[:]:
                tr = new_tow[task_id]
                # Если tr_id = 'None', то заменяем на NoneType
                if 'None' in tr.keys():
                    new_tow[task_id][None] = new_tow[task_id].pop('None')

                # Если task_id - число, значит не нужно добавлять task, только tr
                if isinstance(task_id, int):
                    # Поля для tr
                    for tr_id, v in tr.items():
                        # Добавляем все новые tr_id в список
                        new_tr_set.add(tr_id)

                        tr_tmp_1 = task_id  # task_id
                        tr_tmp_2 = None  # user_id - пока оставляем пустым
                        tr_tmp_3 = 1  # task_status_id - пока оставляем пустым (по умолчанию id-1 не в работе)
                        tr_tmp_4 = ''  # task_responsible_comment - пока оставляем пустым
                        tr_tmp_5 = user_id  # owner
                        tr_tmp_6 = user_id  # last_editor
                        tr_tmp_7 = None  # task_plan_labor_cost

                        # Если не нашли tr_id в списке изменений, вызываем ошибку
                        if tr_id not in user_changes[task_id].keys():
                            app_login.set_warning_log(
                                log_url=sys._getframe().f_code.co_name,
                                log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-5.1",
                                user_id=user_id, ip_address=app_login.get_client_ip()
                            )
                            flash(message=['Ошибка', 'Не найдены данные для вновь созданных задач rev-5.1',
                                           'Обновите страницу'],
                                  category='error')
                            return jsonify({
                                'status': 'error',
                                'description': ['Не найдены данные для вновь созданных задач rev-5',
                                                'Обновите страницу'],
                            })
                        tr_info = user_changes[task_id][tr_id]

                        tr_tmp_2 = tr_info['td_task_responsible_user'] if 'td_task_responsible_user' in tr_info.keys() \
                            else tr_tmp_2
                        tr_tmp_3 = tr_info['td_tow_task_statuses'] if 'td_tow_task_statuses' in tr_info.keys() \
                            else tr_tmp_3
                        tr_tmp_4 = tr_info['input_task_responsible_comment'] if ('input_task_responsible_comment' in
                                                                                 tr_info.keys()) else tr_tmp_4
                        tr_tmp_7 = tr_info['input_task_plan_labor_cost'] if ('input_task_plan_labor_cost' in
                                                                             tr_info.keys()) else tr_tmp_7

                        values_new_tr.append([
                            tr_tmp_1,  # task_id
                            tr_tmp_2,  # user_id
                            tr_tmp_3 if tr_tmp_3 is not None else 1,  # task_status_id (по умолчанию "Не в работе" id 1)
                            tr_tmp_4,  # task_responsible_comment
                            tr_tmp_5,  # owner
                            tr_tmp_6,  # last_editor
                            tr_tmp_7,  # task_plan_labor_cost
                        ])

                        # Удаляем найденный ключ, чтобы не добавить в список изменений
                        del user_changes[task_id][tr_id]
                        if not len(user_changes[task_id].keys()):
                            del user_changes[task_id]
                    continue

                # Поля для task
                task_tmp_1 = 'false'  # main_task - пока оставляем false
                task_tmp_2 = tow_id  # tow_id
                task_tmp_3 = None  # parent_id - пока оставляем пустым
                task_tmp_4 = ''  # task_number - пока оставляем пустым
                task_tmp_5 = ''  # task_name - пока оставляем пустым
                task_tmp_6 = ''  # lvl - пока оставляем пустым
                task_tmp_7 = user_id  # owner
                task_tmp_8 = user_id  # last_editor

                #Если task - main_task
                if len(tr.keys()) == 1 and None in tr.keys():
                    task_tmp_1 = 'true'  # main_task
                    # Определяем остальные переменные для task
                    # Если не нашли task_id в списке изменений, вызываем ошибку
                    if task_id not in user_changes.keys() or None not in user_changes[task_id].keys():
                        app_login.set_warning_log(
                            log_url=sys._getframe().f_code.co_name,
                            log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-1",
                            user_id=user_id, ip_address=app_login.get_client_ip()
                        )
                        flash(message=['Ошибка',
                                       'Не найдены данные для вновь созданных задач rev-1',
                                       'Обновите страницу'],
                              category='error')
                        return jsonify({
                            'status': 'error',
                            'description': ['Не найдены данные для вновь созданных задач rev-1', 'Обновите страницу'],
                        })
                    task_info = user_changes[task_id][None]

                    task_tmp_3 = task_info['parent_id'] if 'parent_id' in task_info.keys() else task_tmp_3
                    task_tmp_4 = task_info['input_task_number'] if 'input_task_number' in task_info.keys() \
                        else task_tmp_4
                    task_tmp_5 = task_info['input_task_name'] if 'input_task_name' in task_info.keys() else task_tmp_5
                    if 'lvl' in task_info.keys():
                         task_tmp_6 = task_info['lvl']
                    else:
                        app_login.set_warning_log(
                            log_url=sys._getframe().f_code.co_name,
                            log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-2",
                            user_id=user_id, ip_address=app_login.get_client_ip()
                        )
                        flash(message=['Ошибка',
                                       'Не найдены данные для вновь созданных задач rev-2',
                                       'Обновите страницу'],
                              category='error')
                        return jsonify({
                            'status': 'error',
                            'description': ['Не найдены данные для вновь созданных задач rev-2', 'Обновите страницу'],
                        })
                    # Удаляем найденный ключ, чтобы не добавить в список изменений
                    del user_changes[task_id]
                else:
                    # Определяем остальные переменные для task
                    # Если не нашли task_id в списке изменений, вызываем ошибку
                    if task_id not in user_changes.keys():
                        app_login.set_warning_log(
                            log_url=sys._getframe().f_code.co_name,
                            log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-3",
                            user_id=user_id, ip_address=app_login.get_client_ip()
                        )
                        flash(message=['Ошибка',
                                       'Не найдены данные для вновь созданных задач rev-3',
                                       'Обновите страницу'],
                              category='error')
                        return jsonify({
                            'status': 'error',
                            'description': ['Не найдены данные для вновь созданных задач rev-3', 'Обновите страницу'],
                        })
                    task_info = user_changes[task_id][list(user_changes[task_id].keys())[0]]

                    task_tmp_3 = task_info['parent_id'] if 'parent_id' in task_info.keys() else task_tmp_3
                    task_tmp_4 = task_info['input_task_number'] if 'input_task_number' in task_info.keys() \
                        else task_tmp_4
                    task_tmp_5 = task_info['input_task_name'] if 'input_task_name' in task_info.keys() else task_tmp_5

                    if 'lvl' in task_info.keys():
                        task_tmp_6 = task_info['lvl']
                    else:
                        app_login.set_warning_log(
                            log_url=sys._getframe().f_code.co_name,
                            log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-4",
                            user_id=user_id, ip_address=app_login.get_client_ip()
                        )
                        flash(message=['Ошибка',
                                       'Не найдены данные для вновь созданных задач rev-4',
                                       'Обновите страницу'],
                              category='error')
                        return jsonify({
                            'status': 'error',
                            'description': ['Не найдены данные для вновь созданных задач rev-4', 'Обновите страницу'],
                        })

                    # Поля для tr
                    for tr_id, v in tr.items():
                        # Добавляем все новые tr_id в список
                        new_tr_set.add(tr_id)

                        tr_tmp_1 = task_id  # task_id
                        tr_tmp_2 = None  # user_id - пока оставляем пустым
                        tr_tmp_3 = 1  # task_status_id - пока оставляем пустым (по умолчанию id-1 не в работе)
                        tr_tmp_4 = ''  # task_responsible_comment - пока оставляем пустым
                        tr_tmp_5 = user_id  # owner
                        tr_tmp_6 = user_id  # last_editor
                        tr_tmp_7 = None  # task_plan_labor_cost

                        # Если не нашли tr_id в списке изменений, вызываем ошибку
                        if tr_id not in user_changes[task_id].keys():
                            app_login.set_warning_log(
                                log_url=sys._getframe().f_code.co_name,
                                log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-5",
                                user_id=user_id, ip_address=app_login.get_client_ip()
                            )
                            flash(message=['Ошибка', 'Не найдены данные для вновь созданных задач rev-5',
                                           'Обновите страницу'],
                                  category='error')
                            return jsonify({
                                'status': 'error',
                                'description': ['Не найдены данные для вновь созданных задач rev-5',
                                                'Обновите страницу'],
                            })
                        tr_info = user_changes[task_id][tr_id]

                        tr_tmp_2 = tr_info['td_task_responsible_user'] if 'td_task_responsible_user' in tr_info.keys() \
                            else tr_tmp_2
                        tr_tmp_3 = tr_info['td_tow_task_statuses'] if 'td_tow_task_statuses' in tr_info.keys() \
                            else tr_tmp_3
                        tr_tmp_4 = tr_info['input_task_responsible_comment'] if ('input_task_responsible_comment' in
                                                                                 tr_info.keys()) else tr_tmp_4
                        tr_tmp_7 = tr_info['input_task_plan_labor_cost'] if ('input_task_plan_labor_cost' in
                                                                               tr_info.keys()) else tr_tmp_7

                        values_new_tr.append([
                            tr_tmp_1,  # task_id
                            tr_tmp_2,  # user_id
                            tr_tmp_3 if tr_tmp_3 is not None else 1,  # task_status_id (по умолчанию "Не в работе" id 1)
                            tr_tmp_4,  # task_responsible_comment
                            tr_tmp_5,  # owner
                            tr_tmp_6,  # last_editor
                            tr_tmp_7,  # task_plan_labor_cost
                        ])

                        # Удаляем найденный ключ, чтобы не добавить в список изменений
                        del user_changes[task_id][tr_id]
                        if not len(user_changes[task_id].keys()):
                            del user_changes[task_id]

                values_new_task.append([
                    task_tmp_1,  # main_task
                    task_tmp_2,  # tow_id
                    None,        # parent_id
                    task_tmp_4,  # task_number
                    task_tmp_5,  # task_name
                    task_tmp_6,  # lvl
                    task_tmp_7,  # owner
                    task_tmp_8,  # last_editor
                ])
                sorted_new_task.append([task_id, task_tmp_6])

                values_upd_task.append([
                    task_id,  # task_id
                    task_tmp_3,  # parent_id
                ])

            # Заменяем тип значения task_id и tr_id на int и проверяем, что не осталось неучтённых текстовых id
            if len(user_changes.keys()):
                # for task_id, tr in user_changes.items()[:]:
                for task_id in list(user_changes.keys())[:]:
                    tr = user_changes[task_id]
                    if len(tr.keys()) == 1 and None in tr.keys():
                        pass
                    else:
                        for tr_id, v in tr.items():
                            pass
                    # Если task_id текстовое значение и отсутствует в списке вновь созданных - вызываем ошибку, т.к.
                    # только новые task_id имеют текстовый тип
                    if task_id not in new_task_set and isinstance(task_id, str):
                        app_login.set_warning_log(
                            log_url=sys._getframe().f_code.co_name,
                            log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-6",
                            user_id=user_id, ip_address=app_login.get_client_ip()
                        )
                        flash(message=['Ошибка',
                                       'Не найдены данные для вновь созданных задач rev-6',
                                       'Обновите страницу'],
                              category='error')
                        return jsonify({
                            'status': 'error',
                            'description': ['Не найдены данные для вновь созданных задач rev-6', 'Обновите страницу'],
                        })
                    # Проверяем все tr_id и parent_id
                    for tr_id in list(tr.keys())[:]:
                        v = tr[tr_id]

                        if 'parent_id' in v.keys():
                            parent_id = v['parent_id']
                            # Если parent_id текстовое значение и отсутствует в списке вновь созданных -
                            # вызываем ошибку, т.к. только новые task_id имеют текстовый тип
                            if parent_id not in new_task_set and isinstance(parent_id, str):
                                app_login.set_warning_log(
                                    log_url=sys._getframe().f_code.co_name,
                                    log_description=f"tow_id:{tow_id}. "
                                                    f"Не найдены данные для вновь созданных задач rev-7",
                                    user_id=user_id, ip_address=app_login.get_client_ip()
                                )
                                flash(message=['Ошибка',
                                               'Не найдены данные для вновь созданных задач rev-7',
                                               'Обновите страницу'],
                                      category='error')
                                return jsonify({
                                    'status': 'error',
                                    'description': ['Не найдены данные для вновь созданных задач rev-7',
                                                    'Обновите страницу'],
                                })

                        if tr_id not in new_tr_set and isinstance(tr_id, str):
                            app_login.set_warning_log(
                                log_url=sys._getframe().f_code.co_name,
                                log_description=f"tow_id:{tow_id}. Не найдены данные для вновь созданных задач rev-8",
                                user_id=user_id, ip_address=app_login.get_client_ip()
                            )
                            flash(message=['Ошибка', 'Не найдены данные для вновь созданных задач rev-8',
                                           'Обновите страницу'],
                                  category='error')
                            return jsonify({
                                'status': 'error',
                                'description': ['Не найдены данные для вновь созданных задач rev-8',
                                                'Обновите страницу'],
                            })

            if len(values_new_task):
                # Добавляем БД task, получаем список task_id, которыми заменим временные task_id
                values_new_task = sorted(values_new_task, key=lambda x: x[-3])
                sorted_new_task = sorted(sorted_new_task, key=lambda x: x[-1])

                action_new_task = 'INSERT INTO'
                table_new_task = 'tasks'
                subquery_new_task = " ON CONFLICT DO NOTHING RETURNING task_id;"

                query_tow = app_payment.get_db_dml_query(action=action_new_task, table=table_new_task, columns=columns_task,
                                                         subquery=subquery_new_task)

                execute_values(cursor, query_tow, values_new_task, page_size=len(values_new_task))
                list_task_id = cursor.fetchall()

                description = 'Изменения сохранены'

                conn.commit()

                # Список старых и новых id для вновь созданных task
                values_new_task_old = values_new_task
                values_new_task = dict()
                for i in range(len(list_task_id)):
                    values_new_task[list_task_id[i][0]] = values_new_task_old[i]
                    new_task_dict[sorted_new_task[i][0]] = list_task_id[i][0]
                    new_task_set.add(list_task_id[i][0])

                # Изменяем parent_id новых tow
                for i in values_upd_task:
                    if i[0] in new_task_dict:
                        i[0] = new_task_dict[i[0]]
                    if i[1] in new_task_dict:
                        i[1] = new_task_dict[i[1]]
                # Изменяем parent_id новых tow
                for i in values_new_tr:
                    if i[0] in new_task_dict:
                        i[0] = new_task_dict[i[0]]

            if len(values_upd_task):
                query_new_task_upd = app_payment.get_db_dml_query(action='UPDATE', table='tasks',
                                                                 columns=columns_upd_task)
                execute_values(cursor, query_new_task_upd, values_upd_task)
                description = 'Изменения сохранены'
                conn.commit()
            if len(values_new_tr):
                query_tr_upd = app_payment.get_db_dml_query(action='INSERT INTO', table='task_responsible',
                                                                  columns=columns_tr)
                execute_values(cursor, query_tr_upd, values_new_tr)
                description = 'Изменения сохранены'
                conn.commit()

        ######################################################################################
        # Список для изменения
        ######################################################################################
        if len(user_changes.keys()):
            task_col_dict = {
                'main_task': ['main_task', 'boolean', '::boolean'],
                'parent_id': ['parent_id', 'int', '::integer'],
                'input_task_number': ['task_number', 'str', '::text'],
                'input_task_name': ['task_name', 'str', '::text'],
                'lvl': ['lvl', 'int', '::smallint'],
                'last_editor': ['last_editor', 'int', 'last_editor::integer']
            }
            tr_col_dict = {
                'td_task_responsible_user': ['user_id', 'int', '::integer'],
                'td_tow_task_statuses': ['task_status_id', 'int', '::integer'],
                'input_task_responsible_comment': ['task_responsible_comment', 'str', '::text'],
                'last_editor': ['last_editor', 'int', 'last_editor::integer'],
                'input_task_plan_labor_cost': ['task_plan_labor_cost', 'float', '::numeric']
            }

            for task_id, tr in user_changes.items():
                # Поля для tr
                # Если task - main_task
                if len(tr.keys()) == 1 and None in tr.keys():
                    # Обновляем значение parent_id если parent_id вновь созданная task
                    if ('parent_id' in user_changes[task_id][None].keys() and
                            user_changes[task_id][None]['parent_id'] in new_task_dict):
                        tmp_parent_id = user_changes[task_id][None]['parent_id']
                        user_changes[task_id][None]['parent_id'] = new_task_dict[tmp_parent_id]

                    task_info = user_changes[task_id][None]

                    columns_task_upd = ["task_id::integer", "last_editor::integer"]
                    values_task_upd = [[task_id, user_id]]

                    for k1, v1 in task_info.items():
                        if k1 in task_col_dict:
                            columns_task_upd.append(task_col_dict[k1][0] + task_col_dict[k1][2])
                            values_task_upd[0].append(
                                app_project.conv_tow_data_upd(val=v1, col_type=task_col_dict[k1][1])
                            )
                    if len(columns_task_upd) > 2:
                        query_task_upd = app_payment.get_db_dml_query(action='UPDATE', table='tasks',
                                                                     columns=columns_task_upd)
                        execute_values(cursor, query_task_upd, values_task_upd)
                        conn.commit()
                        description = 'Изменения сохранены'

                else:
                    # Данные для task
                    task_info = user_changes[task_id][list(user_changes[task_id].keys())[0]]
                    # Обновляем значение parent_id если parent_id вновь созданная task
                    if 'parent_id' in task_info.keys() and task_info['parent_id'] in new_task_dict:
                        tmp_parent_id = task_info['parent_id']
                        task_info['parent_id'] = new_task_dict[tmp_parent_id]
                    columns_task_upd = ["task_id::integer", "last_editor::integer"]
                    values_task_upd = [[task_id, user_id]]

                    for k1, v1 in task_info.items():
                        if k1 in task_col_dict:
                            columns_task_upd.append(task_col_dict[k1][0] + task_col_dict[k1][2])
                            values_task_upd[0].append(
                                app_project.conv_tow_data_upd(val=v1, col_type=task_col_dict[k1][1])
                            )
                    if len(columns_task_upd) > 2:
                        query_task_upd = app_payment.get_db_dml_query(action='UPDATE', table='tasks',
                                                                          columns=columns_task_upd)
                        execute_values(cursor, query_task_upd, values_task_upd)
                        conn.commit()
                        description = 'Изменения сохранены'

                    # Данные для tr
                    for tr_id, v in tr.items():
                        # Обновляем значение parent_id если parent_id вновь созданная task
                        if ('parent_id' in user_changes[task_id][tr_id].keys() and
                                user_changes[task_id][tr_id]['parent_id'] in new_task_dict):
                            tmp_parent_id = user_changes[task_id][tr_id]['parent_id']
                            user_changes[task_id][tr_id]['parent_id'] = new_task_dict[tmp_parent_id]
                        tr_info = user_changes[task_id][tr_id]

                        columns_tr_upd = ["task_responsible_id::integer", "last_editor::integer"]
                        values_tr_upd = [[tr_id, user_id]]

                        for k1, v1 in tr_info.items():
                            if k1 in tr_col_dict:
                                columns_tr_upd.append(tr_col_dict[k1][0] + tr_col_dict[k1][2])
                                values_tr_upd[0].append(
                                    app_project.conv_tow_data_upd(val=v1, col_type=tr_col_dict[k1][1])
                                )
                        query_tr_upd = app_payment.get_db_dml_query(action='UPDATE', table='task_responsible',
                                                                          columns=columns_tr_upd)
                        execute_values(cursor, query_tr_upd, values_tr_upd)
                        conn.commit()
                        description = 'Изменения сохранены'


        ######################################################################################
        # Если удалялись строки если были
        ######################################################################################
        # Удаляем tr
        if 'valued_del_tr' in locals() and len(valued_del_tr):
            columns_del_tow = 'task_responsible_id'
            query_del_tr = app_payment.get_db_dml_query(action='DELETE', table='task_responsible',
                                                         columns=columns_del_tow)
            execute_values(cursor, query_del_tr, (valued_del_tr,))
            conn.commit()
            description = 'Изменения сохранены'
            time.sleep(3)
        # Удаляем task
        if 'valued_del_task' in locals() and len(valued_del_task):
            columns_del_tow_parent = 'parent_id'
            query_del_task_parent = app_payment.get_db_dml_query(action='DELETE', table='tasks',
                                                         columns=columns_del_tow_parent)
            execute_values(cursor, query_del_task_parent, (valued_del_task,))
            conn.commit()

            columns_del_tow = 'task_id'
            query_del_task = app_payment.get_db_dml_query(action='DELETE', table='tasks',
                                                          columns=columns_del_tow)
            execute_values(cursor, query_del_task, (valued_del_task,))
            conn.commit()

            description = 'Изменения сохранены'


        app_login.conn_cursor_close(cursor, conn)

        if description == 'Изменения сохранены':
            flash(message=[description], category='success')
        elif description == 'Изменения не найдены. Ничего не произошло':
            flash(message=[description], category='info')


        return jsonify({'status': 'success', 'contract_id': 'contract_id', 'description': description})
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error',
                        'description': [msg_for_user],
                        })

# Страница задач сотрудника
@task_app_bp.route('/my_tasks', methods=['GET'])
@login_required
def get_my_tasks():
    """Страница задач пользователя"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())

        # Список объектов
        proj_list = app_project.get_proj_list()
        if proj_list[0] == 'error':
            flash(message=proj_list[1], category='error')
            return redirect(url_for('app_project.objects_main'))
        elif not proj_list[1]:
            flash(message=['Ошибка', 'Страница недоступна', 'Список проектов пуст'], category='error')
            return redirect(url_for('app_project.objects_main'))
        proj_list = proj_list[2]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        ########################################################################
        #                       Список изменений статуса трудозатрат
        ########################################################################
        cursor.execute(
            f"""
                SELECT 
                    empl_labor_date,
                    to_char(empl_labor_date, 'dd.mm.yyyy') AS empl_labor_date_txt,
                    empl_labor_status,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt
                FROM labor_status
                WHERE user_id = {user_id} AND empl_labor_date <= CURRENT_DATE
                ORDER BY empl_labor_date , created_at ;
                        """
        )
        labor_status_list = cursor.fetchall()

        if not labor_status_list or not labor_status_list[-1]['empl_labor_status']:
            flash(message=['Ошибка', 'Страница недоступна', 'Статус отправки часов не подтвержден'], category='error')
            return redirect(url_for('app_project.objects_main'))

        # where_labor_status_date = ''
        date_series_ls = None  # Список периодов подачи часов
        tmp_date_start, tmp_date_end = None, None  # Пара начала и окончания подачи часов

        # Границы недель для выбора другого периода на страницу
        min_other_period, max_other_period = '', ''

        for i in range(len(labor_status_list)):
            labor_status_list[i] = dict(labor_status_list[i])

            # Создаём список периодов в которых сотрудник должен отправлять часы
            if tmp_date_start and tmp_date_end:
                if not date_series_ls:
                    date_series_ls = f"""SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
                else:
                    date_series_ls += f""" UNION SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
                tmp_date_start, tmp_date_end = None, None

            if labor_status_list[i]['empl_labor_status']:
                # equal_sign = '>='
                tmp_date_start = labor_status_list[i]['empl_labor_date']
                min_other_period = min_other_period if min_other_period else tmp_date_start
            else:
                # equal_sign = '<='
                if tmp_date_start:
                    tmp_date_end = labor_status_list[i]['empl_labor_date']
                max_other_period = labor_status_list[i]['empl_labor_date']

            # if not where_labor_status_date:
            #     where_labor_status_date = f" hotr_date {equal_sign} '{labor_status_list[i]['empl_labor_date']}' "
            # else:
            #     where_labor_status_date += f"AND hotr_date {equal_sign} '{labor_status_list[i]['empl_labor_date']}' "

        # Обрабатываем для последнего. Создаём список периодов в которых сотрудник отправлять часы
        if tmp_date_start and tmp_date_end:
            max_other_period = tmp_date_end
            if not date_series_ls:
                date_series_ls = f"""SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
            else:
                date_series_ls += f""" UNION SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
            tmp_date_start, tmp_date_end = None, None
        # Если была найдена только дата старта, то добавляем дату окончания - сегодня
        if tmp_date_start and not tmp_date_end:
            tmp_date_end = "CURRENT_DATE::DATE"
            max_other_period = date.today()  + timedelta(weeks=4)
            if not date_series_ls:
                date_series_ls = f"""SELECT 
                generate_series('{tmp_date_start}'::date, {tmp_date_end}, '1 day')::date AS date"""
            else:
                date_series_ls += f""" UNION SELECT 
                generate_series('{tmp_date_start}'::date, {tmp_date_end}, '1 day')::date AS date"""

        min_other_period = min_other_period.strftime("%Y-W%V") if min_other_period else min_other_period
        max_other_period = max_other_period.strftime("%Y-W%V") if max_other_period else max_other_period
        my_tasks_other_period = [min_other_period, max_other_period]

        # Дата текущей недели, понедельник и воскресенье текущей недели
        today = date.today()
        day_0 = today - timedelta(days=today.weekday())
        day_6 = today + timedelta(days=6-today.weekday())
        current_period = [today.strftime("%Y-W%V"), day_0, day_6]

        ########################################################################
        #                       Список изменений статуса почасовой оплаты
        ########################################################################
        cursor.execute(
            f"""
                SELECT 
                    empl_hours_date,
                    to_char(empl_hours_date, 'dd.mm.yyyy') AS empl_hours_date_txt,
                    full_day_status,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt
                FROM hour_per_day_norm
                WHERE user_id = {user_id} AND empl_hours_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE
                ORDER BY empl_hours_date, created_at;
                """
        )
        h_p_d_n_list = cursor.fetchall()

        date_series_h_p_d_n = ''  # Список периодов не почасовой оплаты
        calendar_cur_week_h_p_d_n = ''  # Список периодов подачи часов
        tmp_date_start, tmp_date_end = None, None  # Пара начала и окончания подачи часов

        for i in range(len(h_p_d_n_list)):
            h_p_d_n_list[i] = dict(h_p_d_n_list[i])

            # Создаём список периодов в которых сотрудник может отправить любое кол-во часов
            if tmp_date_start and tmp_date_end:
                date_series_h_p_d_n += f""" hotr_date BETWEEN {tmp_date_start} AND '{tmp_date_end}' OR"""
                calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                        calendar_cur_week_h_p_d_n + ' OR ')
                calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND '{tmp_date_end}' """
                tmp_date_start, tmp_date_end = None, None

            if not h_p_d_n_list[i]['full_day_status']:
                tmp_date_start = h_p_d_n_list[i]['empl_hours_date']
                tmp_date_start = f"(date_trunc('week', '{tmp_date_start}'::DATE) + interval '1 days')::DATE"
            elif tmp_date_start:
                tmp_date_end = h_p_d_n_list[i]['empl_hours_date']

        # Обрабатываем для последнего. Создаём список периодов в которых сотрудник отправлять часы
        if tmp_date_start and tmp_date_end:
            date_series_h_p_d_n += f""" hotr_date BETWEEN {tmp_date_start} AND '{tmp_date_end}' OR"""
            calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                    calendar_cur_week_h_p_d_n + ' OR ')
            calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND '{tmp_date_end}' """
            tmp_date_start, tmp_date_end = None, None

        # Если была найдена только дата старта, то добавляем дату окончания - сегодня
        if tmp_date_start and not tmp_date_end:
            tmp_date_end = "CURRENT_DATE::DATE"
            date_series_h_p_d_n += f""" hotr_date BETWEEN {tmp_date_start} AND  {tmp_date_end} OR"""
            calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                    calendar_cur_week_h_p_d_n + ' OR ')
            calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND {tmp_date_end} """

        # Добавляем в запрос недостающую часть конструкции списка дат неполного рабдня
        date_series_h_p_d_n = f""" AND ({date_series_h_p_d_n[:-3]})""" if date_series_h_p_d_n else ''

        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # Календарь текущей недели и статус выходного дня
        cursor.execute(
            f"""
                WITH holiday_list AS
                    (SELECT
                        holiday_date,
                        holiday_status,
                        EXTRACT(dow FROM holiday_date) AS day_week
                    FROM list_holidays
                    WHERE holiday_date BETWEEN 
                            date_trunc('week', CURRENT_DATE)::DATE
                                AND 
                            (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE

                    ORDER BY holiday_date ASC
                    ),

                work_days AS
                    (SELECT generate_series(
                        date_trunc('week', CURRENT_DATE)::DATE, 
                        (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE, 
                        interval  '1 day')::DATE AS work_day
                    )

                SELECT
                    t0.work_day,
                    COALESCE(to_char(t0.work_day, 'dd.mm.yy'), '') AS work_day_txt,
                    CASE
                        WHEN t1.holiday_status IS NOT NULL THEN t1.holiday_status
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN TRUE
                        ELSE FALSE
                    END AS holiday_status,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'th_task_holiday th_week_day'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'th_task_work_day th_week_day'
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN 'th_task_holiday th_week_day'
                        ELSE 'th_task_work_day th_week_day'
                    END AS class,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'td_task_holiday'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'td_task_work_day'
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN 'td_task_holiday'
                        ELSE 'td_task_work_day'
                    END AS td_class,
                    0 AS hours_per_day,
                    CASE
                        WHEN TRUE {calendar_cur_week_h_p_d_n} THEN FALSE
                        ELSE TRUE
                    END AS hpdn_status
                FROM work_days AS t0
                LEFT JOIN holiday_list AS t1 ON t0.work_day = t1.holiday_date;
                """
        )
        calendar_cur_week = cursor.fetchall()

        if len(calendar_cur_week):
            for i in range(len(calendar_cur_week)):
                calendar_cur_week[i] = dict(calendar_cur_week[i])
                calendar_cur_week[i]['day_week'] = DAYS_OF_THE_WEEK[i]
        else:
            calendar_cur_week = False
            flash(message=['Ошибка', 'Страница недоступна', 'Не удалось определить даты текущей недели'],
                  category='error')
            return redirect(url_for('app_project.objects_main'))

        # Список задач пользователя и часы за текущую неделю
        cursor.execute(
            f"""
            WITH RECURSIVE rel_task_resp AS (
                SELECT
                    10000 AS depth,
                    task_responsible_id,
                    task_id,
                    task_id AS parent_id,
                    0 AS tow_id,
                    task_status_id,
                    ARRAY[''] AS name_path,
                    ARRAY[''] AS short_name_path,
                    ARRAY[task_id] AS child_path,
                    '' AS task_name,
                    ARRAY['tr'] AS tow_task,
                    ARRAY['Текущая задача: '] AS tow_task_title
                FROM task_responsible
                WHERE user_id = %s

                UNION ALL

                SELECT
                    r.depth - 1,
                    r.task_responsible_id,
                    n.task_id,
                    n.parent_id,
                    n.tow_id,
                    r.task_status_id,
                    n.task_name || r.name_path,

                    CASE
                        WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
                        ELSE n.task_name
                    END || r.short_name_path,

                    r.child_path || n.task_id || n.lvl::int,
                    n.task_name,
                    ARRAY['task'] || r.tow_task,
                    ARRAY['Задача: '] || r.tow_task_title
                FROM rel_task_resp AS r
                JOIN tasks AS n ON n.task_id = r.parent_id
            ),
            rel_rec AS (
                SELECT
                    depth,
                    task_responsible_id,
                    task_id,
                    tow_id AS parent_id,
                    tow_id,
                    task_status_id,
                    name_path,
                    short_name_path,
                    child_path,
                    task_name,
                    tow_task,
                    tow_task_title
                FROM rel_task_resp
                WHERE parent_id IS NULL

                UNION ALL

                SELECT
                    r.depth - 1,
                    r.task_responsible_id,
                    r.task_id,
                    n.parent_id,
                    n.tow_id,
                    r.task_status_id,
                    n.tow_name || r.name_path,

                    CASE
                        WHEN length(n.tow_name) > 20 THEN SUBSTRING(n.tow_name, 1, 17) || '...'
                        ELSE n.tow_name
                    END || r.short_name_path,

                    r.child_path || n.tow_id || n.lvl::int,
                    n.tow_name,
                    ARRAY['tow'] || r.tow_task,
                    ARRAY['Вид работ: '] || r.tow_task_title
                FROM rel_rec AS r
                JOIN types_of_work AS n ON n.tow_id = r.parent_id
            ),
            rel_rec_org_works AS (
                SELECT
                    0 AS depth,
                    o.*,
                    ARRAY[o.lvl, o.task_id] AS child_path,
            		ARRAY[task_name] AS name_path,
            		ARRAY[CASE
            			WHEN length(task_name) > 20 THEN SUBSTRING(task_name, 1, 17) || '...'
            			ELSE task_name
            		END] AS short_name_path,
            		ARRAY[CASE
            				WHEN main_task THEN 'tr'
            				ELSE 'task'
            		END] AS tow_task,
            		ARRAY[CASE
            				WHEN main_task THEN 'Базовая задача:'
            				ELSE 'Задача:'
            		END] AS tow_task_title
                FROM public.org_works AS o
                WHERE parent_id IS NULL

                UNION ALL
                SELECT
                    nlevel(r.path) - 1,
                    n.*,
                    r.child_path || n.lvl || n.task_id,
            		r.name_path || n.task_name,
            		r.short_name_path || CASE
            			WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
            			ELSE n.task_name
            		END,
            		ARRAY[CASE
            				WHEN n.main_task THEN 'tr'
            				ELSE 'task'
            		END] || r.tow_task AS tow_task,
            		ARRAY[CASE
            				WHEN n.main_task THEN 'Базовая задача:'
            				ELSE 'Задача:'
            		END] || r.tow_task_title AS tow_task_title
                FROM rel_rec_org_works AS r
                JOIN public.org_works AS n ON n.parent_id = r.task_id
            )
            (SELECT
                'task' AS row_type,
                CASE
                    WHEN t1.task_status_id = 4 THEN 'tr_task_status_closed'
                    ELSE 'tr_task_status_not_closed'
                END AS task_class,
                t1.child_path[1] AS task_id,
                t1.task_responsible_id::text,
                '' as task_number,
                '' as task_number_not_closed,
                t1.task_status_id,
                t1.tow_task,
                t1.tow_task_title,
                t4.project_id,
                t5.task_status_name,
                t6.hotr_value,
                t2.task_plan_labor_cost,
                COALESCE(t6.hotr_value::text, '-') AS hotr_value_txt,
                COALESCE(t2.task_plan_labor_cost::text, '-') AS task_plan_labor_cost_txt,
                CASE
                    WHEN t1.task_status_id = 4 THEN TRUE
                    ELSE FALSE
                END AS editing_is_prohibited,
                t3.tow_id,
                COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,
                t6.input_task_week_1_day_1,
                t6.input_task_week_1_day_2,
                t6.input_task_week_1_day_3,
                t6.input_task_week_1_day_4,
                t6.input_task_week_1_day_5,
                t6.input_task_week_1_day_6,
                t6.input_task_week_1_day_7,

                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt,
                t6.max_date,

                t1.name_path[array_length(t1.name_path, 1) - 1] AS task_name,
                t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,

                t1.short_name_path[array_length(t1.short_name_path, 1) - 1] AS short_task_name,
                t1.short_name_path[1:array_length(t1.short_name_path, 1) - 2] AS short_name_path
            FROM rel_rec AS t1
            LEFT JOIN (
                SELECT 
                    task_id,
                    task_responsible_id,
                    task_status_id,
                    task_responsible_comment,
                    task_plan_labor_cost
                FROM public.task_responsible
            ) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
            LEFT JOIN (
                SELECT 
                    task_id,
                    tow_id
                FROM public.tasks
            ) AS t3 ON t1.child_path[1] = t3.task_id
            LEFT JOIN (
                SELECT 
                    tow_id,
                    project_id
                FROM public.types_of_work
            ) AS t4 ON t1.tow_id = t4.tow_id
            LEFT JOIN (
                SELECT 
                    task_status_id,
                    task_status_name
                FROM public.task_statuses
            ) AS t5 ON t1.task_status_id = t5.task_status_id
            LEFT JOIN (
                SELECT
                    task_responsible_id,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                    SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,
                    SUM(hotr_value) AS hotr_value,
                    MAX(hotr_date) AS max_date
                FROM public.hours_of_task_responsible
                GROUP BY task_responsible_id
            ) AS t6 ON t1.task_responsible_id = t6.task_responsible_id
            WHERE parent_id IS NULL)

            UNION ALL
            (SELECT
                'org_work' AS row_type,
                'tr_task_status_not_closed' AS task_class,
                t1.task_id,
                COALESCE(t2.task_responsible_id::text, MD5(t1.task_id::text)) AS task_responsible_id,
                '' as task_number,
                '' as task_number_not_closed,
                NULL AS task_status_id,
                t1.tow_task,
                t1.tow_task_title,
                NULL AS project_id,
                '' AS task_status_name,
                t6.hotr_value,
                0 AS task_plan_labor_cost,
                COALESCE(t6.hotr_value::text, '-') AS hotr_value_txt,
                '-' AS task_plan_labor_cost_txt,
                TRUE AS editing_is_prohibited,
                NULL AS tow_id,
                COALESCE(t2.task_responsible_comment, '') AS task_responsible_comment,

                t6.input_task_week_1_day_1,
                t6.input_task_week_1_day_2,
                t6.input_task_week_1_day_3,
                t6.input_task_week_1_day_4,
                t6.input_task_week_1_day_5,
                t6.input_task_week_1_day_6,
                t6.input_task_week_1_day_7,

                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                COALESCE(to_char(to_timestamp(((t6.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt,
                t6.max_date,

                t1.name_path[array_length(t1.name_path, 1)] AS task_name,
                t1.name_path[1:array_length(t1.name_path, 1) - 1] AS name_path,

                t1.short_name_path[array_length(t1.short_name_path, 1)] AS short_task_name,
                t1.short_name_path[1:array_length(t1.short_name_path, 1) - 1] AS short_name_path
            FROM rel_rec_org_works AS t1
            LEFT JOIN (
            	SELECT
            		task_id,
            		task_responsible_id,
            		task_responsible_comment
            	FROM public.org_work_responsible
            	WHERE user_id = %s
            ) AS t2 ON t1.task_id = t2.task_id
            LEFT JOIN (
            	SELECT
            		task_responsible_id,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE))::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '1 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '2 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '3 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '4 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '5 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
            		SUM(CASE WHEN hotr_date = (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7,
            		SUM(hotr_value) AS hotr_value,
            		MAX(hotr_date) AS max_date
            	FROM public.org_work_hours_of_task_responsible
            	GROUP BY task_responsible_id
            ) AS t6 ON t2.task_responsible_id = t6.task_responsible_id
            WHERE NOT t1.main_task)

            ORDER BY max_date DESC NULLS LAST, project_id, task_id, task_responsible_id;""",
            [user_id, user_id]
        )

        tasks = cursor.fetchall()
        pr_list = set()
        task_list = list()  # Список задач без закрытых объектов

        if len(tasks):
            task_number_not_closed = 0
            for i in range(len(tasks)):
                tasks[i] = dict(tasks[i])

                proj_id = tasks[i]['project_id']

                # Для задач указываем объект, для орг работ - не указываем
                if tasks[i]['row_type'] == 'task':
                    if proj_list[proj_id]['project_close_status']:
                        continue

                    tasks[i]['project_full_name'] = proj_list[proj_id]['project_full_name']
                    tasks[i]['project_short_name'] = proj_list[proj_id]['project_short_name']
                else:
                    proj_id = 'org_work'
                    tasks[i]['project_id'] = proj_id
                    tasks[i]['project_full_name'] = ''
                    tasks[i]['project_short_name'] = 'орг'

                j = len(task_list)
                tasks[i]['task_number'] = j + 1
                if tasks[i]['task_class'] == 'tr_task_status_not_closed':
                    task_number_not_closed += 1
                    tasks[i]['task_number_not_closed'] = task_number_not_closed
                calendar_cur_week[0]['hours_per_day'] += tasks[i]['input_task_week_1_day_1'] if (
                    tasks)[i]['input_task_week_1_day_1'] else 0
                calendar_cur_week[1]['hours_per_day'] += tasks[i]['input_task_week_1_day_2'] if (
                    tasks)[i]['input_task_week_1_day_2'] else 0
                calendar_cur_week[2]['hours_per_day'] += tasks[i]['input_task_week_1_day_3'] if (
                    tasks)[i]['input_task_week_1_day_3'] else 0
                calendar_cur_week[3]['hours_per_day'] += tasks[i]['input_task_week_1_day_4'] if (
                    tasks)[i]['input_task_week_1_day_4'] else 0
                calendar_cur_week[4]['hours_per_day'] += tasks[i]['input_task_week_1_day_5'] if (
                    tasks)[i]['input_task_week_1_day_5'] else 0
                calendar_cur_week[5]['hours_per_day'] += tasks[i]['input_task_week_1_day_6'] if (
                    tasks)[i]['input_task_week_1_day_6'] else 0
                calendar_cur_week[6]['hours_per_day'] += tasks[i]['input_task_week_1_day_7'] if (
                    tasks)[i]['input_task_week_1_day_7'] else 0
                pr_list.add((tasks[i]['project_short_name'], proj_id))

                task_list.append(tasks[i])

            # Конвертируем сумму часов в день из float в HH:MM
            for i in calendar_cur_week:
                if i['hours_per_day']:
                    i['hours_per_day_txt'] = '{0:02.0f}:{1:02.0f}'.format(*divmod(i['hours_per_day'] * 60, 60))
                else:
                    i['hours_per_day_txt'] = '0'
        else:
            task_list = False

        # Список дат неотправленных часов
        cursor.execute(
            f"""
            WITH date_series AS (
                {date_series_ls}
            ),
            filtered_dates AS (
                SELECT 
                    date
                FROM 
                    date_series 
                WHERE
                    date IN (SELECT holiday_date FROM list_holidays WHERE holiday_status IS FALSE) OR 
                    (date NOT IN (SELECT holiday_date FROM list_holidays WHERE holiday_status IS TRUE) AND
                    EXTRACT(DOW FROM date) NOT IN (0, 6)) -- Exclude weekends (0 = Sunday, 6 = Saturday)
            )
            SELECT 
                fd.date AS unsent_date
            FROM 
                filtered_dates AS fd
            LEFT JOIN 
                (
                    (SELECT 
                        hotr_date
                    FROM public.hours_of_task_responsible
                    WHERE task_responsible_id IN (
                        SELECT 
                            task_responsible_id 
                        FROM public.task_responsible 
                        WHERE user_id = %s))
                UNION
                    (SELECT 
                        hotr_date
                    FROM public.org_work_hours_of_task_responsible
                    WHERE task_responsible_id IN (
                        SELECT 
                            task_responsible_id 
                        FROM public.org_work_responsible 
                        WHERE user_id = %s))
                ) AS htr 
            ON 
                fd.date = htr.hotr_date 
            WHERE 
                htr.hotr_date IS NULL 
            ORDER BY fd.date
            LIMIT 25;
            """,
            [user_id, user_id]
        )

        unsent_hours_list = cursor.fetchall()

        if len(unsent_hours_list):
            for i in range(len(unsent_hours_list)):
                unsent_hours_list[i] = dict(unsent_hours_list[i])
        else:
            unsent_hours_list = False


        # Список дат несогласованных часов
        cursor.execute(
            f"""
                (
                    (
                    SELECT 
                        hotr_date AS unapproved_date
                    FROM 
                        public.hours_of_task_responsible 
                    WHERE
                        task_responsible_id IN 
                            (SELECT 
                                task_responsible_id 
                            FROM task_responsible 
                            WHERE user_id = %s)
                        AND approved_status IS FALSE
                    GROUP BY unapproved_date
                    )
                UNION
                    (
                    SELECT 
                        hotr_date AS unapproved_date
                    FROM 
                        public.org_work_hours_of_task_responsible
                    WHERE
                        task_responsible_id IN 
                            (SELECT 
                                task_responsible_id 
                            FROM public.org_work_responsible
                            WHERE user_id = %s)
                        AND approved_status IS FALSE
                    GROUP BY unapproved_date
                    )
                )
                ORDER BY unapproved_date 
                LIMIT 25;
                """,
            [user_id, user_id]
        )

        unapproved_hours_list = cursor.fetchall()

        if len(unapproved_hours_list):
            for i in range(len(unapproved_hours_list)):
                unapproved_hours_list[i] = dict(unapproved_hours_list[i])
        else:
            unapproved_hours_list = False

        # Список частично заполненных часов
        if date_series_h_p_d_n != '':
            cursor.execute(
                f"""
                    WITH t1 AS (
                        (
                            SELECT                         
                                hotr_date,
                                SUM(hotr_value) AS hotr_value
                            FROM 
                                public.hours_of_task_responsible
                            WHERE
                                task_responsible_id IN 
                                    (SELECT 
                                        task_responsible_id 
                                    FROM public.task_responsible 
                                    WHERE user_id = %s)
                                {date_series_h_p_d_n}
                            GROUP BY hotr_date
                            HAVING sum(hotr_value) != 8
                            )
                        UNION ALL
                            (
                            SELECT                         
                                hotr_date,
                                SUM(hotr_value) AS hotr_value
                            FROM 
                                public.org_work_hours_of_task_responsible
                            WHERE
                                task_responsible_id IN 
                                    (SELECT 
                                        task_responsible_id 
                                    FROM public.org_work_responsible 
                                    WHERE user_id = %s)
                                {date_series_h_p_d_n}
                            GROUP BY hotr_date
                            HAVING sum(hotr_value) != 8
                            )     
                        )  
					SELECT
                        hotr_date,
                        SUM(hotr_value),
                            to_char(hotr_date, 'yy.mm.dd') || 
                            ' - ' || 
                            COALESCE(to_char(to_timestamp(((SUM(hotr_value)) * 60)::INT), 'MI:SS'), '')  || 
                            'ч.' 
                        AS not_full_hours
					FROM t1
					GROUP BY hotr_date
					HAVING sum(hotr_value) != 8
                    ORDER BY hotr_date 
                    LIMIT 25;
                    """,
                [user_id, user_id]
            )

            not_full_sent_list = cursor.fetchall()

            if len(not_full_sent_list):
                for i in range(len(not_full_sent_list)):
                    not_full_sent_list[i] = dict(not_full_sent_list[i])
            else:
                not_full_sent_list = False
        else:
            not_full_sent_list = False

        # Если нет неотправленных, удаляем себя из списка должников (таблица users_statuses_unsent_hours)
        if not unsent_hours_list and not not_full_sent_list:
            delete_from_users_statuses_unsent_hours(conn, cursor, user_id)
        # Есть только одна неотправленная дата и эта дата - сегодня
        elif (unsent_hours_list and not not_full_sent_list and
              len(unsent_hours_list)==1 and datetime.now().date() == unsent_hours_list[0]['unsent_date']):
            delete_from_users_statuses_unsent_hours(conn, cursor, user_id)
        # Есть только одна частично неотправленная дата и эта дата - сегодня
        elif (not_full_sent_list and not unsent_hours_list and
              len(not_full_sent_list)==1 and datetime.now().date() == not_full_sent_list[0]['hotr_date']):
            delete_from_users_statuses_unsent_hours(conn, cursor, user_id)
        # Есть по одной дате и там, и там и эти даты - сегодня
        elif (not_full_sent_list and unsent_hours_list and
              len(unsent_hours_list)==1 and datetime.now().date() == unsent_hours_list[0]['unsent_date'] and
              len(not_full_sent_list)==1 and datetime.now().date() == not_full_sent_list[0]['hotr_date']):
            delete_from_users_statuses_unsent_hours(conn, cursor, user_id)

        # Список статусов задач
        cursor.execute("""
                            SELECT 
                                * 
                            FROM public.task_statuses
                            ORDER BY task_status_name ASC;
                            """)
        task_statuses = cursor.fetchall()
        status_list = set()

        if task_statuses:
            for i in range(len(task_statuses)):
                task_statuses[i] = dict(task_statuses[i])
                status_list.add((task_statuses[i]['task_status_name'], task_statuses[i]['task_status_id']))
        else:
            flash(message=['Ошибка', 'Не найдены статусы задач', 'Страница недоступна'], category='error')
            return redirect(url_for('app_project.objects_main'))

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        print('pr_list')
        print(pr_list)

        return render_template('task-my-tasks.html', menu=hlink_menu, menu_profile=hlink_profile,
                               nonce=get_nonce(), calendar_cur_week=calendar_cur_week, tasks=task_list,
                               unsent_hours_list=unsent_hours_list, my_tasks_other_period = my_tasks_other_period,
                               unapproved_hours_list=unapproved_hours_list, current_period=current_period,
                               not_full_sent_list=not_full_sent_list, pr_list=pr_list, status_list=status_list,
                               task_statuses=task_statuses, title='Мои задачи')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Сохранение часов, которые отправил сотрудник со страницы my_tasks
@task_app_bp.route('/save_my_tasks', methods=['POST'])
@login_required
def save_my_tasks():
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())

        user_changes_task :dict = request.get_json()['userChangesTask']
        user_changes_work :dict = request.get_json()['userChangesWork']
        calendar = request.get_json()['calendar_cur_week']

        if user_changes_task == {} and user_changes_work == {}:
            return jsonify({
                'status': 'error',
                'description': ['Изменений не найдено'],
            })
        elif calendar == []:
            error_description = 'Ошибка с определением дат календаря'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            return jsonify({
                'status': 'error',
                'description': [error_description],
            })
        calendar_cur_week = dict()
        week_day_class_name = [
            'input_task_week_1_day_1',
            'input_task_week_1_day_2',
            'input_task_week_1_day_3',
            'input_task_week_1_day_4',
            'input_task_week_1_day_5',
            'input_task_week_1_day_6',
            'input_task_week_1_day_7',
        ]
        day_1, day_7 = '', ''
        for i in range(len(calendar)):
            calendar_cur_week[week_day_class_name[i]] = datetime.strptime(calendar[i], '%d.%m.%y').date()
            if i == 0:
                day_1 = calendar_cur_week[week_day_class_name[i]]
            elif i == 6:
                day_7 = calendar_cur_week[week_day_class_name[i]]
        # calendar_cur_week = [datetime.strptime(x, '%d.%m.%y').date() for x in calendar_cur_week]

        tr_status = []  # Список изменения статусов
        tr_comment = []  # Список изменения комментариев
        hours_of_task_responsible = []

        #############################################################################################
        # task. Для task_responsible создаём список task_responsible_id, task_id, user_id
        #############################################################################################
        for task_id, v in user_changes_task.items():
            task_id = int(task_id)
            for task_responsible_id, vv in v.items():
                task_responsible_id = int(task_responsible_id)
                # Список для записи значений для одной записи в task_responsible
                tr_tmp = [
                    task_responsible_id,
                    '',                 # task_status_id / task_responsible_comment
                    user_id,            # owner
                    user_id,            # last_editor
                    task_id
                ]
                for kkk, vvv in vv.items():

                    # Если параметр - столбец из КАЛЕНДАРЯ, добавляем данные для таблицы hours_of_task_responsible
                    if kkk in calendar_cur_week.keys():
                        hours_of_task_responsible.append([
                            task_responsible_id,
                            calendar_cur_week[kkk],     # hotr_date
                            vvv,                        # hotr_value
                            user_id,                    # owner
                            user_id,                    # last_editor
                            task_id,                    # нужен для проверки, в конце сохранения этот элемент удаляется
                        ])
                    elif kkk in ['td_tow_task_statuses', 'input_task_responsible_comment']:
                        if kkk == 'td_tow_task_statuses':
                            tr_tmp[1] = int(vvv) if vvv else 1
                            tr_status.append(tr_tmp)
                        elif kkk == 'input_task_responsible_comment':
                            tr_tmp[1] = vvv
                            tr_comment.append(tr_tmp)


        org_work_tr_status = []  # Список изменения статусов
        org_work_tr_comment = []  # Список изменения комментариев
        org_work_hours_of_task_responsible = []
        org_work_responsible = []  # Для новых tr. Список tr для work
        org_work_new_tr_dict = {}
        sorted_new_tr = []  # Для новых tr. Словарь для замены старых id на новые

        # Список вновь созданных tr_id для проверки, что user_changes не останется не учтённых текстовых id
        org_work_new_tr_set = set()
        #############################################################################################
        # work. Для task_responsible создаём список task_responsible_id, task_id, user_id
        #############################################################################################
        for task_id, v in user_changes_work.items():
            task_id = int(task_id)
            for task_responsible_id, vv in v.items():

                # Если tr не новое, то это числовое значчение.
                # Иначе нужно записать tr в БД и заменить везде временные id новым, из БД
                if str_to_int(task_responsible_id):
                    task_responsible_id = int(task_responsible_id)
                else:
                    tr_tmp_1 = task_id  # task_id
                    tr_tmp_2 = user_id  # user_id
                    tr_tmp_3 = None  # task_status_id - у орг работ нет статуса
                    tr_tmp_4 = vv['input_task_responsible_comment'] if 'input_task_responsible_comment' in vv.keys() \
                        else ''  # task_responsible_comment
                    tr_tmp_5 = user_id  # owner
                    tr_tmp_6 = user_id  # last_editor
                    tr_tmp_7 = None  # task_plan_labor_cost

                    org_work_responsible.append([
                        tr_tmp_1,  # task_id
                        tr_tmp_2,  # user_id
                        2,         # task_status_id
                        tr_tmp_4,  # task_responsible_comment
                        tr_tmp_5,  # owner
                        tr_tmp_6,  # last_editor
                        tr_tmp_7,  # task_plan_labor_cost
                    ])
                    sorted_new_tr.append(task_responsible_id)

                # Список для записи значений для одной записи в task_responsible
                tr_tmp = [
                    task_responsible_id,
                    '',  # task_status_id / task_responsible_comment
                    user_id,  # owner
                    user_id,  # last_editor
                    task_id
                ]
                for kkk, vvv in vv.items():

                    # Если параметр - столбец из КАЛЕНДАРЯ, добавляем данные для табл org_work_hours_of_task_responsible
                    if kkk in calendar_cur_week.keys():
                        org_work_hours_of_task_responsible.append([
                            task_responsible_id,
                            calendar_cur_week[kkk],  # hotr_date
                            vvv,  # hotr_value
                            user_id,  # owner
                            user_id,  # last_editor
                            task_id,  # нужен для проверки, в конце сохранения этот элемент удаляется
                        ])
                    elif kkk in ['td_tow_task_statuses', 'input_task_responsible_comment']:
                        if kkk == 'td_tow_task_statuses':
                            tr_tmp[1] = 2  # Статусы не используем. По умолчанию 2 - в работе
                            org_work_tr_status.append(tr_tmp)
                        elif kkk == 'input_task_responsible_comment':
                            tr_tmp[1] = vvv
                            org_work_tr_comment.append(tr_tmp)

        columns_tr = ('task_id', 'user_id', 'task_status_id', 'task_responsible_comment', 'owner', 'last_editor',
                      'task_plan_labor_cost')
        tr_status_columns = ['task_responsible_id', 'task_status_id', 'owner', 'last_editor']
        tr_comment_columns = ['task_responsible_id', 'task_responsible_comment', 'owner', 'last_editor']
        hotr_insert_columns = ['task_responsible_id', 'hotr_date', 'hotr_value', 'owner', 'last_editor']
        hotr_update_columns = ['hotr_id', 'task_responsible_id', 'hotr_date', 'hotr_value', 'last_editor',
                               'last_edit_at']

        # Если есть новые tr для орг работ
        if len(org_work_responsible):
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('tasks')

            action_new_tr = 'INSERT INTO'
            table_new_tr = 'org_work_responsible'
            subquery_new_tr = " ON CONFLICT DO NOTHING RETURNING task_responsible_id;"

            query_tow = app_payment.get_db_dml_query(action=action_new_tr, table=table_new_tr, columns=columns_tr,
                                                     subquery=subquery_new_tr)
            # print('- - - - - - - - INSERT INTO tasks - - - - - - - -', query_tow, values_new_task, sep='\n')

            execute_values(cursor, query_tow, org_work_responsible, page_size=len(org_work_responsible))
            list_tr_id = cursor.fetchall()

            description = 'Изменения сохранены'

            conn.commit()

            app_login.conn_cursor_close(cursor, conn)
            # Список старых и новых id для вновь созданных task
            org_work_responsible_old = org_work_responsible
            org_work_responsible = dict()
            for i in range(len(list_tr_id)):
                org_work_responsible[list_tr_id[i][0]] = org_work_responsible_old[i]
                org_work_new_tr_dict[sorted_new_tr[i]] = list_tr_id[i][0]
                org_work_new_tr_set.add(list_tr_id[i][0])

            # time.sleep(3)
            # Заменяем временные tr_id на вновь созданные id
            if len(org_work_hours_of_task_responsible):
                for i in org_work_hours_of_task_responsible:
                    if i[0] in org_work_new_tr_dict.keys():
                        i[0] = org_work_new_tr_dict[i[0]]
            if len(org_work_tr_status):
                for i in org_work_tr_status:
                    if i[0] in org_work_new_tr_dict.keys():
                        i[0] = org_work_new_tr_dict[i[0]]

        # Календарь за указанный период
        calendar_cur_week = user_week_calendar(user_id, period_date=day_1, tr_id_is_null=False, task_info=True)
        if calendar_cur_week['status'] == 'error':
            error_description = calendar_cur_week['description']
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            return jsonify({
                'status': calendar_cur_week['status'],
                'description': calendar_cur_week['description'],
            })
        calendar_cur_week, days_lst, tasks, org_works  = (calendar_cur_week['calendar_cur_week'],
                                                          calendar_cur_week['days_lst'],
                                                          calendar_cur_week['task_dict'],
                                                          calendar_cur_week['org_work_dict']
                                                          )

        cwd_dict = dict()
        for i in range(len(calendar_cur_week)):
            cwd_dict[calendar_cur_week[i]['work_day']] = calendar_cur_week[i]
        calendar_cur_week = cwd_dict

        if not tasks and not org_works:
            error_description = 'Не найдено задач пользователя'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description, 'Обновите страницу'],
            })



        # ЧАСЫ
        # ПЕРВОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Проверка, наличия tr у task, tr принадлежит пользователю,
        # не имеет статус закрыта, не имеет approved_status/sent_status
        # ВТОРОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Проверка, если нет статуса почасовой оплаты, то общее кол-во часов в сутки не более 8 часов, иначе не более 24 часов
        # ТРЕТЬЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # уведомить, если отправлено в выходной день
        hotr_insert = []
        hotr_update = []
        hotr_delete = []

        # task
        for i in hours_of_task_responsible:
            input_task_week = False
            hours_per_day = False
            work_day_txt = False
            if i[1] in calendar_cur_week.keys() and i[1] == calendar_cur_week[i[1]]['work_day']:
                input_task_week = calendar_cur_week[i[1]]['input_task_week']
                work_day_txt = calendar_cur_week[i[1]]['work_day']
                # Проверяем, что данные отправлены в рабочий день
                if calendar_cur_week[i[1]]['holiday_status']:
                    error_description = f'Запрещено отправлять часы за выходной день ({work_day_txt})'
                    app_login.set_warning_log(
                        log_url=sys._getframe().f_code.co_name,
                        log_description=f'{error_description}. task_id: {i[-1]} / tr_id: {i[0]}',
                        user_id=user_id,
                        ip_address=app_login.get_client_ip())
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка',
                                        error_description,
                                        'Обновите страницу',
                                        f'Задача: {tasks[i[0]]["task_name"]}',
                                        f'task_id: {i[-1]} / tr_id: {i[0]}'
                                        ],
                    })
            else:
                error_description = 'Ошибка обработки даты. rev-1'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}. task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # ПЕРВОЕ  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # наличия tr у task
            task_tr = True if i[0] in tasks.keys() and tasks[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-1'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    # f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in tasks.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Статус задачи
            rt_status = tasks[i[0]]['task_status_id']
            if rt_status == 4:
                error_description = 'По задачам со статусом "Завершено" нельзя подать часы'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обратитесь к руководителю отдела',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Статус согласования руководителем отдела
            rt_approved_status = tasks[i[0]][input_task_week + '_approved_status']
            if rt_approved_status:
                error_description = (f'Часы за указанную дату ({work_day_txt}) были ранее согласованы руководителем '
                                     f'отдела')
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Повторная отправка запрещена',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Статус согласования ведущим
            rt_sent_status = tasks[i[0]][input_task_week + '_sent_status']
            if rt_sent_status:
                error_description = (f'Часы за указанную дату ({work_day_txt}) были ранее согласованы для отправке '
                                     f'руководителю отдела')
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Повторная отправка запрещена',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # ВТОРОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Проверка на превышение 8 часов если статус почасовой оплаты отсутствует, иначе 24ч

            # пересчитываем общее кол-во часов в указанную дату

            prev_val = float(tasks[i[0]][input_task_week]) if tasks[i[0]][input_task_week] else 0
            calendar_cur_week[i[1]]['hours_per_day'] = float(calendar_cur_week[i[1]]['hours_per_day']) - prev_val + i[2]

            # Удаляем task_id, тк его не записываем в БД (нет такого поля, нужен был только для проверки)
            del i[-1]

            # Если в hours_of_task_responsible есть запись - эту запись обновляем/удаляем, для этого нам нужен hotr_id
            # Добавляем в список hotr_id
            if tasks[i[0]][input_task_week]:
                if not i[2]:
                    hotr_delete.append(
                        tasks[i[0]][input_task_week + '_hotr_id']  # hotr_id
                    )
                else:
                    hotr_update.append([
                        tasks[i[0]][input_task_week + '_hotr_id'],   # hotr_id
                        i[0],                     # task_responsible_id
                        i[1],                     # hotr_date
                        i[2],                     # hotr_value
                        i[4],                     # last_editor
                        datetime.now()            # hotr_value
                    ])
            else:
                hotr_insert.append(i)

        org_work_hotr_insert = []
        org_work_hotr_update = []
        org_work_hotr_delete = []
        # work
        for i in org_work_hours_of_task_responsible:
            input_task_week = False
            hours_per_day = False
            work_day_txt = False
            if i[1] in calendar_cur_week.keys() and i[1] == calendar_cur_week[i[1]]['work_day']:
                input_task_week = calendar_cur_week[i[1]]['input_task_week']
                work_day_txt = calendar_cur_week[i[1]]['work_day']
                # Проверяем, что данные отправлены в рабочий день
                if calendar_cur_week[i[1]]['holiday_status']:
                    error_description = f'Запрещено отправлять часы за выходной день ({work_day_txt})'
                    app_login.set_warning_log(
                        log_url=sys._getframe().f_code.co_name,
                        log_description=f'{error_description}. task_id: {i[-1]} / tr_id: {i[0]}',
                        user_id=user_id,
                        ip_address=app_login.get_client_ip())
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка',
                                        error_description,
                                        'Обновите страницу',
                                        f'Задача: {org_works[i[0]]["task_name"]}',
                                        f'task_id: {i[-1]} / tr_id: {i[0]}'
                                        ],
                    })
            else:
                error_description = 'Ошибка обработки даты. rev-1.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}. task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # ПЕРВОЕ  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # наличия tr у task
            task_tr = True if i[0] in org_works.keys() and org_works[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-1.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in org_works.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю rev-1.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Статус задачи - не проверяем, у орг работ нет статусов
            # rt_status = org_works[i[0]]['task_status_id']
            # if rt_status == 4:
            #     error_description = 'По задачам со статусом "Завершено" нельзя подать часы'
            #     app_login.set_warning_log(
            #         log_url=sys._getframe().f_code.co_name,
            #         log_description=f'{error_description}, '
            #                         f'task_id: {i[-1]} / tr_id: {i[0]}',
            #         user_id=user_id,
            #         ip_address=app_login.get_client_ip())
            #     return jsonify({
            #         'status': 'error',
            #         'description': ['Ошибка',
            #                         error_description,
            #                         'Обратитесь к руководителю отдела',
            #                         f'Задача: {org_works[i[0]]["task_name"]}',
            #                         f'task_id: {i[-1]} / tr_id: {i[0]}'
            #                         ],
            #     })

            # Статус согласования руководителем отдела
            rt_approved_status = org_works[i[0]][input_task_week + '_approved_status']
            if rt_approved_status:
                error_description = (f'Часы за указанную дату ({work_day_txt}) были ранее согласованы руководителем '
                                     f'отдела')
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Повторная отправка запрещена',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Статус согласования ведущим
            rt_sent_status = org_works[i[0]][input_task_week + '_sent_status']
            if rt_sent_status:
                error_description = (f'Часы за указанную дату ({work_day_txt}) были ранее согласованы для отправке '
                                     f'руководителю отдела')
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Повторная отправка запрещена',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # ВТОРОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Проверка на превышение 8 часов если статус почасовой оплаты отсутствует, иначе 24ч

            # пересчитываем общее кол-во часов в указанную дату

            prev_val = float(org_works[i[0]][input_task_week]) if org_works[i[0]][input_task_week] else 0
            calendar_cur_week[i[1]]['hours_per_day'] = float(calendar_cur_week[i[1]]['hours_per_day']) - prev_val + i[2]

            # Удаляем task_id, тк его не записываем в БД (нет такого поля, нужен был только для проверки)
            del i[-1]

            # Если в hours_of_task_responsible есть запись - эту запись обновляем/удаляем, для этого нам нужен hotr_id
            # Добавляем в список hotr_id
            if org_works[i[0]][input_task_week]:
                if not i[2]:
                    org_work_hotr_delete.append(
                        org_works[i[0]][input_task_week + '_hotr_id']  # hotr_id
                    )
                else:
                    org_work_hotr_update.append([
                        org_works[i[0]][input_task_week + '_hotr_id'],  # hotr_id
                        i[0],  # task_responsible_id
                        i[1],  # hotr_date
                        i[2],  # hotr_value
                        i[4],  # last_editor
                        datetime.now()  # hotr_value
                    ])
            else:
                org_work_hotr_insert.append(i)

        #############################################################################################
        # Проверяем сохраняемое на превышение часов за день
        #############################################################################################
        notification = []  # Список сообщений
        for k,v in calendar_cur_week.items():
            if not v['hpdn_status'] and v['hours_per_day'] > 8:
                error_description = f'Нельзя внести более 8 часов в сутки'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, work_day: {v["work_day"]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    f'Дата: {v["work_day_txt"]}',
                                    f'Сумма часов: {float_to_time(v["hours_per_day"])}'
                                    ],
                })
            elif v['hpdn_status'] and v['hours_per_day'] > 24:
                error_description = 'Нельзя внести более 24 часов в сутки'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, work_day: {v["work_day"]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    f'Дата: {v["work_day_txt"]}',
                                    f'Сумма часов: {float_to_time(v["hours_per_day"])}'
                                    ],
                })
            elif v['hpdn_status'] and v['hours_per_day'] > 8:
                if not len(notification):
                    notification.append([f'Обратите внимание:'])
                notification.append([f'За {v["work_day_txt"]} указано {float_to_time(v["hours_per_day"])} ч.'])
            elif not v['hpdn_status'] and v['hours_per_day'] < 8:
                if not len(notification):
                    notification.append([f'Обратите внимание:'])
                notification.append([f'За {v["work_day_txt"]} указано {float_to_time(v["hours_per_day"])} ч.'])

        # task СТАТУСЫ
        for i in tr_status:
            # наличия tr у task
            task_tr = True if i[0] in tasks.keys() and tasks[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in tasks.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })
            # Если статус был "Закрыто" изменение статуса запрещено
            if tasks[i[0]]['task_status_id'] == 4:
                error_description = 'По задачам со статусом "Завершено" нельзя сменить статус'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {tasks[i[0]]["task_id"]} / tr_id: {tasks[i[0]]["task_responsible_id"]}'
                                    ],
                })

            # Удаляем task_id, нужен только для проверки
            del i[-1]

        # task КОММЕНТАРИИ
        for i in tr_comment:
            # наличия tr у task
            task_tr = True if i[0] in tasks.keys() and tasks[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-3'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in tasks.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Удаляем task_id, нужен только для проверки
            del i[-1]

        # work СТАТУСЫ
        for i in org_work_tr_status:
            # наличия tr у task
            task_tr = True if i[0] in org_works.keys() and org_works[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-2.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in org_works.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю rev-2.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })
            # Если статус был "Закрыто" изменение статуса запрещено
            if org_works[i[0]]['task_status_id'] == 4:
                error_description = 'По задачам со статусом "Завершено" нельзя сменить статус rev-2.2'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    f'Задача: {org_works[i[0]]["task_name"]}',
                                    f'task_id: {org_works[i[0]]["task_id"]} / '
                                    f'tr_id: {org_works[i[0]]["task_responsible_id"]}'
                                    ],
                })

            # Удаляем task_id, нужен только для проверки
            del i[-1]

        # work КОММЕНТАРИИ
        for i in org_work_tr_comment:
            # наличия tr у task
            task_tr = True if i[0] in tasks.keys() and tasks[i[0]]['task_id'] == i[-1] else False
            if not task_tr:
                error_description = 'Ошибка при проверке привязки задачи rev-3'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in tasks.keys() else False
            if not tr_user:
                error_description = 'Задача больше не привязана к пользователю'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name,
                    log_description=f'{error_description}, '
                                    f'task_id: {i[-1]} / tr_id: {i[0]}',
                    user_id=user_id,
                    ip_address=app_login.get_client_ip())
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка',
                                    error_description,
                                    'Обновите страницу',
                                    f'Задача: {tasks[i[0]]["task_name"]}',
                                    f'task_id: {i[-1]} / tr_id: {i[0]}'
                                    ],
                })

            # Удаляем task_id, нужен только для проверки
            del i[-1]

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # hotr_insert
        if len(hotr_insert):
            columns_hotr_insert = tuple(hotr_insert_columns)
            action_hotr_insert = 'INSERT INTO'
            query_hotr_insert = app_payment.get_db_dml_query(action=action_hotr_insert,
                                                             table='hours_of_task_responsible',
                                                             columns=columns_hotr_insert)
            execute_values(cursor, query_hotr_insert, hotr_insert)

        # org_work_hotr_insert
        if len(org_work_hotr_insert):
            columns_hotr_insert = tuple(hotr_insert_columns)
            action_hotr_insert = 'INSERT INTO'
            query_hotr_insert = app_payment.get_db_dml_query(action=action_hotr_insert,
                                                             table='org_work_hours_of_task_responsible',
                                                             columns=columns_hotr_insert)
            execute_values(cursor, query_hotr_insert, org_work_hotr_insert)

        # hotr_update
        if len(hotr_update):
            columns_hotr_update = tuple(hotr_update_columns)
            action_hotr_update = 'UPDATE'
            query_hotr_update = app_payment.get_db_dml_query(action=action_hotr_update,
                                                             table='hours_of_task_responsible',
                                                             columns=columns_hotr_update)
            execute_values(cursor, query_hotr_update, hotr_update)

        # org_work_hotr_update
        if len(org_work_hotr_update):
            columns_hotr_update = tuple(hotr_update_columns)
            action_hotr_update = 'UPDATE'
            query_hotr_update = app_payment.get_db_dml_query(action=action_hotr_update,
                                                             table='org_work_hours_of_task_responsible',
                                                             columns=columns_hotr_update)
            execute_values(cursor, query_hotr_update, org_work_hotr_update)

        # hotr_delete
        if len(hotr_delete):
            action_hotr_delete = 'DELETE'
            query_hotr_delete = app_payment.get_db_dml_query(action=action_hotr_delete,
                                                             table='hours_of_task_responsible',
                                                             columns='hotr_id::int')
            execute_values(cursor, query_hotr_delete, (hotr_delete,))

        # org_work_hotr_delete
        if len(org_work_hotr_delete):
            action_hotr_delete = 'DELETE'
            query_hotr_delete = app_payment.get_db_dml_query(action=action_hotr_delete,
                                                             table='org_work_hours_of_task_responsible',
                                                             columns='hotr_id::int')
            execute_values(cursor, query_hotr_delete, (org_work_hotr_delete,))

        # tr_status
        if len(tr_status):
            columns_tr_status = tuple(tr_status_columns)
            action_tr_status = 'UPDATE'
            query_tr_status = app_payment.get_db_dml_query(action=action_tr_status,
                                                             table='task_responsible',
                                                             columns=columns_tr_status)
            execute_values(cursor, query_tr_status, tr_status)

        # tr_comment
        if len(tr_comment):
            columns_tr_comment = tuple(tr_comment_columns)
            action_tr_comment = 'UPDATE'
            query_tr_comment = app_payment.get_db_dml_query(action=action_tr_comment,
                                                           table='task_responsible',
                                                           columns=columns_tr_comment)
            execute_values(cursor, query_tr_comment, tr_comment)

        if (len(hotr_insert) or len(hotr_update) or len(hotr_delete) or len(tr_status) or len(tr_comment)
                or len(org_work_hotr_insert) or len(org_work_hotr_update) or len(org_work_hotr_delete)):
            conn.commit()

        app_login.conn_cursor_close(cursor, conn)


        flash(message=['Изменения сохранены'], category='success')

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


# Загружаем другой период задач сотрудника
@task_app_bp.route('/get_my_tasks_other_period/<other_period_date>', methods=['GET'])
@login_required
def get_my_tasks_other_period(other_period_date):
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name,
                               log_description=other_period_date, user_id=user_id, ip_address=app_login.get_client_ip())

        # Конвертируем дату
        if other_period_date.find('-W') >= 0:
            year, week = map(int, other_period_date.split('-W'))
            other_period_date = date.fromisocalendar(year, week, 1)
            today = date.today()
            day_0 = other_period_date - timedelta(days=other_period_date.weekday())
            day_6 = other_period_date + timedelta(days=6-other_period_date.weekday())
            days_lst = [other_period_date - timedelta(days=other_period_date.weekday()-x) for x in range(0, 7)]
        else:
            other_period_date = datetime.strptime(other_period_date, '%Y-%m-%d').date()
            day_0 = other_period_date - timedelta(days=other_period_date.weekday())
            day_6 = other_period_date + timedelta(days=6-other_period_date.weekday())

        # Список: дата недели, первый день недели, последний день недели
        current_period = [other_period_date.strftime("%Y-W%V"), str(day_0), str(day_6)]

        # Календарь пользователя со статусами почасовой оплаты, отпусков, статуса подачи часов и Список из 7 дат недели
        calendar_cur_week = user_week_calendar(user_id, other_period_date)
        if calendar_cur_week['status'] == 'error':
            return jsonify({
                'status': calendar_cur_week['status'],
                'description': calendar_cur_week['description'],
            })
        calendar_cur_week, days_lst, tasks = (calendar_cur_week['calendar_cur_week'],
                                              calendar_cur_week['days_lst'],
                                              calendar_cur_week['task_dict'])

        return jsonify({
            'calendar_cur_week': calendar_cur_week,
            'tasks': tasks,
            'current_period': current_period,
            'status': 'success'
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': [msg_for_user],
        })


# Страница отправки часов ведущим руководителю (страница проверки часов)
@task_app_bp.route('/check_hours', methods=['GET'])
@task_app_bp.route('/check_hours/<unsent_first_date>', methods=['GET'])
@login_required
def check_hours(unsent_first_date=''):
    """Страница отправки часов ведущим руководителю (страница проверки часов)"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())

        # unsent_first_date - дата первых не отправленных часов
        if unsent_first_date:
            try:
                datetime.strptime(unsent_first_date, '%Y-%m-%d').date()
            except Exception as e:
                flash(message=['Ошибка',
                               f'Указана неверная дата: {unsent_first_date}',
                               'Страница обновлена'], category='error')
                return redirect(url_for('.check_hours'))

            unsent_first_date = datetime.strptime(unsent_first_date, '%Y-%m-%d').date()

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = app_login.current_user.is_head_of_dept()
        # Статус, что у рукотдела нет ГАПов ни в одном подотделе
        is_head_of_dept_without_approval = False

        # Статус, является ли пользователь руководителем отдела
        is_approving_hotr = FDataBase(conn).is_approving_hotr(user_id)

        if not is_head_of_dept and not is_approving_hotr:
            flash(message=['Ошибка', 'Страница доступна только для руководителей отделов'], category='error')
            return redirect(url_for('app_project.objects_main'))
        elif is_head_of_dept and is_approving_hotr:
            flash(message=[
                'Ошибка',
                'Запрещено быть и руководителем отдела, и иметь возможность отправлять часы руководителю отдела',
                'Обратитесь к администратору сайта'
            ], category='error')
            return redirect(url_for('app_project.objects_main'))

        # 1. Находим список сотрудников отдела.
        #   1.1. Находим список отделов, по нему найдём список сотрудников
        # 2. По этим сотрудникам ищем все несогласованные часы
        # 3. Формируем список сотрудников, если нужно выбрать часы по конкретному сотруднику
        # 4. Так же находим все даты не отправленных часов, несогласованных часов, не полностью отправленных

        ######################################################################################
        # 1. Находим список сотрудников отдела.
        ######################################################################################
        if is_head_of_dept:
            is_head_of_dept = tuple(is_head_of_dept)

            cursor.execute(
                f"""
                    WITH RECURSIVE ParentHierarchy AS (
                        SELECT child_id, parent_id, 1 AS level, child_id AS main_id
                        FROM public.dept_relation
                        WHERE parent_id IS NOT NULL
                    
                        UNION ALL
                    
                        SELECT dr.child_id, dr.parent_id, ph.level + 1, ph.main_id
                        FROM public.dept_relation dr
                        JOIN ParentHierarchy ph ON dr.child_id = ph.parent_id
                    )
                    SELECT 
                        ld.dept_id,
                        ld.dept_short_name,
                        lg.group_id,
                        lg.group_name,
                        lg.group_short_name,
                        t3.approving_user_id
                    FROM ParentHierarchy AS ph
                    LEFT JOIN public.list_dept AS ld ON ph.child_id = ld.dept_id
                    LEFT JOIN (
                            SELECT 
                                dept_id AS group_id,
                                dept_name AS group_name,
                                dept_short_name AS group_short_name,
                                head_of_dept_id AS head_of_group_id
                            FROM public.list_dept
                    ) AS lg ON ph.main_id = lg.group_id
                    LEFT JOIN (
                            SELECT 
                                dept_id AS group_id,
                                user_id AS approving_user_id
                            FROM public.users_approving_hotr
                    ) AS t3 ON ph.main_id = t3.group_id
                    WHERE ph.parent_id IN %s OR lg.group_id IN %s
                    
                    UNION
                    
                    SELECT 
                        dr2.child_id AS dept_id,
                        lg2.dept_short_name,
                        dr2.child_id AS group_id,
                        lg2.dept_name AS group_name,
                        lg2.dept_short_name AS group_short_name,
                        t3.approving_user_id
                    FROM public.dept_relation AS dr2
                    LEFT JOIN (
                            SELECT 
                                dept_id,
                                dept_name,
                                dept_short_name,
                                head_of_dept_id
                            FROM public.list_dept
                    ) AS lg2 ON dr2.child_id = lg2.dept_id
                    LEFT JOIN (
                            SELECT 
                                dept_id AS group_id,
                                user_id AS approving_user_id
                            FROM public.users_approving_hotr
                    ) AS t3 ON dr2.child_id = t3.group_id
                    WHERE dr2.parent_id IN %s OR dr2.child_id IN %s
                    
                    ORDER BY group_id
                    """,
                [is_head_of_dept, is_head_of_dept, is_head_of_dept, is_head_of_dept]
            )
        else:
            is_approving_hotr = tuple(is_approving_hotr[0])

            cursor.execute(
                f"""
                                WITH RECURSIVE ParentHierarchy AS (
                                    SELECT child_id, parent_id, 1 AS level, child_id AS main_id
                                    FROM public.dept_relation
                                    WHERE parent_id IS NOT NULL

                                    UNION ALL

                                    SELECT dr.child_id, dr.parent_id, ph.level + 1, ph.main_id
                                    FROM public.dept_relation dr
                                    JOIN ParentHierarchy ph ON dr.child_id = ph.parent_id
                                )
                                SELECT 
                                    ld.dept_id,
                                    ld.dept_short_name,
                                    lg.group_id,
                                    lg.group_name,
                                    lg.group_short_name,
                                    t3.approving_user_id
                                FROM ParentHierarchy AS ph
                                LEFT JOIN public.list_dept AS ld ON ph.child_id = ld.dept_id
                                LEFT JOIN (
                                        SELECT 
                                            dept_id AS group_id,
                                            dept_name AS group_name,
                                            dept_short_name AS group_short_name,
                                            head_of_dept_id AS head_of_group_id
                                        FROM public.list_dept
                                ) AS lg ON ph.main_id = lg.group_id
                                LEFT JOIN (
                                        SELECT 
                                            dept_id AS group_id,
                                            user_id AS approving_user_id
                                        FROM public.users_approving_hotr
                                ) AS t3 ON ph.main_id = t3.group_id
                                WHERE ph.parent_id IN %s OR lg.group_id IN %s

                                UNION

                                SELECT 
                                    dr2.child_id AS dept_id,
                                    lg2.dept_short_name,
                                    dr2.child_id AS group_id,
                                    lg2.dept_name AS group_name,
                                    lg2.dept_short_name AS group_short_name,
                                    t3.approving_user_id
                                FROM public.dept_relation AS dr2
                                LEFT JOIN (
                                        SELECT 
                                            dept_id,
                                            dept_name,
                                            dept_short_name,
                                            head_of_dept_id
                                        FROM public.list_dept
                                ) AS lg2 ON dr2.child_id = lg2.dept_id
                                LEFT JOIN (
                                        SELECT 
                                            dept_id AS group_id,
                                            user_id AS approving_user_id
                                        FROM public.users_approving_hotr
                                ) AS t3 ON dr2.child_id = t3.group_id
                                WHERE dr2.parent_id IN %s OR dr2.child_id IN %s

                                ORDER BY group_id
                                """,
                [is_approving_hotr, is_approving_hotr, is_approving_hotr, is_approving_hotr]
            )
        dept_list = cursor.fetchall()
        dept_set = set()
        if dept_list:
            for i in range(len(dept_list)):
                dept_list[i] = dict(dept_list[i])
                dept_set.add(dept_list[i]['group_id'])
                if not dept_list[i]['approving_user_id']:
                    is_head_of_dept_without_approval = True
            is_head_of_dept_without_approval = False if not is_head_of_dept else is_head_of_dept_without_approval
        else:
            flash(message=['ОШИБКА. Не удалось определить подчиняемые отделы'], category='error')
            return redirect(url_for('app_project.objects_main'))
        print('dept_list')
        print(dept_list)
        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        ######################################################################################
        #   1.1. Находим список отделов, по нему найдём список сотрудников
        # 2. По этим сотрудникам ищем все несогласованные часы
        ######################################################################################
        start_date = date.today() if not unsent_first_date else unsent_first_date
        unsent_first_date = date.today() if not unsent_first_date else unsent_first_date
        users_short_full_name_list = dict() # Словарь user_id, ФИО сотрудников
        # years = 1
        # days_per_year = 365.2425
        # start_date = start_date - timedelta(days=(years * days_per_year + 1))
        start_date = start_date - timedelta(days=1000)
        end_date = date.today()

        cursor.execute(
            USER_LABOR_DATE_LIST,
            [tuple(dept_set)]
        )
        user_labor_date_list = cursor.fetchall()

        # Списки с незаполненными, неотправленными, не согласованными датами
        un_hotr = dict() #  Словарь дата - кол-во ФИО
        # incomplete_hotr = list() #  Частично заполненные часы сотрудниками

        # Не отправленные (не согласованных ГАПом) часы
        unsent_hotr = dict() #  Словарь дата - кол-во ФИО
        unsent_user_id = set()  # id сотрудников
        unsent_date = set()  # даты

        # Не согласованные часы
        unapproved_hotr = dict() #  Словарь дата - кол-во ФИО
        unapproved_user_id = set()  # id сотрудников Не согласованные часы
        unapproved_date = set()  # даты Не согласованные часы
        unapproved_first_date = ''  # дата первых не отправленных часов Не согласованные часы

        # Словарь с датами для календаря
        if is_head_of_dept:
            unapproved_first_date = date.today() if not unsent_first_date else unsent_first_date
            calendar_for_month = get_calendar_for_month(unapproved_first_date)
            if not calendar_for_month['status']:
                flash(message=['Ошибка', calendar_for_month['description']], category='error')
                return redirect(url_for('app_project.objects_main'))
            calendar_for_month, calendar_first_monday, calendar_last_sunday, cur_month_title = (
                calendar_for_month['date_weekday_dict'], calendar_for_month['first_monday'],
                calendar_for_month['last_sunday'], calendar_for_month['cur_month_title'])
        else:
            calendar_for_month = get_calendar_for_month(unsent_first_date)
            if not calendar_for_month['status']:
                flash(message=['Ошибка', calendar_for_month['description']], category='error')
                return redirect(url_for('app_project.objects_main'))
            calendar_for_month, calendar_first_monday, calendar_last_sunday, cur_month_title = (
                calendar_for_month['date_weekday_dict'], calendar_for_month['first_monday'],
                calendar_for_month['last_sunday'], calendar_for_month['cur_month_title'])

        if len(user_labor_date_list):
            for i in range(len(user_labor_date_list)):
                user_labor_date_list[i] = dict(user_labor_date_list[i])

                # print(i, user_labor_date_list[i])

                usr_id = user_labor_date_list[i]['user_id']
                usr_name = user_labor_date_list[i]['short_full_name']
                usr_date = user_labor_date_list[i]['labor_date']

                # Добавляем ФИО в словарь
                users_short_full_name_list[user_labor_date_list[i]['user_id']] = usr_name

                # Не заполненные часы сотрудниками
                if not user_labor_date_list[i]['total_hotr']:
                    if usr_date in un_hotr.keys():
                        un_hotr[usr_date].add((usr_id, usr_name, '8 часов'))
                    elif len(un_hotr.keys()) < 25:
                        un_hotr[usr_date] = {(usr_id, usr_name, '8 часов')}
                    # Для календаря
                    if usr_date in calendar_for_month.keys():
                        calendar_for_month[usr_date]['un_hotr'] += 1


                # Частично заполненные часы сотрудниками
                if (user_labor_date_list[i]['full_day_status'] and
                        user_labor_date_list[i]['total_hotr'] and user_labor_date_list[i]['total_hotr'] != 8):
                    # incomplete_hotr.append([usr_id, usr_date, usr_name])
                    if usr_date in un_hotr.keys():
                        un_hotr[usr_date].add((usr_id, usr_name, 'Частично'))
                    elif len(un_hotr.keys()) < 25:
                        un_hotr[usr_date] = {(usr_id, usr_name, 'Частично')}

                    # Для календаря
                    if usr_date in calendar_for_month.keys():
                        calendar_for_month[usr_date]['un_hotr'] += 1

                # Не отправленные (не согласованных ГАПом) часы
                if (user_labor_date_list[i]['total_hotr'] and
                        user_labor_date_list[i]['unapproved_hotr'] not in (None, 0)):
                    unsent_user_id.add(usr_id)
                    unsent_date.add(usr_date)

                    if usr_date in unsent_hotr.keys():
                        unsent_hotr[usr_date].add((usr_id, usr_name))
                    elif len(unsent_hotr.keys()) < 25:
                        unsent_hotr[usr_date] = {(usr_id, usr_name)}
                    # Для календаря
                    if usr_date in calendar_for_month.keys():
                        # Для ГАПа используем основной счётчик, для рукотдела,
                        # второй счётчик, для несогласованных ГАПом часов
                        if is_approving_hotr:
                            calendar_for_month[usr_date]['unsent_hotr'] += 1
                        else:
                            pass
                            calendar_for_month[usr_date]['unsent_hotr_hide'].append(usr_id)

                # Не согласованные часы
                if (user_labor_date_list[i]['total_hotr'] and
                        user_labor_date_list[i]['unsent_hotr'] not in (None, 0)):

                    unapproved_user_id.add(usr_id)
                    unapproved_date.add(usr_date)
                    if usr_date in unapproved_hotr.keys():
                        unapproved_hotr[usr_date].add((usr_id, usr_name))
                    elif len(unapproved_hotr.keys()) < 25:
                        unapproved_hotr[usr_date] = {(usr_id, usr_name)}
                    # Для календаря
                    if usr_date in calendar_for_month.keys() and is_head_of_dept:
                        calendar_for_month[usr_date]['unsent_hotr'] += 1
                        calendar_for_month[usr_date]['unsent_hotr_hide'].append(usr_id)

        # Упорядочиваем фамилии не отправленных сотрудников
        for k in un_hotr.keys():
            k_weekday = k.weekday()
            k_week_name = DAYS_OF_THE_WEEK_FULL[k_weekday]
            un_hotr[k] = [sorted(un_hotr[k], key=lambda x: x[1]), k_week_name]
        # Если есть Не отправленные (не согласованных ГАПом) часы
        unsent_user = set() # Список ФИО - id для выпадающего списка поиска
        unsent_user_hide = set() # Для рук отдела Список ФИО - id для выпадающего списка поиска
        first_date = {
            'unsent_first_date': '',
            'day_week_first_date': '',
            'work_day_txt': '',
        }
        unsent_hotr_list = list()
        pr_list = set()
        pr_list_hide = set()  # Для рук отдела список объектов, если захочет сам отправить
        unapproved_hotr_list = list()
        unapproved_hotr_list_hide = list()  # Для рук отдела список несогласованных ГАПом часов, если захочет сам отправить

        if len(unsent_hotr) and is_approving_hotr:
            # Список объектов
            proj_list = app_project.get_proj_list()
            if proj_list[0] == 'error':
                flash(message=proj_list[1], category='error')
                return redirect(url_for('app_project.objects_main'))
            elif not proj_list[1]:
                flash(message=['Ошибка', 'Страница недоступна', 'Список проектов пуст'], category='error')
                return redirect(url_for('app_project.objects_main'))
            proj_list = proj_list[2]

            #Данные для календаря
            day_week_first_date = unsent_first_date.weekday()
            day_week_full_day_week_name = DAYS_OF_THE_WEEK_FULL[day_week_first_date]
            day_week_first_date = DAYS_OF_THE_WEEK[day_week_first_date]
            work_day_txt = unsent_first_date.strftime("%d.%m.%y")

            first_date = {
                'unsent_first_date': unsent_first_date,
                'day_week_first_date': day_week_first_date,
                'day_week_full_day_week_name': day_week_full_day_week_name,
                'work_day_txt': work_day_txt,
                'previous_month': unsent_first_date - relativedelta(months=1),
                'next_month': unsent_first_date + relativedelta(months=1),
                'cur_month_title': cur_month_title,
            }
            print(100, [tuple(unsent_user_id), unsent_first_date, tuple(unsent_user_id), unsent_first_date])
            # Список не согласованных ГАПом часов
            cursor.execute(
                UNAPPROVED_HOTR_LIST,
                [tuple(unsent_user_id), unsent_first_date, tuple(unsent_user_id), unsent_first_date]
            )
            unsent_hotr_list = cursor.fetchall()

            if unsent_hotr_list:
                for i in range(len(unsent_hotr_list)):
                    unsent_hotr_list[i] = dict(unsent_hotr_list[i])

                    proj_id = unsent_hotr_list[i]['project_id']

                    # Добавляем данные о проекте. Только у задач, не у орг работ
                    if unsent_hotr_list[i]['row_type'] == 'task':
                        unsent_hotr_list[i]['project_full_name'] = proj_list[proj_id]['project_full_name']
                        unsent_hotr_list[i]['project_short_name'] = proj_list[proj_id]['project_short_name']
                    else:
                        proj_id = 'org_work'
                        unsent_hotr_list[i]['project_id'] = proj_id
                        unsent_hotr_list[i]['project_full_name'] = ''
                        unsent_hotr_list[i]['project_short_name'] = 'орг'

                    pr_list.add((unsent_hotr_list[i]['project_short_name'], proj_id))

                    # Добавляем ФИО
                    unsent_hotr_list[i]['short_full_name'] = users_short_full_name_list[unsent_hotr_list[i]['user_id']]

                    unsent_user.add((unsent_hotr_list[i]['short_full_name'], unsent_hotr_list[i]['user_id']))

        # Если есть Не согласованные часы
        elif is_head_of_dept:

            # Список объектов
            proj_list = app_project.get_proj_list()
            if proj_list[0] == 'error':
                flash(message=proj_list[1], category='error')
                return redirect(url_for('app_project.objects_main'))
            elif not proj_list[1]:
                flash(message=['Ошибка', 'Страница недоступна', 'Список проектов пуст'], category='error')
                return redirect(url_for('app_project.objects_main'))
            proj_list = proj_list[2]

            #Данные для календаря
            day_week_first_date = unapproved_first_date.weekday()
            day_week_full_day_week_name = DAYS_OF_THE_WEEK_FULL[day_week_first_date]
            day_week_first_date = DAYS_OF_THE_WEEK[day_week_first_date]
            work_day_txt = unapproved_first_date.strftime("%d.%m.%y")

            first_date = {
                'unsent_first_date': unapproved_first_date,
                'day_week_first_date': day_week_first_date,
                'day_week_full_day_week_name': day_week_full_day_week_name,
                'work_day_txt': work_day_txt,
                'previous_month': unapproved_first_date - relativedelta(months=1),
                'next_month': unapproved_first_date + relativedelta(months=1),
                'cur_month_title': cur_month_title,
            }

            unapproved_user_id = unapproved_user_id if unapproved_user_id else unsent_user_id
            # Список не согласованных руком часов
            cursor.execute(
                UNSENT_HOTR_LIST,
                [tuple(unapproved_user_id), unapproved_first_date, tuple(unapproved_user_id), unapproved_first_date]
            )
            unapproved_hotr_list = cursor.fetchall()
            set_unapproved = set()  # Список id чтобы не задвоились часы из UNAPPROVED_HOTR_LIST

            if unapproved_hotr_list:
                for i in range(len(unapproved_hotr_list)):
                    unapproved_hotr_list[i] = dict(unapproved_hotr_list[i])

                    proj_id = unapproved_hotr_list[i]['project_id']

                    # Добавляем данные о проекте. Только у задач, не у орг работ
                    if unapproved_hotr_list[i]['row_type'] == 'task':
                        unapproved_hotr_list[i]['project_full_name'] = proj_list[proj_id]['project_full_name']
                        unapproved_hotr_list[i]['project_short_name'] = proj_list[proj_id]['project_short_name']
                    else:
                        proj_id = 'org_work'
                        unapproved_hotr_list[i]['project_id'] = proj_id
                        unapproved_hotr_list[i]['project_full_name'] = ''
                        unapproved_hotr_list[i]['project_short_name'] = 'орг'

                    pr_list.add((unapproved_hotr_list[i]['project_short_name'], proj_id))

                    # Добавляем ФИО
                    unapproved_hotr_list[i]['short_full_name'] = (
                        users_short_full_name_list)[unapproved_hotr_list[i]['user_id']]

                    set_unapproved.add((
                        unapproved_hotr_list[i]['row_type'],
                        unapproved_hotr_list[i]['task_id'],
                        unapproved_hotr_list[i]['task_responsible_id']
                    ))

            # Список не согласованных ГАПом часов
            print(200, [tuple(unsent_user_id), unsent_first_date, tuple(unsent_user_id), unsent_first_date])
            cursor.execute(
                UNAPPROVED_HOTR_LIST,
                [tuple(unsent_user_id), unsent_first_date, tuple(unsent_user_id), unsent_first_date]
            )
            unapproved_hotr_list_hide = cursor.fetchall()

            if unapproved_hotr_list_hide:
                for i in range(len(unapproved_hotr_list_hide)):
                    unapproved_hotr_list_hide[i] = dict(unapproved_hotr_list_hide[i])

                    is_same_row = (
                        unapproved_hotr_list_hide[i]['row_type'],
                        unapproved_hotr_list_hide[i]['task_id'],
                        unapproved_hotr_list_hide[i]['task_responsible_id']
                    )
                    if is_same_row in set_unapproved:
                        unapproved_hotr_list_hide[i] = ''
                        continue

                    proj_id = unapproved_hotr_list_hide[i]['project_id']

                    # Добавляем данные о проекте. Только у задач, не у орг работ
                    if unapproved_hotr_list_hide[i]['row_type'] == 'task':
                        unapproved_hotr_list_hide[i]['project_full_name'] = proj_list[proj_id]['project_full_name']
                        unapproved_hotr_list_hide[i]['project_short_name'] = proj_list[proj_id]['project_short_name']
                    else:
                        proj_id = 'org_work'
                        unapproved_hotr_list_hide[i]['project_id'] = proj_id
                        unapproved_hotr_list_hide[i]['project_full_name'] = ''
                        unapproved_hotr_list_hide[i]['project_short_name'] = 'орг'

                    pr_list_hide.add((unapproved_hotr_list_hide[i]['project_short_name'], proj_id))
                    pr_list.add((unapproved_hotr_list_hide[i]['project_short_name'], proj_id))

                    # Добавляем ФИО
                    unapproved_hotr_list_hide[i]['short_full_name'] = users_short_full_name_list[
                        unapproved_hotr_list_hide[i]['user_id']]

                    unsent_user_hide.add((
                        unapproved_hotr_list_hide[i]['short_full_name'],
                        unapproved_hotr_list_hide[i]['user_id']
                    ))

                print('len:', len(unapproved_hotr_list_hide), '_unapproved_hotr_list_hide', unapproved_hotr_list_hide)

                # Проходим повторно и удаляем пустые строки
                for i in range(len(unapproved_hotr_list_hide[:])-1, -1, -1):
                    if not unapproved_hotr_list_hide[i]:
                        unapproved_hotr_list_hide.pop(i)

        # Список статусов задач
        cursor.execute("""
                            SELECT 
                                * 
                            FROM public.task_statuses
                            ORDER BY task_status_name ASC;
                            """)
        task_statuses = cursor.fetchall()
        status_list = set()

        if task_statuses:
            for i in range(len(task_statuses)):
                task_statuses[i] = dict(task_statuses[i])
                status_list.add((task_statuses[i]['task_status_name'], task_statuses[i]['task_status_id']))
        else:
            flash(message=['Ошибка', 'Не найдены статусы задач', 'Страница недоступна'], category='error')
            return redirect(url_for('app_project.objects_main'))

        app_login.conn_cursor_close(cursor, conn)

        #Для календаря, добавляем класс не проверено, если были найдены несогласованные часы
        for k,v in calendar_for_month.items():
            if not v['unsent_hotr'] and not v['un_hotr']:
                v['unsent_hotr'] = '' if not v['unsent_hotr'] else v['unsent_hotr']
                v['un_hotr'] = '' if not v['un_hotr'] else v['un_hotr']

            # Для рукотдела, если есть непроверенные ГАПом часы и если к отделу привязан ГАП,
            # то добавляем счётчик непроверенное ГАПом и проверенное ГАПом
            v['unsent_hotr_hide'] = set(v['unsent_hotr_hide'])
            v['unsent_hotr_hide'].discard('')
            v['unsent_hotr_hide'] = len(v['unsent_hotr_hide'])
            if not v['un_hotr'] and not v['unsent_hotr_hide']:
                v['unsent_hotr_hide'] = ''

            # Для рукотдела, если не привязан ГАП, в счетчике отображаем и проверенное и не проверенное ГАПом
            v['unsent_hotr'] = v['unsent_hotr_hide'] if is_head_of_dept_without_approval else v['unsent_hotr']

            # Добавляем стиль ОРАНЖЕВЫЙ КРУГ если есть что-то не отправленное
            if v['unsent_hotr'] and len(v['circle_class'].split(' ')) == 1:
                v['circle_class'] += ' unsent_day'

            if v['unsent_hotr_hide'] and len(v['circle_class'].split(' ')) == 1:
                v['circle_class'] += ' unsent_day_hotr_hide'

        # Список объектов
        proj_list = app_project.get_proj_list()
        if proj_list[0] == 'error':
            flash(message=proj_list[1], category='error')
            return redirect(url_for('app_project.objects_main'))
        elif not proj_list[1]:
            flash(message=['Ошибка', 'Страница недоступна', 'Список проектов пуст'], category='error')
            return redirect(url_for('app_project.objects_main'))
        proj_list = proj_list[2]

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()

        # Для рукотдела для кнопки скрыть/показать непроверенное список дат с учетом непроверенного
        unsent_hotr_hide = []

        if is_head_of_dept:
            print('1 unsent_hotr')
            print(unsent_hotr)
            print('1 unapproved_hotr')
            print(unapproved_hotr)
            unsent_hotr_copy = unsent_hotr.copy()
            unapproved_hotr_copy = unapproved_hotr.copy()

            for k, v in unsent_hotr_copy.items():
                if k in unapproved_hotr_copy.keys():
                    z = unsent_hotr_copy[k].union(unapproved_hotr_copy[k])
                    unsent_hotr_copy[k] = z
                    del unapproved_hotr_copy[k]
            unsent_hotr_copy.update(unapproved_hotr_copy)

            if is_head_of_dept_without_approval:
                unsent_hotr_list = unapproved_hotr_list + unapproved_hotr_list_hide
                # Для календаря и списка неотправленного объединяем два словаря с датами
                unsent_hotr = unsent_hotr_copy

                unapproved_hotr_list_hide = []


            else:
                unsent_hotr_list = unapproved_hotr_list
                unsent_hotr = unapproved_hotr
                unsent_hotr_hide = unsent_hotr_copy

            print('2 unsent_hotr')
            print(unsent_hotr)
            print('2 unapproved_hotr')
            print(unapproved_hotr)


        return render_template('task-check-hours.html', menu=hlink_menu, menu_profile=hlink_profile,
                               nonce=get_nonce(),
                               un_hotr=un_hotr,
                               unsent_hotr=unsent_hotr,
                               unsent_hotr_hide=unsent_hotr_hide,
                               unapproved_hotr=unapproved_hotr,
                               first_date=first_date,
                               unsent_hotr_list=unsent_hotr_list,
                               unapproved_hotr_list_hide = unapproved_hotr_list_hide,
                               unsent_user=unsent_user,
                               unsent_user_hide=unsent_user_hide,
                               calendar_for_month=calendar_for_month,
                               pr_list=pr_list,
                               pr_list_hide=pr_list_hide,
                               status_list=status_list,
                               task_statuses=task_statuses,
                               is_head_of_dept=is_head_of_dept,
                               is_head_of_dept_without_approval=is_head_of_dept_without_approval,





                               # calendar_cur_week='calendar_cur_week',
                               # tasks='task_list',
                               # unsent_hours_list='unsent_hours_list',
                               # my_tasks_other_period = 'my_tasks_other_period',
                               # unapproved_hours_list='unapproved_hours_list',
                               # current_period='current_period',
                               # not_full_sent_list='not_full_sent_list',
                               title='Проверка часов')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())

# Сохранение часов, которые проверили со страницы check_hours
@task_app_bp.route('/save_check_hours', methods=['POST'])
@login_required
def save_check_hours():
    try:
        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())

        user_changes_task: dict = request.get_json()['userChangesTask']
        user_changes_work: dict = request.get_json()['userChangesWork']
        current_day = request.get_json()['currentDay']
        is_save = request.get_json()['isSave'] # Согласование или аннулирование часов

        # Данные для сверки актуальности статуса рук отдела/ГАП. Полученное с frontend сверяем с тем, что в БД
        is_head_of_dept = request.get_json()['is_head_of_dept']

        # Изменений не обнаружено
        if user_changes_task == {} and user_changes_work == {}:
            error_description = 'Изменений не найдено'
            flash(message=['Ошибка', error_description], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Изменений не найдено'],
            })
        # Не указана дата по которым согласовываются часы
        if current_day == []:
            error_description = 'Ошибка с определением дат календаря'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=[error_description], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description, 'Обновите страницу'],
            })
        # Нет данных о рукотделе/ГАПе
        elif is_head_of_dept == '':
            error_description = 'Не удалось определить роль "проверяющий часы"/"руководитель отдела"'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=['Ошибка', error_description], category='error')
            return jsonify({
                'status': 'error',
                'description': [
                    'Ошибка', 'Не удалось определить роль', '"проверяющий часы"/"руководитель отдела"',
                    'Обновите страницу'
                ],
            })

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept_db = app_login.current_user.is_head_of_dept()

        # Статус, является ли пользователь руководителем отдела
        is_approving_hotr = FDataBase(conn).is_approving_hotr(user_id)

        app_login.conn_cursor_close(cursor, conn)

        print('user_changes_task', user_changes_task)

        print('user_changes_work', user_changes_work)

        print('current_day', current_day)

        print('is_save', is_save)

        print('is_head_of_dept', type(is_head_of_dept), is_head_of_dept, is_head_of_dept != 'None')

        print('_ ' * 20)

        print('is_head_of_dept_db', type(is_head_of_dept_db), is_head_of_dept_db, is_head_of_dept_db != None)

        print('is_approving_hotr', is_approving_hotr)

        # Пользователь ни рукотдела, ни ГАП
        if not is_head_of_dept_db and not is_approving_hotr:
            error_description = 'Страница доступна только для руководителей отделов'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=['Ошибка', error_description], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description],
            })
        # Пользователь и рукотдела, и ГАП
        elif is_head_of_dept_db and is_approving_hotr:
            error_description = ('Запрещено быть и руководителем отдела, '
                                 'и иметь возможность отправлять часы руководителю отдела')
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=['Ошибка', error_description, 'Обратитесь к администратору сайта'], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description, 'Обратитесь к администратору сайта'],
            })
        # Проверка, что пользователь отправлял данные, как рук отдела и в БД он рук отдела
        elif is_head_of_dept_db and is_head_of_dept == 'None':
            error_description = 'Не пройдена проверка Вашего статуса проверки часов с текущим состоянием БД. rev-1'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=['Ошибка', error_description, 'Обратитесь к администратору сайта'], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description, 'Обратитесь к администратору сайта'],
            })
        # Проверка, что пользователь отправлял данные, как ГАП и в БД он ГАП
        elif is_approving_hotr and is_head_of_dept != 'None':
            error_description = 'Не пройдена проверка Вашего статуса проверки часов с текущим состоянием БД. rev-2'
            app_login.set_warning_log(
                log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                ip_address=app_login.get_client_ip()
            )
            flash(message=['Ошибка', error_description, 'Обратитесь к администратору сайта'], category='error')
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', error_description, 'Обратитесь к администратору сайта'],
            })

        ######################################################################################
        # 1. Создаём список task_responsible_id для проверки в БД
        # 1.1 Проверка, что task_responsible_id принадлежит к отделам проверяющего
        # 1.2 Проверка, что кол-во часов в БД равно кол-ву присланных часов
        # 1.3 Создаём список для таблиц hours_of_task_responsible и org_work_hours_of_task_responsible
        # 1.3.1 Если изменяли комментарий, то записываем в task_responsible и org_work_responsible
        # 1.4 Записываем данные в таблицы hours_of_task_responsible и org_work_hours_of_task_responsible
        # 1.5 Записываем данные в таблицы hotr_status_history и org_work_hotr_status_history
        # 1.5.1 Удаляем старые строки со статусом аннул если согласовываем и добавляем строки согласования
        # 1.5.2 Добавляем строки согласования
        ######################################################################################
        # columns_ta_upd = [['act_id::integer', 'tow_id::integer'], 'tow_cost::numeric', 'tow_cost_percent::numeric']
        # action = 'UPDATE DOUBLE'
        # query_ta_upd = app_payment.get_db_dml_query(action=action, table=table_ta, columns=columns_ta_upd)
        # execute_values(cursor, query_ta_upd, values_ta_upd)


        # 1. Создаём список task_responsible_id для проверки в БД

        # Данные для обновления в таблицах task_responsible/org_work_responsible
        tr = [[], [], []]  # 1.Статус и Коммент, 2.Статус, 3.Коммент
        org_work_tr = list()  # 1.Коммент

        # Список отделов, по которым пользователь может согласовывать часы
        if is_head_of_dept_db:
            for i in range(len(is_head_of_dept_db)):
                is_head_of_dept_db[i] = (is_head_of_dept_db[i],)
        if is_approving_hotr:
            for i in range(len(is_approving_hotr)):
                is_approving_hotr[i] = (is_approving_hotr[i][0],)
        dept_list = is_head_of_dept_db if is_head_of_dept_db else is_approving_hotr

        # Статусы hotr, которые обновляем ('approved_status', 'sent_status')
        # Если аннулируем часы(is_save=False), то hotr_status = False
        hotr_status = 'approved_status' if is_approving_hotr else 'sent_status'
        hotr_status = hotr_status if is_save else False

        print('hotr_status')
        print(hotr_status)

        # Списки согласованных часов
        hotr = list()
        org_work_hotr = list()

        # Список tr_id для проверки полученных данных
        tr_id_list = list()
        org_work_tr_id_list = list()

        #####################################################################################
        # Данные для обновления в таблицах task_responsible/org_work_responsible
        #####################################################################################
        if user_changes_task != {}:
            for t_id,v in user_changes_task.items():
                t_id = int(t_id)
                for tr_id, vv in v.items():
                    tr_id = int(tr_id)
                    tr_id_list.append((tr_id,))
                    for _user_id, vvv in vv.items():
                        _user_id = int(_user_id)
                        #Добавляем в список tr
                        hotr.append([
                            t_id,
                            tr_id,
                            _user_id,
                            float(vvv['hotr_value'])
                        ])

                        if 'td_tow_task_statuses' in vvv.keys() and 'input_task_responsible_comment' in vvv.keys():
                            tr[0].append([
                                tr_id,
                                int(vvv['td_tow_task_statuses']),
                                vvv['input_task_responsible_comment']
                            ])
                        elif 'td_tow_task_statuses' in vvv.keys():
                            tr[1].append([
                                tr_id,
                                int(vvv['td_tow_task_statuses'])
                            ])
                        elif 'input_task_responsible_comment' in vvv.keys():
                            tr[2].append([
                                tr_id,
                                vvv['input_task_responsible_comment']
                            ])

        if user_changes_work != {}:
            for t_id, v in user_changes_work.items():
                t_id = int(t_id)
                for tr_id, vv in v.items():
                    tr_id = int(tr_id)
                    org_work_tr_id_list.append((tr_id,))
                    for _user_id, vvv in vv.items():
                        _user_id = int(_user_id)
                        # Добавляем в список tr
                        org_work_hotr.append([
                            t_id,
                            tr_id,
                            _user_id,
                            float(vvv['hotr_value'])
                        ])

                        if 'input_task_responsible_comment' in vvv.keys():
                            org_work_tr.append([
                                tr_id,
                                vvv['input_task_responsible_comment']
                            ])

        print('tr')
        print(tr)

        print('org_work_tr')
        print(org_work_tr)

        print('hotr')
        print(hotr)

        print('org_work_hotr')
        print(org_work_hotr)

        print('tr_id_list')
        print(tr_id_list)

        print('org_work_tr_id_list')
        print(org_work_tr_id_list)

        print('dept_list')
        print(dept_list)

        # Список hotr_id для согласуемых часов
        hotr_id_list = list()
        org_work_hotr_id_list = list()

        # Словарь выгруженных из БД часов
        hotr_dict = dict()
        org_work_hotr_dict = dict()

        # Статус, что что-то изменено/добавлено в БД
        conn_commit = False

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        ######################################################################################
        # Проверяем присланные данные на валидность. Если согласовываются часы по проектам
        ######################################################################################
        if tr_id_list:
            cursor.execute(
                """
                SELECT
                    t1.hotr_id,
                    t1.task_responsible_id,
                    t1.hotr_value::FLOAT AS hotr_value,
                    t2.task_id,
                    t2.user_id,
                    t3.tow_id,
                    t3.task_name,
                    t4.dept_id
                FROM public.hours_of_task_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id,
                        task_id,
                        user_id
                    FROM public.task_responsible
                ) 
                AS t2 ON t1.task_responsible_id=t2.task_responsible_id
                LEFT JOIN (
                    SELECT
                        task_id,
                        tow_id,
                        task_name
                    FROM public.tasks
                )
                AS t3 ON t2.task_id=t3.task_id
                LEFT JOIN (
                    SELECT
                        tow_id,
                        dept_id
                    FROM public.types_of_work
                )
                AS t4 ON t3.tow_id=t4.tow_id
                WHERE t1.task_responsible_id IN %s AND t1.hotr_date = %s::DATE AND t4.dept_id IN %s
                """,
                [tuple(tr_id_list), current_day, tuple(dept_list)]
            )
            check_list_hotr = cursor.fetchall()

            if check_list_hotr:
                for i in range(len(check_list_hotr)):
                    check_list_hotr[i] = dict(check_list_hotr[i])

                    tmp_t_id = check_list_hotr[i]['task_id']
                    tmp_tr_id = check_list_hotr[i]['task_responsible_id']
                    tmp_user_id = check_list_hotr[i]['user_id']
                    tmp_hotr = check_list_hotr[i]['hotr_value']
                    tmp_hotr_id = check_list_hotr[i]['hotr_id']

                    hotr_dict[tmp_hotr_id] = check_list_hotr[i]

                    #Проверяем, есть ли совпадения отправленного и данных из БД
                    if len(hotr):
                        for _ in range(len(hotr[:])):
                            v = hotr[_]
                            if v[0] == tmp_t_id and v[1] == tmp_tr_id and v[2] == tmp_user_id and v[3] == tmp_hotr:
                                print("hotr", check_list_hotr[i])
                                hotr_id_list.append((check_list_hotr[i]['hotr_id'], ))
                                hotr.pop(_)
                                break
                # Если какие-то часы не были найдены, сообщаем об ошибке
                if len(hotr):
                    error_description = f'Проект: Часть данных не было найдено: {hotr}'
                    app_login.set_warning_log(
                        log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                        ip_address=app_login.get_client_ip()
                    )
                    flash(message=[
                        'Ошибка',
                        'Проект: Часть данных не было найдено',
                        str(hotr),
                        'Обратитесь к администратору сайта'
                    ], category='error')
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', error_description, 'Обновите страницу'],
                    })

            else:
                error_description = 'Согласуемые часы по проектам не найдены'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                    ip_address=app_login.get_client_ip()
                )
                flash(message=[error_description], category='error')
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', error_description, 'Обновите страницу'],
                })

        ######################################################################################
        # Проверяем присланные данные на валидность. Если согласовываются часы по орг работам
        ######################################################################################
        if org_work_tr_id_list:
            cursor.execute(
                """
                SELECT
                    t1.hotr_id,
                    t1.task_responsible_id,
                    t1.hotr_value::FLOAT AS hotr_value,
                    t2.task_id,
                    t2.user_id,
                    t3.task_name
                FROM public.org_work_hours_of_task_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id,
                        task_id,
                        user_id
                    FROM public.org_work_responsible
                ) 
                AS t2 ON t1.task_responsible_id=t2.task_responsible_id
                LEFT JOIN (
                    SELECT
                        task_id,
                        task_name
                    FROM public.org_works
                )
                AS t3 ON t2.task_id=t3.task_id
                WHERE t1.task_responsible_id IN %s AND t1.hotr_date = %s::DATE
                """,
                [tuple(org_work_tr_id_list), current_day]
            )
            check_list_hotr = cursor.fetchall()

            if check_list_hotr:
                for i in range(len(check_list_hotr)):
                    check_list_hotr[i] = dict(check_list_hotr[i])
                    tmp_t_id = check_list_hotr[i]['task_id']
                    tmp_tr_id = check_list_hotr[i]['task_responsible_id']
                    tmp_user_id = check_list_hotr[i]['user_id']
                    tmp_hotr = check_list_hotr[i]['hotr_value']
                    tmp_hotr_id = check_list_hotr[i]['hotr_id']

                    org_work_hotr_dict[tmp_hotr_id] = check_list_hotr[i]

                    # Проверяем, есть ли совпадения отправленного и данных из БД
                    if len(org_work_hotr):
                        for _ in range(len(org_work_hotr[:])):
                            v = org_work_hotr[_]
                            if v[0] == tmp_t_id and v[1] == tmp_tr_id and v[2] == tmp_user_id and v[3] == tmp_hotr:
                                print("org_work_hotr", check_list_hotr[i])
                                org_work_hotr_id_list.append((check_list_hotr[i]['hotr_id'],))
                                org_work_hotr.pop(_)
                                break
                # Если какие-то часы не были найдены, сообщаем об ошибке
                if len(org_work_hotr):
                    error_description = f'Орг.работы: Часть данных не было найдено: {org_work_hotr}'
                    app_login.set_warning_log(
                        log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                        ip_address=app_login.get_client_ip()
                    )
                    flash(message=[
                        'Ошибка',
                        'Орг.работы: Часть данных не было найдено',
                        str(org_work_hotr),
                        'Обратитесь к администратору сайта'
                    ], category='error')
                    return jsonify({
                        'status': 'error',
                        'description': ['Ошибка', error_description, 'Обновите страницу'],
                    })

            else:
                error_description = 'Согласуемые часы по орг.работам не найдены'
                app_login.set_warning_log(
                    log_url=sys._getframe().f_code.co_name, log_description=error_description, user_id=user_id,
                    ip_address=app_login.get_client_ip()
                )
                flash(message=[error_description], category='error')
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', error_description, 'Обновите страницу'],
                })

        print('hotr_id_list')
        print(hotr_id_list)

        print('org_work_hotr_id_list')
        print(org_work_hotr_id_list)

        ######################################################################################
        # 1.3.1 Если изменяли комментарий, то записываем в task_responsible и org_work_responsible
        ######################################################################################
        if tr != [[], [], []]:
            # Обновляем данные о "Статус и Коммент"
            if tr[0]:
                columns_upd_tr0 = ('task_responsible_id', 'task_status_id::integer', 'task_responsible_comment')
                query_tr0_upd = app_payment.get_db_dml_query(action='UPDATE', table='task_responsible',
                                                                  columns=columns_upd_tr0)
                execute_values(cursor, query_tr0_upd, tr[0])
                description = 'Изменения сохранены'

            # Обновляем данные о "Статус"
            if tr[1]:
                columns_upd_tr1 = ('task_responsible_id', 'task_status_id::integer')
                query_tr1_upd = app_payment.get_db_dml_query(action='UPDATE', table='task_responsible',
                                                             columns=columns_upd_tr1)
                execute_values(cursor, query_tr1_upd, tr[1])
                description = 'Изменения сохранены'
            # Обновляем данные о "Коммент"
            if tr[2]:
                columns_upd_tr2 = ('task_responsible_id', 'task_responsible_comment')
                query_tr2_upd = app_payment.get_db_dml_query(action='UPDATE', table='task_responsible',
                                                             columns=columns_upd_tr2)
                execute_values(cursor, query_tr2_upd, tr[2])
                description = 'Изменения сохранены'
            conn_commit = True

        if org_work_tr != list():
            # Обновляем данные
            columns_upd_org_work_tr = ('task_responsible_id', 'task_responsible_comment')
            query_org_work_tr_upd = app_payment.get_db_dml_query(action='UPDATE', table='org_work_responsible',
                                                              columns=columns_upd_org_work_tr)
            execute_values(cursor, query_org_work_tr_upd, org_work_tr)
            description = 'Изменения сохранены'
            conn_commit = True

        ######################################################################################
        # 1.4 Записываем данные в таблицы hours_of_task_responsible и org_work_hours_of_task_responsible
        ######################################################################################
        if hotr_id_list:
            # Аннулирование
            if not hotr_status:
                for i in range(len(hotr_id_list)):
                    hotr_id_list[i] =(hotr_id_list[i][0], False, False)
            # Отправка ГАПом
            elif hotr_status == 'approved_status':
                for i in range(len(hotr_id_list)):
                    hotr_id_list[i] =(hotr_id_list[i][0], True, False)
            # Отправка рукотделом
            elif hotr_status == 'sent_status':
                for i in range(len(hotr_id_list)):
                    hotr_id_list[i] =(hotr_id_list[i][0], True, True)

            columns_upd_hotr = ('hotr_id', 'approved_status', 'sent_status')
            query_hotr_upd = app_payment.get_db_dml_query(action='UPDATE', table='hours_of_task_responsible',
                                                         columns=columns_upd_hotr)
            execute_values(cursor, query_hotr_upd, hotr_id_list)
            description = 'Изменения сохранены'

            # Добавляем информацию о смене статусов часов в таблицу hotr_status_history
            columns_hotr_insert = tuple()
            # Аннулирование
            if not hotr_status:
                columns_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'annul_status'])
                for i in range(len(hotr_id_list)):
                    hotr_id = hotr_id_list[i][0]
                    hotr_id_list[i] = (hotr_id, hotr_dict[hotr_id]['hotr_value'], user_id, True)
            # Отправка ГАПом
            elif hotr_status == 'approved_status':
                columns_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'approved_status'])
                for i in range(len(hotr_id_list)):
                    hotr_id = hotr_id_list[i][0]
                    hotr_id_list[i] = (hotr_id, hotr_dict[hotr_id]['hotr_value'], user_id, True)
            # Отправка рукотделом
            elif hotr_status == 'sent_status':
                columns_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'approved_status', 'sent_status'])
                for i in range(len(hotr_id_list)):
                    hotr_id = hotr_id_list[i][0]
                    hotr_id_list[i] = (hotr_id, hotr_dict[hotr_id]['hotr_value'], user_id, True, True)

            query_hotr_insert = app_payment.get_db_dml_query(action='INSERT INTO',
                                                             table='hotr_status_history',
                                                             columns=columns_hotr_insert)
            execute_values(cursor, query_hotr_insert, hotr_id_list)

            conn_commit = True

        if org_work_hotr_id_list:
            # Аннулирование
            if not hotr_status:
                for i in range(len(org_work_hotr_id_list)):
                    org_work_hotr_id_list[i] =(org_work_hotr_id_list[i][0], False, False)
            # Отправка ГАПом
            elif hotr_status == 'approved_status':
                for i in range(len(org_work_hotr_id_list)):
                    org_work_hotr_id_list[i] =(org_work_hotr_id_list[i][0], True, False)
            # Отправка рукотделом
            elif hotr_status == 'sent_status':
                for i in range(len(org_work_hotr_id_list)):
                    org_work_hotr_id_list[i] =(org_work_hotr_id_list[i][0], True, True)

            columns_upd_org_work_hotr = ('hotr_id', 'approved_status', 'sent_status')
            query_org_work_hotr_upd = app_payment.get_db_dml_query(
                action='UPDATE', table='org_work_hours_of_task_responsible', columns=columns_upd_org_work_hotr
            )
            execute_values(cursor, query_org_work_hotr_upd, org_work_hotr_id_list)
            description = 'Изменения сохранены'

            # Добавляем информацию о смене статусов часов в таблицу org_work_hotr_status_history
            columns_org_work_hotr_insert = tuple()
            # Аннулирование
            if not hotr_status:
                columns_org_work_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'annul_status'])
                for i in range(len(org_work_hotr_id_list)):
                    hotr_id = org_work_hotr_id_list[i][0]
                    org_work_hotr_id_list[i] = (hotr_id, org_work_hotr_dict[hotr_id]['hotr_value'], user_id, True)
            # Отправка ГАПом
            elif hotr_status == 'approved_status':
                columns_org_work_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'approved_status'])
                for i in range(len(org_work_hotr_id_list)):
                    hotr_id = org_work_hotr_id_list[i][0]
                    org_work_hotr_id_list[i] = (hotr_id, org_work_hotr_dict[hotr_id]['hotr_value'], user_id, True)
            # Отправка рукотделом
            elif hotr_status == 'sent_status':
                columns_org_work_hotr_insert = tuple(['hotr_id', 'hotr_value', 'owner', 'approved_status', 'sent_status'])
                for i in range(len(org_work_hotr_id_list)):
                    hotr_id = org_work_hotr_id_list[i][0]
                    org_work_hotr_id_list[i] = (hotr_id, org_work_hotr_dict[hotr_id]['hotr_value'], user_id, True, True)

            query_org_work_hotr_insert = app_payment.get_db_dml_query(action='INSERT INTO',
                                                             table='org_work_hotr_status_history',
                                                             columns=columns_org_work_hotr_insert)
            execute_values(cursor, query_org_work_hotr_insert, org_work_hotr_id_list)

            conn_commit = True



        if conn_commit:
            conn.commit()

        print('hotr_id_list')
        print(hotr_id_list)
        app_login.conn_cursor_close(cursor, conn)

        flash(message=['Изменения сохранены'], category='success')
        return jsonify({
            'status': 'success',
        })

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        flash(message=['Ошибка', msg_for_user, 'Обратитесь к администратору сайта'], category='error')
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })

@task_app_bp.route('/get_employees_list/<location>/<int:tow_id>', methods=['GET'])
@login_required
def get_employees_list(location, tow_id:int):
    """Список ФИО отделов и статусов задачи"""
    try:

        if location == 'employees_and_task_statuses':
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('tasks')

            # Находим dept_id для запрашиваемого tow
            cursor.execute("""
                    SELECT
                        dept_id
                    FROM types_of_work 
                    WHERE tow_id = %s ;
                    """,
                    [tow_id])
            dept_id = cursor.fetchone()

            if not dept_id:
                flash(message=['Ошибка', 'К виду работы не привязан отдел', 'Создание задач невозможна'],
                      category='error')
                return jsonify({
                    'status': 'error',
                    'description': ['К виду работы не привязан отдел', 'Создание задач невозможна']})
            dept_id = dept_id[0]

            # Список статусов задач
            cursor.execute("""
                    SELECT 
                        * 
                    FROM public.task_statuses
                    ORDER BY task_status_name ASC;
                    """)
            task_statuses = cursor.fetchall()

            if task_statuses:
                for i in range(len(task_statuses)):
                    task_statuses[i] = dict(task_statuses[i])
            else:
                flash(message=['Ошибка', 'Не найдены статусы задач', 'Создание задач невозможна'], category='error')
                return jsonify({
                    'status': 'error',
                    'description': ['Не найдены статусы задач', 'Создание задач невозможна']})

            app_login.conn_cursor_close(cursor, conn)

            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('users')

            # Родительский отдел текущей tow
            cursor.execute(
                f'{DEPT_LIST_WITH_PARENT_part_1} AND lg.group_id = {dept_id}'
                f'{DEPT_LIST_WITH_PARENT_part_2} AND dr2.child_id = {dept_id}')
            parent_dept_id = cursor.fetchone()
            if not parent_dept_id:
                flash(message=['Ошибка',
                               'Не найден родительский отдел выбранного вида работ',
                               'Создание задач невозможна'],
                      category='error')
                return jsonify({
                    'status': 'error',
                    'description': ['Не найден родительский отдел выбранного вида работ', 'Создание задач невозможна']})
            parent_dept_id = parent_dept_id[0]

            # Список ФИО сотрудников отделов
            cursor.execute(
                f'''
                {EMPLOYEES_LIST} 
                WHERE t3.dept_id = {parent_dept_id} AND t1.is_fired = FALSE 
                ORDER BY t1.last_name, t1.first_name, t1.surname
                ''')
            employees_list = cursor.fetchall()

            app_login.conn_cursor_close(cursor, conn)
            if employees_list:
                for i in range(len(employees_list)):
                    employees_list[i] = dict(employees_list[i])
                return jsonify({
                    'employees_list': employees_list,
                    'task_statuses': task_statuses,
                    'status': 'success'
                })
        else:
            pass
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return jsonify({
            'status': 'error',
            'description': msg_for_user,
        })


def get_header_menu(role: int = 0, link: str = '', cur_name: (int, None) = 0, is_head_of_dept=None):
    header_menu = []
    # Админ и директор
    if role in (1, 4):
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'В проект'},
            {'link': f'/objects/{link}/tasks', 'name': 'Задачи. Главная'},
            {'link': f'/objects/{link}/archive', 'name': 'Архив'},
            {'link': f'/objects/check-labor-cost', 'name': 'Проверка часов'},
            {'link': f'/objects/employee-task-list', 'name': 'Список задач инженеров'},
            {'link': f'/objects/unsent-labor-costs', 'name': 'Проверка невнесенных данных'},
        ])
    elif is_head_of_dept:
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'В проект'},
            {'link': f'/objects/{link}/tasks', 'name': 'Задачи. Главная'},
            {'link': f'/objects/{link}/archive', 'name': 'Архив'},
            {'link': f'/objects/check-labor-cost', 'name': 'Проверка часов'},
            {'link': f'/objects/employee-task-list', 'name': 'Список задач инженеров'},
            {'link': f'/objects/unsent-labor-costs', 'name': 'Проверка невнесенных данных'},
        ])
    else:
        header_menu.extend([
            {'link': f'/objects/{link}', 'name': 'В проект'},
            {'link': f'/objects/{link}/tasks', 'name': 'Задачи. Главная'},
            {'link': f'', 'name': 'Проверка невнесенных данных'},
        ])

    if cur_name is not None:
        header_menu[cur_name]['class'] = 'current'
        header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu


# Календарь пользователя со статусами почасовой оплаты, отпусков, статуса подачи часов
def user_week_calendar(user_id :int, period_date, tr_id_is_null :bool = True, task_info :bool = False) -> dict:
    """
    period_date - первая дата недели, по которой проверяем часы
    tr_id_is_null - статус, отображать/не отображать задачи без часов за указанный период
    task_info - статус - отображать информацию о согласовании часов ведущим и руководителем
    """
    try:
        days_lst = [period_date - timedelta(days=period_date.weekday() - x) for x in range(0, 7)]
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        ########################################################################
        #                       Список изменений статуса почасовой оплаты
        ########################################################################
        cursor.execute(
            f"""
                SELECT 
                    empl_hours_date,
                    to_char(empl_hours_date, 'dd.mm.yyyy') AS empl_hours_date_txt,
                    full_day_status,
                    to_char(created_at::timestamp without time zone, 'dd.mm.yyyy HH24:MI:SS') AS created_at_txt
                FROM hour_per_day_norm
                WHERE user_id = {user_id} AND empl_hours_date <= (date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE
                ORDER BY empl_hours_date, created_at;
                """
        )
        h_p_d_n_list = cursor.fetchall()

        date_series_h_p_d_n = ''  # Список периодов не почасовой оплаты
        calendar_cur_week_h_p_d_n = ''  # Список периодов подачи часов
        tmp_date_start, tmp_date_end = None, None  # Пара начала и окончания подачи часов

        for i in range(len(h_p_d_n_list)):
            h_p_d_n_list[i] = dict(h_p_d_n_list[i])

            # Создаём список периодов в которых сотрудник может отправить любое кол-во часов
            if tmp_date_start and tmp_date_end:
                date_series_h_p_d_n += f""" AND hotr_date BETWEEN {tmp_date_start} AND '{tmp_date_end}' """
                calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                        calendar_cur_week_h_p_d_n + ' OR ')
                calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND '{tmp_date_end}' """
                tmp_date_start, tmp_date_end = None, None

            if not h_p_d_n_list[i]['full_day_status']:
                tmp_date_start = h_p_d_n_list[i]['empl_hours_date']
                tmp_date_start = f"(date_trunc('week', '{tmp_date_start}'::DATE) + interval '1 days')::DATE"
            elif tmp_date_start:
                tmp_date_end = h_p_d_n_list[i]['empl_hours_date']

        # Обрабатываем для последнего. Создаём список периодов в которых сотрудник отправлять часы
        if tmp_date_start and tmp_date_end:
            calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                    calendar_cur_week_h_p_d_n + ' OR ')
            calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND '{tmp_date_end}' """
            tmp_date_start, tmp_date_end = None, None

        # Если была найдена только дата старта, то добавляем дату окончания - сегодня
        if tmp_date_start and not tmp_date_end:
            tmp_date_end = "(date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE"
            date_series_h_p_d_n += f""" AND hotr_date BETWEEN {tmp_date_start} AND  {tmp_date_end} """
            calendar_cur_week_h_p_d_n = ' AND ' if calendar_cur_week_h_p_d_n == '' else (
                    calendar_cur_week_h_p_d_n + ' OR ')
            calendar_cur_week_h_p_d_n += f""" t0.work_day BETWEEN {tmp_date_start} AND {tmp_date_end} """

        app_login.conn_cursor_close(cursor, conn)

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # Календарь выбранной недели и статус выходного дня
        cursor.execute(
            f"""
                WITH holiday_list AS
                    (SELECT
                        holiday_date,
                        holiday_status,
                        EXTRACT(dow FROM holiday_date) AS day_week
                    FROM list_holidays
                    WHERE holiday_date BETWEEN %s::DATE AND %s::DATE
                    ORDER BY holiday_date ASC
                    ),

                work_days AS
                    (SELECT generate_series(%s::DATE, %s::DATE, interval  '1 day')::DATE AS work_day
                    )

                SELECT
                    t0.work_day,
                    COALESCE(to_char(t0.work_day, 'dd.mm.yy'), '') AS work_day_txt,
                    CASE
                        WHEN t1.holiday_status IS NOT NULL THEN t1.holiday_status
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN TRUE
                        ELSE FALSE
                    END AS holiday_status,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'th_task_holiday th_week_day'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'th_task_work_day th_week_day'
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN 'th_task_holiday th_week_day'
                        ELSE 'th_task_work_day th_week_day'
                    END AS class,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'td_task_holiday'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'td_task_work_day'
                        WHEN EXTRACT(dow FROM t0.work_day) IN (0,6) THEN 'td_task_holiday'
                        ELSE 'td_task_work_day'
                    END AS td_class,
                    0 AS hours_per_day,
                    CASE
                        WHEN TRUE {calendar_cur_week_h_p_d_n} THEN FALSE
                        ELSE TRUE
                    END AS hpdn_status
                FROM work_days AS t0
                LEFT JOIN holiday_list AS t1 ON t0.work_day = t1.holiday_date;
                """,
            [days_lst[0], days_lst[-1], days_lst[0], days_lst[-1]]
        )
        calendar_cur_week = cursor.fetchall()

        if len(calendar_cur_week):
            for i in range(len(calendar_cur_week)):
                calendar_cur_week[i] = dict(calendar_cur_week[i])
                calendar_cur_week[i]['day_week'] = DAYS_OF_THE_WEEK[i]
                calendar_cur_week[i]['input_task_week'] = f'input_task_week_1_day_{i + 1}'

        else:
            return {
                'status': 'error',
                'description': ['Ошибка', 'Страница недоступна', 'Не удалось определить даты календаря'],
            }
        tr_id_is_null = '''AND (
            t2.input_task_week_1_day_1 IS NOT NULL OR t2.input_task_week_1_day_2 IS NOT NULL OR 
            t2.input_task_week_1_day_3 IS NOT NULL OR t2.input_task_week_1_day_4 IS NOT NULL OR 
            t2.input_task_week_1_day_5 IS NOT NULL OR t2.input_task_week_1_day_6 IS NOT NULL OR 
            t2.input_task_week_1_day_7 IS NOT NULL)''' if tr_id_is_null else ''

        task_info = [
            't3.task_name,',
            ''' LEFT JOIN (
                    SELECT
                        task_id,
                        task_name
                    FROM tasks
                ) AS t3 ON t1.task_id = t3.task_id''',
            '''
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_1_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_2_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_3_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_4_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_5_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_6_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_7_hotr_id,
                
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN approved_status ELSE NULL END) AS input_task_week_1_day_1_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN approved_status ELSE NULL END) AS input_task_week_1_day_2_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN approved_status ELSE NULL END) AS input_task_week_1_day_3_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN approved_status ELSE NULL END) AS input_task_week_1_day_4_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN approved_status ELSE NULL END) AS input_task_week_1_day_5_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN approved_status ELSE NULL END) AS input_task_week_1_day_6_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN approved_status ELSE NULL END) AS input_task_week_1_day_7_approved_status,
                
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN sent_status ELSE NULL END) AS input_task_week_1_day_1_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN sent_status ELSE NULL END) AS input_task_week_1_day_2_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN sent_status ELSE NULL END) AS input_task_week_1_day_3_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN sent_status ELSE NULL END) AS input_task_week_1_day_4_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN sent_status ELSE NULL END) AS input_task_week_1_day_5_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN sent_status ELSE NULL END) AS input_task_week_1_day_6_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN sent_status ELSE NULL END) AS input_task_week_1_day_7_sent_status,
            '''] if task_info else False

        org_work_info = [
            't3.task_name,',
            ''' LEFT JOIN (
                    SELECT
                        task_id,
                        task_name
                    FROM public.org_works
                ) AS t3 ON t1.task_id = t3.task_id''',
            '''
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_1_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_2_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_3_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_4_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_5_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_6_hotr_id,
                MAX(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_id ELSE NULL END) AS input_task_week_1_day_7_hotr_id,

                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN approved_status ELSE NULL END) AS input_task_week_1_day_1_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN approved_status ELSE NULL END) AS input_task_week_1_day_2_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN approved_status ELSE NULL END) AS input_task_week_1_day_3_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN approved_status ELSE NULL END) AS input_task_week_1_day_4_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN approved_status ELSE NULL END) AS input_task_week_1_day_5_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN approved_status ELSE NULL END) AS input_task_week_1_day_6_approved_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN approved_status ELSE NULL END) AS input_task_week_1_day_7_approved_status,

                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN sent_status ELSE NULL END) AS input_task_week_1_day_1_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN sent_status ELSE NULL END) AS input_task_week_1_day_2_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN sent_status ELSE NULL END) AS input_task_week_1_day_3_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN sent_status ELSE NULL END) AS input_task_week_1_day_4_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN sent_status ELSE NULL END) AS input_task_week_1_day_5_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN sent_status ELSE NULL END) AS input_task_week_1_day_6_sent_status,
                bool_or(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN sent_status ELSE NULL END) AS input_task_week_1_day_7_sent_status,
            ''']
        org_works = list()  # Список часов орг работ в случае если сохраняем часы
        # Часы пользователя за указанный период

        # cursor.execute(
        #     f"""
        #             SELECT
        #                 t1.task_id,
        #                 t1.user_id,
        #                 t1.task_status_id,
        #                 t1.task_responsible_id,
        #                 t2.*,
        #                 {task_info[0]}
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
        #                 COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt
        #             FROM task_responsible AS t1
        #             LEFT JOIN (
        #                 SELECT
        #                     task_responsible_id AS tr_id,
        #                     {task_info[2]}
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
        #                     SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7
        #                 FROM hours_of_task_responsible
        #                 WHERE hotr_date BETWEEN %s AND %s
        #                 GROUP BY tr_id
        #             ) AS t2 ON t1.task_responsible_id = t2.tr_id
        #             {task_info[1]}
        #
        #             WHERE t1.user_id = %s {tr_id_is_null};""",
        #     [days_lst[0], days_lst[6], user_id]
        # )
        if task_info:
            cursor.execute(
                f"""
                SELECT
                    t1.task_id,
                    t1.user_id,
                    t1.task_status_id,
                    t1.task_responsible_id,
                    t2.*,
                    {task_info[0]}
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt
                FROM task_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id AS tr_id,
                        {task_info[2]}
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7
                    FROM hours_of_task_responsible
                    WHERE hotr_date BETWEEN %s AND %s
                    GROUP BY tr_id
                ) AS t2 ON t1.task_responsible_id = t2.tr_id
                {task_info[1]}

                WHERE t1.user_id = %s {tr_id_is_null};""",
                [days_lst[0], days_lst[6], user_id]
            )
            tasks = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT
                    t1.task_id,
                    t1.user_id,
                    t1.task_status_id,
                    t1.task_responsible_id,
                    t2.*,
                    {org_work_info[0]}
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt
                FROM public.org_work_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id AS tr_id,
                        {org_work_info[2]}
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7
                    FROM public.org_work_hours_of_task_responsible
                    WHERE hotr_date BETWEEN %s AND %s
                    GROUP BY tr_id
                ) AS t2 ON t1.task_responsible_id = t2.tr_id
                {org_work_info[1]}

                WHERE t1.user_id = %s {tr_id_is_null};""",
                [days_lst[0], days_lst[6], user_id]
            )
            org_works = cursor.fetchall()
            # print(cursor.query)
        else:
            cursor.execute(
                f"""
                SELECT
                    t1.task_id,
                    t1.user_id,
                    t1.task_status_id,
                    t1.task_responsible_id,
                    t2.*,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt
                FROM task_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id AS tr_id,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7
                    FROM hours_of_task_responsible
                    WHERE hotr_date BETWEEN %s AND %s
                    GROUP BY tr_id
                ) AS t2 ON t1.task_responsible_id = t2.tr_id

                WHERE t1.user_id = %s {tr_id_is_null}
                
                UNION ALL
                
                SELECT
                    t1.task_id,
                    t1.user_id,
                    t1.task_status_id,
                    t1.task_responsible_id,
                    t2.*,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_1) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_2) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_3) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_4) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_5) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_6) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp(((t2.input_task_week_1_day_7) * 60)::INT), 'MI:SS'), '') AS input_task_week_1_day_7_txt
                FROM org_work_responsible AS t1
                LEFT JOIN (
                    SELECT
                        task_responsible_id AS tr_id,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 1 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_1,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 2 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_2,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 3 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_3,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 4 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_4,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 5 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_5,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 6 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_6,
                        SUM(CASE WHEN EXTRACT(dow FROM hotr_date) = 0 THEN hotr_value ELSE NULL END) AS input_task_week_1_day_7
                    FROM org_work_hours_of_task_responsible
                    WHERE hotr_date BETWEEN %s AND %s
                    GROUP BY tr_id
                ) AS t2 ON t1.task_responsible_id = t2.tr_id

                WHERE t1.user_id = %s {tr_id_is_null}
                
                ;""",
                [days_lst[0], days_lst[6], user_id, days_lst[0], days_lst[6], user_id]
            )

            tasks = cursor.fetchall()
        # print(cursor.query)

        app_login.conn_cursor_close(cursor, conn)

        task_dict = dict()
        org_work_dict = dict()

        if len(tasks):
            for i in range(len(tasks)):
                tasks[i] = dict(tasks[i])
                task_dict[tasks[i]['task_responsible_id']] = tasks[i]
                calendar_cur_week[0]['hours_per_day'] += tasks[i]['input_task_week_1_day_1'] if (
                    tasks)[i]['input_task_week_1_day_1'] else 0
                calendar_cur_week[1]['hours_per_day'] += tasks[i]['input_task_week_1_day_2'] if (
                    tasks)[i]['input_task_week_1_day_2'] else 0
                calendar_cur_week[2]['hours_per_day'] += tasks[i]['input_task_week_1_day_3'] if (
                    tasks)[i]['input_task_week_1_day_3'] else 0
                calendar_cur_week[3]['hours_per_day'] += tasks[i]['input_task_week_1_day_4'] if (
                    tasks)[i]['input_task_week_1_day_4'] else 0
                calendar_cur_week[4]['hours_per_day'] += tasks[i]['input_task_week_1_day_5'] if (
                    tasks)[i]['input_task_week_1_day_5'] else 0
                calendar_cur_week[5]['hours_per_day'] += tasks[i]['input_task_week_1_day_6'] if (
                    tasks)[i]['input_task_week_1_day_6'] else 0
                calendar_cur_week[6]['hours_per_day'] += tasks[i]['input_task_week_1_day_7'] if (
                    tasks)[i]['input_task_week_1_day_7'] else 0

            # Конвертируем сумму часов в день из float в HH:MM
            for i in calendar_cur_week:
                if i['hours_per_day']:
                    i['hours_per_day_txt'] = '{0:02.0f}:{1:02.0f}'.format(*divmod(i['hours_per_day'] * 60, 60))
                else:
                    i['hours_per_day_txt'] = '0'
        if len(org_works):
            for i in range(len(org_works)):
                org_works[i] = dict(org_works[i])
                org_work_dict[org_works[i]['task_responsible_id']] = org_works[i]
                calendar_cur_week[0]['hours_per_day'] += org_works[i]['input_task_week_1_day_1'] if (
                    org_works)[i]['input_task_week_1_day_1'] else 0
                calendar_cur_week[1]['hours_per_day'] += org_works[i]['input_task_week_1_day_2'] if (
                    org_works)[i]['input_task_week_1_day_2'] else 0
                calendar_cur_week[2]['hours_per_day'] += org_works[i]['input_task_week_1_day_3'] if (
                    org_works)[i]['input_task_week_1_day_3'] else 0
                calendar_cur_week[3]['hours_per_day'] += org_works[i]['input_task_week_1_day_4'] if (
                    org_works)[i]['input_task_week_1_day_4'] else 0
                calendar_cur_week[4]['hours_per_day'] += org_works[i]['input_task_week_1_day_5'] if (
                    org_works)[i]['input_task_week_1_day_5'] else 0
                calendar_cur_week[5]['hours_per_day'] += org_works[i]['input_task_week_1_day_6'] if (
                    org_works)[i]['input_task_week_1_day_6'] else 0
                calendar_cur_week[6]['hours_per_day'] += org_works[i]['input_task_week_1_day_7'] if (
                    org_works)[i]['input_task_week_1_day_7'] else 0

            # Конвертируем сумму часов в день из float в HH:MM
            if not len(tasks):
                for i in calendar_cur_week:
                    if i['hours_per_day']:
                        i['hours_per_day_txt'] = '{0:02.0f}:{1:02.0f}'.format(*divmod(i['hours_per_day'] * 60, 60))
                    else:
                        i['hours_per_day_txt'] = '0'
        if not len(tasks) and not len(org_works):
            task_dict = False
            # Конвертируем сумму часов в день из float в HH:MM
            for i in calendar_cur_week:
                i['hours_per_day_txt'] = '0'

        return {
            'status': 'success',
            'calendar_cur_week': calendar_cur_week,
            'days_lst': days_lst,
            'task_dict': task_dict,
            'org_work_dict': org_work_dict,
        }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': 'error',
            'description': [msg_for_user],
        }

# Конвертируем число в ЧЧ:ММ и наоборот
def float_to_time(val :(float, str), ftt_status :bool = True) -> (str, float):
    if ftt_status:
        hours = int(val)
        minutes = int((val - hours) * 60)
        return f"{hours:02}:{minutes:02}"
    else:
        hrs, minutes = map(int, val.split(':'))
        return hrs + minutes / 60

# Конвертируем текст в int
def str_to_int(val, need_to_convert:bool=False) -> (list, bool):
    try:
        number = int(val)
        return [True, number] if need_to_convert else True
    except ValueError:
        return [False, val] if need_to_convert else False

# Конвертируем текст в int
def str_to_float(val, need_to_convert:bool=False) -> (list, bool):
    try:
        number = float(val)
        return [True, number] if need_to_convert else True
    except ValueError:
        return [False, val] if need_to_convert else False

# # Проверка строку на int или float
# def check_string(val, need_to_convert:bool=False) -> (list, str):
#     try:
#         number = int(val)
#         return [type(number), number] if need_to_convert else type(number)
#     except ValueError:
#         try:
#             number = float(val)
#             return [type(number), number] if need_to_convert else type(number)
#         except ValueError:
#             return [type(val), val] if need_to_convert else type(val)

# Проверяем список задач на наличие в БД
def task_list_is_actual(checked_list: set = None, tow_id: int = None, is_del=True, is_task=True) -> dict:
    try:
        description = 'Список задач не актуален (v.2). Обновите страницу'
        # Обрабатываем полученные id. Удаляем все не цифровые id

        if is_task:
            for i in checked_list.copy():
                if not i.isdigit():
                    checked_list.remove(i)
                else:
                    checked_list.remove(i)
                    checked_list.add(int(i))
        else:
            for i in checked_list.copy():
                if not i[0].isdigit():
                    checked_list.remove(i)
                else:
                    if i[1] in ('None', None) :
                        tr_id = None
                    elif not i[1].isdigit():
                        checked_list.remove(i)
                    else:
                        tr_id = int(i[1])
                    checked_list.remove(i)
                    checked_list.add((int(i[0]), tr_id))

        if checked_list:
            # Connect to the database
            conn, cursor = app_login.conn_cursor_init_dict('tasks')
            # Список tasks
            cursor.execute(
                """
                SELECT 
                    t0.task_id,
                    t1.task_responsible_id,
                    t1.task_plan_labor_cost,
                    t2.task_responsible_id
                FROM tasks AS t0
                LEFT JOIN 
                    (SELECT task_id, task_responsible_id, task_plan_labor_cost FROM task_responsible) 
                AS t1 ON t0.task_id = t1.task_id
                LEFT JOIN 
                (SELECT DISTINCT task_responsible_id AS task_responsible_id FROM hours_of_task_responsible) 
                AS t2 ON t1.task_responsible_id = t2.task_responsible_id
                WHERE tow_id = %s;""",
                (tow_id,)
            )
            tasks = cursor.fetchall()
            app_login.conn_cursor_close(cursor, conn)

            if is_del and len(tasks):
                if is_task:
                    pass
                else:
                    recheck_list = set()  # Список для повторной проверки удаляемых задач
                    # В случае если помимо удаления, у задачи могли убрать плановые трудозатраты, добавляем
                    # пару task_id - tr_id, и проверяем повторно, плановый трудозатраты действительно удалены

                    for i in tasks.copy():
                        # Если удаляется только задача, без tr, то не нужна проверка на плановые и факт трудозатраты,
                        # т.к. они есть только у tr. В этом случае удаляем строку из checked_list
                        # Иначе происходит проверка tr
                        if tuple((i[0], None)) in checked_list:
                            checked_list.remove(tuple((i[0], None)))
                        if tuple((i[0], i[1])) in checked_list:
                            # Если есть плановые трудозатраты - то добавляем в recheck_list
                            if i[2]:
                                recheck_list.add((i[0], i[1]))
                            # Если есть плановые или фактические трудозатраты - ошибка, нельзя удалять задачи имеющие трудозатраты
                            if i[3]:
                                return {
                                    'status':False,
                                    'description':'У задачи есть фактические трудозатраты (v.1)',
                                    'tr_id': i[1]
                                }
                            checked_list.remove(tuple((i[0], i[1])))
                            tasks.remove(i)

                    # Возвращаем список для повторной проверки удаляемых задач у которых есть плановые трудозатраты
                    if len(recheck_list):
                        return {
                            'status': True,
                            'recheck_list': recheck_list,
                            'description': 'Проверить список удаляемых задач'
                        }

            else:
                return {
                    'status': False,
                    'description': 'Список задач не актуален (v.1/1). Обновите страницу'
                }

            if checked_list:
                return {
                    'status': False,
                    'description': description
                }
            else:
                return {
                    'status': True,
                    'description': 'Список задач актуален'
                }

        return {
            'status': True,
            'description': 'Нет видов работ для проверки'
        }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': False,
            'description': f'Ошибка при проверки актуальности списка задач: {msg_for_user}'}

# Информация о task_responsible_id
def get_tr_info(tr_id: int = None) -> dict:
    try:
        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')
        # Список tasks
        cursor.execute(
            """
                SELECT 
                    t0.*,
                    t1.last_name, 
                    t1.first_name,
                    t1.surname,
                    concat_ws(' ', 
                        t1.last_name, 
                        LEFT(t1.first_name, 1) || '.', 
                        CASE
                        WHEN t1.surname<>'' THEN LEFT(t1.surname, 1) || '.' ELSE ''
                        END) AS short_full_name,
                    t2.tow_id,
                    t2.task_number,
                    t2.task_name,
                    CASE
                        WHEN length(t2.task_name) > 50 THEN SUBSTRING(t2.task_name, 1, 47) || '...'
                        ELSE t2.task_name
                    END AS short_task_name,
                    t2.path,
                    t2.lvl,
                    t3.task_status_name,
                    t3.task_status_value
                FROM task_responsible AS t0
                LEFT JOIN (SELECT user_id, last_name, first_name, surname FROM users) 
                AS t1 ON t0.user_id = t1.user_id
                LEFT JOIN (SELECT * FROM tasks) 
                AS t2 ON t0.task_id = t2.task_id
                LEFT JOIN (SELECT * FROM task_statuses) 
                AS t3 ON t0.task_status_id = t3.task_status_id                    
                WHERE t0.task_responsible_id = %s;""",
            (tr_id,)
        )
        tr_info = cursor.fetchone()
        return dict(tr_info)
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': False,
            'description': f'Ошибка при проверки актуальности списка задач: {msg_for_user}'}

# Генерация дат для календаря на странице проверки часов
def get_calendar_for_month(cur_day:[bool, datetime.date]=False, last_date:[bool, str]=False) -> dict:
    try:
        # Конвертируем first_date в формат datetime
        try:
            cur_day = cur_day if cur_day else datetime.now()
            first_date = cur_day
        except:
            first_date = datetime.now()

        # Конвертируем last_date в формат datetime
        try:
            last_date = datetime.strptime(first_date, "%Y-%m-%d")
        except:
            last_date = False

        # Define the current month
        first_date = datetime.now() if not first_date else first_date

        current_month = first_date.month
        current_year = first_date.year
        month_list_dict = {
            1: 'Январь',
            2: 'Февраль',
            3: 'Март',
            4: 'Апрель',
            5: 'Май',
            6: 'Июнь',
            7: 'Июль',
            8: 'Август',
            9: 'Сентябрь',
            10: 'Октябрь',
            11: 'Ноябрь',
            12: 'Декабрь',
        }

        # # Find the first day of the current month
        # first_day_current_month = datetime(current_year, current_month, 1)
        #
        # # Find the last day of the previous month
        # last_day_prev_month = first_day_current_month - timedelta(days=1)
        #
        # # Find the first Monday before or on the last day of the previous month
        # last_monday_prev_month = last_day_prev_month - timedelta(days=last_day_prev_month.weekday())
        #
        # # Find the first day of the next month
        # first_day_next_month = first_day_current_month + timedelta(days=32)
        # first_day_next_month = datetime(first_day_next_month.year, first_day_next_month.month, 1)
        #
        # # Find the first Sunday of the next month
        # first_sunday_next_month = first_day_next_month + timedelta(days=(6 - first_day_next_month.weekday()))
        #
        # current_date = last_monday_prev_month

        # Get the first day of the current month
        today = datetime.today()
        today = first_date
        first_day_of_month = datetime(today.year, today.month, 1)

        # Determine the first Monday on or before the first day of the month
        first_monday = first_day_of_month - timedelta(days=first_day_of_month.weekday())
        last_sunday = first_monday + timedelta(days=41)

        # Define the last date
        if not last_date:
            last_date = last_sunday

        # Create a dictionary with 42 consecutive days starting from the first Monday
        calendar_dict = {}

        first_date = datetime(first_date.year, first_date.month, 1)
        first_date = first_date - timedelta(days=first_date.weekday())

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # Календарь выбранной недели и статус выходного дня
        cursor.execute(
            f"""
                        WITH holiday_list AS
                    (SELECT
                        holiday_date,
                        holiday_status
                    FROM list_holidays
                    WHERE holiday_date BETWEEN %s::DATE AND %s::DATE
                    ORDER BY holiday_date ASC
                    ),

                work_days AS
                    (
					SELECT generate_series(%s::DATE, %s::DATE, interval  '1 day')::DATE AS work_day,
                    EXTRACT(dow from generate_series(%s::DATE, %s::DATE, interval  '1 day')::DATE)::int AS day_week
                    )

                SELECT
                    t0.work_day,
					t0.day_week,
					EXTRACT(DAY FROM t0.work_day) AS only_day,
					0 AS unsent_hotr,
					ARRAY[''] AS unsent_hotr_hide,
					0 AS un_hotr,
					CASE
						WHEN EXTRACT(MONTH FROM t0.work_day) = {current_month}::int THEN 'day'
						ELSE 'day_another_month'
					END AS div_class,
	                CASE 
						WHEN t0.work_day=%s::DATE THEN
                            CASE
                                WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'circle weekend'
                                WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'circle'
                                WHEN t0.day_week IN (0,6) THEN 'circle weekend'
                                ELSE 'circle'
                            END || ' current-day' 
						ELSE 
                            CASE
                                WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'circle weekend'
                                WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'circle'
                                WHEN t0.day_week IN (0,6) THEN 'circle weekend'
                                ELSE 'circle'
                            END
					END AS circle_class
                FROM work_days AS t0
                LEFT JOIN holiday_list AS t1 ON t0.work_day = t1.holiday_date;
                        """,
            [first_date, last_date,
             first_date, last_date,
             first_date, last_date,
             cur_day]
        )
        date_weekday = cursor.fetchall()

        date_weekday_dict = dict()
        if len(date_weekday):
            for i in range(len(date_weekday)):
                date_weekday_dict[date_weekday[i]['work_day']] = dict(date_weekday[i])
        else:
            return {
                'status': 'error',
                'description': ['Ошибка', 'Страница недоступна', 'Не удалось определить даты календаря'],
            }



        app_login.conn_cursor_close(cursor, conn)

        # while current_date <= first_sunday_next_month:
        #     #date_weekday_dict[current_date.strftime("%Y-%m-%d")] = {
        #     date_weekday_dict[current_date.date()] = {
        #         'weekday': current_date.weekday(),
        #         'unsent_hotr': 0,
        #         'un_hotr': 0,
        #         'div_class': "day" if current_month == current_date.month else "day_another_month"
        #         'asd': current_month == current_date.month
        #     }
        #     current_date += timedelta(days=1)

        return {
            'status': True,
            'date_weekday_dict': date_weekday_dict,
            'first_monday': first_monday,
            'last_sunday': last_sunday,
            'cur_month_title': f'{month_list_dict[current_month]} {current_year}'
        }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': False,
            'description': f'Ошибка при создании дней календаря: {msg_for_user}'}

# Удаляем сотрудника из таблицы должников отправки часов
def delete_from_users_statuses_unsent_hours(conn, cursor, user_id:int) -> None:
    try:
        columns_del_usuh = 'user_id'
        query_del_usuh = app_payment.get_db_dml_query(action='DELETE', table='users_statuses_unsent_hours',
                                                      columns=columns_del_usuh)
        execute_values(cursor, query_del_usuh, ((user_id,),))
        conn.commit()
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
