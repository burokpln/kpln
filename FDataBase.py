import json
import psycopg2
import psycopg2.extras
import time
import math
import re
from flask import url_for, flash, current_app
from werkzeug.security import generate_password_hash
from flask_wtf.recaptcha import RecaptchaField
import app_login
import sys


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def add_user(self, form_data):
        try:
            # Получаем данные из формы регистрации
            first_name = form_data.get('first_name')
            last_name = form_data.get('last_name')
            surname = form_data.get('surname')
            email = form_data.get('email')
            user_role = form_data.get('user_role')
            user_priority = form_data.get('user_priority')
            password = generate_password_hash(form_data.get('password'))

            query = """INSERT INTO users (first_name, last_name, surname, email, user_priority, password, user_role_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            values = (first_name, last_name, surname, email, user_priority, password, user_role)
            # Check to same email value in db
            self.__cur.execute(f"SELECT email FROM users WHERE email = '{email}'")
            res = self.__cur.fetchone()
            if res:
                flash(message=['Логин уже есть в базе', ''], category='error')
                return False

            self.__cur.execute(query, values)
            self.__db.commit()
            self.__cur.close()

            flash(message=['Пользователь внесен', ''], category='success')
            return True
        except Exception as e:
            msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
            return False

    def get_user(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE user_id = {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                flash(message=['Пользователь не найден', ''], category='error')
                return False

            return res
        except Exception as e:
            msg_for_user = app_login.create_traceback(info=sys.exc_info())
            flash(message=['Ошибка получения данных из БД', msg_for_user], category='error')
            return False

    def is_head_of_dept(self, user_id):
        try:
            self.__cur.execute(f"SELECT dept_id FROM list_dept WHERE head_of_dept_id = %s LIMIT 1", (user_id,))
            res = self.__cur.fetchone()
            return res
        except Exception as e:
            msg_for_user = app_login.create_traceback(info=sys.exc_info())
            flash(message=['Ошибка получения данных из БД', msg_for_user], category='error')
            return None

    def set_password(self, password, user_id):
        try:
            password = generate_password_hash(password)

            query = """UPDATE users SET password = %s WHERE user_id = %s"""

            value = [password, user_id]

            self.__cur.execute(query, value)
            self.__db.commit()
            self.__cur.close()
        except Exception as e:
            msg_for_user = app_login.create_traceback(info=sys.exc_info())
            flash(message=['Ошибка обновления пароля в БД', str(e)], category='error')
            return False

        return True

    def get_user_by_email(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                flash(message=['Пользователь не найден', ''], category='error')
                return False

            return res
        except Exception as e:
            msg_for_user = app_login.create_traceback(info=sys.exc_info())
            flash(message=['Ошибка получения данных из БД', msg_for_user], category='error')
            return False
