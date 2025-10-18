from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class Header(QWidget):
    def __init__(self, title: str, logo_path: str):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        logo = QLabel()
        pix = QPixmap(logo_path)
        # Высота логотипа 60 и сглаживание; фиксируем высоту, чтобы не сжимался по вертикали
        logo.setPixmap(pix.scaledToHeight(60, Qt.SmoothTransformation))
        logo.setFixedHeight(60)

        title_lbl = QLabel(title)
        title_lbl.setProperty("role", "title")

        # Центрируем группу логотип + заголовок
        layout.addStretch(1)
        layout.addWidget(logo)
        layout.addWidget(title_lbl)
        layout.addStretch(1)
