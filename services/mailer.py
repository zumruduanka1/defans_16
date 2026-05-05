import smtplib, os, hashlib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

sent_cache = set()

def send_mail(text, score, status):
    key = hashlib.md5(text.encode()).hexdigest()

    # 🔒 aynı haberi tekrar gönderme
    if key in sent_cache:
        return

    sent_cache.add(key)

    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    receivers = [
        os.getenv("EMAIL_TO_1"),
        os.getenv("EMAIL_TO_2")
    ]

    body = f"""
🚨 DEFANS PRO

📊 Risk: %{score}
⚠️ Durum: {status}

📰 İçerik:
{text}

🔍 Sistem bu içeriği riskli olarak işaretledi.
"""

    msg = MIMEText(body)
    msg["Subject"] = f"⚠️ Risk %{score}"
    msg["From"] = sender

    s = smtplib.SMTP("smtp.gmail.com",587)
    s.starttls()
    s.login(sender,password)

    for r in receivers:
        s.sendmail(sender,r,msg.as_string())

    s.quit()