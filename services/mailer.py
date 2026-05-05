import smtplib, os
from email.mime.text import MIMEText

def send_mail(subject, body):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    receivers = [
        os.getenv("EMAIL_TO_1"),
        os.getenv("EMAIL_TO_2")
    ]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)

    for r in receivers:
        server.sendmail(sender, r, msg.as_string())

    server.quit()