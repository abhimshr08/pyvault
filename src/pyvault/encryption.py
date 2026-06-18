from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
import os

def generate_secret_key() -> str:
    import secrets
    raw = secrets.token_hex(16).upper()
    parts = [raw[i:i+4] for i in range(0, len(raw), 4)]
    return "PV-" + "-".join(parts)

def derive_user_key(master_password: str, secret_key: str, salt: bytes) -> bytes:
    clean_secret = secret_key.replace("PV-", "").replace("-", "").strip()
    combined = f"{master_password}{clean_secret}"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(combined.encode()))

def encrypt_password(password, key):
    if isinstance(key, str):
        key = key.encode()
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password, key):
    if isinstance(key, str):
        key = key.encode()
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()