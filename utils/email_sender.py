"""
Sends site photos as email attachments — entirely in-memory. Nothing is ever
written to Supabase, disk, or any other storage; the uploaded file bytes go
straight from the browser upload into the email attachment.

Uses plain SMTP (works with Gmail, Outlook, or most providers) via secrets:
    EMAIL_SENDER   = "youraddress@gmail.com"
    EMAIL_PASSWORD = "your-app-password"      (NOT your normal password — see below)
    EMAIL_RECEIVER = "recipient@example.com"
    EMAIL_SMTP_HOST = "smtp.gmail.com"        (optional, defaults to Gmail)
    EMAIL_SMTP_PORT = 587                      (optional, defaults to 587)

For Gmail: you must create an "App Password" (Google Account -> Security ->
2-Step Verification -> App Passwords) — a normal Gmail password will NOT work
for SMTP login.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import streamlit as st


def is_email_configured() -> bool:
    try:
        return bool(st.secrets["EMAIL_SENDER"]) and bool(st.secrets["EMAIL_PASSWORD"]) and bool(st.secrets["EMAIL_RECEIVER"])
    except Exception:
        return False


def send_site_photos_email(site: dict, uploaded_files, team_name: str, note: str = "") -> tuple[bool, str]:
    """
    uploaded_files: list of Streamlit UploadedFile objects (from st.file_uploader)
    Returns (success, message).
    """
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        receiver = st.secrets["EMAIL_RECEIVER"]
        smtp_host = st.secrets.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("EMAIL_SMTP_PORT", 587))
    except Exception:
        return False, (
            "Email settings configure nahi hai. Streamlit Secrets mein "
            "EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER daalo."
        )

    if not uploaded_files:
        return False, "Koi photo select nahi ki gayi."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"Site Photos — {site.get('Site Name', '')} ({site.get('Site ID', '')})"

    body_lines = [
        f"Team: {team_name}",
        f"Site Name: {site.get('Site Name', '')}",
        f"Site ID: {site.get('Site ID', '')}",
        f"Project ID: {site.get('Project ID', '')}",
        f"Photos attached: {len(uploaded_files)}",
    ]
    if note:
        body_lines.append("")
        body_lines.append(f"Note: {note}")
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    for f in uploaded_files:
        f.seek(0)
        img_bytes = f.read()
        image = MIMEImage(img_bytes, name=f.name)
        msg.attach(image)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True, f"✅ {len(uploaded_files)} photo(s) email ho gayi {receiver} par."
    except Exception as e:
        return False, f"Email bhejne mein error: {e}"
