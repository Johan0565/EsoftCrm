import sys
from PyQt5 import QtWidgets
from register_window import RegisterWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = RegisterWindow()
    w.show()
    sys.exit(app.exec_())
