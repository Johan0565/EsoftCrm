import os
import pymysql

def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST","127.0.0.1"),
        port=int(os.getenv("DB_PORT","3306")),
        user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASSWORD",""),
        database=os.getenv("DB_NAME","esoft_crm"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_schema():
    # База esoft_crm: добавим только сервисную таблицу для OTP и роль client.
    ddl = [
        '''CREATE TABLE IF NOT EXISTS registration_tokens (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            for stmt in ddl:
                cur.execute(stmt)
            # Роль client (если нет)
            cur.execute("INSERT IGNORE INTO roles(id, code, name) VALUES (NULL,'client','Клиент')")
