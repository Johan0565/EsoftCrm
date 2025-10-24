
from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QComboBox, QMessageBox, QGroupBox, QAbstractItemView
)
from ui_header import Header
from db import get_conn
from lead_form import LeadForm

EXECUTOR_ROLE_CODES = ('agent','manager','admin')

def load_executor_combo(combo: QComboBox, current_user_id:int):
    combo.clear()
    combo.addItem('Только я', current_user_id)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT u.id, COALESCE(u.full_name,u.login) as name
                     FROM users u
                     JOIN user_roles ur ON ur.user_id=u.id
                     JOIN roles r ON r.id=ur.role_id
                     WHERE u.is_active=1 AND r.code IN ({','.join(['%s']*len(EXECUTOR_ROLE_CODES))})
                     GROUP BY u.id, name
                     ORDER BY name""", EXECUTOR_ROLE_CODES)
            for row in cur.fetchall():
                combo.addItem(row['name'], row['id'])

class LeadsWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, current_user_id: int, current_user_name: str):
        super().__init__()
        self.setWindowTitle(app_title)
        self.current_user_id = current_user_id
        self.current_user_name = current_user_name

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(12)

        root.addWidget(Header(app_title, logo_path))

        bar = QHBoxLayout()
        bar.addWidget(QLabel('Ответственный:'))
        self.user_combo = QComboBox()
        bar.addWidget(self.user_combo, 1)

        bar.addWidget(QLabel('Активность:'))
        self.active_combo = QComboBox()
        self.active_combo.addItem('Только активные', 1)
        self.active_combo.addItem('Только неактивные', 0)
        self.active_combo.addItem('Все', None)
        bar.addWidget(self.active_combo)

        self.refresh_btn = QPushButton('Обновить')
        self.open_btn = QPushButton('Открыть')
        self.new_btn = QPushButton('Новый лид')
        self.delete_btn = QPushButton('Удалить')

        self.refresh_btn.clicked.connect(self.reload)
        self.open_btn.clicked.connect(self.open_selected)
        self.new_btn.clicked.connect(self.create_new)
        self.delete_btn.clicked.connect(self.delete_selected)

        bar.addStretch(1)
        bar.addWidget(self.refresh_btn)
        bar.addWidget(self.open_btn)
        bar.addWidget(self.new_btn)
        bar.addWidget(self.delete_btn)

        card = QGroupBox('Список лидов')
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12,12,12,12)
        card_lay.setSpacing(12)
        card_lay.addLayout(bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Пользователь', 'Контакты', 'Требования', 'Дата создания', 'Активен', 'assignee_id'
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(6, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_selected)

        card_lay.addWidget(self.table)
        root.addWidget(card)

        load_executor_combo(self.user_combo, self.current_user_id)
        idx = self.user_combo.findData(self.current_user_id)
        if idx != -1:
            self.user_combo.setCurrentIndex(idx)
        idx = self.active_combo.findData(1)
        if idx != -1:
            self.active_combo.setCurrentIndex(idx)

        self.reload()

    def _requirements_schema(self):
        with get_conn() as conn:
            with conn.cursor() as cur:
                for name in ('requirements', 'skills_requirements', 'skills'):
                    cur.execute('SHOW COLUMNS FROM leads LIKE %s', (name,))
                    if cur.fetchone():
                        return {'mode':'single', 'names':(name,)}
                triple = []
                for n in ('req_products','req_objections','req_sales'):
                    cur.execute('SHOW COLUMNS FROM leads LIKE %s', (n,))
                    if cur.fetchone():
                        triple.append(n)
                if len(triple)==3:
                    return {'mode':'triple', 'names':tuple(triple)}
        return {'mode':None, 'names':()}

    def reload(self):
        assignee_id = self.user_combo.currentData()
        is_active = self.active_combo.currentData()
        req = self._requirements_schema()

        base = [
            'l.id',
            'u.full_name AS assignee',
            'COALESCE(l.email, l.phone) AS contact',
            'l.created_at',
            'l.is_active',
            'l.current_assignee_id'
        ]

        if req['mode'] == 'single':
            base.insert(3, f"l.{req['names'][0]} AS requirements")
        elif req['mode'] == 'triple':
            n1,n2,n3 = req['names']
            base.insert(3, f"l.{n1} AS rp")
            base.insert(4, f"l.{n2} AS ro")
            base.insert(5, f"l.{n3} AS rs")

        sql = 'SELECT ' + ', '.join(base) + ' FROM leads l JOIN users u ON u.id = l.current_assignee_id WHERE 1=1 AND COALESCE(l.is_deleted,0)=0 '
        params = []
        if assignee_id is not None:
            sql += 'AND l.current_assignee_id = %s '
            params.append(assignee_id)
        if is_active is not None:
            sql += 'AND l.is_active = %s '
            params.append(is_active)
        sql += 'ORDER BY l.created_at DESC'

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(r['assignee'])))
            self.table.setItem(row, 2, QTableWidgetItem('' if r['contact'] is None else str(r['contact'])))

            req_text = ''
            if req['mode'] == 'single':
                req_text = '' if r['requirements'] is None else str(r['requirements'])
            elif req['mode'] == 'triple':
                rp = float(r.get('rp', 0) or 0)
                ro = float(r.get('ro', 0) or 0)
                rs = float(r.get('rs', 0) or 0)
                req_text = f'прод.: {rp:.2f}; возраж.: {ro:.2f}; продажи: {rs:.2f}'
            self.table.setItem(row, 3, QTableWidgetItem(req_text))

            self.table.setItem(row, 4, QTableWidgetItem(str(r['created_at'])))
            self.table.setItem(row, 5, QTableWidgetItem('Да' if int(r['is_active'])==1 else 'Нет'))
            self.table.setItem(row, 6, QTableWidgetItem(str(r['current_assignee_id'])))

        self.table.resizeColumnsToContents()

    def _selected(self) -> Optional[Tuple[int,int]]:
        sel = self.table.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        return int(self.table.item(row, 0).text()), int(self.table.item(row, 6).text())

    def open_selected(self):
        s = self._selected()
        if not s:
            QMessageBox.information(self, 'Открыть', 'Выберите лид в списке')
            return
        lead_id, _ = s
        LeadForm(lead_id, current_user_id=self.current_user_id, parent=self).exec()

    def create_new(self):
        LeadForm(None, current_user_id=self.current_user_id, parent=self).exec()
        self.reload()

    def delete_selected(self):
        s = self._selected()
        if not s:
            QMessageBox.information(self, 'Удалить', 'Выберите лид в списке')
            return
        row = self.table.currentRow()
        if self.table.item(row, 5).text() != 'Да':
            QMessageBox.warning(self, 'Удаление запрещено', 'Удалять можно только активные лиды.')
            return
        lead_id, _ = s
        if QMessageBox.question(self, 'Подтверждение', 'Удалить выбранный лид?') != QMessageBox.Yes:
            return
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute('UPDATE leads SET is_deleted=1 WHERE id=%s AND is_active=1 AND COALESCE(is_deleted,0)=0', (lead_id,))
            self.reload()
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка удаления', f'Удаление не удалось: {e}')
