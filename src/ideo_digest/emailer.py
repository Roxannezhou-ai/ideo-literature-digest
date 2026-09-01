from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def send_gmail(
    sender: str,
    recipient: str,
    app_password: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    message = EmailMessage()
    message["From"] = formataddr(("IDEO Literature Digest", sender))
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=45) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message)

