import os
import pytest
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
    assert "registered successfully" in result.output

    # Check database
    db = SessionLocal()
    user = db.query(User).filter_by(email='test@example.com').first()
    assert user is not None
    db.close()

def test_add_password():
    runner = CliRunner()
    # Register user first
    runner.invoke(cli, [
        'register',
        '--email', 'user@example.com',
        '--password', 'mypassword'
    ])

    # Add password
    result = runner.invoke(cli, [
        'add', 
        '--email', 'user@example.com',
        '--password', 'mypassword',
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
    # Register user
    runner.invoke(cli, [
        'register',
        '--email', 'user2@example.com',
        '--password', 'mypassword2'
    ])

    # First add a password
    runner.invoke(cli, [
        'add', 
        '--email', 'user2@example.com',
        '--password', 'mypassword2',
        '--service', 'gmail', 
        '--username', 'gmailuser', 
        '--password-to-store', 'gmail_pass'
    ])

    # Now retrieve it
    result = runner.invoke(cli, [
        'get', 
        '--email', 'user2@example.com',
        '--password', 'mypassword2',
        '--service', 'gmail'
    ])
    assert result.exit_code == 0
    assert "Username: gmailuser" in result.output
    assert "Password: gmail_pass" in result.output