import os, smtplib, ssl
from email.message import EmailMessage

def send_mail(to_email: str, subject: str, html: str):
    host = os.getenv("SMTP_HOST","smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT","587"))
    security = os.getenv("SMTP_SECURITY","starttls").lower()
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASSWORD")
    mail_from = os.getenv("SMTP_FROM", user)

    if not (user and pwd):
        raise RuntimeError("SMTP creds not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = to_email
    msg.set_content("Ваш почтовый клиент не поддерживает HTML.")
    msg.add_alternative(html, subtype="html")

    if security == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as s:
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.login(user, pwd)
            s.send_message(msg)
