from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
from ui_header import Header
import auth

class LoginWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, on_open_register, on_logged_in):
        super().__init__()
        self.setWindowTitle(app_title)
        self.on_open_register = on_open_register
        self.on_logged_in = on_logged_in

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)

        root.addWidget(Header(app_title, logo_path))

        card = QGroupBox('Вход')
        form = QVBoxLayout(card)
        form.setContentsMargins(12,12,12,12)
        form.setSpacing(12)

        self.login = QLineEdit()
        self.login.setPlaceholderText('Логин')
        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd.setPlaceholderText('Пароль')

        form.addWidget(QLabel('Логин'))
        form.addWidget(self.login)
        form.addWidget(QLabel('Пароль'))
        form.addWidget(self.pwd)

        actions = QHBoxLayout()
        btn_login = QPushButton('Войти')
        btn_login.clicked.connect(self.try_login)
        btn_reg = QPushButton('Регистрация')
        btn_reg.setObjectName('secondary')
        btn_reg.clicked.connect(self.on_open_register)
        actions.addWidget(btn_login)
        actions.addWidget(btn_reg)
        actions.addStretch(1)

        form.addLayout(actions)

        hint = QLabel('Вход по логину и паролю.')
        hint.setProperty('role','hint')
        form.addWidget(hint)

        root.addWidget(card)

    def try_login(self):
        ok, res = auth.login_by_login(self.login.text().strip(), self.pwd.text())
        if not ok:
            QMessageBox.warning(self, 'Ошибка входа', res)
            return
        self.on_logged_in(res)
