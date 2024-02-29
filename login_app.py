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
from db_data_conf import db_payments, db_users, db_objects, recapcha_key
from flask_wtf.recaptcha import RecaptchaField
import requests
import error_handlers


login_bp = Blueprint('login_app', __name__)

login_manager = LoginManager()
login_manager.login_view = 'login_app.login'
login_manager.login_message = ["Недостаточно прав для доступа", '']
login_manager.login_message_category = "error"

# reCAPCHA v3
RECAPTCHA_PUBLIC_KEY = recapcha_key()['RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = recapcha_key()['RECAPTCHA_PRIVATE_KEY']
# reCAPCHA v3 - localHost
RECAPTCHA_PUBLIC_KEY_LH = recapcha_key()['RECAPTCHA_PUBLIC_KEY_LH']
RECAPTCHA_PRIVATE_KEY_LH = recapcha_key()['RECAPTCHA_PRIVATE_KEY_LH']

RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


@login_bp.record_once
def on_load(state):
    try:
        login_manager.init_app(state.app)
    except Exception as e:
        flash(message=['Ошибка', f'on_load: {e}'], category='error')
        return render_template('page_error.html')
        # return f'on_load ❗❗❗ Ошибка \n---{e}'


# PostgreSQL database PAYMENT configuration
db_pay_name = db_payments()['db_name']
db_pay_user = db_payments()['db_user']
db_pay_password = db_payments()['db_password']
db_pay_host = db_payments()['db_host']
db_pay_port = db_payments()['db_port']

# PostgreSQL database PAYMENT configuration
db_user_name = db_users()['db_name']
db_user_user = db_users()['db_user']
db_user_password = db_users()['db_password']
db_user_host = db_users()['db_host']
db_user_port = db_users()['db_port']

# PostgreSQL database OBJECTS configuration
db_object_name = db_objects()['db_name']
db_object_user = db_objects()['db_user']
db_object_password = db_objects()['db_password']
db_object_host = db_objects()['db_host']
db_object_port = db_objects()['db_port']

dbase = None

# Меню страницы
hlink_menu = None

# Меню профиля
hlink_profile = None


# Конект к БД
def conn_init(db_name='payments'):
    try:
        if db_name == 'users':
            db_name = db_user_name
            db_user = db_user_user
            db_password = db_user_password
            db_host = db_user_host
            db_port = db_user_port
        elif db_name == 'payments':
            db_name = db_pay_name
            db_user = db_pay_user
            db_password = db_pay_password
            db_host = db_pay_host
            db_port = db_pay_port
        elif db_name == 'objects':
            db_name = db_object_name
            db_user = db_object_user
            db_password = db_object_password
            db_host = db_object_host
            db_port = db_object_port
        else:
            print(db_name, db_name)
            current_app.logger.info(f"conn_init - connectable database not specified")
            flash(message=['Ошибка', 'Не указано название БД'], category='error')
            return render_template('page_error.html')

        g.conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        return g.conn
    except Exception as e:
        flash(message=['Ошибка', f'conn_init: {e}'], category='error')
        return render_template('page_error.html')
        # return f'conn_init ❗❗❗ Ошибка \n---{e}'


# Закрытие соединения
def conn_cursor_close(cursor, conn):
    try:
        g.cursor.close()
        g.conn.close()
    except Exception as e:
        flash(message=['Ошибка', f'conn_cursor_close: {e}'], category='error')
        return render_template('page_error.html')
        # return f'conn_cursor_close ❗❗❗ Ошибка \n---{e}'


@login_manager.user_loader
def load_user(user_id):
    try:
        return UserLogin().from_db(user_id, dbase)
    except Exception as e:
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
        return render_template('page_error.html')
        # return f'before_request ❗❗❗ Ошибка \n---{e}'


@login_bp.teardown_app_request
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'conn'):
        g.conn.close()


def conn_cursor_init_dict(db_name='payments'):
    try:
        conn = conn_init(db_name)
        g.cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return conn, g.cursor
    except Exception as e:
        flash(
            message=['Ошибка', f'conn_cursor_init_dict: {e}'], category='error')
        return render_template('page_error.html')
        # return f'conn_cursor_init_dict ❗❗❗ Ошибка \n---{e}'


def conn_cursor_init(db_name='payments'):
    try:
        conn = conn_init(db_name)
        g.cursor = conn.cursor()
        return conn, g.cursor
    except Exception as e:
        flash(message=['Ошибка', f'conn_cursor_init: {e}'], category='error')
        return render_template('page_error.html')
        # return f'conn_cursor_init ❗❗❗ Ошибка \n---{e}'


@login_bp.route('/', methods=["POST", "GET"])
@login_required
def index():
    """Главная страница"""
    try:
        global hlink_menu, hlink_profile

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()

        return render_template('index.html', menu=hlink_menu,
                               menu_profile=hlink_profile, title='Главная страница')
    except Exception as e:
        flash(message=['Ошибка', f'index: {e}'], category='error')
        return render_template('page_error.html')
        # return f'❗❗❗ index \n---{e}'


@login_bp.route("/login", methods=["POST", "GET"])
def login():
    try:
        global hlink_menu, hlink_profile, RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()
        if current_user.is_authenticated:
            return redirect(url_for('login_app.index'))

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

            if user and check_password_hash(user['password'], password):
                userlogin = UserLogin().create(user)
                login_user(userlogin, remember=remain)
                conn.close()
                # flash(message=['Вы вошли в систему', ''], category='success')
                return redirect(request.args.get("next") or url_for("login_app.index"))

            else:
                flash(message=['Пользователь не найден', ''], category='error')

            conn.close()
            return redirect(url_for('.login'))

        return render_template("login.html", site_key=RECAPTCHA_PUBLIC_KEY,
                               title="Авторизация", menu=hlink_menu,
                               menu_profile=hlink_profile)
    except Exception as e:
        current_app.logger.info(
            f"url {request.path[1:]}  -  id {current_user.get_id()}  -  {e}")
        flash(message=['Ошибка', f'login: {e}'], category='error')
        return render_template('page_error.html')
        # return f'login ❗❗❗ Ошибка \n---{e}'


# @login_bp.route('/logout')
# @login_required
# def logout():
#     try:
#         global hlink_menu, hlink_profile
#
#         logout_user()
#         hlink_menu, hlink_profile = func_hlink_profile()
#         # flash(message=['Вы вышли из аккаунта', ''], category='success')
#
#         return redirect(request.args.get('next') or request.referrer)
#     except Exception as e:
#         flash(message=['Ошибка', f'logout: {e}'], category='error')
#         return render_template('page_error.html')
#         # return f'logout ❗❗❗ Ошибка \n---{e}'


@login_bp.route('/logout', methods=["POST"])
@login_required
def logout():
    try:
        global hlink_menu, hlink_profile

        logout_user()
        hlink_menu, hlink_profile = func_hlink_profile()
        flash(message=['Вы вышли из аккаунта', ''], category='success')

        return jsonify({'status': 'success'})
    except Exception as e:
        flash(message=['Ошибка', f'logout: {e}'], category='error')
        current_app.logger.info(f"url {request.path[1:]}  -  id {current_user.get_id()}  -  {e}")
        return jsonify({'status': 'error'})


@login_bp.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    try:
        global hlink_menu, hlink_profile
        name = current_user.get_name()

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()
        user_id = current_user.get_id()

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

            return render_template("login-profile.html", title="Профиль", menu=hlink_menu,
                                   menu_profile=hlink_profile, user=user, name=name)
    except Exception as e:
        flash(message=['Ошибка', f'profile: {e}'], category='error')
        current_app.logger.info(f"url {request.path[1:]}  -  id {current_user.get_id()}  -  {e}")
        return jsonify({'status': 'error'})


@login_bp.route('/changePas', methods=["POST"])
@login_required
def change_password():
    try:
        global hlink_menu, hlink_profile
        name = current_user.get_name()

        # Create profile name dict
        hlink_menu, hlink_profile = func_hlink_profile()
        user_id = current_user.get_id()

        password = request.get_json()['new_password']  # Новый пароль
        confirm_password = request.get_json()['confirm_password']  # Подтвердить пароль

        if password != confirm_password:
            flash(message=['Пароли не совпадают', ''], category='error')
            return jsonify({'status': 'error'})

        password_status = check_password(password)

        if password_status == 1:
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
        flash(message=['Ошибка. Пароль не изменен', f'change_password: {e}'], category='error')
        current_app.logger.info(f"url {request.path[1:]}  -  id {current_user.get_id()}  -  {e}")
        return jsonify({'status': 'error'})


def check_password(password):
    digits = '1234567890'
    upper_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lower_letters = 'abcdefghijklmnopqrstuvwxyz'
    symbols = '!@#$%^&*()-+'
    acceptable = digits+upper_letters+lower_letters+symbols

    passwd = set(password)
    if any(char not in acceptable for char in passwd):
        # flash(message=['Ошибка. Запрещенный спецсимвол', ''], category='error')
        return 'Ошибка. Запрещенный спецсимвол'
    else:
        recommendations = []
        if len(password) < 8:
            recommendations.append(f'увеличить число символов на {8-len(password)}')
        for what, message in ((digits,        'цифру'),
                              (symbols,       'спецсимвол'),
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
        if current_user.get_role() != 1:
            return abort(403)
        else:
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
                        # Close the database connection
                        conn.close()
                        return render_template("login-register.html",
                                               title="Регистрация новых пользователей", menu=hlink_menu,
                                               menu_profile=hlink_profile, roles=roles)
                    else:
                        conn.rollback()
                        conn.close()
                        return render_template("login-register.html",
                                               title="Регистрация новых пользователей", menu=hlink_menu,
                                               menu_profile=hlink_profile, roles=roles)

                except Exception as e:
                    flash(message=['register ❗❗❗ Ошибка',
                          str(e)], category='error')
                    return render_template("login-register.html", title="Регистрация новых пользователей",
                                           menu=hlink_menu,
                                           menu_profile=hlink_profile, roles=roles)

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
                                   menu_profile=hlink_profile, roles=roles)
    except Exception as e:
        flash(message=['Ошибка', f'register: {e}'], category='error')
        return render_template('page_error.html')
        # return f'register ❗❗❗ Ошибка \n---{e}'


@login_bp.route("/create_news", methods=["GET", "POST"])
@login_required
def create_news():
    try:
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

                    return render_template("news-create.html", title="Создать новость",
                                           not_save_val=not_save_val, menu=hlink_menu, menu_profile=hlink_profile,
                                           categories=categories)
                except Exception as e:
                    flash(
                        message=['Ошибка', f'create_news GET: {e}'], category='error')
                    return render_template('page_error.html')

            if request.method == 'POST':
                try:
                    user_id = current_user.get_id()

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
                                )
                                VALUES %s"""
                    value = [(user_id, news_title, news_subtitle,
                              news_description, news_img_link, news_category)]
                    execute_values(cursor, query, value)

                    conn.commit()

                    conn_cursor_close(cursor, conn)

                    flash(message=['Новость создана',
                          f'{news_title}'], category='success')

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
                    flash(
                        message=['Ошибка', f'create_news POST: {e}'], category='error')
                    current_app.logger.info(
                        f"url {request.path[1:]}  -  id {user_id}  -  {e}")
                    return redirect(url_for('.create_news'))

    except Exception as e:
        flash(message=['Ошибка', f'create_news: {e}'], category='error')
        return render_template('page_error.html')


def func_hlink_profile():
    # try:
    global hlink_menu, hlink_profile

    if current_user.is_authenticated:
        # Меню профиля
        hlink_profile = {
            "name": [current_user.get_profile_name(), '(Выйти)'], "url": "logout", "role_id": current_user.get_role()},

        # Check user role.
        # Role: Admin
        if current_user.get_role() == 1:
            # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
            hlink_menu = [
                {"menu_item": "Платежи", "sub_item":
                    [
                        {"name": "Добавить поступления", "url": "/cash-inflow",
                         "img": "/static/img/mainpage/cashinflow.png"},
                        {"name": "Новая заявка на оплату", "url": "/new-payment",
                         "img": "/static/img/mainpage/newpayment.png"},
                        {"name": "Согласование платежей", "url": "/payment-approval",
                         "img": "/static/img/mainpage/paymentapproval.png"},
                        {"name": "Оплата платежей", "url": "/payment-pay",
                         "img": "/static/img/mainpage/paymentpay.png"},
                        {"name": "Список платежей", "url": "/payment-list",
                         "img": "/static/img/mainpage/paymentlist.png"},
                    ]
                 },
                {"menu_item": "Администрирование", "sub_item":
                    [
                        {"name": "Создать новость", "url": "/create_news",
                         "img": "/static/img/mainpage/newscreate.png"},
                        {"name": "Регистрация пользователей", "url": "/register",
                         "img": "/static/img/mainpage/register.png"},

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
                         "img": "/static/img/mainpage/newpayment.png"},
                        {"name": "Согласование платежей", "url": "/payment-approval",
                         "img": "/static/img/mainpage/paymentapproval.png"},
                        {"name": "Список платежей", "url": "/payment-list",
                         "img": "/static/img/mainpage/paymentlist.png"},
                    ]
                 },
            ]

        # Role: buh
        elif current_user.get_role() == 6:
            # НОВЫЙ СПИСОК МЕНЮ - СПИСОК СЛОВАРЕЙ со словарями
            hlink_menu = [
                {"menu_item": "Платежи", "sub_item":
                    [
                        {"name": "Добавить поступления", "url": "/cash-inflow",
                         "img": "/static/img/mainpage/cashinflow.png"},
                        {"name": "Новая заявка на оплату", "url": "/new-payment",
                         "img": "/static/img/mainpage/newpayment.png"},
                        {"name": "Согласование платежей", "url": "/payment-approval",
                         "img": "/static/img/mainpage/paymentapproval.png"},
                        {"name": "Оплата платежей", "url": "/payment-pay",
                         "img": "/static/img/mainpage/paymentpay.png"},
                        {"name": "Список платежей", "url": "/payment-list",
                         "img": "/static/img/mainpage/paymentlist.png"},
                    ]
                 },
            ]

        else:
            hlink_menu = [
                {"menu_item": "Платежи", "sub_item":
                    [{"name": "Новая заявка на оплату", "url": "/new-payment",
                      "img": "/static/img/mainpage/newpayment.png"},
                     {"name": "Список платежей", "url": "/payment-list",
                      "img": "/static/img/mainpage/paymentlist.png"}, ]
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
    # except Exception as e:
    #     return f'func_hlink_profile ❗❗❗ Ошибка \n---{e}'
