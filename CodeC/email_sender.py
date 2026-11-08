"""Envoi d'e-mail avec CV en pièce jointe (SMTP)."""
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote


def smtp_configure() -> bool:
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def envoyer_email(destinataire, sujet, corps, cv_bytes=None, cv_nom="CV.pdf"):
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.set_content(corps)

    if cv_bytes:
        msg.add_attachment(cv_bytes, maintype="application", subtype="pdf", filename=cv_nom)

    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
        smtp.send_message(msg)


def lien_mailto(destinataire, sujet, corps):
    """Plan B : ouvre le client mail (Gmail/Outlook) — sans pièce jointe."""
    return f"mailto:{destinataire}?subject={quote(sujet)}&body={quote(corps)}"
