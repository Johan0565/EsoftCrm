from PyQt5 import QtWidgets
from ui_header import Header

class RegisterWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация (+ список пользователей)")
        self.resize(640, 420)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(Header("Регистрация"))

        form = QtWidgets.QFormLayout()
        self.fio = QtWidgets.QLineEdit()
        self.login = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("ФИО:", self.fio)
        form.addRow("Логин:", self.login)
        form.addRow("Пароль:", self.password)

        buttons = QtWidgets.QHBoxLayout()
        self.btn_register = QtWidgets.QPushButton("Зарегистрировать")
        self.btn_users = QtWidgets.QPushButton("Открыть список пользователей")
        self.btn_register.clicked.connect(self._stub)
        self.btn_users.clicked.connect(self.open_users)

        root.addLayout(form)
        root.addStretch(1)
        buttons.addWidget(self.btn_register)
        buttons.addWidget(self.btn_users)
        root.addLayout(buttons)

    def _stub(self):
        QtWidgets.QMessageBox.information(self, "Заглушка",
            "Регистрация пока не подключена к БД.
Этап 2: добавлен список пользователей.")

    def open_users(self):
        # Ленивый импорт, чтобы на этапах без файла не падало
        from users_window import UsersWindow
        w = UsersWindow(self)
        w.show()
