from PyQt5 import QtWidgets
from ui_header import Header

class LeadsWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Лиды — список (заглушка)")
        self.resize(880, 520)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(Header("Лиды"))

        filters = QtWidgets.QHBoxLayout()
        self.cb_only_active = QtWidgets.QCheckBox("Только активные")
        self.cb_only_active.setChecked(True)
        filters.addWidget(self.cb_only_active)
        filters.addStretch(1)
        root.addLayout(filters)

        self.table = QtWidgets.QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["ID", "Назначен", "Телефон", "Создан", "Активен", "Требования (prod/sales/obj)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)

        # Заглушечные данные
        data = [
            (101, "Иванов", "+7 900 111-22-33", "2025-10-15", "Да", "0.5 / 0.8 / 0.6"),
            (102, "Петров", "+7 900 222-33-44", "2025-10-16", "Да", "0.2 / 0.4 / 0.9"),
            (103, "Сидорова", "+7 900 333-44-55", "2025-10-17", "Нет", "0.9 / 0.4 / 0.3"),
        ]
        for row, rec in enumerate(data):
            self.table.insertRow(row)
            for col, val in enumerate(rec):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))
