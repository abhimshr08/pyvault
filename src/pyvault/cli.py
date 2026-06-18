import click
from sqlalchemy.orm import Session
import os

from .database import SessionLocal, init_db
from .models import Password, User
from .encryption import generate_secret_key, derive_user_key, encrypt_password, decrypt_password
from .utils import generate_password

def authenticate_user(db: Session, email: str, password: str, secret_key: str, totp_code: str):
    from werkzeug.security import check_password_hash
    import pyotp
    
    user = db.query(User).filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        click.echo("Error: Invalid email or master password.", err=True)
        raise click.Abort()
        
    # Verify TOTP 2FA code
    totp = pyotp.totp.TOTP(user.totp_secret)
    if not totp.verify(totp_code.strip()):
        click.echo("Error: Invalid 2FA verification code.", err=True)
        raise click.Abort()
        
    # Derive user key from password and secret key
    salt_bytes = bytes.fromhex(user.salt)
    try:
        user_key = derive_user_key(password, secret_key, salt_bytes)
    except Exception:
        click.echo("Error: Invalid secret key format.", err=True)
        raise click.Abort()
        
    return user, user_key

@click.group()
def cli():
    """PyVault: A secure command-line password manager."""
    pass

@cli.command()
@click.option('--email', prompt=True, help='Email address to register.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Master password.')
def register(email, password):
    """Register a new master account."""
    from werkzeug.security import generate_password_hash
    import pyotp
    
    db = SessionLocal()
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        click.echo("Error: Email address already registered.")
        db.close()
        raise click.Abort()
        
    salt = os.urandom(16).hex()
    password_hash = generate_password_hash(password)
    totp_secret = pyotp.random_base32()
    secret_key = generate_secret_key()
    
    click.echo("\n==================================================")
    click.echo("ACCOUNT SETUP INITIALIZED (PENDING 2FA ACTIVATION)")
    click.echo("==================================================")
    click.echo(f"Registrant Email: {email}")
    click.echo(f"Your Secret Key:  {secret_key}")
    click.echo(f"2FA Setup Key:    {totp_secret}")
    click.echo("==================================================")
    click.echo("IMPORTANT SECURITY INSTRUCTIONS:")
    click.echo("1. Copy the Secret Key above and store it in a safe place.")
    click.echo("2. Add the 2FA Setup Key manually to Google Authenticator.")
    click.echo("==================================================\n")
    
    totp = pyotp.totp.TOTP(totp_secret)
    code = click.prompt("Enter the 6-digit Google Authenticator code to verify and activate your vault")
    
    if not totp.verify(code.strip()):
        click.echo("Error: Invalid 2FA verification code. Registration aborted. User not created.", err=True)
        db.close()
        raise click.Abort()
        
    new_user = User(email=email, password_hash=password_hash, salt=salt, totp_secret=totp_secret)
    db.add(new_user)
    db.commit()
    db.close()
    
    click.echo("\n==================================================")
    click.echo("ACCOUNT SUCCESSFULLY REGISTERED AND ACTIVATED")
    click.echo("==================================================\n")

@cli.command()
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--secret-key', prompt=True, hide_input=True, help='Your unique secret key.')
@click.option('--totp-code', prompt=True, help='Your 6-digit Google Authenticator code.')
@click.option('--service', prompt='Service name', help='The service for the password.')
@click.option('--username', prompt='Username', help='The username for the service.')
@click.option('--password-to-store', prompt='Password to store (leave blank to auto-generate)', default='', hide_input=True, confirmation_prompt=True, help='Password to encrypt and store.')
def add(email, password, secret_key, totp_code, service, username, password_to_store):
    """Add a new password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password, secret_key, totp_code)
    
    # Check if service already exists for this user
    existing = db.query(Password).filter_by(user_id=user.id, service=service).first()
    if existing:
        click.echo(f"Error: Password for {service} already exists.")
        db.close()
        raise click.Abort()
        
    final_password = password_to_store or generate_password()
    encrypted = encrypt_password(final_password, user_key)
    new_pass = Password(user_id=user.id, service=service, username=username, encrypted_password=encrypted)
    db.add(new_pass)
    db.commit()
    db.close()
    click.echo(f"Password for {service} added successfully.")

@cli.command()
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--secret-key', prompt=True, hide_input=True, help='Your unique secret key.')
@click.option('--totp-code', prompt=True, help='Your 6-digit Google Authenticator code.')
@click.option('--service', prompt='Service name', help='The service to retrieve the password for.')
def get(email, password, secret_key, totp_code, service):
    """Retrieve a password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password, secret_key, totp_code)
    password_entry = db.query(Password).filter_by(user_id=user.id, service=service).first()
    db.close()
    if password_entry:
        decrypted = decrypt_password(password_entry.encrypted_password, user_key)
        click.echo(f"Username: {password_entry.username}")
        click.echo(f"Password: {decrypted}")
    else:
        click.echo(f"No password found for {service}.")

@cli.command()
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--secret-key', prompt=True, hide_input=True, help='Your unique secret key.')
@click.option('--totp-code', prompt=True, help='Your 6-digit Google Authenticator code.')
@click.option('--service', prompt='Service name', help='The service to update the password for.')
@click.option('--username', prompt='New username (leave blank to keep current)', default='', help='The new username.')
@click.option('--password-to-store', prompt='New password (leave blank to auto-generate)', default='', hide_input=True, confirmation_prompt=True, help='New password.')
def update(email, password, secret_key, totp_code, service, username, password_to_store):
    """Update an existing password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password, secret_key, totp_code)
    password_entry = db.query(Password).filter_by(user_id=user.id, service=service).first()
    if password_entry:
        final_pass = password_to_store or generate_password()
        encrypted = encrypt_password(final_pass, user_key)
        password_entry.encrypted_password = encrypted
        if username:
            password_entry.username = username
        db.commit()
        click.echo(f"Password for {service} updated successfully.")
    else:
        click.echo(f"No password found for {service}.")
    db.close()

@cli.command()
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--secret-key', prompt=True, hide_input=True, help='Your unique secret key.')
@click.option('--totp-code', prompt=True, help='Your 6-digit Google Authenticator code.')
@click.option('--service', prompt='Service name', help='The service to delete.')
def delete(email, password, secret_key, totp_code, service):
    """Delete a password."""
    db = SessionLocal()
    user, _ = authenticate_user(db, email, password, secret_key, totp_code)
    password_entry = db.query(Password).filter_by(user_id=user.id, service=service).first()
    if password_entry:
        db.delete(password_entry)
        db.commit()
        click.echo(f"Password for {service} deleted successfully.")
    else:
        click.echo(f"No password found for {service}.")
    db.close()

@click.command('list')
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--secret-key', prompt=True, hide_input=True, help='Your unique secret key.')
@click.option('--totp-code', prompt=True, help='Your 6-digit Google Authenticator code.')
def list_services(email, password, secret_key, totp_code):
    """List all stored services."""
    db = SessionLocal()
    user, _ = authenticate_user(db, email, password, secret_key, totp_code)
    passwords = db.query(Password).filter_by(user_id=user.id).all()
    db.close()
    if passwords:
        for p in passwords:
            click.echo(f"Service: {p.service}, Username: {p.username}")
    else:
        click.echo("No passwords stored.")

cli.add_command(list_services, name='list')

@cli.command()
@click.option('--length', default=12, help='Length of the generated password.')
def generate(length):
    """Generate a random password."""
    password = generate_password(length)
    click.echo(f"Generated password: {password}")

if __name__ == '__main__':
    init_db()
    cli()