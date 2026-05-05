import smtplib
from email.mime.text import MIMEText

EMAIL = "tubitaktest0@gmail.com"
PASSWORD = "cndmsduniivopskh"

TO = ["tubitaktest0@gmail.com", "rumeyysauslu@gmail.com"]

def send_alert(text):
    msg = MIMEText(f"Riskli içerik bulundu:\n\n{text}")
    msg["Subject"] = "⚠️ DEFANS UYARI"
    msg["From"] = EMAIL
    msg["To"] = ", ".join(TO)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, TO, msg.as_string())
    except:
        pass