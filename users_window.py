from PyQt5 import QtWidgets, QtCore
from ui_header import Header

class UsersWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пользователи — список (заглушка)")
        self.resize(720, 480)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(Header("Пользователи"))

        self.table = QtWidgets.QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Логин", "Активн. лидов", "Всего лидов"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)

        # Заглушечные данные
        data = [
            (1, "Иванов Иван", "ivanov", 2, 7),
            (2, "Петров Пётр", "petrov", 0, 1),
            (3, "Сидорова Анна", "sidorova", 4, 12),
        ]
        for row, rec in enumerate(data):
            self.table.insertRow(row)
            for col, val in enumerate(rec):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))
