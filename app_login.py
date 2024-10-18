import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values
from pprint import pprint
from flask import g, abort, request, render_template, redirect, flash, url_for, jsonify
from flask import get_flashed_messages, Blueprint, current_app, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from user_login import UserLogin
from FDataBase import FDataBase
from db_data_conf import db_payments, db_users, db_objects, db_contracts, db_logs, db_tasks, recapcha_key
from flask_wtf.recaptcha import RecaptchaField
import requests
import error_handlers
import traceback
import sys
import app_login

login_bp = Blueprint('app_login', __name__)

login_manager = LoginManager()
login_manager.login_view = 'app_login.login'
login_manager.login_message = ["Недостаточно прав для доступа", '']
login_manager.login_message_category = "error"

# reCAPCHA v3
RECAPTCHA_PUBLIC_KEY = recapcha_key()['RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = recapcha_key()['RECAPTCHA_PRIVATE_KEY']
# reCAPCHA v3 - localHost
RECAPTCHA_PUBLIC_KEY_LH = recapcha_key()['RECAPTCHA_PUBLIC_KEY_LH']
RECAPTCHA_PRIVATE_KEY_LH = recapcha_key()['RECAPTCHA_PRIVATE_KEY_LH']

RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


# Define a function to retrieve nonce within the application context
def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@login_bp.record_once
def on_load(state):
    try:
        login_manager.init_app(state.app)
    except Exception as e:
        flash(message=['Ошибка', f'on_load: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())
        # return f'on_load ❗❗❗ Ошибка \n---{e}'


# PostgreSQL database PAYMENT configuration
db_pay = db_payments()
db_pay_name = db_pay['db_name']
db_pay_user = db_pay['db_user']
db_pay_password = db_pay['db_password']
db_pay_host = db_pay['db_host']
db_pay_port = db_pay['db_port']

# PostgreSQL database PAYMENT configuration
db_user = db_users()
db_user_name = db_user['db_name']
db_user_user = db_user['db_user']
db_user_password = db_user['db_password']
db_user_host = db_user['db_host']
db_user_port = db_user['db_port']

# PostgreSQL database OBJECTS configuration
db_object = db_objects()
db_object_name = db_object['db_name']
db_object_user = db_object['db_user']
db_object_password = db_object['db_password']
db_object_host = db_object['db_host']
db_object_port = db_object['db_port']

# PostgreSQL database CONTRACTS configuration
db_contract = db_contracts()
db_contract_name = db_contract['db_name']
db_contract_user = db_contract['db_user']
db_contract_password = db_contract['db_password']
db_contract_host = db_contract['db_host']
db_contract_port = db_contract['db_port']

# PostgreSQL database LOGS configuration
db_log = db_logs()
db_log_name = db_log['db_name']
db_log_user = db_log['db_user']
db_log_password = db_log['db_password']
db_log_host = db_log['db_host']
db_log_port = db_log['db_port']

# PostgreSQL database TASKS configuration
db_task = db_tasks()
db_task_name = db_task['db_name']
db_task_user = db_task['db_user']
db_task_password = db_task['db_password']
db_task_host = db_task['db_host']
db_task_port = db_task['db_port']

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None


# Коннект к БД
def conn_init(db_name='payments'):
    try:
        if db_name == 'users':
            _db_name = db_user_name
            _db_user = db_user_user
            _db_password = db_user_password
            _db_host = db_user_host
            _db_port = db_user_port
        elif db_name == 'payments':
            _db_name = db_pay_name
            _db_user = db_pay_user
            _db_password = db_pay_password
            _db_host = db_pay_host
            _db_port = db_pay_port
        elif db_name == 'objects':
            _db_name = db_object_name
            _db_user = db_object_user
            _db_password = db_object_password
            _db_host = db_object_host
            _db_port = db_object_port
        elif db_name == 'contracts':
            _db_name = db_contract_name
            _db_user = db_contract_user
            _db_password = db_contract_password
            _db_host = db_contract_host
            _db_port = db_contract_port
        elif db_name == 'logs':
            _db_name = db_log_name
            _db_user = db_log_user
            _db_password = db_log_password
            _db_host = db_log_host
            _db_port = db_log_port
        elif db_name == 'tasks':
            _db_name = db_task_name
            _db_user = db_task_user
            _db_password = db_task_password
            _db_host = db_task_host
            _db_port = db_task_port
        else:
            print(db_name, db_name)
            current_app.logger.exception(f"conn_init - connectable database not specified")
            flash(message=['Ошибка', 'Не указано название БД'], category='error')
            return render_template('page_error.html', error=['Не указано название БД'], nonce=get_nonce())

        g.conn = psycopg2.connect(
            dbname=_db_name,
            user=_db_user,
            password=_db_password,
            host=_db_host,
            port=_db_port
        )
        return g.conn
    except Exception as e:
        current_app.logger.exception(f"url {request.path[1:]}  -  {e}")
        flash(message=['Ошибка', f'conn_init: Ошибка доступа к БД'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


# Закрытие соединения
def conn_cursor_close(cursor, conn):
    try:
        g.cursor.close()
        g.conn.close()
    except Exception as e:
        flash(message=['Ошибка', f'conn_cursor_close: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@login_manager.user_loader
def load_user(user_id):
    try:
        if dbase:
            return UserLogin().from_db(user_id, dbase)
        # else:
        #     return None
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return None


@login_bp.before_request
def before_request(db_name='payments'):
    try:
        # Установление соединения с БД перед выполнением запроса
        global dbase
        conn = conn_init(db_name)
        dbase = FDataBase(conn)

    except Exception as e:
        flash(message=['Ошибка', f'before_request: {e}'], category='error')
        return render_template('page_error.html', error=[e], nonce=get_nonce())


@login_bp.teardown_app_request
def close_db(error):
    """Закрываем соединение с БД, если оно было установлено"""
    if hasattr(g, 'conn'):
        g.conn.close()


def is_user_fired(user_id):
    conn, cursor = conn_cursor_init_dict("users")
    cursor.execute("SELECT is_fired FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else False


@login_bp.before_request
def check_user_status():
    user_id = session.get('_user_id')
    if user_id:
        if app_login.is_user_fired(user_id):
            session.clear()
            return app_login.logout_user()


def conn_cursor_init_dict(db_name='payments'):
    try:
        conn = conn_init(db_name)
        g.cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return conn, g.cursor
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


def conn_cursor_init(db_name='payments'):
    try:
        conn = conn_init(db_name)
        g.cursor = conn.cursor()
        return conn, g.cursor
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@login_bp.route("/login", methods=["POST", "GET"])
def login():
    try:
        global hlink_menu, hlink_profile, RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()
        if current_user.is_authenticated:
            set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method,
                         user_id=current_user.get_id())
            return redirect(url_for('app_project.objects_main'))

        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method)

        if request.headers['Host'] == '127.0.0.1:5000':
            RECAPTCHA_PUBLIC_KEY = RECAPTCHA_PUBLIC_KEY_LH
            RECAPTCHA_PRIVATE_KEY = RECAPTCHA_PRIVATE_KEY_LH

        if request.method == 'POST':
            conn = conn_init()
            dbase = FDataBase(conn)

            email = request.form.get('email')
            password = request.form.get('password')
            remain = request.form.get('remainme')

            secret_response = request.form['g-recaptcha-response']
            verify_response = requests.post(
                url=f'{RECAPTCHA_VERIFY_URL}?secret={RECAPTCHA_PRIVATE_KEY}&response={secret_response}').json()

            # if verify_response['success'] == False or verify_response['score'] < 0.5:
            if verify_response['success'] == False:
                return error_handlers.handle401(401)

            user = dbase.get_user_by_email(email)

            print("user['is_fired']", user['is_fired'])

            if user and not user['is_fired'] and check_password_hash(user['password'], password):
                userlogin = UserLogin().create(user)
                login_user(userlogin, remember=remain)
                conn.close()
                # flash(message=['Вы вошли в систему', ''], category='success')
                return redirect(request.args.get("next") or url_for("app_project.objects_main"))

            else:
                flash(message=['Ошибка', 'Пользователь не найден', ''], category='error')

            conn.close()
            return redirect(url_for('.login'))

        return render_template("login.html", site_key=RECAPTCHA_PUBLIC_KEY, title="Авторизация", menu=hlink_menu,
                               nonce=get_nonce(),
                               menu_profile=hlink_profile)
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@login_bp.route('/logout', methods=["POST"])
@login_required
def logout():
    try:
        global hlink_menu, hlink_profile

        user_id = current_user.get_id()
        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        logout_user()
        hlink_menu, hlink_profile = func_hlink_profile()
        flash(message=['Вы вышли из аккаунта', ''], category='success')

        return jsonify({'status': 'success'})
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error'})


@login_bp.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    try:
        global hlink_menu, hlink_profile

        user_id = current_user.get_id()
        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        name = current_user.get_name()

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()

        if request.method == 'GET':
            last_name = current_user.get_last_name()  # Фамилия
            first_name = current_user.get_name()  # Имя
            surname = current_user.get_surname()  # Отчество

            user = {
                'last_name': last_name,
                'first_name': first_name,
                'surname': surname,
                'user_id': user_id
            }

            return render_template("login-profile.html", title="Профиль", menu=hlink_menu, nonce=get_nonce(),
                                   menu_profile=hlink_profile, user=user, name=name)
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error'})


@login_bp.route('/changePas', methods=["POST"])
@login_required
def change_password():
    try:
        global hlink_menu, hlink_profile

        user_id = current_user.get_id()
        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        name = current_user.get_name()

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()

        password = request.get_json()['new_password']  # Новый пароль
        confirm_password = request.get_json()['confirm_password']  # Подтвердить пароль

        if password != confirm_password:
            flash(message=['Пароли не совпадают', ''], category='error')
            return jsonify({'status': 'error'})

        password_status = check_password(password)

        if password_status == 1:
            conn = conn_init("users")
            dbase = FDataBase(conn)
            res = dbase.set_password(password, user_id)
            if res:
                flash(message=['Пароль обновлён', ''], category='success')
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': 'error'})
        else:
            flash(message=['Пароль не изменен', password_status], category='error')
            return jsonify({'status': 'error'})
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return jsonify({'status': 'error'})


def check_password(password):
    digits = '1234567890'
    upper_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lower_letters = 'abcdefghijklmnopqrstuvwxyz'
    symbols = '!@#$%^&*()-+'
    acceptable = digits + upper_letters + lower_letters + symbols

    passwd = set(password)
    if any(char not in acceptable for char in passwd):
        # flash(message=['Ошибка. Запрещенный спецсимвол', ''], category='error')
        return 'Ошибка. Запрещенный спецсимвол'
    else:
        recommendations = []
        if len(password) < 8:
            recommendations.append(f'увеличить число символов на {8 - len(password)}')
        for what, message in ((digits, 'цифру'),
                              (symbols, 'спецсимвол'),
                              (upper_letters, 'заглавную букву'),
                              (lower_letters, 'строчную букву')):
            if all(char not in what for char in passwd):
                recommendations.append(f'добавить 1 {message}')

        if recommendations:
            rec = "Слабый пароль. Рекомендации: " + ", ".join(recommendations)
            # flash(message=['Пароль не изменен', rec], category='error')
            return rec
        else:
            # flash(message=['Пароль изменен', ''], category='success')
            return 1


@login_bp.route("/register", methods=["POST", "GET"])
@login_required
def register():
    try:
        user_id = current_user.get_id()
        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        if current_user.get_role() != 1:
            return abort(403)

        global hlink_menu, hlink_profile

        hlink_menu, hlink_profile = func_hlink_profile()

        if request.method == 'POST':
            try:
                conn = conn_init("users")
                dbase = FDataBase(conn)
                form_data = request.form
                res = dbase.add_user(form_data)

                conn, cursor = conn_cursor_init_dict("users")
                cursor.execute(
                    """SELECT 
                            *
                    FROM user_role;"""
                )
                roles = cursor.fetchall()
                conn_cursor_close(cursor, conn)
                if res:
                    return render_template("login-register.html", title="Регистрация новых пользователей",
                                           menu=hlink_menu, nonce=get_nonce(), menu_profile=hlink_profile,
                                           roles=roles)
                else:
                    msg_for_user = create_traceback(info=sys.exc_info(), error_type='warning', flash_status=True)
                    return render_template("login-register.html", title="Регистрация новых пользователей",
                                           menu=hlink_menu, nonce=get_nonce(), menu_profile=hlink_profile,
                                           roles=roles)

            except Exception as e:
                msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
                return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())

        if request.method == 'GET':
            conn, cursor = conn_cursor_init_dict("users")
            cursor.execute(
                """SELECT 
                        *
                FROM user_role;"""
            )
            roles = cursor.fetchall()
            conn_cursor_close(cursor, conn)

            return render_template("login-register.html", title="Регистрация новых пользователей", menu=hlink_menu,
                                   nonce=get_nonce(), menu_profile=hlink_profile, roles=roles)
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@login_bp.route("/create_news", methods=["GET", "POST"])
@login_required
def create_news():
    try:
        user_id = current_user.get_id()
        set_info_log(log_url=sys._getframe().f_code.co_name, log_description=request.method, user_id=user_id)

        if current_user.get_role() != 1:
            return abort(403)
        else:
            global hlink_menu, hlink_profile

            hlink_menu, hlink_profile = func_hlink_profile()

            if request.method == 'GET':
                try:
                    not_save_val = session['n_s_v_create_news'] if session.get(
                        'n_s_v_create_news') else {}

                    conn, cursor = conn_cursor_init_dict('users')

                    # Список категорий
                    cursor.execute(
                        "SELECT DISTINCT news_category FROM news_alerts")
                    categories = cursor.fetchall()

                    conn_cursor_close(cursor, conn)

                    return render_template("news-create.html", title="Создать новость", not_save_val=not_save_val,
                                           nonce=get_nonce(), menu=hlink_menu, menu_profile=hlink_profile,
                                           categories=categories)
                except Exception as e:
                    msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
                    return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())

            if request.method == 'POST':
                try:
                    news_title = request.form.get('news_title')  # Заголовок
                    news_subtitle = request.form.get('news_subtitle')  # Подзаголовок
                    news_description = request.form.get('news_description')  # Описание новости
                    news_img_link = request.form.get('news_img_link')  # Ссылка на картинку
                    news_category = request.form.get('news_category')  # Категория новости
                    news_category = news_category.replace(' ', '_')

                    if not news_title or not news_category:
                        flash(message=['Не заполнены обязательные поля',
                                       f'Поля: {"news_title, " if not news_title else ""} '
                                       f'{"news_category" if not news_category else ""}'], category='error')
                        session['n_s_v_create_news'] = {
                            'news_title': news_title,
                            'news_subtitle': news_subtitle,
                            'news_description': news_description,
                            'news_img_link': news_img_link,
                            'news_category': news_category
                        }
                        return redirect(url_for('.create_news'))

                    conn, cursor = conn_cursor_init_dict('users')

                    query = """
                                INSERT INTO news_alerts (
                                    owner_id,
                                    news_title,
                                    news_subtitle,
                                    news_description,
                                    news_img_link,
                                    news_category
                                ) VALUES %s"""
                    value = [(user_id, news_title, news_subtitle,
                              news_description, news_img_link, news_category)]
                    execute_values(cursor, query, value)

                    conn.commit()

                    conn_cursor_close(cursor, conn)

                    flash(message=['Новость создана', f'{news_title}'], category='success')

                    session.pop('n_s_v_create_news', default=None)

                    return redirect(url_for('.create_news'))
                except Exception as e:
                    session['n_s_v_create_news'] = {
                        'news_title': news_title,
                        'news_subtitle': news_subtitle,
                        'news_description': news_description,
                        'news_img_link': news_img_link,
                        'news_category': news_category
                    }
                    current_app.logger.exception(f"url {request.path[1:]} POST  -  id {user_id}  -  {e}")
                    flash(message=['Ошибка', f'create_news POST: {e}'], category='error')
                    return redirect(url_for('.create_news'))

    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


@login_bp.route('/reload_page', methods=['POST'])
def reload_page():
    flash(message=['Изменения отменены, страница обновлена'], category='info')
    return jsonify({
        'status': 'success'
    })



def func_hlink_profile():
    try:
        global hlink_menu, hlink_profile

        if current_user.is_authenticated:
            # Меню профиля
            hlink_profile = {
                "name": [current_user.get_profile_name(), '(Выйти)'], "url": "logout",
                "role_id": current_user.get_role()},

            # Check user role.
            # Role: Admin
            if current_user.get_role() == 1:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Добавить поступления", "url": "/cash-inflow",
                             "img": "/static/img/payments/cashinflow.png"},
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "Согласование платежей", "url": "/payment-approval",
                             "img": "/static/img/payments/paymentapproval.png"},
                            {"name": "Оплата платежей", "url": "/payment-pay",
                             "img": "/static/img/payments/paymentpay.png"},
                            {"name": "Список платежей", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"},
                        ]
                     },
                    {"menu_item": "Объекты", "sub_item":
                        [
                            {"name": "Объекты - Главная", "url": "/",
                             "img": "/static/img/payments/project.png"},
                        ]
                     },
                    {"menu_item": "Договоры", "sub_item":
                        [
                            {"name": "Свод", "url": "/contract-main",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Объекты", "url": "/contract-objects",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр договоров", "url": "/contract-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр актов", "url": "/contract-acts-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр платежей", "url": "/contract-payments-list",
                             "img": "/static/img/payments/contract.png"},
                        ]
                     },
                    {"menu_item": "Дополнительно", "sub_item":
                        [
                            {"name": "Сотрудники", "url": "/employees-list",
                             "img": "/static/img/payments/employee.png"},
                            {"name": "отчёты", "url": "#",
                             "img": "/static/img/payments/statistic.png"},
                            {"name": "Настройки", "url": "#",
                             "img": "/static/img/payments/setting.png"},
                        ]
                     },
                    {"menu_item": "Администрирование", "sub_item":
                        [
                            {"name": "Создать новость", "url": "/create_news",
                             "img": "/static/img/payments/newscreate.png"},
                            {"name": "Регистрация пользователей", "url": "/register",
                             "img": "/static/img/payments/register.png"},
                        ]
                     },
                ]

            # Role: Director
            elif current_user.get_role() == 4:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "Согласование платежей", "url": "/payment-approval",
                             "img": "/static/img/payments/paymentapproval.png"},
                            {"name": "Список платежей", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"},
                        ]
                     },
                    {"menu_item": "Объекты", "sub_item":
                        [
                            {"name": "Объекты - Главная", "url": "/",
                             "img": "/static/img/payments/project.png"},
                        ]
                     },
                    {"menu_item": "Договоры", "sub_item":
                        [
                            {"name": "Свод", "url": "/contract-main",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Объекты", "url": "/contract-objects",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр договоров", "url": "/contract-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр актов", "url": "/contract-acts-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр платежей", "url": "/contract-payments-list",
                             "img": "/static/img/payments/contract.png"},
                        ]
                     },
                    {"menu_item": "Дополнительно", "sub_item":
                        [
                            {"name": "Сотрудники", "url": "/employees-list",
                             "img": "/static/img/payments/employee.png"},
                            {"name": "отчёты", "url": "#",
                             "img": "/static/img/payments/statistic.png"},
                            {"name": "Настройки", "url": "#",
                             "img": "/static/img/payments/setting.png"},
                        ]
                     },
                ]

            # Role: lawyer
            elif current_user.get_role() == 5:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "Список платежей", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"},
                        ]
                     },
                    {"menu_item": "Объекты", "sub_item":
                        [
                            {"name": "Объекты - Главная", "url": "/",
                             "img": "/static/img/payments/project.png"},
                        ]
                     },
                    {"menu_item": "Договоры", "sub_item":
                        [
                            {"name": "Свод", "url": "/contract-main",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Объекты", "url": "/contract-objects",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр договоров", "url": "/contract-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр актов", "url": "/contract-acts-list",
                             "img": "/static/img/payments/contract.png"},
                            {"name": "Реестр платежей", "url": "/contract-payments-list",
                             "img": "/static/img/payments/contract.png"},
                        ]
                     },
                ]

            # Role: buh (*Для ТМ)
            elif current_user.get_role() == 6:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Добавить поступления", "url": "/cash-inflow",
                             "img": "/static/img/payments/cashinflow.png"},
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "Согласование платежей", "url": "/payment-approval",
                             "img": "/static/img/payments/paymentapproval.png"},
                            {"name": "Оплата платежей", "url": "/payment-pay",
                             "img": "/static/img/payments/paymentpay.png"},
                            {"name": "Список платежей", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"},
                        ]
                     },
                    {"menu_item": "Договоры", "sub_item":
                        [
                            {"name": "Реестр договоров", "url": "/contract-main",
                             "img": "/static/img/payments/contract.png"},
                        ]
                     },
                ]

            # Role: cheef_buh (*Для ЛВ)
            elif current_user.get_role() == 7:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Добавить поступления", "url": "/cash-inflow",
                             "img": "/static/img/payments/cashinflow.png"},
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "Согласование платежей", "url": "/payment-approval",
                             "img": "/static/img/payments/paymentapproval.png"},
                            {"name": "Оплата платежей", "url": "/payment-pay",
                             "img": "/static/img/payments/paymentpay.png"},
                            {"name": "Список платежей", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"},
                        ]
                     },
                    {"menu_item": "Сотрудники", "sub_item":
                        [
                            {"name": "Сотрудники", "url": "/employees-list",
                             "img": "/static/img/payments/employee.png"},
                            {"name": "Настройки", "url": "#",
                             "img": "/static/img/payments/setting.png"},
                        ]
                     },
                ]
            # Role: commercial_director (*Для Воскресенской)
            elif current_user.get_role() == 8:
                # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
                hlink_menu = [
                    {"menu_item": "Платежи", "sub_item":
                        [
                            {"name": "Новая заявка на оплату", "url": "/new-payment",
                             "img": "/static/img/payments/newpayment.png"},
                            {"name": "История входящих платежей", "url": "/payment-inflow-history-list",
                             "img": "/static/img/payments/paymentInflowHistory.png"},
                            {"name": "Список ваших заявок", "url": "/payment-list",
                             "img": "/static/img/payments/paymentlist.png"}
                        ]
                    },
                ]

            else:
                hlink_menu = [
                    {"menu_item": "Объекты", "sub_item":
                        [
                            {"name": "Объекты - Главная", "url": "/",
                             "img": "/static/img/payments/project.png"},
                        ]
                     },
                    {"menu_item": "Платежи", "sub_item":
                        [{"name": "Новая заявка на оплату", "url": "/new-payment",
                          "img": "/static/img/payments/newpayment.png"},
                         {"name": "Список платежей", "url": "/payment-list",
                          "img": "/static/img/payments/paymentlist.png"}, ]
                     },
                ]

        else:
            # Меню профиля
            hlink_profile = {
                "name": ["Гостевой доступ", '(Войти)'], "url": "login"},

            hlink_menu = [
                # {"menu_item": "Платежи", "sub_item":
                #     [
                #         {"name": "Новая заявка на оплату", "url": "new-payment",
                #          "img": "/static/img/menu/new-payment.png"},
                #     ]
                #  },
            ]

        return hlink_menu, hlink_profile
    except Exception as e:
        msg_for_user = create_traceback(info=sys.exc_info(), flash_status=True)
        return False


def create_traceback(info: list, flash_status: bool = False, error_type: str = 'fatal_error',
                     full_description: bool = False):
    try:
        ex_type, ex_value, ex_traceback = info

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)
        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            stack_trace.extend([
                f"  File \"{trace[0]}\", line {trace[1]}, in {trace[2]}",
                f"    {trace[3]}",
                f"{ex_type.__name__}: {ex_value}"
            ])

        stack_trace = '\n'.join(stack_trace)

        msg_for_user = f"{ex_type.__name__}: {ex_value}"
        print('     ОПИСАНИЕ ОШИБКИ create_traceback', error_type)

        exception_data = ''
        if error_type == 'warning':
            exception_data = 'traceback_warning'
        current_app.logger.exception(exception_data)

        if error_type == 'fatal_error':
            if current_user.is_authenticated:
                set_fatal_error_log(trace[2], stack_trace, current_user.get_id())
            else:
                set_fatal_error_log(trace[2], stack_trace)

            if flash_status:
                flash(message=['Ошибка', msg_for_user], category='error')

        elif error_type == 'warning':
            if current_user.is_authenticated:
                set_warning_log(trace[2], stack_trace, current_user.get_id())
            else:
                set_warning_log(trace[2], stack_trace)
        if not full_description:
            msg_for_user = f'Ошибка: {error_type}'
        return msg_for_user
    except Exception as e:
        set_fatal_error_log(log_url=sys._getframe().f_code.co_name, log_description=request.method)


def create_traceback_exception(info):
    ex_type, ex_value, ex_traceback = info
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()

    for trace in trace_back:
        stack_trace.extend([
            f"  File \"{trace[0]}\", line {trace[1]}, in {trace[2]}",
            f"    {trace[3]}",
            f"{ex_type.__name__}: {ex_value}"
        ])

    stack_trace = '\n'.join(stack_trace)
    return stack_trace


def set_fatal_error_log(log_url: str, log_description: str, user_id: int = None):
    try:
        conn, cursor = conn_cursor_init_dict('logs')

        query = """
            INSERT INTO log_fatal_error (
                log_url,
                log_description,
                user_id
            )
            VALUES %s"""
        value = [(log_url, log_description, user_id)]
        execute_values(cursor, query, value)

        conn.commit()

        conn_cursor_close(cursor, conn)
    except Exception as e:
        current_app.logger.exception('set_fatal_error_log')


def set_warning_log(log_url: str, log_description: str = None, user_id: int = None, info: list = None):
    try:
        conn, cursor = conn_cursor_init_dict('logs')

        query = """
            INSERT INTO log_warning (
                log_url,
                log_description,
                user_id
            )
            VALUES %s"""
        value = [(log_url, log_description, user_id)]
        execute_values(cursor, query, value)

        conn.commit()

        conn_cursor_close(cursor, conn)
    except Exception as e:
        current_app.logger.exception('set_warning_log')


def set_info_log(log_url: str, log_description: str = None, user_id: int = None):
    try:
        conn, cursor = conn_cursor_init_dict('logs')

        query = """
            INSERT INTO log_info (
                log_url,
                log_description,
                user_id
            )
            VALUES %s"""
        value = [(log_url, log_description, user_id)]
        execute_values(cursor, query, value)

        conn.commit()

        conn_cursor_close(cursor, conn)
    except Exception as e:
        current_app.logger.exception('set_info_log')
