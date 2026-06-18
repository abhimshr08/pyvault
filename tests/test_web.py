import os
import pytest

# Configure in-memory database for web tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Mock encryption key
os.environ["PYVAULT_SECRET_KEY"] = "sQO-n-Z-vX5_Hj5i-4QkPqVpU9Y8tLw5sQO-n-Z-vX4="
# Mock Flask secret
os.environ["FLASK_SECRET_KEY"] = "testsecret"

from pyvault.web import app
from pyvault.database import init_db, SessionLocal
from pyvault.models import Password

@pytest.fixture
def client():
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    # Clean up DB
    db = SessionLocal()
    db.query(Password).delete()
    db.commit()
    db.close()

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"Your Stored Passwords" in rv.data

def test_add_password(client):
    # Form post
    rv = client.post('/add', data={
        'service': 'facebook',
        'username': 'fbuser',
        'password': 'fbpassword'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"added successfully" in rv.data

    # Check db
    db = SessionLocal()
    entry = db.query(Password).filter_by(service='facebook').first()
    assert entry is not None
    assert entry.username == 'fbuser'
    db.close()

def test_generate_password(client):
    rv = client.get('/generate')
    assert rv.status_code == 200
    assert b"Generated Password" in rv.data
