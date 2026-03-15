import pytest
from pyvault.models import Password

def test_password_model():
    password = Password(service="test", username="user", encrypted_password="enc")
    assert password.service == "test"
    assert password.username == "user"