from PyQt5 import QtWidgets, QtCore

class Header(QtWidgets.QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.title = QtWidgets.QLabel(title)
        self.title.setStyleSheet("font-family: Tahoma; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title, 1, QtCore.Qt.AlignLeft)
        logo = QtWidgets.QLabel("esoft")
        logo.setStyleSheet("font-family: Tahoma; font-size: 12px; color: rgb(84,110,122);")
        layout.addWidget(logo, 0, QtCore.Qt.AlignRight)
