import smtplib
from email.mime.text import MIMEText
import os

def send_email(to_email, subject, body):
    smtp_host = os.getenv('BREVIOBOT_SMTP_HOST')
    smtp_port = int(os.getenv('BREVIOBOT_SMTP_PORT', '587'))
    smtp_user = os.getenv('BREVIOBOT_SMTP_USER')
    smtp_password = os.getenv('BREVIOBOT_SMTP_PASSWORD')
    from_email = os.getenv('BREVIOBOT_EMAIL_FROM')
    from_name = os.getenv('BREVIOBOT_EMAIL_FROM_NAME', 'BrevioBot')

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
