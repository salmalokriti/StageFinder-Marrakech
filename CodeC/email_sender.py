"""Envoi d'e-mail avec CV en pièce jointe (SMTP)."""

import os
import smtplib
import streamlit as st

from email.message import EmailMessage
from urllib.parse import quote


def configuration(nom, defaut=""):
    """Lire une configuration depuis Streamlit Secrets ou les variables d'environnement."""

    try:
        valeur = str(st.secrets.get(nom, "")).strip()
    except Exception:
        valeur = ""

    if not valeur:
        valeur = os.getenv(nom, defaut).strip()

    return valeur.strip('"').strip("'")


def smtp_configure():
    """Vérifier que les paramètres SMTP sont présents."""

    return all(
        configuration(k)
        for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD")
    )


def envoyer_email(destinataire, sujet, corps, cv_bytes=None, cv_nom="CV.pdf"):

    utilisateur = configuration("SMTP_USER")
    mot_de_passe = configuration("SMTP_PASSWORD")
    host = configuration("SMTP_HOST", "smtp.gmail.com")
    port = int(configuration("SMTP_PORT", "587"))

    msg = EmailMessage()

    msg["From"] = utilisateur
    msg["To"] = destinataire
    msg["Subject"] = sujet

    msg.set_content(corps)

    if cv_bytes:
        msg.add_attachment(
            cv_bytes,
            maintype="application",
            subtype="pdf",
            filename=cv_nom
        )

    with smtplib.SMTP(host, port, timeout=30) as smtp:

        smtp.starttls()

        smtp.login(utilisateur, mot_de_passe)

        smtp.send_message(msg)


def lien_mailto(destinataire, sujet, corps):
    """Ouvrir le client mail sans pièce jointe."""

    return (
        f"mailto:{destinataire}"
        f"?subject={quote(sujet)}"
        f"&body={quote(corps)}"
    )
