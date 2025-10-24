from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QMessageBox, QAbstractItemView
)
from db import get_conn

# Только эти роли могут быть ответственными исполнителями
EXECUTOR_ROLE_CODES = ('agent', 'manager', 'admin')

def ensure_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # leads.comment
            cur.execute("SHOW COLUMNS FROM leads LIKE %s", ('comment',))
            if not cur.fetchone():
                cur.execute("ALTER TABLE leads ADD COLUMN comment TEXT NULL")
            # требования лида (3 компонента)
            for col in ('req_products', 'req_objections', 'req_sales'):
                cur.execute("SHOW COLUMNS FROM leads LIKE %s", (col,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE leads ADD COLUMN {col} DECIMAL(3,2) NOT NULL DEFAULT 0")
            # навыки пользователя
            for col in ('skill_products', 'skill_objections', 'skill_sales'):
                cur.execute("SHOW COLUMNS FROM users LIKE %s", (col,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} DECIMAL(3,2) NOT NULL DEFAULT 0")
            # активность пользователя
            cur.execute("SHOW COLUMNS FROM users LIKE %s", ('is_active',))
            if not cur.fetchone():
                cur.execute("ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1")


def eligible_users_sql(where_extra: str = ''):
    """
    Возвращает SQL и параметры для выборки пользователей-исполнителей.
    Поддерживает *две* возможные схемы:
      1) users(role_id) -> roles(id)
      2) user_roles(user_id, role_id) + roles(id)
    """
    placeholders = ','.join(['%s'] * len(EXECUTOR_ROLE_CODES))

    # Определяем схему на лету
    try:
        with get_conn() as _conn:
            with _conn.cursor() as _cur:
                _cur.execute("SHOW COLUMNS FROM users LIKE 'role_id'")
                has_role_id = _cur.fetchone() is not None
    except Exception:
        has_role_id = False

    if has_role_id:
        base = f"""
            SELECT u.id, COALESCE(u.full_name, u.login) AS name,
                   COALESCE(u.skill_products,0) sp, COALESCE(u.skill_objections,0) so, COALESCE(u.skill_sales,0) ss
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.is_active = 1 AND r.code IN ({placeholders})
            {where_extra}
            GROUP BY u.id, name, sp, so, ss
            ORDER BY name
        """
    else:
        base = f"""
            SELECT u.id, COALESCE(u.full_name, u.login) AS name,
                   COALESCE(u.skill_products,0) sp, COALESCE(u.skill_objections,0) so, COALESCE(u.skill_sales,0) ss
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE u.is_active = 1 AND r.code IN ({placeholders})
            {where_extra}
            GROUP BY u.id, name, sp, so, ss
            ORDER BY name
        """
    params = list(EXECUTOR_ROLE_CODES)
    return base, params

def load_executor_combo(combo: QComboBox):
    combo.clear()
    sql, params = eligible_users_sql()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for r in cur.fetchall():
                combo.addItem(r['name'], r['id'])

class LeadForm(QDialog):
    def __init__(self, lead_id: Optional[int], current_user_id: int, parent=None):
        super().__init__(parent)
        self.lead_id = lead_id
        self.current_user_id = current_user_id
        self.setWindowTitle('Лид')
        ensure_schema()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        card = QGroupBox('Данные лида')
        form = QVBoxLayout(card)

        self.created_at_lbl = QLabel('—')
        self.phone = QLineEdit(); self.phone.setPlaceholderText('+7XXXXXXXXXX')
        self.comment = QTextEdit(); self.comment.setPlaceholderText('Комментарий...')

        req_lay = QHBoxLayout()
        self.req_prod = QDoubleSpinBox(); self.req_prod.setRange(0, 1); self.req_prod.setSingleStep(0.05)
        self.req_obj  = QDoubleSpinBox(); self.req_obj.setRange(0, 1); self.req_obj.setSingleStep(0.05)
        self.req_sale = QDoubleSpinBox(); self.req_sale.setRange(0, 1); self.req_sale.setSingleStep(0.05)
        req_lay.addWidget(QLabel('Требования: продукты'));  req_lay.addWidget(self.req_prod)
        req_lay.addWidget(QLabel('возражения'));            req_lay.addWidget(self.req_obj)
        req_lay.addWidget(QLabel('продажи'));               req_lay.addWidget(self.req_sale)

        ass_lay = QHBoxLayout()
        self.assignee = QComboBox()
        ass_lay.addWidget(QLabel('Назначен:')); ass_lay.addWidget(self.assignee, 1)

        p_lay = QHBoxLayout()
        self.p1 = QDoubleSpinBox(); self.p2 = QDoubleSpinBox(); self.p3 = QDoubleSpinBox()
        for w in (self.p1, self.p2, self.p3):
            w.setRange(0, 1); w.setSingleStep(0.05)
        self.p1.setValue(1/3); self.p2.setValue(1/3); self.p3.setValue(1/3)
        p_lay.addWidget(QLabel('Стратегия p1/p2/p3:')); p_lay.addWidget(self.p1); p_lay.addWidget(self.p2); p_lay.addWidget(self.p3)

        act = QHBoxLayout()
        self.btn_save = QPushButton('Сохранить')
        self.btn_inactivate = QPushButton('Сделать неактивным')
        self.btn_new_call = QPushButton('Создать звонок')
        self.btn_auto = QPushButton('Авто-назначение')
        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.accept)
        self.btn_save.clicked.connect(self.save)
        self.btn_inactivate.clicked.connect(self.make_inactive)
        self.btn_new_call.clicked.connect(self.create_call)
        self.btn_auto.clicked.connect(self.auto_assign)
        act.addWidget(self.btn_save); act.addWidget(self.btn_inactivate); act.addWidget(self.btn_new_call)
        act.addStretch(1); act.addWidget(self.btn_auto); act.addWidget(self.btn_close)

        form.addWidget(QLabel('Дата создания:')); form.addWidget(self.created_at_lbl)
        form.addWidget(QLabel('Телефон клиента:')); form.addWidget(self.phone)
        form.addLayout(req_lay)
        form.addWidget(QLabel('Комментарий:')); form.addWidget(self.comment)
        form.addLayout(ass_lay); form.addLayout(p_lay); form.addLayout(act)
        root.addWidget(card)

        calls_card = QGroupBox('Звонки по лиду'); c_lay = QVBoxLayout(calls_card)
        self.calls = QTableWidget(0, 4)
        self.calls.setHorizontalHeaderLabels(['Дата/время', 'Пользователь', 'Длительность (с)', 'Комментарий'])
        self.calls.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.calls.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        c_lay.addWidget(self.calls)
        root.addWidget(calls_card)

        load_executor_combo(self.assignee)
        if self.lead_id is None:
            self.created_at_lbl.setText('будет установлена при сохранении')
            self.btn_inactivate.setEnabled(False)
        else:
            self.load_lead()

    def load_lead(self):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, phone, comment, created_at, is_active, current_assignee_id,
                           COALESCE(req_products,0) rp, COALESCE(req_objections,0) ro, COALESCE(req_sales,0) rs
                    FROM leads WHERE id=%s
                """, (self.lead_id,))
                L = cur.fetchone()
                if not L:
                    QMessageBox.warning(self, 'Лид', 'Не найден')
                    self.reject()
                    return

                self.created_at_lbl.setText(str(L['created_at']))
                self.phone.setText('' if L['phone'] is None else str(L['phone']))
                self.comment.setPlainText('' if L['comment'] is None else str(L['comment']))
                self.req_prod.setValue(float(L['rp']))
                self.req_obj.setValue(float(L['ro']))
                self.req_sale.setValue(float(L['rs']))

                is_active = int(L['is_active']) == 1
                for w in (self.phone, self.comment, self.req_prod, self.req_obj, self.req_sale,
                          self.assignee, self.btn_save, self.btn_new_call, self.btn_auto):
                    w.setEnabled(is_active)

                idx = self.assignee.findData(L['current_assignee_id'])
                if idx != -1:
                    self.assignee.setCurrentIndex(idx)

                cur.execute("""
                    SELECT c.call_time, u.full_name AS user_name, c.duration_seconds, c.notes
                    FROM calls c JOIN users u ON u.id = c.user_id
                    WHERE c.lead_id = %s AND COALESCE(c.is_deleted,0) = 0
                    ORDER BY c.call_time DESC
                """, (self.lead_id,))
                rows = cur.fetchall()

        self.calls.setRowCount(0)
        for r in rows:
            row = self.calls.rowCount(); self.calls.insertRow(row)
            self.calls.setItem(row, 0, QTableWidgetItem(str(r['call_time'])))
            self.calls.setItem(row, 1, QTableWidgetItem(str(r['user_name'])))
            self.calls.setItem(row, 2, QTableWidgetItem('' if r['duration_seconds'] is None else str(r['duration_seconds'])))
            self.calls.setItem(row, 3, QTableWidgetItem('' if r['notes'] is None else str(r['notes'])))

    def save(self):
        # нормализуем веса
        s = self.p1.value() + self.p2.value() + self.p3.value()
        if s <= 0:
            self.p1.setValue(1/3); self.p2.setValue(1/3); self.p3.setValue(1/3)
        else:
            self.p1.setValue(self.p1.value()/s)
            self.p2.setValue(self.p2.value()/s)
            self.p3.setValue(self.p3.value()/s)

        assign_id = self.assignee.currentData()
        if assign_id is None:
            QMessageBox.warning(self, 'Назначение', 'Выберите ответственного из списка.')
            return

        with get_conn() as conn:
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(EXECUTOR_ROLE_CODES))
                cur.execute(f"""
                    SELECT u.is_active
                    FROM users u
                    JOIN user_roles ur ON ur.user_id = u.id
                    JOIN roles r ON r.id = ur.role_id
                    WHERE u.id = %s AND u.is_active = 1 AND r.code IN ({placeholders})
                    LIMIT 1
                """, (assign_id, *EXECUTOR_ROLE_CODES))
                if not cur.fetchone():
                    QMessageBox.warning(self, 'Назначение запрещено',
                                        'Выбранный пользователь не является исполнителем или неактивен.')
                    return

        if self.lead_id is None:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO leads
                            (phone, comment, created_at, is_active, current_assignee_id,
                             req_products, req_objections, req_sales)
                        VALUES (%s, %s, NOW(), 1, %s, %s, %s, %s)
                    """, (
                        self.phone.text().strip() or None,
                        self.comment.toPlainText().strip() or None,
                        assign_id, self.req_prod.value(), self.req_obj.value(), self.req_sale.value()
                    ))
                    cur.execute("SELECT LAST_INSERT_ID() AS id")
                    self.lead_id = cur.fetchone()['id']
            QMessageBox.information(self, 'Лид', 'Создан')
            self.load_lead()
        else:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE leads SET phone=%s, comment=%s, current_assignee_id=%s,
                            req_products=%s, req_objections=%s, req_sales=%s
                        WHERE id=%s AND is_active=1
                    """, (
                        self.phone.text().strip() or None,
                        self.comment.toPlainText().strip() or None,
                        assign_id,
                        self.req_prod.value(), self.req_obj.value(), self.req_sale.value(),
                        self.lead_id
                    ))
            QMessageBox.information(self, 'Лид', 'Сохранено')
            self.load_lead()

    def make_inactive(self):
        if self.lead_id is None:
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM calls WHERE lead_id=%s AND COALESCE(is_deleted,0)=0", (self.lead_id,))
                n = cur.fetchone()['n']
                if n == 0:
                    QMessageBox.warning(self, 'Запрещено', 'Нельзя деактивировать лид без звонков.')
                    return
                cur.execute("UPDATE leads SET is_active=0 WHERE id=%s", (self.lead_id,))
        QMessageBox.information(self, 'Лид', 'Статус изменён на «неактивный».')
        self.load_lead()

    def create_call(self):
        if self.lead_id is None:
            QMessageBox.information(self, 'Звонок', 'Сначала сохраните лид.')
            return
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT is_active FROM leads WHERE id=%s", (self.lead_id,))
                if int(cur.fetchone()['is_active']) != 1:
                    QMessageBox.warning(self, 'Запрещено', 'Нельзя создать звонок по неактивному лиду.')
                    return
                cur.execute(
                    "INSERT INTO calls(lead_id,user_id,call_time,duration_seconds,notes,is_deleted) "
                    "VALUES(%s,%s,NOW(),NULL,NULL,0)",
                    (self.lead_id, self.current_user_id)
                )
                cur.execute("SELECT LAST_INSERT_ID() AS id")
                call_id = cur.fetchone()['id']
        from call_form import CallForm
        CallForm(call_id, self.current_user_id, parent=self).exec()
        self.load_lead()

    def auto_assign(self):
        # нормализация весов
        s = self.p1.value() + self.p2.value() + self.p3.value()
        p1, p2, p3 = (1/3, 1/3, 1/3) if s <= 0 else (self.p1.value()/s, self.p2.value()/s, self.p3.value()/s)

        R = (self.req_prod.value(), self.req_obj.value(), self.req_sale.value())
        sql, params = eligible_users_sql()
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                users = cur.fetchall()
                for u in users:
                    cur.execute("SELECT COUNT(*) AS L FROM leads WHERE current_assignee_id=%s", (u['id'],))
                    u['L'] = cur.fetchone()['L']
                    cur.execute("SELECT COUNT(*) AS A FROM leads WHERE current_assignee_id=%s AND is_active=1", (u['id'],))
                    u['A'] = cur.fetchone()['A']

        if not users:
            QMessageBox.warning(self, 'Авто-назначение', 'Нет доступных исполнителей')
            return

        Lmax = max([u['L'] for u in users]) or 1
        Amax = max([u['A'] for u in users]) or 1

        best_id, best_score = None, -1.0
        for u in users:
            dot = (float(u['sp'])*R[0] + float(u['so'])*R[1] + float(u['ss'])*R[2]) / 3.0
            score = ((Lmax - u['L'])/max(Lmax,1)) * p1 + ((Amax - u['A'])/max(Amax,1)) * p2 + dot * p3
            if score > best_score:
                best_score, best_id = score, u['id']

        if best_id is None:
            QMessageBox.warning(self, 'Авто-назначение', 'Подходящий исполнитель не найден')
            return
        idx = self.assignee.findData(best_id)
        if idx != -1:
            self.assignee.setCurrentIndex(idx)
        QMessageBox.information(self, 'Авто-назначение', f'Выбран исполнитель ID={best_id}. Нажмите «Сохранить».')
