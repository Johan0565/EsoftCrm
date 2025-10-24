from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox
import auth

class VerifyDialog(QDialog):
    def __init__(self, login: str, parent=None):
        super().__init__(parent)
        self.login = login
        self.user_id = None
        self.setWindowTitle('Подтверждение регистрации')
        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)

        card = QGroupBox('Подтверждение')
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12,12,12,12)
        lay.setSpacing(12)

        self.code = QLineEdit()
        self.code.setPlaceholderText('Код из письма (6 цифр)')
        self.code.setMaxLength(6)

        lay.addWidget(QLabel(f'Логин: {login}'))
        lay.addWidget(QLabel('Код из письма'))
        lay.addWidget(self.code)

        actions = QHBoxLayout()
        btn_ok = QPushButton('Подтвердить')
        btn_ok.clicked.connect(self.verify)
        btn_cancel = QPushButton('Отмена')
        btn_cancel.setObjectName('secondary')
        btn_cancel.clicked.connect(self.reject)
        actions.addWidget(btn_ok); actions.addWidget(btn_cancel); actions.addStretch(1)

        lay.addLayout(actions)
        hint = QLabel('Срок действия кода — 15 минут.')
        hint.setProperty('role','hint')
        lay.addWidget(hint)

        root.addWidget(card)

    def verify(self):
        ok, res = auth.verify_registration(self.login, self.code.text().strip())
        if not ok:
            QMessageBox.warning(self, 'Ошибка', res)
            return
        self.user_id = res
        self.accept()
