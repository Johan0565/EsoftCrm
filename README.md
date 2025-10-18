# TransitDB Desktop (PySide6)

Десктоп‑приложение на Python (PySide6) с окнами **Вход**, **Регистрация с кодом на email**, **Клиент** (пустое окно).
Оформление согласно гайдлайну (Tahoma 12 / заголовки bold 14, интервалы ≥ 12 px, высоты 25/30/35, белый фон, 
акцент rgb(255,74,109), основной/доп. текст rgb(36,50,56) и rgb(84,110,122)).

## Запуск
```bash
python -m venv .venv
. .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env      # при необходимости скорректируйте параметры
# В MySQL заранее создайте БД:
# CREATE DATABASE transitdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

python main.py
```

## Переменные окружения (.env)
Смотрите `.env.example`. Используется MySQL (PyMySQL) и SMTP (Gmail STARTTLS).

## Структура
- `main.py` — запуск и маршрутизация окон.
- `login_window.py` — окно входа.
- `register_window.py` — окно регистрации и отправка кода.
- `verify_dialog.py` — ввод 6‑значного кода.
- `client_window.py` — пустое окно клиента.
- `auth.py` — PBKDF2‑SHA256 (200k итераций), логика регистрации/входа.
- `db.py` — подключение и инициализация схемы (users, roles, user_roles, auth_credentials, registration_tokens).
- `email_utils.py` — отправка писем.
- `style.qss` — визуальный стиль (Tahoma, отступы, цвета, высоты).
- `resources/logo.png` — логотип в шапке (можно заменить своим).
```
