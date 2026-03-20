from __future__ import annotations
import smtplib
from pathlib import Path
from email.message import EmailMessage

class MailService:
    def __init__(self, gmail_address: str, gmail_app_password: str):
        self.gmail_address = gmail_address
        self.gmail_app_password = gmail_app_password

    def send(self, to_email: str, subject: str, body: str, attachments: list[dict]):
        msg = EmailMessage()
        msg["From"] = self.gmail_address
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        for item in attachments:
            path = Path(item["file_path"])
            if not path.exists():
                continue
            data = path.read_bytes()
            ext = path.suffix.lower()
            subtype = "octet-stream"
            if ext == ".pdf":
                subtype = "pdf"
            elif ext == ".doc":
                subtype = "msword"
            elif ext == ".docx":
                subtype = "vnd.openxmlformats-officedocument.wordprocessingml.document"
            msg.add_attachment(data, maintype="application", subtype=subtype, filename=path.name)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(self.gmail_address, self.gmail_app_password)
            smtp.send_message(msg)
