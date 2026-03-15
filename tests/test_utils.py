import pytest
from pyvault.utils import generate_password

def test_generate_password():
    password = generate_password(10)
    assert len(password) == 10
    # Check contains mix of characters
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)