import click
from sqlalchemy.orm import Session
import os

from .database import SessionLocal, init_db
from .models import Password, User
from .encryption import derive_user_key, encrypt_password, decrypt_password
from .utils import generate_password

def authenticate_user(db: Session, email: str, password: str):
    from werkzeug.security import check_password_hash
    user = db.query(User).filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        click.echo("Error: Invalid email or master password.", err=True)
        raise click.Abort()
    
    salt_bytes = bytes.fromhex(user.salt)
    user_key = derive_user_key(password, salt_bytes)
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
    db = SessionLocal()
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        click.echo("Error: Email address already registered.")
        db.close()
        raise click.Abort()
        
    salt = os.urandom(16).hex()
    password_hash = generate_password_hash(password)
    new_user = User(email=email, password_hash=password_hash, salt=salt)
    db.add(new_user)
    db.commit()
    db.close()
    click.echo(f"Account for {email} registered successfully.")

@cli.command()
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
@click.option('--service', prompt='Service name', help='The service for the password.')
@click.option('--username', prompt='Username', help='The username for the service.')
@click.option('--password-to-store', prompt='Password to store (leave blank to auto-generate)', default='', hide_input=True, confirmation_prompt=True, help='Password to encrypt and store.')
def add(email, password, service, username, password_to_store):
    """Add a new password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password)
    
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
@click.option('--service', prompt='Service name', help='The service to retrieve the password for.')
def get(email, password, service):
    """Retrieve a password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password)
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
@click.option('--service', prompt='Service name', help='The service to update the password for.')
@click.option('--username', prompt='New username (leave blank to keep current)', default='', help='The new username.')
@click.option('--password-to-store', prompt='New password (leave blank to auto-generate)', default='', hide_input=True, confirmation_prompt=True, help='New password.')
def update(email, password, service, username, password_to_store):
    """Update an existing password."""
    db = SessionLocal()
    user, user_key = authenticate_user(db, email, password)
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
@click.option('--service', prompt='Service name', help='The service to delete.')
def delete(email, password, service):
    """Delete a password."""
    db = SessionLocal()
    user, _ = authenticate_user(db, email, password)
    password_entry = db.query(Password).filter_by(user_id=user.id, service=service).first()
    if password_entry:
        db.delete(password_entry)
        db.commit()
        click.echo(f"Password for {service} deleted successfully.")
    else:
        click.echo(f"No password found for {service}.")
    db.close()

@click.command('list') # Click commands are by default named after function name, but list is a built-in
@click.option('--email', prompt=True, help='Your account email.')
@click.option('--password', prompt=True, hide_input=True, help='Your master password.')
def list_services(email, password):
    """List all stored services."""
    db = SessionLocal()
    user, _ = authenticate_user(db, email, password)
    passwords = db.query(Password).filter_by(user_id=user.id).all()
    db.close()
    if passwords:
        for p in passwords:
            click.echo(f"Service: {p.service}, Username: {p.username}")
    else:
        click.echo("No passwords stored.")

# Manually add list command to avoid conflict with standard keyword in function name and ensure clean parsing
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