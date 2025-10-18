from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QMessageBox, QAbstractItemView
)
from ui_header import Header
from db import get_conn
from algorithms import fuzzy_match
from user_form import UserForm

class UsersWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, current_user_id: int):
        super().__init__()
        self.setWindowTitle(app_title)
        self.current_user_id = current_user_id

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)

        root.addWidget(Header(app_title, logo_path))

        tools = QHBoxLayout()
        tools.addWidget(QLabel('Поиск (ФИО/логин, Левенштейн ≤ 2):'))
        self.search = QLineEdit()
        self.search.setPlaceholderText('введите запрос...')
        self.search.textChanged.connect(self.apply_filter)
        tools.addWidget(self.search, 1)

        self.btn_refresh = QPushButton('Обновить')
        self.btn_open = QPushButton('Открыть')
        self.btn_new = QPushButton('Новый пользователь')
        self.btn_delete = QPushButton('Удалить')

        self.btn_refresh.clicked.connect(self.reload)
        self.btn_open.clicked.connect(self.open_selected)
        self.btn_new.clicked.connect(self.create_new)
        self.btn_delete.clicked.connect(self.delete_selected)

        tools.addStretch(1)
        tools.addWidget(self.btn_refresh)
        tools.addWidget(self.btn_open)
        tools.addWidget(self.btn_new)
        tools.addWidget(self.btn_delete)

        card = QGroupBox('Пользователи')
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12,12,12,12)
        lay.setSpacing(12)
        lay.addLayout(tools)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(['ID','ФИО','Логин','Активных лидов','Неактивных лидов','Звонков','Удалён'])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_selected)
        lay.addWidget(self.table)

        root.addWidget(card)

        self._raw_rows = []
        self.reload()

    def ensure_schema(self):
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

    def reload(self):
        self.ensure_schema()
        sql = (
            "SELECT u.id, COALESCE(u.full_name, CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name)) AS fio, "
            "u.login, COALESCE(u.is_deleted,0) AS is_deleted, "
            "(SELECT COUNT(*) FROM leads WHERE current_assignee_id=u.id AND is_active=1) AS active_leads, "
            "(SELECT COUNT(*) FROM leads WHERE current_assignee_id=u.id AND is_active=0) AS inactive_leads, "
            "(SELECT COUNT(*) FROM calls WHERE user_id=u.id AND COALESCE(is_deleted,0)=0) AS calls_cnt "
            "FROM users u ORDER BY fio"
        )
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql); self._raw_rows = cur.fetchall()
        self.apply_filter()

    def apply_filter(self):
        query = self.search.text().strip()
        self.table.setRowCount(0)
        for r in self._raw_rows:
            fio = r['fio'] or ''
            login = r['login'] or ''
            if query and not fuzzy_match(fio, login, query, 2):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(fio))
            self.table.setItem(row, 2, QTableWidgetItem(login))
            self.table.setItem(row, 3, QTableWidgetItem(str(r['active_leads'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(r['inactive_leads'])))
            self.table.setItem(row, 5, QTableWidgetItem(str(r['calls_cnt'])))
            self.table.setItem(row, 6, QTableWidgetItem('Да' if int(r['is_deleted'])==1 else 'Нет'))
        self.table.resizeColumnsToContents()

    def _selected_user_id(self) -> Optional[int]:
        sel = self.table.selectedItems()
        if not sel: return None
        return int(self.table.item(sel[0].row(), 0).text())

    def open_selected(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.information(self,'Открыть','Выберите пользователя'); return
        dlg = UserForm(uid, parent=self)
        dlg.exec()
        self.reload()

    def create_new(self):
        dlg = UserForm(None, parent=self)
        dlg.exec()
        self.reload()

    def delete_selected(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.information(self,'Удалить','Выберите пользователя'); return
        if uid == self.current_user_id:
            QMessageBox.warning(self,'Удаление запрещено','Нельзя удалить себя.'); return
        if QMessageBox.question(self,'Подтверждение','Пометить пользователя как удалённого?') != QMessageBox.Yes:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_deleted=1 WHERE id=%s", (uid,))
        self.reload()