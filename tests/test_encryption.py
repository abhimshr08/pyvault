import pytest
from cryptography.fernet import Fernet
from pyvault.encryption import generate_key, encrypt_password, decrypt_password

def test_generate_key():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 44  # Fernet key length

def test_encrypt_decrypt():
    key = generate_key()
    password = "testpassword"
    encrypted = encrypt_password(password, key)
    decrypted = decrypt_password(encrypted, key)
    assert decrypted == password