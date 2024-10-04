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
TASK_LIST1 = """
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
	t0.task_number,
	t0.task_name,
    t0.depth,
    t0.lvl,
	t1.task_responsible_id,
	COALESCE(t1.task_responsible_comment, '') AS task_responsible_comment,
	t1.task_status_id,
	t1.user_id,
	t1.rowspan,
    t4.task_cnt,
	
	CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '📅 ' || COALESCE(t2.task_sum_fact, t3.task_sum_fact) ELSE '' END AS task_sum_fact_txt,
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
	t0.task_number,
	t0.task_name,
    t0.depth,
    t0.lvl,
	t1.task_responsible_id,
	COALESCE(t1.task_responsible_comment, '') AS task_responsible_comment,
	t1.task_status_id,
	t1.user_id,
	t1.rowspan,
    t4.task_cnt,
	
	CASE WHEN COALESCE(t2.task_sum_fact, t3.task_sum_fact) IS NOT NULL THEN '' || COALESCE(t2.task_sum_fact, t3.task_sum_fact) ELSE '' END AS task_sum_fact_txt,
    COALESCE(t2.task_sum_fact, t3.task_sum_fact) AS task_sum_fact,
	
	CASE WHEN COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) IS NOT NULL THEN '' || COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) ELSE '' END AS task_sum_previous_fact_txt,
    COALESCE(t2.task_sum_previous_fact, t3.task_sum_previous_fact) AS task_sum_previous_fact,
    
    --text format
	CASE WHEN COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) IS NOT NULL THEN '' || COALESCE(t2.input_task_sum_week_1, t3.input_task_sum_week_1) ELSE '' END AS input_task_sum_week_1_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_1, t3.input_task_week_1_day_1) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_1 IS NOT NULL THEN t2.input_task_week_1_day_1::text ELSE '' || t3.input_task_week_1_day_1 END
		ELSE '' END AS input_task_week_1_day_1_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_2, t3.input_task_week_1_day_2) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_2 IS NOT NULL THEN t2.input_task_week_1_day_2::text ELSE '' || t3.input_task_week_1_day_2 END
		ELSE '' END AS input_task_week_1_day_2_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_3, t3.input_task_week_1_day_3) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_3 IS NOT NULL THEN t2.input_task_week_1_day_3::text ELSE '' || t3.input_task_week_1_day_3 END 
		ELSE '' END AS input_task_week_1_day_3_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_4, t3.input_task_week_1_day_4) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_4 IS NOT NULL THEN t2.input_task_week_1_day_4::text ELSE '' || t3.input_task_week_1_day_4 END 
		ELSE '' END AS input_task_week_1_day_4_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_5, t3.input_task_week_1_day_5) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_5 IS NOT NULL THEN t2.input_task_week_1_day_5::text ELSE '' || t3.input_task_week_1_day_5 END 
		ELSE '' END AS input_task_week_1_day_5_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_6, t3.input_task_week_1_day_6) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_6 IS NOT NULL THEN t2.input_task_week_1_day_6::text ELSE '' || t3.input_task_week_1_day_6 END 
		ELSE '' END AS input_task_week_1_day_6_txt,
	CASE WHEN COALESCE(t2.input_task_week_1_day_7, t3.input_task_week_1_day_7) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_1_day_7 IS NOT NULL THEN t2.input_task_week_1_day_7::text ELSE '' || t3.input_task_week_1_day_7 END 
		ELSE '' END AS input_task_week_1_day_7_txt,
	
	CASE WHEN COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) IS NOT NULL THEN '' || COALESCE(t2.input_task_sum_week_2, t3.input_task_sum_week_2) ELSE '' END AS input_task_sum_week_2_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_1, t3.input_task_week_2_day_1) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_1 IS NOT NULL THEN t2.input_task_week_2_day_1::text ELSE '' || t3.input_task_week_2_day_1 END
		ELSE '' END AS input_task_week_2_day_1_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_2, t3.input_task_week_2_day_2) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_2 IS NOT NULL THEN t2.input_task_week_2_day_2::text ELSE '' || t3.input_task_week_2_day_2 END
		ELSE '' END AS input_task_week_2_day_2_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_3, t3.input_task_week_2_day_3) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_3 IS NOT NULL THEN t2.input_task_week_2_day_3::text ELSE '' || t3.input_task_week_2_day_3 END 
		ELSE '' END AS input_task_week_2_day_3_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_4, t3.input_task_week_2_day_4) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_4 IS NOT NULL THEN t2.input_task_week_2_day_4::text ELSE '' || t3.input_task_week_2_day_4 END 
		ELSE '' END AS input_task_week_2_day_4_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_5, t3.input_task_week_2_day_5) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_5 IS NOT NULL THEN t2.input_task_week_2_day_5::text ELSE '' || t3.input_task_week_2_day_5 END 
		ELSE '' END AS input_task_week_2_day_5_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_6, t3.input_task_week_2_day_6) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_6 IS NOT NULL THEN t2.input_task_week_2_day_6::text ELSE '' || t3.input_task_week_2_day_6 END 
		ELSE '' END AS input_task_week_2_day_6_txt,
	CASE WHEN COALESCE(t2.input_task_week_2_day_7, t3.input_task_week_2_day_7) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_2_day_7 IS NOT NULL THEN t2.input_task_week_2_day_7::text ELSE '' || t3.input_task_week_2_day_7 END 
		ELSE '' END AS input_task_week_2_day_7_txt,

	CASE WHEN COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) IS NOT NULL THEN '' || COALESCE(t2.input_task_sum_week_3, t3.input_task_sum_week_3) ELSE '' END AS input_task_sum_week_3_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_1, t3.input_task_week_3_day_1) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_1 IS NOT NULL THEN t2.input_task_week_3_day_1::text ELSE '' || t3.input_task_week_3_day_1 END
		ELSE '' END AS input_task_week_3_day_1_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_2, t3.input_task_week_3_day_2) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_2 IS NOT NULL THEN t2.input_task_week_3_day_2::text ELSE '' || t3.input_task_week_3_day_2 END
		ELSE '' END AS input_task_week_3_day_2_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_3, t3.input_task_week_3_day_3) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_3 IS NOT NULL THEN t2.input_task_week_3_day_3::text ELSE '' || t3.input_task_week_3_day_3 END 
		ELSE '' END AS input_task_week_3_day_3_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_4, t3.input_task_week_3_day_4) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_4 IS NOT NULL THEN t2.input_task_week_3_day_4::text ELSE '' || t3.input_task_week_3_day_4 END 
		ELSE '' END AS input_task_week_3_day_4_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_5, t3.input_task_week_3_day_5) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_5 IS NOT NULL THEN t2.input_task_week_3_day_5::text ELSE '' || t3.input_task_week_3_day_5 END 
		ELSE '' END AS input_task_week_3_day_5_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_6, t3.input_task_week_3_day_6) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_6 IS NOT NULL THEN t2.input_task_week_3_day_6::text ELSE '' || t3.input_task_week_3_day_6 END 
		ELSE '' END AS input_task_week_3_day_6_txt,
	CASE WHEN COALESCE(t2.input_task_week_3_day_7, t3.input_task_week_3_day_7) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_3_day_7 IS NOT NULL THEN t2.input_task_week_3_day_7::text ELSE '' || t3.input_task_week_3_day_7 END 
		ELSE '' END AS input_task_week_3_day_7_txt,

	CASE WHEN COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) IS NOT NULL THEN '' || COALESCE(t2.input_task_sum_week_4, t3.input_task_sum_week_4) ELSE '' END AS input_task_sum_week_4_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_1, t3.input_task_week_4_day_1) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_1 IS NOT NULL THEN t2.input_task_week_4_day_1::text ELSE '' || t3.input_task_week_4_day_1 END
		ELSE '' END AS input_task_week_4_day_1_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_2, t3.input_task_week_4_day_2) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_2 IS NOT NULL THEN t2.input_task_week_4_day_2::text ELSE '' || t3.input_task_week_4_day_2 END
		ELSE '' END AS input_task_week_4_day_2_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_3, t3.input_task_week_4_day_3) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_3 IS NOT NULL THEN t2.input_task_week_4_day_3::text ELSE '' || t3.input_task_week_4_day_3 END 
		ELSE '' END AS input_task_week_4_day_3_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_4, t3.input_task_week_4_day_4) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_4 IS NOT NULL THEN t2.input_task_week_4_day_4::text ELSE '' || t3.input_task_week_4_day_4 END 
		ELSE '' END AS input_task_week_4_day_4_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_5, t3.input_task_week_4_day_5) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_5 IS NOT NULL THEN t2.input_task_week_4_day_5::text ELSE '' || t3.input_task_week_4_day_5 END 
		ELSE '' END AS input_task_week_4_day_5_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_6, t3.input_task_week_4_day_6) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_6 IS NOT NULL THEN t2.input_task_week_4_day_6::text ELSE '' || t3.input_task_week_4_day_6 END 
		ELSE '' END AS input_task_week_4_day_6_txt,
	CASE WHEN COALESCE(t2.input_task_week_4_day_7, t3.input_task_week_4_day_7) IS NOT NULL THEN 
		CASE WHEN t2.input_task_week_4_day_7 IS NOT NULL THEN t2.input_task_week_4_day_7::text ELSE '' || t3.input_task_week_4_day_7 END 
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
	
	CASE WHEN COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) IS NOT NULL THEN '' || COALESCE(t2.task_sum_future_fact, t3.task_sum_future_fact) ELSE '' END AS task_sum_future_fact_txt,
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


ORDER BY t0.child_path, t0.lvl, t1.task_responsible_id;


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

        # print(role, objects[0])
        # print(role, objects[1])

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

        # Список задач вида работ
        cursor.execute(
            TASK_LIST,
            [tow_id, tow_id, tow_id, tow_id])
        tasks = cursor.fetchall()

        for i in range(len(tasks)):
            tasks[i] = dict(tasks[i])

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
        if responsible:
            for i in range(len(responsible)):
                responsible[i] = dict(responsible[i])

        # Список дней 4-х недель
        today = date.today()
        current_week_monday = today - timedelta(days=today.weekday())  # Дата текущего дня
        days_of_the_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']  # Дни недели
        th_week_list = []  # Список дат 4-х недель
        for i in range(0, 4):
            week_start = current_week_monday + timedelta(weeks=i - 1)
            week_dates = [
                {
                    'name': (week_start + timedelta(days=j)).strftime('%d.%m.%y'),
                    'class': "th_task_labor_1_day th_week_day" if j==0 else "th_task_labor th_week_day",
                    'day_week': days_of_the_week[j]
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

