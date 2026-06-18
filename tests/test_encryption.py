import pytest
from cryptography.fernet import Fernet
from pyvault.encryption import derive_user_key, encrypt_password, decrypt_password

def test_derive_user_key():
    salt = b'1234567890abcdef'  # 16 bytes salt
    key = derive_user_key("masterpassword", salt)
    assert isinstance(key, bytes)
    assert len(key) == 44  # Fernet key is base64 encoded 32 bytes (which is 44 characters long)

def test_encrypt_decrypt():
    salt = b'1234567890abcdef'
    key = derive_user_key("masterpassword", salt)
    password = "testpassword"
    encrypted = encrypt_password(password, key)
    decrypted = decrypt_password(encrypted, key)
    assert decrypted == password

def test_encrypt_decrypt_with_string_key():
    salt = b'1234567890abcdef'
    key_str = derive_user_key("masterpassword", salt).decode()
    password = "testpassword"
    encrypted = encrypt_password(password, key_str)
    decrypted = decrypt_password(encrypted, key_str)
    assert decrypted == password