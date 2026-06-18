from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import io
import pyotp
import qrcode
import qrcode.image.svg

from .database import init_db, SessionLocal
from .models import Password, User
from .encryption import generate_secret_key, derive_user_key, encrypt_password, decrypt_password
from .utils import generate_password

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# Initialize database
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'user_key' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Home page - list all passwords for current user"""
    db = SessionLocal()
    passwords = db.query(Password).filter_by(user_id=session['user_id']).all()
    db.close()
    return render_template('index.html', passwords=passwords)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register step 1: Email and Master Password"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        
        db = SessionLocal()
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            flash('Email address already registered.', 'error')
            db.close()
            return redirect(url_for('register'))
            
        salt = os.urandom(16).hex()
        password_hash = generate_password_hash(password)
        totp_secret = pyotp.random_base32()
        secret_key = generate_secret_key()
        
        new_user = User(email=email, password_hash=password_hash, salt=salt, totp_secret=totp_secret)
        db.add(new_user)
        db.commit()
        db.close()
        
        # Save setup information in session for Step 2
        session['setup_email'] = email
        session['setup_totp_secret'] = totp_secret
        session['setup_secret_key'] = secret_key
        
        return redirect(url_for('setup_2fa'))
        
    return render_template('register.html')

@app.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    """Register step 2: Display Secret Key and scan TOTP QR Code"""
    if 'setup_email' not in session or 'setup_totp_secret' not in session:
        return redirect(url_for('register'))
        
    email = session['setup_email']
    totp_secret = session['setup_totp_secret']
    secret_key = session['setup_secret_key']
    
    # Generate Google Authenticator URI
    totp = pyotp.totp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(name=email, issuer_name="PyVault")
    
    # Render SVG QR Code
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(provisioning_uri, image_factory=factory)
    stream = io.BytesIO()
    img.save(stream)
    qr_svg = stream.getvalue().decode('utf-8')
    
    if request.method == 'POST':
        code = request.form['code'].strip()
        if totp.verify(code):
            # 2FA code is valid! Cleanup and finish registration.
            session.pop('setup_email', None)
            session.pop('setup_totp_secret', None)
            session.pop('setup_secret_key', None)
            flash('Registration successful! Please log in using your Master Password, Secret Key, and 2FA Code.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid 2FA code. Please verify that your authenticator app is synced and try again.', 'error')
            
    return render_template('setup_2fa.html', qr_svg=qr_svg, secret_key=secret_key, email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login step 1: Check Master Password and Secret Key"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        secret_key = request.form['secret_key'].strip()
        
        db = SessionLocal()
        user = db.query(User).filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            db.close()
            return redirect(url_for('login'))
            
        # Derive the key using BOTH Master Password and Secret Key
        salt_bytes = bytes.fromhex(user.salt)
        try:
            user_key = derive_user_key(password, secret_key, salt_bytes)
        except Exception:
            flash('Invalid secret key format.', 'error')
            db.close()
            return redirect(url_for('login'))
            
        session['temp_user_id'] = user.id
        session['temp_email'] = user.email
        session['temp_user_key'] = user_key.decode()
        db.close()
        
        return redirect(url_for('verify_2fa'))
        
    return render_template('login.html')

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Login step 2: Prompt for Google Authenticator TOTP Code"""
    if 'temp_user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        code = request.form['code'].strip()
        
        db = SessionLocal()
        user = db.query(User).filter_by(id=session['temp_user_id']).first()
        db.close()
        
        if user:
            totp = pyotp.totp.TOTP(user.totp_secret)
            if totp.verify(code):
                # Promote to full authenticated session
                session['user_id'] = session.pop('temp_user_id')
                session['email'] = session.pop('temp_email')
                session['user_key'] = session.pop('temp_user_key')
                
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid 2FA code. Please try again.', 'error')
        else:
            return redirect(url_for('login'))
            
    return render_template('verify_2fa.html')

@app.route('/logout')
def logout():
    """Logout current user"""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_password():
    """Add a new password"""
    if request.method == 'POST':
        service = request.form['service'].strip()
        username = request.form['username'].strip()
        password = request.form['password'] or generate_password()

        db = SessionLocal()

        # Check if service already exists for this user
        existing = db.query(Password).filter_by(user_id=session['user_id'], service=service).first()
        if existing:
            flash(f'Password for {service} already exists!', 'error')
            db.close()
            return redirect(url_for('add_password'))

        encrypted_password = encrypt_password(password, session['user_key'])
        new_password = Password(
            user_id=session['user_id'],
            service=service,
            username=username,
            encrypted_password=encrypted_password
        )
        db.add(new_password)
        db.commit()
        db.close()

        flash(f'Password for {service} added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/get/<service>')
@login_required
def get_password(service):
    """Retrieve and display a password"""
    db = SessionLocal()
    password_entry = db.query(Password).filter_by(user_id=session['user_id'], service=service).first()
    db.close()

    if not password_entry:
        flash(f'No password found for {service}', 'error')
        return redirect(url_for('index'))

    decrypted_password = decrypt_password(password_entry.encrypted_password, session['user_key'])
    return render_template('get.html', service=service, username=password_entry.username, password=decrypted_password)

@app.route('/update/<service>', methods=['GET', 'POST'])
@login_required
def update_password(service):
    """Update an existing password"""
    db = SessionLocal()
    password_entry = db.query(Password).filter_by(user_id=session['user_id'], service=service).first()

    if not password_entry:
        db.close()
        flash(f'No password found for {service}', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_password = request.form['password'] or generate_password()
        password_entry.encrypted_password = encrypt_password(new_password, session['user_key'])
        db.commit()
        db.close()
        flash(f'Password for {service} updated successfully!', 'success')
        return redirect(url_for('index'))

    username = password_entry.username
    db.close()
    return render_template('update.html', service=service, username=username)

@app.route('/delete/<service>')
@login_required
def delete_password(service):
    """Delete a password"""
    db = SessionLocal()
    password_entry = db.query(Password).filter_by(user_id=session['user_id'], service=service).first()

    if password_entry:
        db.delete(password_entry)
        db.commit()
        flash(f'Password for {service} deleted successfully!', 'success')
    else:
        flash(f'No password found for {service}', 'error')

    db.close()
    return redirect(url_for('index'))

@app.route('/generate')
def generate():
    """Generate a random password"""
    password = generate_password()
    return render_template('generate.html', password=password)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host=host, port=port, debug=debug)