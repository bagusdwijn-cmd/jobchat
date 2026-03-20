from __future__ import annotations
import base64
import hashlib
from cryptography.fernet import Fernet

def _derive(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

class SecretBox:
    def __init__(self, secret: str):
        self.fernet = Fernet(_derive(secret))

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str | None) -> str:
        if not value:
            return ""
        return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
