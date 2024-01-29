from flask_login import UserMixin
from flask import url_for, current_app


class UserLogin(UserMixin):
    def from_db(self, user_id, db):
        self.__user = db.get_user(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return int(self.__user['user_id'])

    def get_name(self):
        return self.__user['first_name'] if self.__user else False

    def get_last_name(self):
        return self.__user['last_name'] if self.__user else False

    def get_surname(self):
        return self.__user['surname'] if self.__user else False

    def get_profile_name(self):
        return str(self.__user['last_name'] + ' ' + self.__user['first_name'][0].upper() + '.') if self.__user else "Без имени"

    def get_email(self):
        return self.__user['email'] if self.__user else "Без email"

    def get_role(self):
        return self.__user['user_role_id'] if self.__user else "Без роли"

    def get_priority(self):
        return self.__user['user_priority'] if self.__user else "Без приоритета"

    def get_avatar(self, app):
        img = None
        if not self.__user['avatar']:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: " + str(e))
        else:
            img = self.__user['avatar']

        return img

    def verifyExt(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG":
            return True
        return False
