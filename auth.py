import os, binascii, hashlib, datetime as dt, random
from email_validator import validate_email, EmailNotValidError
from db import get_conn
from email_utils import send_mail

def pbkdf2(password: str, iterations: int = 200_000):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return {
        'algo': 'pbkdf2_sha256',
        'iterations': iterations,
        'salt_hex': binascii.hexlify(salt).decode('ascii'),
        'password_hash_hex': binascii.hexlify(dk).decode('ascii'),
    }

def pbkdf2_verify(password: str, salt_hex: str, iterations: int, password_hash_hex: str) -> bool:
    salt = binascii.unhexlify(salt_hex.encode('ascii'))
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return binascii.hexlify(dk).decode('ascii') == password_hash_hex

def send_registration_code(full_name: str, login: str, email: str, password: str):
    login = (login or '').strip()
    email = (email or '').strip()
    if not login or len(login) < 3:
        raise ValueError('Укажите логин (не короче 3 символов)')
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        raise ValueError('Неверный формат email') from e
    if not full_name or len(full_name) < 3:
        raise ValueError('Укажите корректное ФИО')
    if not password or len(password) < 6:
        raise ValueError('Пароль должен быть не короче 6 символов')

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE login=%s', (login,))
            if cur.fetchone():
                raise ValueError('Такой логин уже существует')

    digest = pbkdf2(password)
    code = f"{random.randint(0,999999):06d}"
    expires = (dt.datetime.utcnow() + dt.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS registration_tokens (
                        login VARCHAR(64) NOT NULL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        algo VARCHAR(32) NOT NULL,
                        iterations INT NOT NULL,
                        salt_hex CHAR(32) NOT NULL,
                        password_hash_hex CHAR(64) NOT NULL,
                        code CHAR(6) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        attempts INT NOT NULL DEFAULT 0
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            cur.execute(
                """REPLACE INTO registration_tokens(login, email, full_name, algo, iterations, salt_hex, password_hash_hex, code, expires_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (login, email, full_name, digest['algo'], digest['iterations'], digest['salt_hex'],
                 digest['password_hash_hex'], code, expires)
            )

    html = (
        '<div style="font-family:Tahoma,Arial,sans-serif;font-size:12px;color:rgb(36,50,56)">'
        f'<p>Здравствуйте, {full_name}!</p>'
        '<p>Ваш код подтверждения регистрации в TransitDB:</p>'
        f'<p style="font-size:14px;font-weight:bold;color:rgb(255,74,109)">{code}</p>'
        '<p style="color:rgb(84,110,122)">Код действует 15 минут.</p>'
        f'<p>Логин: <b>{login}</b></p>'
        '</div>'
    )
    send_mail(email, 'Код подтверждения TransitDB', html)

def verify_registration(login: str, code: str):
    now = dt.datetime.utcnow()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM registration_tokens WHERE login=%s', (login,))
            tok = cur.fetchone()
            if not tok:
                return False, 'Сессия регистрации не найдена'
            cur.execute('UPDATE registration_tokens SET attempts = attempts + 1 WHERE login=%s', (login,))

            if tok['code'] != code:
                return False, 'Неверный код'

            exp = tok['expires_at']
            if isinstance(exp, str):
                from datetime import datetime as _dt
                exp_dt = _dt.strptime(exp, '%Y-%m-%d %H:%M:%S')
            else:
                exp_dt = exp
            if now > exp_dt:
                cur.execute('DELETE FROM registration_tokens WHERE login=%s', (login,))
                return False, 'Код истёк. Зарегистрируйтесь заново.'

            cur.execute('SELECT id FROM users WHERE login=%s', (login,))
            u = cur.fetchone()
            if not u:
                cur.execute('INSERT INTO users(login, full_name, created_at) VALUES(%s,%s,NOW())', (login, tok['full_name']))
                cur.execute('SELECT LAST_INSERT_ID() AS id')
                uid = cur.fetchone()['id']
            else:
                uid = u['id']

            # Ensure users.email exists and update
            cur.execute("SHOW COLUMNS FROM users LIKE 'email'")
            if not cur.fetchone():
                cur.execute('ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT NULL')
                # MySQL/MariaDB lacks IF NOT EXISTS for indexes broadly; guard by try/except
                try:
                    cur.execute('CREATE UNIQUE INDEX uq_users_email ON users(email)')
                except Exception:
                    pass
            cur.execute('UPDATE users SET email=%s WHERE id=%s', (tok['email'], uid))

            # Ensure auth_credentials exists and upsert
            cur.execute(
                """CREATE TABLE IF NOT EXISTS auth_credentials (
                    id INT NOT NULL AUTO_INCREMENT,
                    user_id INT NOT NULL UNIQUE,
                    algo VARCHAR(32) NOT NULL,
                    iterations INT NOT NULL,
                    salt_hex CHAR(32) NOT NULL,
                    password_hash_hex CHAR(64) NOT NULL,
                    is_temp TINYINT(1) NOT NULL DEFAULT 0,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            cur.execute(
                'REPLACE INTO auth_credentials(user_id, algo, iterations, salt_hex, password_hash_hex, is_temp) VALUES(%s,%s,%s,%s,%s,0)',
                (uid, tok['algo'], tok['iterations'], tok['salt_hex'], tok['password_hash_hex'])
            )

            # Ensure roles & user_roles and assign client
            cur.execute(
                """CREATE TABLE IF NOT EXISTS roles (
                    id INT NOT NULL AUTO_INCREMENT,
                    code VARCHAR(64) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    PRIMARY KEY(id),
                    UNIQUE KEY uq_roles_code(code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            cur.execute(
                """CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INT NOT NULL,
                    role_id INT NOT NULL,
                    PRIMARY KEY(user_id, role_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            cur.execute("INSERT IGNORE INTO roles(id, code, name) VALUES (NULL,'client','Клиент')")
            cur.execute("SELECT id FROM roles WHERE code='client'")
            rid = cur.fetchone()['id']
            cur.execute('INSERT IGNORE INTO user_roles(user_id, role_id) VALUES(%s,%s)', (uid, rid))

            cur.execute('DELETE FROM registration_tokens WHERE login=%s', (login,))
            return True, uid

def login_by_login(login: str, password: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.id, u.full_name, a.iterations, a.salt_hex, a.password_hash_hex '
                'FROM users u JOIN auth_credentials a ON a.user_id=u.id WHERE u.login=%s',
                (login,)
            )
            row = cur.fetchone()
            if not row:
                return False, 'Пользователь не найден'
            if not pbkdf2_verify(password, row['salt_hex'], row['iterations'], row['password_hash_hex']):
                return False, 'Неверный пароль'
            return True, {'id': row['id'], 'full_name': row['full_name']}

def get_user_by_id(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, login, full_name FROM users WHERE id=%s', (user_id,))
            return cur.fetchone()
