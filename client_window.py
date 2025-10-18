from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox
from ui_header import Header

class ClientWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, full_name: str):
        super().__init__()
        self.setWindowTitle(app_title)
        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)
        root.addWidget(Header(app_title, logo_path))

        card = QGroupBox("Клиент")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12,12,12,12)
        lay.setSpacing(12)

        lay.addWidget(QLabel(f"Добро пожаловать, {full_name}!"))
        hint = QLabel("Рабочее окно клиента (скоро здесь появится функциональность).")
        hint.setProperty("role","hint")
        lay.addWidget(hint)

        root.addWidget(card)
