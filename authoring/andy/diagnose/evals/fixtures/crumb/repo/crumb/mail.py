"""Hand the sheet to the host's mail relay."""
import smtplib
from email.message import EmailMessage

RELAY = ("localhost", 25)
SENDER = "Crumb orders <orders@crumbandco.example>"


def send(to, subject, body):
    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(*RELAY, timeout=30) as smtp:
        smtp.send_message(msg)
