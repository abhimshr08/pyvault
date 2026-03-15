from cryptography.fernet import Fernet
import os

def generate_key():
    return Fernet.generate_key()

def load_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def encrypt_password(password, key):
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()