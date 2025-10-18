from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
from ui_header import Header
import auth

class RegisterWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, on_open_login, on_registration_started):
        super().__init__()
        self.setWindowTitle(app_title)
        self.on_open_login = on_open_login
        self.on_registration_started = on_registration_started

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)

        root.addWidget(Header(app_title, logo_path))

        card = QGroupBox('Регистрация')
        form = QVBoxLayout(card)
        form.setContentsMargins(12,12,12,12)
        form.setSpacing(12)

        self.full_name = QLineEdit()
        self.login = QLineEdit()
        self.email = QLineEdit()
        self.pwd = QLineEdit(); self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd2 = QLineEdit(); self.pwd2.setEchoMode(QLineEdit.Password)

        form.addWidget(QLabel('ФИО'))
        form.addWidget(self.full_name)
        form.addWidget(QLabel('Логин'))
        form.addWidget(self.login)
        form.addWidget(QLabel('Email'))
        form.addWidget(self.email)
        form.addWidget(QLabel('Пароль'))
        form.addWidget(self.pwd)
        form.addWidget(QLabel('Повторите пароль'))
        form.addWidget(self.pwd2)

        actions = QHBoxLayout()
        btn_send = QPushButton('Получить код на почту')
        btn_send.clicked.connect(self.start_registration)
        btn_login = QPushButton('Ко входу')
        btn_login.setObjectName('secondary')
        btn_login.clicked.connect(self.on_open_login)
        actions.addWidget(btn_send)
        actions.addWidget(btn_login)
        actions.addStretch(1)

        form.addLayout(actions)
        hint = QLabel('На почту придёт 6-значный код подтверждения.')
        hint.setProperty('role','hint')
        form.addWidget(hint)

        root.addWidget(card)

    def start_registration(self):
        if self.pwd.text() != self.pwd2.text():
            QMessageBox.warning(self, 'Ошибка', 'Пароль и подтверждение не совпадают')
            return
        try:
            auth.send_registration_code(
                self.full_name.text().strip(),
                self.login.text().strip(),
                self.email.text().strip(),
                self.pwd.text()
            )
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка регистрации', str(e))
            return
        self.on_registration_started(self.login.text().strip())
