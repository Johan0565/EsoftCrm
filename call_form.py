from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGroupBox, QMessageBox,
    QDateTimeEdit, QSpinBox, QTextEdit
)
from PySide6.QtCore import QDateTime
from db import get_conn

class CallForm(QDialog):
    def __init__(self, call_id: Optional[int], current_user_id:int, parent=None):
        super().__init__(parent)
        self.call_id = call_id
        self.current_user_id = current_user_id
        self.lead_id = None
        self.setWindowTitle('Звонок')

        root = QVBoxLayout(self); root.setContentsMargins(12,12,12,12); root.setSpacing(12)
        card = QGroupBox('Данные звонка'); lay = QVBoxLayout(card)

        line = QHBoxLayout()
        self.dt = QDateTimeEdit(); self.dt.setCalendarPopup(True)
        self.dt.setDateTime(QDateTime.currentDateTime())
        self.duration = QSpinBox(); self.duration.setRange(0, 24*60*60)
        line.addWidget(QLabel('Дата/время:')); line.addWidget(self.dt)
        line.addWidget(QLabel('Длительность, сек:')); line.addWidget(self.duration, 1)
        lay.addLayout(line)

        self.lead_info = QLabel('Лид: —')
        self.user_info = QLabel('Пользователь: —')
        lay.addWidget(self.lead_info)
        lay.addWidget(self.user_info)

        self.notes = QTextEdit(); self.notes.setPlaceholderText('Комментарий к звонку...')
        lay.addWidget(self.notes)

        btns = QHBoxLayout()
        self.btn_save = QPushButton('Сохранить')
        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.accept)
        self.btn_save.clicked.connect(self.save)
        btns.addWidget(self.btn_save); btns.addStretch(1); btns.addWidget(self.btn_close)
        lay.addLayout(btns)
        root.addWidget(card)

        if self.call_id is not None:
            self.load_call()

    def load_call(self):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id, lead_id, user_id, call_time, duration_seconds, notes FROM calls WHERE id=%s', (self.call_id,))
                c = cur.fetchone()
                if not c:
                    QMessageBox.warning(self,'Звонок','Не найден'); self.reject(); return
                self.lead_id = int(c['lead_id'])
                self.dt.setDateTime(QDateTime.fromString(str(c['call_time']), 'yyyy-MM-dd HH:mm:ss'))
                if c['duration_seconds'] is not None:
                    self.duration.setValue(int(c['duration_seconds']))
                self.notes.setPlainText('' if c['notes'] is None else str(c['notes']))

                cur.execute('SELECT COALESCE(email, phone) AS contact FROM leads WHERE id=%s', (self.lead_id,))
                L = cur.fetchone()
                lead_text = f'Лид: ID {self.lead_id}'
                if L and L['contact']:
                    lead_text += f' (контакт: {L["contact"]})'
                self.lead_info.setText(lead_text)

                cur.execute('SELECT COALESCE(full_name, login) AS uname FROM users WHERE id=%s', (c['user_id'],))
                U = cur.fetchone()
                self.user_info.setText('Пользователь: ' + (U['uname'] if U and U['uname'] else str(c['user_id'])))

    def save(self):
        if self.call_id is None:
            QMessageBox.warning(self,'Сохранение','Создавайте звонки из карточки лида.'); return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT is_active FROM leads WHERE id=%s', (self.lead_id,))
                if int(cur.fetchone()['is_active']) != 1:
                    QMessageBox.warning(self,'Запрещено','Лид неактивен — редактирование звонка запрещено.'); return
                cur.execute('UPDATE calls SET call_time=%s, duration_seconds=%s, notes=%s WHERE id=%s',
                            (self.dt.dateTime().toString('yyyy-MM-dd HH:mm:ss'),
                             self.duration.value(), self.notes.toPlainText().strip() or None, self.call_id))
        QMessageBox.information(self,'Звонок','Сохранено')
        self.accept()
