import os
import pytest
from click.testing import CliRunner

# Configure DB to run in-memory for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock/Ensure encryption key is present so Fernet doesn't generate a random key file
os.environ["PYVAULT_SECRET_KEY"] = "sQO-n-Z-vX5_Hj5i-4QkPqVpU9Y8tLw5sQO-n-Z-vX4="

from pyvault.database import init_db, SessionLocal
from pyvault.cli import cli
from pyvault.models import Password

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    # Clear the database before each test
    db.query(Password).delete()
    db.commit()
    db.close()

def test_add_password():
    runner = CliRunner()
    result = runner.invoke(cli, [
        'add', 
        '--service', 'github', 
        '--username', 'testuser', 
        '--password', 'secure_pass_123'
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
    # First add a password
    runner.invoke(cli, [
        'add', 
        '--service', 'gmail', 
        '--username', 'gmailuser', 
        '--password', 'gmail_pass'
    ])

    # Now retrieve it
    result = runner.invoke(cli, ['get', '--service', 'gmail'])
    assert result.exit_code == 0
    assert "Username: gmailuser" in result.output
    assert "Password: gmail_pass" in result.output