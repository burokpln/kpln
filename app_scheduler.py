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
import pandas as pd
from openpyxl import Workbook
import os
import tempfile
import sys
import re

scheduler_app_bp = Blueprint('app_scheduler', __name__)

dbase = None


# Define a function to retrieve nonce within the application context
def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@scheduler_app_bp.before_request
def before_request():
    app_login.before_request()



###################################################################################################
#               ОБНОВЛЕНИЕ СТАТУСОВ ДОЛГОВ ПО ОТПРАВКИ ЧАСОВ
###################################################################################################
def check_user_sent_hours():
    """Ежедневно обновляем статусы, кто не отправил часы. Только для работающих сотрудников"""
    try:
        # 1. Находим всех работающих сотрудников на текущий день
        # 2. Для каждого сотрудника находим даты, когда нужно подавать часы и почасовая оплата и полный день
        # 3. Проверяем, что часы отправлены, если нет, обновляем статус на False
        # 4. записываем изменения в таблицу

        user_id = app_login.current_user.get_id()
        app_login.set_info_log(log_url=sys._getframe().f_code.co_name, user_id=user_id,
                               ip_address=app_login.get_client_ip())


        # Connect to the database
        conn, cursor = app_login.conn_cursor_init_dict('users')

        ########################################################################
        #                 1. Находим всех работающих сотрудников на текущий день
        ########################################################################

        if app_login.current_user.is_authenticated:
            app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method,
                                   user_id=app_login.current_user.get_id(), ip_address=app_login.get_client_ip())
        else:
            app_login.set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method,
                                   ip_address=app_login.get_client_ip())
        return render_template('__po_payment_control.html', nonce=get_nonce())
    except Exception as e:
        msg_for_user = app_login.create_traceback(sys.exc_info())
