from PyQt5 import QtWidgets
from ui_header import Header

class RegisterWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация (заглушка)")
        self.resize(480, 360)

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

        self.btn_register = QtWidgets.QPushButton("Зарегистрировать")
        self.btn_register.clicked.connect(self._stub)

        root.addLayout(form)
        root.addStretch(1)
        root.addWidget(self.btn_register)

    def _stub(self):
        QtWidgets.QMessageBox.information(self, "Заглушка",
            "Регистрация пока не подключена к БД Это 1-й этап: только окно регистрации.")
