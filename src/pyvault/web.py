from flask import Flask, render_template, request, redirect, url_for, flash
from .database import init_db, SessionLocal
from .models import Password
from .encryption import encrypt_password, decrypt_password
from .utils import generate_password
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database
init_db()

@app.route('/')
def index():
    """Home page - list all passwords"""
    session = SessionLocal()
    passwords = session.query(Password).all()
    session.close()
    return render_template('index.html', passwords=passwords)

@app.route('/add', methods=['GET', 'POST'])
def add_password():
    """Add a new password"""
    if request.method == 'POST':
        service = request.form['service']
        username = request.form['username']
        password = request.form['password'] or generate_password()

        session = SessionLocal()

        # Check if service already exists
        existing = session.query(Password).filter_by(service=service).first()
        if existing:
            flash(f'Password for {service} already exists!', 'error')
            session.close()
            return redirect(url_for('add_password'))

        encrypted_password = encrypt_password(password)
        new_password = Password(service=service, username=username, password=encrypted_password)
        session.add(new_password)
        session.commit()
        session.close()

        flash(f'Password for {service} added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/get/<service>')
def get_password(service):
    """Retrieve and display a password"""
    session = SessionLocal()
    password_entry = session.query(Password).filter_by(service=service).first()
    session.close()

    if not password_entry:
        flash(f'No password found for {service}', 'error')
        return redirect(url_for('index'))

    decrypted_password = decrypt_password(password_entry.password)
    return render_template('get.html', service=service, username=password_entry.username, password=decrypted_password)

@app.route('/update/<service>', methods=['GET', 'POST'])
def update_password(service):
    """Update an existing password"""
    session = SessionLocal()
    password_entry = session.query(Password).filter_by(service=service).first()

    if not password_entry:
        session.close()
        flash(f'No password found for {service}', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_password = request.form['password'] or generate_password()
        password_entry.password = encrypt_password(new_password)
        session.commit()
        session.close()
        flash(f'Password for {service} updated successfully!', 'success')
        return redirect(url_for('index'))

    session.close()
    return render_template('update.html', service=service, username=password_entry.username)

@app.route('/delete/<service>')
def delete_password(service):
    """Delete a password"""
    session = SessionLocal()
    password_entry = session.query(Password).filter_by(service=service).first()

    if password_entry:
        session.delete(password_entry)
        session.commit()
        flash(f'Password for {service} deleted successfully!', 'success')
    else:
        flash(f'No password found for {service}', 'error')

    session.close()
    return redirect(url_for('index'))

@app.route('/generate')
def generate():
    """Generate a random password"""
    password = generate_password()
    return render_template('generate.html', password=password)

if __name__ == '__main__':
    app.run(debug=True, port=5002)