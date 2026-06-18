import os
import re
import pytest
import pyotp
from click.testing import CliRunner

# Configure DB to run in-memory for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from pyvault.database import init_db, SessionLocal
from pyvault.cli import cli
from pyvault.models import Password, User

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    # Clear the database before each test
    db.query(Password).delete()
    db.query(User).delete()
    db.commit()
    db.close()

def test_register():
    runner = CliRunner()
    result = runner.invoke(cli, [
        'register',
        '--email', 'test@example.com',
        '--password', 'masterpassword'
    ])
    assert result.exit_code == 0
    assert "ACCOUNT SUCCESSFULLY INITIALIZED" in result.output
    assert "Your Secret Key" in result.output
    assert "2FA Setup Key" in result.output

    # Check database
    db = SessionLocal()
    user = db.query(User).filter_by(email='test@example.com').first()
    assert user is not None
    db.close()

def test_add_password():
    runner = CliRunner()
    
    # 1. Register user
    reg_result = runner.invoke(cli, [
        'register',
        '--email', 'user@example.com',
        '--password', 'mypassword'
    ])
    assert reg_result.exit_code == 0
    
    # Parse Secret Key and TOTP secret from output
    secret_key_match = re.search(r'Your Secret Key:\s+(PV-\S+)', reg_result.output)
    totp_secret_match = re.search(r'2FA Setup Key:\s+(\S+)', reg_result.output)
    
    assert secret_key_match is not None
    assert totp_secret_match is not None
    
    secret_key = secret_key_match.group(1)
    totp_secret = totp_secret_match.group(1)
    
    # Generate 2FA code
    totp = pyotp.totp.TOTP(totp_secret)
    totp_code = totp.now()

    # 2. Add password using credentials
    result = runner.invoke(cli, [
        'add', 
        '--email', 'user@example.com',
        '--password', 'mypassword',
        '--secret-key', secret_key,
        '--totp-code', totp_code,
        '--service', 'github', 
        '--username', 'testuser', 
        '--password-to-store', 'secure_pass_123'
    ])
    assert result.exit_code == 0
    assert "added successfully" in result.output

    # Verify in DB
    db = SessionLocal()
    entry = db.query(Password).filter_by(service='github').first()
    assert entry is not None
    assert entry.username == 'testuser'
    db.close()

def test_get_password():
    runner = CliRunner()
    
    # 1. Register user
    reg_result = runner.invoke(cli, [
        'register',
        '--email', 'user2@example.com',
        '--password', 'mypassword2'
    ])
    
    secret_key = re.search(r'Your Secret Key:\s+(PV-\S+)', reg_result.output).group(1)
    totp_secret = re.search(r'2FA Setup Key:\s+(\S+)', reg_result.output).group(1)
    
    totp = pyotp.totp.TOTP(totp_secret)

    # 2. Add password
    runner.invoke(cli, [
        'add', 
        '--email', 'user2@example.com',
        '--password', 'mypassword2',
        '--secret-key', secret_key,
        '--totp-code', totp.now(),
        '--service', 'gmail', 
        '--username', 'gmailuser', 
        '--password-to-store', 'gmail_pass'
    ])

    # 3. Retrieve it
    result = runner.invoke(cli, [
        'get', 
        '--email', 'user2@example.com',
        '--password', 'mypassword2',
        '--secret-key', secret_key,
        '--totp-code', totp.now(),
        '--service', 'gmail'
    ])
    assert result.exit_code == 0
    assert "Username: gmailuser" in result.output
    assert "Password: gmail_pass" in result.output