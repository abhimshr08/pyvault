import click
from sqlalchemy.orm import Session
from .database import SessionLocal, init_db
from .models import Password
from .encryption import load_key, encrypt_password, decrypt_password
from .utils import generate_password

@click.group()
def cli():
    """PyVault: A secure command-line password manager."""
    pass

@cli.command()
@click.option('--service', prompt='Service name', help='The service for the password.')
@click.option('--username', prompt='Username', help='The username for the service.')
@click.option('--password', prompt='Password', help='The password to store.', hide_input=True, confirmation_prompt=True)
def add(service, username, password):
    """Add a new password."""
    db: Session = SessionLocal()
    key = load_key()
    encrypted = encrypt_password(password, key)
    new_pass = Password(service=service, username=username, encrypted_password=encrypted)
    db.add(new_pass)
    db.commit()
    db.close()
    click.echo(f"Password for {service} added successfully.")

@cli.command()
@click.option('--service', prompt='Service name', help='The service to retrieve the password for.')
def get(service):
    """Retrieve a password."""
    db: Session = SessionLocal()
    password_entry = db.query(Password).filter(Password.service == service).first()
    db.close()
    if password_entry:
        key = load_key()
        decrypted = decrypt_password(password_entry.encrypted_password, key)
        click.echo(f"Username: {password_entry.username}")
        click.echo(f"Password: {decrypted}")
    else:
        click.echo(f"No password found for {service}.")

@cli.command()
@click.option('--service', prompt='Service name', help='The service to update the password for.')
@click.option('--username', prompt='New username (leave blank to keep current)', default='', help='The new username.')
@click.option('--password', prompt='New password', help='The new password.', hide_input=True, confirmation_prompt=True)
def update(service, username, password):
    """Update an existing password."""
    db: Session = SessionLocal()
    password_entry = db.query(Password).filter(Password.service == service).first()
    if password_entry:
        key = load_key()
        encrypted = encrypt_password(password, key)
        password_entry.encrypted_password = encrypted
        if username:
            password_entry.username = username
        db.commit()
        click.echo(f"Password for {service} updated successfully.")
    else:
        click.echo(f"No password found for {service}.")
    db.close()

@cli.command()
@click.option('--service', prompt='Service name', help='The service to delete the password for.')
def delete(service):
    """Delete a password."""
    db: Session = SessionLocal()
    password_entry = db.query(Password).filter(Password.service == service).first()
    if password_entry:
        db.delete(password_entry)
        db.commit()
        click.echo(f"Password for {service} deleted successfully.")
    else:
        click.echo(f"No password found for {service}.")
    db.close()

@cli.command()
def list():
    """List all stored services."""
    db: Session = SessionLocal()
    passwords = db.query(Password).all()
    db.close()
    if passwords:
        for p in passwords:
            click.echo(f"Service: {p.service}, Username: {p.username}")
    else:
        click.echo("No passwords stored.")

@cli.command()
@click.option('--length', default=12, help='Length of the generated password.')
def generate(length):
    """Generate a random password."""
    password = generate_password(length)
    click.echo(f"Generated password: {password}")

if __name__ == '__main__':
    init_db()
    cli()