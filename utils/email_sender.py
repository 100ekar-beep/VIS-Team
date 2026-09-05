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
from email.mime.application import MIMEApplication

import streamlit as st


def is_email_configured() -> bool:
    try:
        return bool(st.secrets["EMAIL_SENDER"]) and bool(st.secrets["EMAIL_PASSWORD"]) and bool(st.secrets["EMAIL_RECEIVER"])
    except Exception:
        return False


def send_site_photos_email(
    site: dict, uploaded_files, team_name: str, note: str = "",
    jms_files=None,
) -> tuple[bool, str]:
    """
    uploaded_files: list of Streamlit UploadedFile objects (photos)
    jms_files: optional list of Streamlit UploadedFile objects (PDF and/or
    photo) for the JMS attachment(s) — attached to this same email, in
    memory only, never saved anywhere.
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

    uploaded_files = uploaded_files or []
    jms_files = jms_files or []
    if not uploaded_files and not jms_files:
        return False, "Koi photo select nahi ki gayi aur JMS bhi attach nahi ki."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"Photos_{site.get('Project ID', '')}_{site.get('Site ID', '')}_{site.get('Site Name', '')}"

    what_attached = "subjected site photos"
    if uploaded_files and jms_files:
        what_attached = "subjected site photos and JMS"
    elif jms_files:
        what_attached = "subjected site JMS"

    detail_lines = (
        f"Project ID: {site.get('Project ID', '')}\n"
        f"Site ID: {site.get('Site ID', '')}\n"
        f"Site Name: {site.get('Site Name', '')}\n"
        f"Cluster: {site.get('Cluster', '')}\n"
        f"Photos attached: {len(uploaded_files)}\n"
        f"JMS files attached: {len(jms_files)}"
    )

    body = (
        f"Hello Sir,\n\n"
        f"Please find attached {what_attached}.\n\n"
        f"{detail_lines}\n\n"
        f"Thanks,\n"
        f"{team_name}"
    )
    if note:
        body = (
            f"Hello Sir,\n\n"
            f"Please find attached {what_attached}.\n\n"
            f"{detail_lines}\n\n"
            f"Note: {note}\n\n"
            f"Thanks,\n"
            f"{team_name}"
        )
    msg.attach(MIMEText(body, "plain"))

    for f in uploaded_files:
        f.seek(0)
        img_bytes = f.read()
        image = MIMEImage(img_bytes, name=f.name)
        msg.attach(image)

    for f in jms_files:
        f.seek(0)
        file_bytes = f.read()
        name_lower = (f.name or "").lower()
        if name_lower.endswith(".pdf"):
            attachment = MIMEApplication(file_bytes, _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename=f.name)
            msg.attach(attachment)
        else:
            image = MIMEImage(file_bytes, name=f.name)
            msg.attach(image)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        parts = []
        if uploaded_files:
            parts.append(f"{len(uploaded_files)} photo(s)")
        if jms_files:
            parts.append(f"{len(jms_files)} JMS file(s)")
        return True, f"✅ {' + '.join(parts)} email ho gayi {receiver} par."
    except Exception as e:
        return False, f"Email bhejne mein error: {e}"


def send_site_jms_email(site: dict, pdf_bytes: bytes, pdf_filename: str, team_name: str) -> tuple[bool, str]:
    """
    Emails the already-generated JMS PDF as an attachment — same in-memory
    approach as photos (never saved to Supabase). Subject/body match the
    Site Photos email, just "Photo" swapped for "JMS".
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

    if not pdf_bytes:
        return False, "Pehle 'Create JMS' tab mein JMS PDF generate karo."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"JMS_{site.get('Project ID', '')}_{site.get('Site ID', '')}_{site.get('Site Name', '')}"

    detail_lines = (
        f"Project ID: {site.get('Project ID', '')}\n"
        f"Site ID: {site.get('Site ID', '')}\n"
        f"Site Name: {site.get('Site Name', '')}\n"
        f"Cluster: {site.get('Cluster', '')}"
    )

    body = (
        f"Hello Sir,\n\n"
        f"Please find attached subjected site JMS.\n\n"
        f"{detail_lines}\n\n"
        f"Thanks,\n"
        f"{team_name}"
    )
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(attachment)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True, f"✅ JMS PDF email ho gayi {receiver} par."
    except Exception as e:
        return False, f"Email bhejne mein error: {e}"
