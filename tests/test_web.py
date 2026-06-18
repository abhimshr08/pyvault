import os
import pytest

# Configure in-memory database for web tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Mock Flask secret
os.environ["FLASK_SECRET_KEY"] = "testsecret"

from pyvault.web import app
from pyvault.database import init_db, SessionLocal
from pyvault.models import Password, User

@pytest.fixture
def client():
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    # Clean up DB
    db = SessionLocal()
    db.query(Password).delete()
    db.query(User).delete()
    db.commit()
    db.close()

def register_and_login(client, email, password):
    # Register
    client.post('/register', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    # Login
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

def test_unauthenticated_redirect(client):
    rv = client.get('/', follow_redirects=True)
    assert b"Please log in to access this page." in rv.data

def test_index_logged_in(client):
    register_and_login(client, 'user@example.com', 'password123')
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"Your Stored Passwords" in rv.data

def test_add_password(client):
    register_and_login(client, 'user@example.com', 'password123')
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

def test_user_isolation(client):
    # User 1 registers, logs in, and adds a password
    register_and_login(client, 'user1@example.com', 'pass1')
    client.post('/add', data={
        'service': 'github',
        'username': 'u1',
        'password': 'p1'
    }, follow_redirects=True)
    
    # Logout User 1
    client.get('/logout', follow_redirects=True)

    # User 2 registers and logs in
    register_and_login(client, 'user2@example.com', 'pass2')
    
    # Check index page: User 2 should NOT see User 1's password
    rv = client.get('/')
    assert b"github" not in rv.data
    assert b"No passwords stored yet" in rv.data

def test_generate_password(client):
    rv = client.get('/generate')
    assert rv.status_code == 200
    assert b"Generated Password" in rv.data
