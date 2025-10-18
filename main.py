import os, sys
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from db import init_schema
from login_window import LoginWindow
from register_window import RegisterWindow
from verify_dialog import VerifyDialog
from calls_window import CallsWindow
from auth import get_user_by_id
from PySide6.QtGui import QIcon
import sys, os
from pathlib import Path

def resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel)



def main():
    load_dotenv()
    init_schema()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("App.ico")))  # иконка окна
    style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    app_title = os.getenv('APP_TITLE', 'TransitDB')
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')


    def open_calls_for_user(user_id: int):
        user = get_user_by_id(user_id)
        if not user:
            return
        cw = CallsWindow(app_title, logo_path, user['id'], user['full_name'])
        cw.resize(900, 560)
        cw.show()
        app.calls_window = cw

    def on_logged_in(user):
        loginw.hide(); regw.hide()
        open_calls_for_user(user['id'])

    def show_verify(login):
        dlg = VerifyDialog(login, parent=regw)
        if dlg.exec():
            regw.hide(); loginw.hide()
            open_calls_for_user(dlg.user_id)
        else:
            regw.hide(); loginw.show()

    regw = RegisterWindow(app_title, logo_path,
                          on_open_login=lambda: (regw.hide(), loginw.show()),
                          on_registration_started=show_verify)

    loginw = LoginWindow(app_title, logo_path,
                         on_open_register=lambda: (loginw.hide(), regw.show()),
                         on_logged_in=on_logged_in)

    loginw.resize(450, 450)
    regw.resize(450, 600)

    loginw.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
