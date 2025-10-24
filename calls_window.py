from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QComboBox, QMessageBox, QGroupBox, QAbstractItemView
)
from ui_header import Header
from db import get_conn
from lead_form import LeadForm
from leads_window import LeadsWindow

class CallsWindow(QWidget):
    def __init__(self, app_title: str, logo_path: str, current_user_id: int, current_user_name: str):
        super().__init__()
        self.setWindowTitle(app_title)
        self.current_user_id = current_user_id
        self.current_user_name = current_user_name
        self.app_title = app_title; self.logo_path = logo_path

        root = QVBoxLayout(self); root.setContentsMargins(12,12,12,12); root.setSpacing(12)
        root.addWidget(Header(app_title, logo_path))

        bar = QHBoxLayout()
        lbl = QLabel('Пользователь:'); self.user_combo = QComboBox()
        self.refresh_btn = QPushButton('Обновить')
        self.open_btn = QPushButton('Открыть')
        self.new_btn = QPushButton('Новый звонок')
        self.delete_btn = QPushButton('Удалить')
        self.leads_btn = QPushButton('Лиды…')
        self.refresh_btn.clicked.connect(self.reload)
        self.open_btn.clicked.connect(self.open_selected)
        self.new_btn.clicked.connect(self.create_new)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.leads_btn.clicked.connect(self.open_leads)
        bar.addWidget(lbl); bar.addWidget(self.user_combo,1); bar.addStretch(1)
        for b in (self.refresh_btn,self.open_btn,self.new_btn,self.delete_btn,self.leads_btn): bar.addWidget(b)

        card = QGroupBox('Список звонков'); card_lay=QVBoxLayout(card)
        card_lay.setContentsMargins(12,12,12,12); card_lay.setSpacing(12)
        card_lay.addLayout(bar)

        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(['ID','Дата звонка','Пользователь','Контакт лида','Длительность, c','lead_active'])
        self.table.setColumnHidden(0, True); self.table.setColumnHidden(5, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_selected)
        card_lay.addWidget(self.table); root.addWidget(card)

        self.load_users(); self.reload()

    def open_leads(self):
        wnd = LeadsWindow(self.app_title, self.logo_path, self.current_user_id, self.current_user_name)
        wnd.resize(900, 560); wnd.show(); self._leads_window = wnd

    def load_users(self):
        self.user_combo.clear(); self.user_combo.addItem('Только я', self.current_user_id)
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, full_name FROM users ORDER BY full_name')
                for r in cur.fetchall(): self.user_combo.addItem(r['full_name'], r['id'])
        i=self.user_combo.findData(self.current_user_id)
        if i!=-1: self.user_combo.setCurrentIndex(i)

    def reload(self):
        uid=self.user_combo.currentData()
        sql=('SELECT c.id, c.call_time, u.full_name AS user_name, '
             'COALESCE(l.email,l.phone) AS lead_contact, c.duration_seconds, l.is_active AS lead_active '
             'FROM calls c JOIN users u ON u.id=c.user_id JOIN leads l ON l.id=c.lead_id '
             'WHERE COALESCE(c.is_deleted,0)=0 AND (%s IS NULL OR c.user_id=%s) ORDER BY c.call_time DESC')
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(uid,uid)); rows=cur.fetchall()
        self.table.setRowCount(0)
        for r in rows:
            row=self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row,0,QTableWidgetItem(str(r['id'])))
            self.table.setItem(row,1,QTableWidgetItem(str(r['call_time'])))
            self.table.setItem(row,2,QTableWidgetItem(str(r['user_name'])))
            self.table.setItem(row,3,QTableWidgetItem('' if r['lead_contact'] is None else str(r['lead_contact'])))
            self.table.setItem(row,4,QTableWidgetItem('' if r['duration_seconds'] is None else str(r['duration_seconds'])))
            self.table.setItem(row,5,QTableWidgetItem(str(r['lead_active'])))
        self.table.resizeColumnsToContents()

    def _selected(self)->Optional[Tuple[int,int]]:
        sel=self.table.selectedItems()
        if not sel: return None
        row=sel[0].row()
        return int(self.table.item(row,0).text()), int(self.table.item(row,5).text())

    def open_selected(self):
        s=self._selected()
        if not s: QMessageBox.information(self,'Открыть','Выберите звонок'); return
        call_id,_=s
        from call_form import CallForm
        CallForm(call_id, self.current_user_id, parent=self).exec()

    def create_new(self):
        QMessageBox.information(self,'Новый звонок','Создайте звонок из карточки конкретного лида.')

    def delete_selected(self):
        s=self._selected()
        if not s: QMessageBox.information(self,'Удалить','Выберите звонок'); return
        call_id, lead_active = s
        if lead_active==0:
            QMessageBox.warning(self,'Удаление запрещено','Нельзя удалить звонок по неактивному лиду.'); return
        if QMessageBox.question(self,'Подтверждение','Удалить выбранный звонок?')!=QMessageBox.Yes: return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE calls SET is_deleted=1 WHERE id=%s',(call_id,))
        self.reload()
