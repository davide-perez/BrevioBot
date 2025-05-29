import smtplib
from email.mime.text import MIMEText
from core.settings import settings

def send_email(to_email, subject, body):
    smtp_host = settings.email.smtp_host
    smtp_port = settings.email.smtp_port
    smtp_user = settings.email.smtp_user
    smtp_password = settings.email.smtp_password
    from_email = settings.email.from_email
    from_name = settings.email.from_name

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
