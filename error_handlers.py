import flask
from flask import render_template, current_app, request, flash
import app_login
import sys

errorhandler_bp = flask.Blueprint('error_handlers', __name__)


def get_nonce():
    with current_app.app_context():
        nonce = current_app.config.get('NONCE')
    return nonce


@errorhandler_bp.before_request
def before_request():
    app_login.before_request()


# Обработчик ошибки 403
@errorhandler_bp.app_errorhandler(403)
def handle403(e):
    try:
        if app_login.current_user.is_authenticated:
            app_login.set_fatal_error_log(log_url=request.path[1:], log_description='Error 403',
                                          user_id=app_login.current_user.get_id(), ip_address=request.remote_addr)
        else:
            app_login.set_fatal_error_log(log_url=request.path[1:], log_description='Error 403',
                                          ip_address=request.remote_addr)
        hlink_menu, hlink_profile = app_login.func_hlink_profile()
        return render_template('page403.html', title="Нет доступа", menu=hlink_menu,
                                   menu_profile=hlink_profile), 403
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())


# Обработчик ошибки 404
@errorhandler_bp.app_errorhandler(404)
def handle404(e):
    try:
        if app_login.current_user.is_authenticated:
            app_login.set_fatal_error_log(log_url=request.path[1:], log_description='Error 404',
                                          user_id=app_login.current_user.get_id(), ip_address=request.remote_addr)
        else:
            app_login.set_fatal_error_log(log_url=request.path[1:], log_description='Error 404',
                                          ip_address=request.remote_addr)
        hlink_menu, hlink_profile = app_login.func_hlink_profile()
        return render_template('page404.html', title="Страница не найдена", menu=hlink_menu,
                                   menu_profile=hlink_profile), 404
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', 'msg_for_user'], nonce=get_nonce())


# Обработчик ошибки 401
@errorhandler_bp.app_errorhandler(401)
def handle401(e):
    try:
        app_login.set_fatal_error_log(log_url=request.path[1:], log_description='Error 401',
                                      ip_address=request.remote_addr)
        hlink_menu, hlink_profile = app_login.func_hlink_profile()
        return render_template('page401.html', title="Отказ в авторизации. Проверка не пройдена", menu=hlink_menu,
                                   menu_profile=hlink_profile), 401
    except Exception as e:
        msg_for_user = app_login.create_traceback(info=sys.exc_info(), flash_status=True)
        return render_template('page_error.html', error=['Ошибка', msg_for_user], nonce=get_nonce())
