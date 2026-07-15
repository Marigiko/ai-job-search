# .agents/skills/job-scraper/linkedin_email_apply.py
"""Apply to LinkedIn recruiter posts via email."""
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def _deobfuscate_email(text: str) -> str:
    """Convert obfuscated emails to real format."""
    text = re.sub(r"\s*\[at\]\s*", "@", text)
    text = re.sub(r"\s*\[dot\]\s*", ".", text)
    text = text.replace(" (at) ", "@").replace(" (dot) ", ".").replace("&#64;", "@")
    return text


def get_apply_email(text: str) -> str | None:
    """Extract apply-by-email address from recruiter post text."""
    deobfuscated = _deobfuscate_email(text)
    matches = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    for m in matches:
        if "linkedin" not in m.lower():
            return m
    return matches[0] if matches else None


def send_application_email(to_email: str, cv_path: str, cover_path: str | None, job_title: str) -> bool:
    """Send application via Gmail SMTP."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender = os.getenv("GMAIL_SENDER", "marioaquinojob@gmail.com")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not password:
        raise ValueError("GMAIL_APP_PASSWORD not set in .env")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = f"Application: {job_title} — Mario Aquino"
    body = f"""Dear Hiring Team,

I am writing to express my interest in the {job_title} position.

My name is Mario Aquino, a Senior Full-Stack / Backend Engineer with 5+ years of experience in Node.js, TypeScript, Python, AWS, Docker, Kubernetes, and AI/LLM automation. I have attached my CV and cover letter for your review.

I would welcome the opportunity to discuss how my background aligns with your needs.

Best regards,
Mario Aquino
marioaquinojob@gmail.com · linkedin.com/in/keyzdev
"""
    msg.attach(MIMEText(body, "plain"))

    for path in [cv_path, cover_path]:
        if path and Path(path).exists():
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(path).name}")
            msg.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
    return True
