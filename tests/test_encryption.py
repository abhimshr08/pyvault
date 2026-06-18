import pytest
from cryptography.fernet import Fernet
from pyvault.encryption import derive_user_key, generate_secret_key, encrypt_password, decrypt_password

def test_generate_secret_key():
    key = generate_secret_key()
    assert isinstance(key, str)
    assert key.startswith("PV-")
    assert len(key) == 42

def test_derive_user_key():
    salt = b'1234567890abcdef'
    secret_key = generate_secret_key()
    key = derive_user_key("masterpassword", secret_key, salt)
    assert isinstance(key, bytes)
    assert len(key) == 44  # Fernet key length (base64 encoded 32 bytes)

def test_encrypt_decrypt():
    salt = b'1234567890abcdef'
    secret_key = generate_secret_key()
    key = derive_user_key("masterpassword", secret_key, salt)
    password = "testpassword"
    encrypted = encrypt_password(password, key)
    decrypted = decrypt_password(encrypted, key)
    assert decrypted == password

def test_encrypt_decrypt_with_string_key():
    salt = b'1234567890abcdef'
    secret_key = generate_secret_key()
    key_str = derive_user_key("masterpassword", secret_key, salt).decode()
    password = "testpassword"
    encrypted = encrypt_password(password, key_str)
    decrypted = decrypt_password(encrypted, key_str)
    assert decrypted == password