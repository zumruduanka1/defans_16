def send_mail(subject, body):
    import smtplib
    from email.mime.text import MIMEText

    sender = "MAILIN@gmail.com"
    password = "APP_PASSWORD"

    receivers = [
        "MAILIN@gmail.com",
        "ARKADASMAIL@gmail.com"
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