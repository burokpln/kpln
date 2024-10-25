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
TASK_LIST_ols_WITHOUL_last_row = """
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
    
    CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '📅 ' || ROUND(COALESCE(t2.task_sum_fact, t3.task_sum_fact)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
    COALESCE(t2.task_sum_fact, t3.task_sum_fact) AS task_sum_fact,
    
    CASE WHEN COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) IS NOT NULL THEN '📅 ' || COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) ELSE '' END AS task_sum_previous_fact_txt,
    COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
    --text format
    CASE WHEN COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) ELSE '' END AS input_task_sum_week_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_1 IS NOT NULL THEN t2.input_task_week_1_day_1::text ELSE '📅 ' || t3.input_task_week_1_day_1 END
        ELSE '' END AS input_task_week_1_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_2 IS NOT NULL THEN t2.input_task_week_1_day_2::text ELSE '📅 ' || t3.input_task_week_1_day_2 END
        ELSE '' END AS input_task_week_1_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_3 IS NOT NULL THEN t2.input_task_week_1_day_3::text ELSE '📅 ' || t3.input_task_week_1_day_3 END 
        ELSE '' END AS input_task_week_1_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_4 IS NOT NULL THEN t2.input_task_week_1_day_4::text ELSE '📅 ' || t3.input_task_week_1_day_4 END 
        ELSE '' END AS input_task_week_1_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_5 IS NOT NULL THEN t2.input_task_week_1_day_5::text ELSE '📅 ' || t3.input_task_week_1_day_5 END 
        ELSE '' END AS input_task_week_1_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_6 IS NOT NULL THEN t2.input_task_week_1_day_6::text ELSE '📅 ' || t3.input_task_week_1_day_6 END 
        ELSE '' END AS input_task_week_1_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_1_day_7 IS NOT NULL THEN t2.input_task_week_1_day_7::text ELSE '📅 ' || t3.input_task_week_1_day_7 END 
        ELSE '' END AS input_task_week_1_day_7_txt,
    
    CASE WHEN COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) ELSE '' END AS input_task_sum_week_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_1 IS NOT NULL THEN t2.input_task_week_2_day_1::text ELSE '📅 ' || t3.input_task_week_2_day_1 END
        ELSE '' END AS input_task_week_2_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_2 IS NOT NULL THEN t2.input_task_week_2_day_2::text ELSE '📅 ' || t3.input_task_week_2_day_2 END
        ELSE '' END AS input_task_week_2_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_3 IS NOT NULL THEN t2.input_task_week_2_day_3::text ELSE '📅 ' || t3.input_task_week_2_day_3 END 
        ELSE '' END AS input_task_week_2_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_4 IS NOT NULL THEN t2.input_task_week_2_day_4::text ELSE '📅 ' || t3.input_task_week_2_day_4 END 
        ELSE '' END AS input_task_week_2_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_5 IS NOT NULL THEN t2.input_task_week_2_day_5::text ELSE '📅 ' || t3.input_task_week_2_day_5 END 
        ELSE '' END AS input_task_week_2_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_6 IS NOT NULL THEN t2.input_task_week_2_day_6::text ELSE '📅 ' || t3.input_task_week_2_day_6 END 
        ELSE '' END AS input_task_week_2_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_2_day_7 IS NOT NULL THEN t2.input_task_week_2_day_7::text ELSE '📅 ' || t3.input_task_week_2_day_7 END 
        ELSE '' END AS input_task_week_2_day_7_txt,

    CASE WHEN COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) ELSE '' END AS input_task_sum_week_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_1 IS NOT NULL THEN t2.input_task_week_3_day_1::text ELSE '📅 ' || t3.input_task_week_3_day_1 END
        ELSE '' END AS input_task_week_3_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_2 IS NOT NULL THEN t2.input_task_week_3_day_2::text ELSE '📅 ' || t3.input_task_week_3_day_2 END
        ELSE '' END AS input_task_week_3_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_3 IS NOT NULL THEN t2.input_task_week_3_day_3::text ELSE '📅 ' || t3.input_task_week_3_day_3 END 
        ELSE '' END AS input_task_week_3_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_4 IS NOT NULL THEN t2.input_task_week_3_day_4::text ELSE '📅 ' || t3.input_task_week_3_day_4 END 
        ELSE '' END AS input_task_week_3_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_5 IS NOT NULL THEN t2.input_task_week_3_day_5::text ELSE '📅 ' || t3.input_task_week_3_day_5 END 
        ELSE '' END AS input_task_week_3_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_6 IS NOT NULL THEN t2.input_task_week_3_day_6::text ELSE '📅 ' || t3.input_task_week_3_day_6 END 
        ELSE '' END AS input_task_week_3_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_3_day_7 IS NOT NULL THEN t2.input_task_week_3_day_7::text ELSE '📅 ' || t3.input_task_week_3_day_7 END 
        ELSE '' END AS input_task_week_3_day_7_txt,

    CASE WHEN COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) ELSE '' END AS input_task_sum_week_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_1 IS NOT NULL THEN t2.input_task_week_4_day_1::text ELSE '📅 ' || t3.input_task_week_4_day_1 END
        ELSE '' END AS input_task_week_4_day_1_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_2 IS NOT NULL THEN t2.input_task_week_4_day_2::text ELSE '📅 ' || t3.input_task_week_4_day_2 END
        ELSE '' END AS input_task_week_4_day_2_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_3 IS NOT NULL THEN t2.input_task_week_4_day_3::text ELSE '📅 ' || t3.input_task_week_4_day_3 END 
        ELSE '' END AS input_task_week_4_day_3_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_4 IS NOT NULL THEN t2.input_task_week_4_day_4::text ELSE '📅 ' || t3.input_task_week_4_day_4 END 
        ELSE '' END AS input_task_week_4_day_4_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_5 IS NOT NULL THEN t2.input_task_week_4_day_5::text ELSE '📅 ' || t3.input_task_week_4_day_5 END 
        ELSE '' END AS input_task_week_4_day_5_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_6 IS NOT NULL THEN t2.input_task_week_4_day_6::text ELSE '📅 ' || t3.input_task_week_4_day_6 END 
        ELSE '' END AS input_task_week_4_day_6_txt,
    CASE WHEN COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) IS NOT NULL THEN 
        CASE WHEN t2.input_task_week_4_day_7 IS NOT NULL THEN t2.input_task_week_4_day_7::text ELSE '📅 ' || t3.input_task_week_4_day_7 END 
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
    
    CASE WHEN COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) IS NOT NULL THEN '📅 ' || COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) ELSE '' END AS task_sum_future_fact_txt,
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
--EXPLAIN
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
)
    (SELECT
        CASE 
            WHEN t1.task_responsible_id IS NULL THEN 'tom-' || t0.task_id 
            ELSE 'task-' || t1.task_responsible_id 
        END AS row_id,
        t1.task_plan_labor_cost,
        t1.task_plan_labor_cost AS task_plan_labor_cost_txt,
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
        t6.task_status_name,
        COALESCE(t1.task_responsible_comment, '') AS task_responsible_comment,
        t1.task_status_id,
        t1.user_id,
        t5.short_full_name,
        t1.rowspan,
        t4.task_cnt,
    
        CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '📅 ' || ROUND(COALESCE(t2.task_sum_fact, t3.task_sum_fact)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
        COALESCE(t2.task_sum_fact, t3.task_sum_fact) AS task_sum_fact,
    
        CASE WHEN COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) IS NOT NULL THEN '📅 ' || ROUND(COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact)/8::numeric, 2) ELSE '' END AS task_sum_previous_fact_txt,
        COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
        --text format
        CASE WHEN COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) ELSE '' END AS input_task_sum_week_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_1 IS NOT NULL THEN t2.input_task_week_1_day_1::text ELSE '📅 ' || t3.input_task_week_1_day_1 END
            ELSE '' END AS input_task_week_1_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_2 IS NOT NULL THEN t2.input_task_week_1_day_2::text ELSE '📅 ' || t3.input_task_week_1_day_2 END
            ELSE '' END AS input_task_week_1_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_3 IS NOT NULL THEN t2.input_task_week_1_day_3::text ELSE '📅 ' || t3.input_task_week_1_day_3 END 
            ELSE '' END AS input_task_week_1_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_4 IS NOT NULL THEN t2.input_task_week_1_day_4::text ELSE '📅 ' || t3.input_task_week_1_day_4 END 
            ELSE '' END AS input_task_week_1_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_5 IS NOT NULL THEN t2.input_task_week_1_day_5::text ELSE '📅 ' || t3.input_task_week_1_day_5 END 
            ELSE '' END AS input_task_week_1_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_6 IS NOT NULL THEN t2.input_task_week_1_day_6::text ELSE '📅 ' || t3.input_task_week_1_day_6 END 
            ELSE '' END AS input_task_week_1_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_1_day_7 IS NOT NULL THEN t2.input_task_week_1_day_7::text ELSE '📅 ' || t3.input_task_week_1_day_7 END 
            ELSE '' END AS input_task_week_1_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) ELSE '' END AS input_task_sum_week_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_1 IS NOT NULL THEN t2.input_task_week_2_day_1::text ELSE '📅 ' || t3.input_task_week_2_day_1 END
            ELSE '' END AS input_task_week_2_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_2 IS NOT NULL THEN t2.input_task_week_2_day_2::text ELSE '📅 ' || t3.input_task_week_2_day_2 END
            ELSE '' END AS input_task_week_2_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_3 IS NOT NULL THEN t2.input_task_week_2_day_3::text ELSE '📅 ' || t3.input_task_week_2_day_3 END 
            ELSE '' END AS input_task_week_2_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_4 IS NOT NULL THEN t2.input_task_week_2_day_4::text ELSE '📅 ' || t3.input_task_week_2_day_4 END 
            ELSE '' END AS input_task_week_2_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_5 IS NOT NULL THEN t2.input_task_week_2_day_5::text ELSE '📅 ' || t3.input_task_week_2_day_5 END 
            ELSE '' END AS input_task_week_2_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_6 IS NOT NULL THEN t2.input_task_week_2_day_6::text ELSE '📅 ' || t3.input_task_week_2_day_6 END 
            ELSE '' END AS input_task_week_2_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_2_day_7 IS NOT NULL THEN t2.input_task_week_2_day_7::text ELSE '📅 ' || t3.input_task_week_2_day_7 END 
            ELSE '' END AS input_task_week_2_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) ELSE '' END AS input_task_sum_week_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_1 IS NOT NULL THEN t2.input_task_week_3_day_1::text ELSE '📅 ' || t3.input_task_week_3_day_1 END
            ELSE '' END AS input_task_week_3_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_2 IS NOT NULL THEN t2.input_task_week_3_day_2::text ELSE '📅 ' || t3.input_task_week_3_day_2 END
            ELSE '' END AS input_task_week_3_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_3 IS NOT NULL THEN t2.input_task_week_3_day_3::text ELSE '📅 ' || t3.input_task_week_3_day_3 END 
            ELSE '' END AS input_task_week_3_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_4 IS NOT NULL THEN t2.input_task_week_3_day_4::text ELSE '📅 ' || t3.input_task_week_3_day_4 END 
            ELSE '' END AS input_task_week_3_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_5 IS NOT NULL THEN t2.input_task_week_3_day_5::text ELSE '📅 ' || t3.input_task_week_3_day_5 END 
            ELSE '' END AS input_task_week_3_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_6 IS NOT NULL THEN t2.input_task_week_3_day_6::text ELSE '📅 ' || t3.input_task_week_3_day_6 END 
            ELSE '' END AS input_task_week_3_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_3_day_7 IS NOT NULL THEN t2.input_task_week_3_day_7::text ELSE '📅 ' || t3.input_task_week_3_day_7 END 
            ELSE '' END AS input_task_week_3_day_7_txt,
    
        CASE WHEN COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣ ' || COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) ELSE '' END AS input_task_sum_week_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_1 IS NOT NULL THEN t2.input_task_week_4_day_1::text ELSE '📅 ' || t3.input_task_week_4_day_1 END
            ELSE '' END AS input_task_week_4_day_1_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_2 IS NOT NULL THEN t2.input_task_week_4_day_2::text ELSE '📅 ' || t3.input_task_week_4_day_2 END
            ELSE '' END AS input_task_week_4_day_2_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_3 IS NOT NULL THEN t2.input_task_week_4_day_3::text ELSE '📅 ' || t3.input_task_week_4_day_3 END 
            ELSE '' END AS input_task_week_4_day_3_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_4 IS NOT NULL THEN t2.input_task_week_4_day_4::text ELSE '📅 ' || t3.input_task_week_4_day_4 END 
            ELSE '' END AS input_task_week_4_day_4_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_5 IS NOT NULL THEN t2.input_task_week_4_day_5::text ELSE '📅 ' || t3.input_task_week_4_day_5 END 
            ELSE '' END AS input_task_week_4_day_5_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_6 IS NOT NULL THEN t2.input_task_week_4_day_6::text ELSE '📅 ' || t3.input_task_week_4_day_6 END 
            ELSE '' END AS input_task_week_4_day_6_txt,
        CASE WHEN COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) IS NOT NULL THEN 
            CASE WHEN t2.input_task_week_4_day_7 IS NOT NULL THEN t2.input_task_week_4_day_7::text ELSE '📅 ' || t3.input_task_week_4_day_7 END 
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
    
        CASE WHEN COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) IS NOT NULL THEN '📅 ' || ROUND(COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact)/8::numeric, 2) ELSE '' END AS task_sum_future_fact_txt,
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
        NULL AS task_plan_labor_cost,
        '' AS task_plan_labor_cost_txt,
        TRUE AS is_not_edited,
        NULL AS task_id,
        NULL AS tow_id,
        ARRAY[NULL::int] AS child_path,
        TRUE AS main_task,
        'last_row' AS class,
        '' AS task_number,
        'ИТОГО' AS task_name,
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
    
        CASE WHEN SUM(t3.hotr_value) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.hotr_value)/8::numeric, 2) ELSE '' END AS task_sum_fact_txt,
        SUM(t3.hotr_value) AS task_sum_fact,
    
        CASE WHEN SUM(t3.task_sum_previous_fact) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.task_sum_previous_fact)/8::numeric, 2) ELSE '' END AS task_sum_previous_fact_txt,
        SUM(t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
        --text format
        CASE WHEN SUM(t3.input_task_sum_week_1) IS NOT NULL THEN '7️⃣ ' || ROUND(SUM(t3.input_task_sum_week_1)/8::numeric, 2) ELSE '' END AS input_task_sum_week_1_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_1) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_2) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_3) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_4) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_5) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_6) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_1_day_7) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_1_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_1_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_2) IS NOT NULL THEN '7️⃣ ' || ROUND(SUM(t3.input_task_sum_week_2)/8::numeric, 2) ELSE '' END AS input_task_sum_week_2_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_1) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_2) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_3) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_4) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_5) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_6) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_2_day_7) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_2_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_2_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_3) IS NOT NULL THEN '7️⃣ ' || ROUND(SUM(t3.input_task_sum_week_3)/8::numeric, 2) ELSE '' END AS input_task_sum_week_3_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_1) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_2) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_3) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_4) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_5) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_6) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_3_day_7) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_3_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_3_day_7_txt,
        
        CASE WHEN SUM(t3.input_task_sum_week_4) IS NOT NULL THEN '7️⃣ ' || ROUND(SUM(t3.input_task_sum_week_4)/8::numeric, 2) ELSE '' END AS input_task_sum_week_4_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_1) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_1)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_1_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_2) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_2)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_2_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_3) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_3)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_3_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_4) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_4)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_4_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_5) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_5)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_5_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_6) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_6)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_6_txt,
        CASE WHEN SUM(t3.input_task_week_4_day_7) IS NOT NULL THEN '📅 ' || ROUND(SUM(t3.input_task_week_4_day_7)/8::numeric, 2) ELSE '' END AS input_task_week_4_day_7_txt,
        
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
        
        CASE WHEN SUM(t3.task_sum_future_fact) IS NOT NULL THEN '📅 ' || SUM(t3.task_sum_future_fact) ELSE '' END AS task_sum_future_fact_txt,
        SUM(t3.task_sum_future_fact) AS task_sum_future_fact
    
    FROM hotr AS t3;
"""

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
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

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
                if tow[i]['dept_id'] is not None:
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
            if is_head_of_dept is not None:
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
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

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

        if not link_name:
            link_name = app_contract.get_proj_id(project_id=project_id)
            link_name = dict(link_name)['link_name']

        project = app_project.get_proj_info(link_name)
        if project[0] == 'error':
            flash(message=project[1], category='error')
            return redirect(url_for('app_project.objects_main'))
        elif not project[1]:
            flash(message=['ОШИБКА. Проект не найден'], category='error')
            return redirect(url_for('app_project.objects_main'))
        proj = project[1]
        tep_info = False

        role = app_login.current_user.get_role()

        # Если объект закрыт и юзер не админ - ошибка. В закрытый проект пройти нельзя
        if proj['project_close_status'] and role not in (11, 4):
            flash(message=['Ошибка', proj['project_full_name'],'Проект закрыт', 'Ошибка доступа'], category='error')
            return redirect(url_for('app_project.objects_main'))

        # Статус, является ли пользователь руководителем отдела
        is_head_of_dept = FDataBase(conn).is_head_of_dept(user_id)

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
            [tow_id, tow_id, tow_id, tow_id])
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
            if is_head_of_dept is not None:
                tep_info = True

        return render_template('task-tasks.html', menu=hlink_menu, menu_profile=hlink_profile,
                               header_menu=header_menu, nonce=get_nonce(), tep_info=tep_info, tow_info=tow_info,
                               th_week_list=th_week_list, tasks=tasks, responsible=responsible, proj=proj,
                               task_statuses=task_statuses, title='Задачи раздела')

    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Страница задач сотрудника
@task_app_bp.route('/my_tasks', methods=['GET'])
@login_required
def get_my_tasks():
    """Страница задач пользователя"""
    try:
        global hlink_menu, hlink_profile

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

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

        where_labor_status_date = ''
        date_series_ls = None  # Список периодов подачи часов
        tmp_date_start, tmp_date_end = None, None  # Пара начала и окончания подачи часов

        # Границы недель для выбора другого периода на страницу
        min_other_period, max_other_period = '', ''

        for i in range(len(labor_status_list)):
            labor_status_list[i] = dict(labor_status_list[i])

            # Создаём список периодов в которых сотрудник отправлять часы
            if tmp_date_start and tmp_date_end:
                if not date_series_ls:
                    date_series_ls = f"""SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
                else:
                    date_series_ls += f""" UNION SELECT 
                    generate_series('{tmp_date_start}'::date, '{tmp_date_end}', '1 day')::date AS date"""
                tmp_date_start, tmp_date_end = None, None

            if labor_status_list[i]['empl_labor_status']:
                equal_sign = '>='
                tmp_date_start = labor_status_list[i]['empl_labor_date']
                min_other_period = min_other_period if min_other_period else tmp_date_start
            else:
                equal_sign = '<='
                if tmp_date_start:
                    tmp_date_end = labor_status_list[i]['empl_labor_date']
                max_other_period = labor_status_list[i]['empl_labor_date']

            if not where_labor_status_date:
                where_labor_status_date = f" hotr_date {equal_sign} '{labor_status_list[i]['empl_labor_date']}' "
            else:
                where_labor_status_date += f"AND hotr_date {equal_sign} '{labor_status_list[i]['empl_labor_date']}' "

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
            tmp_date_end = "(date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE"
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

            # Создаём список периодов в которых сотрудник отправлять часы
            if tmp_date_start and tmp_date_end:
                date_series_h_p_d_n += f""" AND hotr_date NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
                calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
                tmp_date_start, tmp_date_end = None, None

            if h_p_d_n_list[i]['full_day_status']:
                tmp_date_start = h_p_d_n_list[i]['empl_hours_date']
            elif tmp_date_start:
                tmp_date_end = h_p_d_n_list[i]['empl_hours_date']

        # Обрабатываем для последнего. Создаём список периодов в которых сотрудник отправлять часы
        if tmp_date_start and tmp_date_end:
            date_series_h_p_d_n += f""" AND hotr_date NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
            calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
            tmp_date_start, tmp_date_end = None, None

        # Если была найдена только дата старта, то добавляем дату окончания - сегодня
        if tmp_date_start and not tmp_date_end:
            tmp_date_end = "(date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE"
            date_series_h_p_d_n += f""" AND hotr_date NOT BETWEEN '{tmp_date_start}' AND {tmp_date_end} """
            calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND {tmp_date_end} """

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
                        extract(dow from holiday_date) AS day_week
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
                        WHEN t1.holiday_status THEN t1.holiday_status
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN TRUE
                        ELSE FALSE
                    END AS holiday_status,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'th_task_holiday th_week_day'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'th_task_work_day th_week_day'
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN 'th_task_holiday th_week_day'
                        ELSE 'th_task_work_day th_week_day'
                    END AS class,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'td_task_holiday'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'td_task_work_day'
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN 'td_task_holiday'
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
                        '' AS task_name
                    FROM task_responsible
                    WHERE user_id = %s
                    
                    UNION ALL
                    
                    SELECT
                        r.depth - 1,
                        r.task_responsible_id,
                        n.task_id,
                        n.tow_id AS parent_id,
                        n.tow_id,
                        r.task_status_id,
                        n.task_name || r.name_path,
                        
                        CASE
                            WHEN length(n.task_name) > 20 THEN SUBSTRING(n.task_name, 1, 17) || '...'
                            ELSE n.task_name
                        END || r.short_name_path,
          
                        r.child_path || n.task_id || n.lvl::int,
                        n.task_name
                    FROM rel_task_resp AS r
                    JOIN tasks AS n ON n.task_id = r.parent_id
                ),
                rel_rec AS (
                    SELECT
                        *
                    FROM rel_task_resp
                    WHERE parent_id = tow_id
                
                    UNION ALL
                
                    SELECT
                        r.depth - 1,
                        r.task_responsible_id,
                        r.task_id,
                        n.parent_id AS parent_id,
                        n.tow_id,
                        r.task_status_id,
                        n.tow_name || r.name_path,

                        CASE
                            WHEN length(n.tow_name) > 20 THEN SUBSTRING(n.tow_name, 1, 17) || '...'
                            ELSE n.tow_name
                        END || r.short_name_path,
                                        
                        r.child_path || n.tow_id || n.lvl::int,
                        n.tow_name
                    FROM rel_rec AS r
                    JOIN types_of_work AS n ON n.tow_id = r.parent_id
                )
                SELECT
                    CASE
                        WHEN t1.task_status_id = 4 THEN 'tr_task_status_closed'
                        ELSE 'tr_task_status_not_closed'
                    END AS task_class,
                    t1.task_id,
                    t1.task_responsible_id,
                    '' as task_number,
                    t1.task_status_id,
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
                    /*COALESCE(t6.input_task_week_1_day_1::text, '') AS input_task_week_1_day_1_txt,
                    COALESCE(t6.input_task_week_1_day_2::text, '') AS input_task_week_1_day_2_txt,
                    COALESCE(t6.input_task_week_1_day_3::text, '') AS input_task_week_1_day_3_txt,
                    COALESCE(t6.input_task_week_1_day_4::text, '') AS input_task_week_1_day_4_txt,
                    COALESCE(t6.input_task_week_1_day_5::text, '') AS input_task_week_1_day_5_txt,
                    COALESCE(t6.input_task_week_1_day_6::text, '') AS input_task_week_1_day_6_txt,
                    COALESCE(t6.input_task_week_1_day_7::text, '') AS input_task_week_1_day_7_txt,*/
                    
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_1) * 60), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_2) * 60), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_3) * 60), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_4) * 60), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_5) * 60), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_6) * 60), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                    COALESCE(to_char(to_timestamp((t6.input_task_week_1_day_7) * 60), 'MI:SS'), '') AS input_task_week_1_day_7_txt,
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
                ) AS t3 ON t1.task_id = t3.task_id
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
                        SUM(hotr_value) AS hotr_value
                    FROM public.hours_of_task_responsible
                    GROUP BY task_responsible_id
                ) AS t6 ON t1.task_responsible_id = t6.task_responsible_id
                WHERE parent_id IS NULL
                ORDER BY t4.project_id, t1.task_id, t1.task_responsible_id;""",
            [user_id]
        )

        tasks = cursor.fetchall()

        if len(tasks):
            for i in range(len(tasks)):
                tasks[i] = dict(tasks[i])
                proj_id = tasks[i]['project_id']
                tasks[i]['task_number'] = i + 1
                tasks[i]['project_full_name'] = proj_list[proj_id]['project_full_name']
                tasks[i]['project_short_name'] = proj_list[proj_id]['project_short_name']
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
                    i['hours_per_day_txt'] = ''
        else:
            tasks = False

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
                filtered_dates fd
            LEFT JOIN 
                public.hours_of_task_responsible htr 
            ON 
                fd.date = htr.hotr_date AND htr.task_responsible_id IN 
                    (SELECT 
                        task_responsible_id 
                    FROM task_responsible 
                    WHERE user_id = %s)
            WHERE 
                htr.hotr_date IS NULL 
            ORDER BY fd.date
            LIMIT 25;
            """,
            [user_id]
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
                SELECT 
                    hotr_date AS unapproved_date
                FROM 
                    public.hours_of_task_responsible AS t1 
                WHERE
                    t1.task_responsible_id IN 
                        (SELECT 
                            task_responsible_id 
                        FROM task_responsible 
                        WHERE user_id = %s)
                    AND approved_status IS FALSE
                GROUP BY hotr_date
                ORDER BY hotr_date 
                LIMIT 25;
                """,
            [user_id]
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
                    SELECT                         
                        hotr_date,
                        sum(hotr_value),
                            to_char(hotr_date, 'yy.mm.dd') || 
                            ' - ' || 
                            TRIM(TRAILING ',' FROM TRIM(TRAILING '0' FROM TRIM(TRAILING '0' FROM TRIM(BOTH ' ' FROM to_char(sum(hotr_value), '990D99')))))::TEXT || 
                            'ч.' AS not_full_hours
                    FROM 
                        public.hours_of_task_responsible
                    WHERE
                        task_responsible_id IN 
                            (SELECT 
                                task_responsible_id 
                            FROM task_responsible 
                            WHERE user_id = %s)
                        {date_series_h_p_d_n}
                    GROUP BY hotr_date
                    HAVING sum(hotr_value) != 8
                    ORDER BY hotr_date 
                    LIMIT 25;
                    """,
                [user_id]
            )

            not_full_sent_list = cursor.fetchall()

            if len(not_full_sent_list):
                for i in range(len(not_full_sent_list)):
                    not_full_sent_list[i] = dict(not_full_sent_list[i])
            else:
                not_full_sent_list = False
        else:
            not_full_sent_list = False

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
            flash(message=['Ошибка', 'Не найдены статусы задач', 'Страница недоступна'], category='error')
            return redirect(url_for('app_project.objects_main'))

        app_login.conn_cursor_close(cursor, conn)

        # Список меню и имя пользователя
        hlink_menu, hlink_profile = app_login.func_hlink_profile()


        return render_template('task-my-tasks.html', menu=hlink_menu, menu_profile=hlink_profile,
                               nonce=get_nonce(), calendar_cur_week=calendar_cur_week, tasks=tasks,
                               unsent_hours_list=unsent_hours_list, my_tasks_other_period = my_tasks_other_period,
                               unapproved_hours_list=unapproved_hours_list, current_period=current_period,
                               not_full_sent_list=not_full_sent_list,
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
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id)

        user_changes :dict = request.get_json()['userChanges']
        calendar = request.get_json()['calendar_cur_week']

        print(type(user_changes), user_changes)
        print(calendar)

        if user_changes == {}:
            return jsonify({
                'status': 'error',
                'description': ['Изменений не найдено'],
            })
        elif calendar == []:
            return jsonify({
                'status': 'error',
                'description': ['Ошибка с определением дат календаря'],
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
        # Для task_responsible создаём список task_responsible_id, task_id, user_id
        for task_id, v in user_changes.items():
            for task_responsible_id, vv in v.items():
                # Список для записи значений для одной записи в task_responsible
                tr_tmp = [
                    task_responsible_id,
                    task_id,
                    user_id,
                    '',                 # task_status_id / task_responsible_comment
                    user_id,            # owner
                    user_id,            # last_editor
                ]
                tr_flag = False  # Статус, что в task_responsible произошли изменения
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
                        tr_flag = True
                        if kkk == 'td_tow_task_statuses':
                            tr_tmp[4] = vvv
                            tr_status.append(tr_tmp)
                        elif kkk == 'input_task_responsible_comment':
                            tr_tmp[4] = vvv
                            tr_comment.append(tr_tmp)

        print('user_changes')
        print(user_changes)
        print('calendar_cur_week')
        print(calendar_cur_week)
        print('tr_status')
        print(tr_status)
        print('tr_comment')
        print(tr_comment)
        print('hours_of_task_responsible')
        print(hours_of_task_responsible)

        # Считываем информацию из БД и проверяем валидность изменений

        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('tasks')

        # Список статусов и комментарии задач сотрудника
        cursor.execute(
            f"""
                SELECT
                    task_responsible_id,
                    task_id,
                    task_status_id,
                    task_responsible_comment
                FROM task_responsible
                WHERE user_id = %s;
                """,
            [user_id]
        )
        tasks = cursor.fetchall()

        if len(tasks):
            for i in range(len(tasks)):
                tasks[i] = dict(tasks[i])
        else:
            return jsonify({
                'status': 'error',
                'description': ['Ошибка', 'Не найдено задач пользователя', 'Обновите страницу'],
            })


        # Список отправленных часов и дат сотрудника
        cursor.execute(
            f"""
                SELECT
                    hotr_id
                    task_responsible_id,
                    hotr_date,
                    hotr_value,
                    sent_status,
                    approved_status
                FROM hours_of_task_responsible
                WHERE 
                    task_responsible_id IN (SELECT task_responsible_id FROM task_responsible WHERE user_id = %s)
                    AND 
                    hotr_date BETWEEN %s AND %s ;
                    """,
            [user_id, day_1, day_7]
        )
        hotr = cursor.fetchall()

        if len(hotr):
            for i in range(len(hotr)):
                hotr[i] = dict(hotr[i])


        print('tasks')
        print(tasks)

        print('hotr')
        print(hotr)



        app_login.conn_cursor_close(cursor, conn)


        # Календарь за указанный период
        calendar_cur_week = user_week_calendar(user_id, period_date=day_1, tr_id_is_null=False, task_info=True)
        if calendar_cur_week['status'] == 'error':
            return jsonify({
                'status': calendar_cur_week['status'],
                'description': calendar_cur_week['description'],
            })
        calendar_cur_week, days_lst, tasks = (calendar_cur_week['calendar_cur_week'],
                                              calendar_cur_week['days_lst'],
                                              calendar_cur_week['task_dict'])

        print('calendar_cur_week')
        print(calendar_cur_week)

        # ПЕРВОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Проверка, наличия tr у task, tr принадлежит пользователю, не имеет статус закрыта, не имеет sent_status
        # ВТОРОЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Проверка, если нет статуса почасовой оплаты, то общее кол-во часов в сутки не более 8 часов, иначе не более 24 часов
        # ТРЕТЬЕ # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # уведомить, если отправлено в выходной день
        for i in hours_of_task_responsible:
            # наличия tr у task
            task_tr = True if i[0] in tasks.keys() and tasks[0]['task_id'] == i[-1] else False
            if not task_tr:
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', 'Ошибка при проверки привязки задачи', 'Обновите страницу'],
                })

            # tr принадлежит пользователю
            tr_user = True if i[0] in tasks.keys() else False
            if not tr_user:
                return jsonify({
                    'status': 'error',
                    'description': ['Ошибка', 'Задача больше не привязана к пользователю', 'Обновите страницу'],
                })

            # статуса почасовой оплаты
            hpdn_status = [x for x in calendar_cur_week if x['work_day'] == i[1]][0]
            tasks[i[0]]

            # Удаляем task_id, тк его не записываем в БД (нет такого поля, нужен был только для проверки)
            del i[-1]




        flash(message=['Изменение сохранены'], category='success')

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
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=other_period_date, user_id=user_id)

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
            {'link': f'/objects/unsent-labor-costs', 'name': 'Проверка невнесенных данных'},
        ])

    if cur_name is not None:
        header_menu[cur_name]['class'] = 'current'
        header_menu[cur_name]['name'] = header_menu[cur_name]['name'].upper()
    return header_menu


# Календарь пользователя со статусами почасовой оплаты, отпусков, статуса подачи часов
def user_week_calendar(user_id :int, period_date, tr_id_is_null :bool = True, task_info :bool = False) -> dict:
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

            # Создаём список периодов в которых сотрудник отправлять часы
            if tmp_date_start and tmp_date_end:
                date_series_h_p_d_n += f""" AND hotr_date NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
                calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
                tmp_date_start, tmp_date_end = None, None

            if h_p_d_n_list[i]['full_day_status']:
                tmp_date_start = h_p_d_n_list[i]['empl_hours_date']
            elif tmp_date_start:
                tmp_date_end = h_p_d_n_list[i]['empl_hours_date']

        # Обрабатываем для последнего. Создаём список периодов в которых сотрудник отправлять часы
        if tmp_date_start and tmp_date_end:
            calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND '{tmp_date_end}' """
            tmp_date_start, tmp_date_end = None, None

        # Если была найдена только дата старта, то добавляем дату окончания - сегодня
        if tmp_date_start and not tmp_date_end:
            tmp_date_end = "(date_trunc('week', CURRENT_DATE) + interval '6 days')::DATE"
            calendar_cur_week_h_p_d_n += f""" AND t0.work_day NOT BETWEEN '{tmp_date_start}' AND {tmp_date_end} """

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
                        extract(dow from holiday_date) AS day_week
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
                        WHEN t1.holiday_status THEN t1.holiday_status
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN TRUE
                        ELSE FALSE
                    END AS holiday_status,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'th_task_holiday th_week_day'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'th_task_work_day th_week_day'
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN 'th_task_holiday th_week_day'
                        ELSE 'th_task_work_day th_week_day'
                    END AS class,
                    CASE
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status THEN 'td_task_holiday'
                        WHEN t1.holiday_date IS NOT NULL AND t1.holiday_status IS FALSE THEN 'td_task_work_day'
                        WHEN extract(dow from t0.work_day) IN (0,6) THEN 'td_task_holiday'
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

        task_info = ['t3.task_name,', '''LEFT JOIN (
                        SELECT
                            task_id,
                            task_name
                        FROM tasks
                    ) AS t3 ON t1.task_id = t3.task_id'''] if task_info else ['', '']

        # Часы пользователя за указанный период
        cursor.execute(
            f"""
                    SELECT
                        t1.task_id,
                        t1.user_id,
                        t2.*,
                        {task_info[0]}
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_1) * 60), 'MI:SS'), '') AS input_task_week_1_day_1_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_2) * 60), 'MI:SS'), '') AS input_task_week_1_day_2_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_3) * 60), 'MI:SS'), '') AS input_task_week_1_day_3_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_4) * 60), 'MI:SS'), '') AS input_task_week_1_day_4_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_5) * 60), 'MI:SS'), '') AS input_task_week_1_day_5_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_6) * 60), 'MI:SS'), '') AS input_task_week_1_day_6_txt,
                        COALESCE(to_char(to_timestamp((t2.input_task_week_1_day_7) * 60), 'MI:SS'), '') AS input_task_week_1_day_7_txt
                    FROM task_responsible AS t1
                    LEFT JOIN (
                        SELECT
                            task_responsible_id,
                            approved_status,
                            sent_status,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_1,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_2,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_3,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_4,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_5,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_6,
                            CASE WHEN hotr_date = %s::DATE THEN hotr_value ELSE NULL END AS input_task_week_1_day_7
                        FROM hours_of_task_responsible
                    ) AS t2 ON t1.task_responsible_id = t2.task_responsible_id
                    {task_info[1]}

                    WHERE t1.user_id = %s {tr_id_is_null};""",
            [days_lst[0], days_lst[1], days_lst[2], days_lst[3], days_lst[4], days_lst[5], days_lst[6], user_id]
        )

        tasks = cursor.fetchall()

        app_login.conn_cursor_close(cursor, conn)

        task_dict = dict()

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
                    i['hours_per_day_txt'] = ''
        else:
            task_dict = False

        return {
            'status': 'success',
            'calendar_cur_week': calendar_cur_week,
            'days_lst': days_lst,
            'task_dict': task_dict,
        }

    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
        return {
            'status': 'error',
            'description': [msg_for_user],
        }