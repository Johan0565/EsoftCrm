from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QCheckBox
)
from db import get_conn
import bcrypt

def ensure_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            for col, ddl in [
                ('login', "ALTER TABLE users ADD COLUMN login VARCHAR(100) UNIQUE"),
                ('password_hash', "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"),
                ('first_name', "ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"),
                ('last_name', "ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"),
                ('middle_name', "ALTER TABLE users ADD COLUMN middle_name VARCHAR(100)"),
                ('skill_products', "ALTER TABLE users ADD COLUMN skill_products DECIMAL(3,2) NOT NULL DEFAULT 0"),
                ('skill_objections', "ALTER TABLE users ADD COLUMN skill_objections DECIMAL(3,2) NOT NULL DEFAULT 0"),
                ('skill_sales', "ALTER TABLE users ADD COLUMN skill_sales DECIMAL(3,2) NOT NULL DEFAULT 0"),
                ('is_deleted', "ALTER TABLE users ADD COLUMN is_deleted TINYINT(1) NOT NULL DEFAULT 0")
            ]:
                cur.execute("SHOW COLUMNS FROM users LIKE %s", (col,))
                if not cur.fetchone():
                    cur.execute(ddl)

def hash_password(pwd: str) -> str:
    if not pwd:
        return ''
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

class UserForm(QDialog):
    def __init__(self, user_id: Optional[int], parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle('Пользователь')
        ensure_schema()

        root = QVBoxLayout(self); root.setContentsMargins(12,12,12,12); root.setSpacing(12)

        card = QGroupBox('Данные'); form = QVBoxLayout(card)
        name_lay = QHBoxLayout()
        self.last_name = QLineEdit(); self.last_name.setPlaceholderText('Фамилия')
        self.first_name = QLineEdit(); self.first_name.setPlaceholderText('Имя')
        self.middle_name = QLineEdit(); self.middle_name.setPlaceholderText('Отчество')
        for w in (self.last_name,self.first_name,self.middle_name): name_lay.addWidget(w)
        form.addLayout(name_lay)

        skills = QHBoxLayout()
        self.skill_products = QDoubleSpinBox(); self.skill_products.setRange(0,1); self.skill_products.setSingleStep(0.05)
        self.skill_objections = QDoubleSpinBox(); self.skill_objections.setRange(0,1); self.skill_objections.setSingleStep(0.05)
        self.skill_sales = QDoubleSpinBox(); self.skill_sales.setRange(0,1); self.skill_sales.setSingleStep(0.05)
        skills.addWidget(QLabel('Знание продуктов')); skills.addWidget(self.skill_products)
        skills.addWidget(QLabel('Работа с возражениями')); skills.addWidget(self.skill_objections)
        skills.addWidget(QLabel('Навыки продаж')); skills.addWidget(self.skill_sales)
        form.addLayout(skills)

        login_lay = QHBoxLayout()
        self.login = QLineEdit(); self.login.setPlaceholderText('Логин')
        self.password = QLineEdit(); self.password.setPlaceholderText('Пароль'); self.password.setEchoMode(QLineEdit.Password)
        self.ch_pass = QCheckBox('сменить пароль')
        self.ch_pass.stateChanged.connect(self._toggle_pass)
        login_lay.addWidget(QLabel('Логин:')); login_lay.addWidget(self.login,1)
        login_lay.addWidget(QLabel('Пароль:')); login_lay.addWidget(self.password,1); login_lay.addWidget(self.ch_pass)
        form.addLayout(login_lay)

        btns = QHBoxLayout()
        self.btn_save = QPushButton('Сохранить'); self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.accept); self.btn_save.clicked.connect(self.save)
        btns.addWidget(self.btn_save); btns.addStretch(1); btns.addWidget(self.btn_close)
        form.addLayout(btns)
        root.addWidget(card)

        leads_card = QGroupBox('Назначенные лиды'); l_lay = QVBoxLayout(leads_card)
        self.leads_tbl = QTableWidget(0,5)
        self.leads_tbl.setHorizontalHeaderLabels(['ID','Телефон','Комментарий','Дата','Активен'])
        self.leads_tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.leads_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l_lay.addWidget(self.leads_tbl)
        root.addWidget(leads_card)

        calls_card = QGroupBox('Совершённые звонки'); c_lay = QVBoxLayout(calls_card)
        self.calls_tbl = QTableWidget(0,4)
        self.calls_tbl.setHorizontalHeaderLabels(['Дата/время','Лид','Длительность, с','Комментарий'])
        self.calls_tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.calls_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        c_lay.addWidget(self.calls_tbl)
        root.addWidget(calls_card)

        if self.user_id is not None:
            self.load_user()
            self.ch_pass.setChecked(False)
            self.password.setEnabled(False)

    def _toggle_pass(self, _):
        self.password.setEnabled(self.ch_pass.isChecked())

    def load_user(self):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, login, first_name, last_name, middle_name,
                           COALESCE(skill_products,0) sp, COALESCE(skill_objections,0) so, COALESCE(skill_sales,0) ss
                    FROM users WHERE id=%s
                """, (self.user_id,))
                u = cur.fetchone()
                if not u:
                    QMessageBox.warning(self,'Пользователь','Не найден'); self.reject(); return
                self.login.setText(u['login'] or '')
                self.first_name.setText(u['first_name'] or '')
                self.last_name.setText(u['last_name'] or '')
                self.middle_name.setText(u['middle_name'] or '')
                self.skill_products.setValue(float(u['sp'])); self.skill_objections.setValue(float(u['so'])); self.skill_sales.setValue(float(u['ss']))

                cur.execute("""
                    SELECT id, phone, comment, created_at, is_active
                    FROM leads WHERE current_assignee_id=%s ORDER BY created_at DESC
                """, (self.user_id,))
                leads = cur.fetchall()
                self.leads_tbl.setRowCount(0)
                for L in leads:
                    r = self.leads_tbl.rowCount(); self.leads_tbl.insertRow(r)
                    self.leads_tbl.setItem(r,0,QTableWidgetItem(str(L['id'])))
                    self.leads_tbl.setItem(r,1,QTableWidgetItem('' if L['phone'] is None else str(L['phone'])))
                    self.leads_tbl.setItem(r,2,QTableWidgetItem('' if L['comment'] is None else str(L['comment'])))
                    self.leads_tbl.setItem(r,3,QTableWidgetItem(str(L['created_at'])))
                    self.leads_tbl.setItem(r,4,QTableWidgetItem('Да' if int(L['is_active'])==1 else 'Нет'))
                self.leads_tbl.resizeColumnsToContents()

                cur.execute("""
                    SELECT c.call_time, c.lead_id, c.duration_seconds, c.notes
                    FROM calls c WHERE c.user_id=%s AND COALESCE(is_deleted,0)=0
                    ORDER BY c.call_time DESC
                """, (self.user_id,))
                calls = cur.fetchall()
        self.calls_tbl.setRowCount(0)
        for C in calls:
            r = self.calls_tbl.rowCount(); self.calls_tbl.insertRow(r)
            self.calls_tbl.setItem(r,0,QTableWidgetItem(str(C['call_time'])))
            self.calls_tbl.setItem(r,1,QTableWidgetItem(str(C['lead_id'])))
            self.calls_tbl.setItem(r,2,QTableWidgetItem('' if C['duration_seconds'] is None else str(C['duration_seconds'])))
            self.calls_tbl.setItem(r,3,QTableWidgetItem('' if C['notes'] is None else str(C['notes'])))
        self.calls_tbl.resizeColumnsToContents()

    def save(self):
        if not self.login.text().strip():
            QMessageBox.warning(self,'Проверка','Укажите логин'); return

        pwd_hash = None
        if self.user_id is None or self.ch_pass.isChecked():
            if not self.password.text().strip():
                QMessageBox.warning(self,'Проверка','Введите пароль'); return
            pwd_hash = hash_password(self.password.text().strip())

        values = (
            self.login.text().strip(),
            self.first_name.text().strip() or None,
            self.last_name.text().strip() or None,
            self.middle_name.text().strip() or None,
            self.skill_products.value(), self.skill_objections.value(), self.skill_sales.value()
        )

        with get_conn() as conn:
            with conn.cursor() as cur:
                if self.user_id is None:
                    cur.execute("""
                        INSERT INTO users(login, password_hash, first_name, last_name, middle_name,
                                          skill_products, skill_objections, skill_sales, is_deleted)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,0)
                    """, (values[0], pwd_hash, values[1], values[2], values[3], values[4], values[5], values[6]))
                    QMessageBox.information(self,'Пользователь','Создан')
                else:
                    if pwd_hash is not None:
                        cur.execute("""
                            UPDATE users SET login=%s, password_hash=%s, first_name=%s, last_name=%s, middle_name=%s,
                                skill_products=%s, skill_objections=%s, skill_sales=%s
                            WHERE id=%s
                        """, (values[0], pwd_hash, values[1], values[2], values[3], values[4], values[5], values[6], self.user_id))
                    else:
                        cur.execute("""
                            UPDATE users SET login=%s, first_name=%s, last_name=%s, middle_name=%s,
                                skill_products=%s, skill_objections=%s, skill_sales=%s
                            WHERE id=%s
                        """, (values[0], values[1], values[2], values[3], values[4], values[5], values[6], self.user_id))
                    QMessageBox.information(self,'Пользователь','Сохранено')
        self.accept()