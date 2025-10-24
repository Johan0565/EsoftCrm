from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QMessageBox, QAbstractItemView
)
from ui_header import Header
from db import get_conn
from algorithms import fuzzy_match
from user_form import UserForm

def _is_admin(user_id: int) -> bool:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT 1
                              FROM user_roles ur
                              JOIN roles r ON r.id=ur.role_id
                              WHERE ur.user_id=%s AND r.code='admin'
                              LIMIT 1""", (user_id,))
                return cur.fetchone() is not None
    except Exception:
        return False

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

        # delete доступна только администратору
        self.btn_delete.setEnabled(_is_admin(self.current_user_id))

        self._raw_rows = []
        self.reload()

    def reload(self):
        sql = (
            "SELECT u.id, u.full_name AS fio, u.login, COALESCE(u.is_deleted,0) AS is_deleted, "
            "(SELECT COUNT(*) FROM leads WHERE current_assignee_id=u.id AND is_active=1 AND COALESCE(is_deleted,0)=0) AS active_leads, "
            "(SELECT COUNT(*) FROM leads WHERE current_assignee_id=u.id AND is_active=0 AND COALESCE(is_deleted,0)=0) AS inactive_leads, "
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
        dlg = UserForm(uid, current_user_id=self.current_user_id, parent=self)
        dlg.exec()
        self.reload()

    def create_new(self):
        dlg = UserForm(None, current_user_id=self.current_user_id, parent=self)
        dlg.exec()
        self.reload()

    def delete_selected(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.information(self,'Удалить','Выберите пользователя'); return
        if uid == self.current_user_id:
            QMessageBox.warning(self,'Удаление запрещено','Нельзя удалить себя.'); return
        if not _is_admin(self.current_user_id):
            QMessageBox.warning(self, 'Удаление запрещено', 'Удалять пользователей может только администратор.')
            return
        if QMessageBox.question(self,'Подтверждение','Полностью удалить пользователя из БД? Это действие нельзя отменить.') != QMessageBox.Yes:
            return
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Переназначаем все лиды на текущего админа
                    cur.execute("UPDATE leads SET current_assignee_id=%s WHERE current_assignee_id=%s", (self.current_user_id, uid))
                    # Чистим зависимые записи (где нет каскада)
                    cur.execute("DELETE FROM calls WHERE user_id=%s", (uid,))
                    cur.execute("DELETE FROM lead_assignments WHERE user_id=%s", (uid,))
                    # Остальные связи имеют CASCADE, но выполним безопасно
                    cur.execute("DELETE FROM auth_credentials WHERE user_id=%s", (uid,))
                    cur.execute("DELETE FROM email_verification_codes WHERE user_id=%s", (uid,))
                    cur.execute("DELETE FROM user_roles WHERE user_id=%s", (uid,))
                    cur.execute("DELETE FROM user_skills WHERE user_id=%s", (uid,))
                    # Наконец удаляем пользователя
                    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
            QMessageBox.information(self, 'Удаление', 'Пользователь полностью удалён.')
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка удаления', f'Не удалось удалить: {e}')
        self.reload()