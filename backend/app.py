"""
CSSC - Cyber Security Students Club
Backend Member Management System
Flask Application (app.py)

Modernized with SQLite, SQLAlchemy, and Security Hardening.
"""

import os
import csv
import re
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, request, jsonify, render_template_string,
                   redirect, url_for, session, send_file, abort)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# APP SETUP
# ============================================================
app = Flask(__name__)

# CONFIGURATION
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_low_security')

# Detect if running on Vercel (read-only filesystem)
is_vercel = os.environ.get('VERCEL', False)
if is_vercel:
    # Use /tmp for SQLite in Vercel's serverless environment
    db_path = os.path.join('/tmp', 'cssc_members.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cssc_members.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
# In a real app, you'd store the hash of the admin password in the DB.
# For simplicity here, we'll hash the env/default password for comparison.
ADMIN_PASS_PLAIN = os.environ.get('ADMIN_PASS', 'cssc@2026')
ADMIN_PASS_HASH = generate_password_hash(ADMIN_PASS_PLAIN)

# ============================================================
# DATABASE MODELS
# ============================================================
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    skills = db.Column(db.Text, nullable=True)
    interest_area = db.Column(db.String(100), nullable=False)
    accept_oath = db.Column(db.Boolean, default=False)
    accept_terms = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminAccess(db.Model):
    """Tracks the active session token to enforce single-session access."""
    id = db.Column(db.Integer, primary_key=True)
    active_token = db.Column(db.String(100), nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ID': self.member_id,
            'Full Name': self.full_name,
            'Department': self.department,
            'Year': self.year,
            'Email': self.email,
            'Phone': self.phone,
            'Skills': self.skills or 'Not specified',
            'Interest Area': self.interest_area,
            'Accept Oath': 'Yes' if self.accept_oath else 'No',
            'Accept Terms': 'Yes' if self.accept_terms else 'No',
            'Registered At': self.registered_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# ============================================================
# HELPERS
# ============================================================
def sanitize(value, max_len=500):
    """Basic sanitization: strip whitespace, limit length, remove dangerous chars."""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()[:max_len]
    dangerous = ['<', '>', '"', "'", '=', ';', '(', ')', '{', '}', '\\']
    for ch in dangerous:
        value = value.replace(ch, '')
    return value

def generate_id():
    """Generate a unique member ID: CSSC-XXX."""
    last_member = Member.query.order_by(Member.id.desc()).first()
    if not last_member:
        return 'CSSC-001'
    try:
        num = int(last_member.member_id.split('-')[1]) + 1
    except (IndexError, ValueError):
        num = Member.query.count() + 1
    return f'CSSC-{num:03d}'

def migrate_csv_to_db():
    """Import existing data from members.csv into SQLite if DB is empty."""
    csv_path = os.path.join(os.path.dirname(__file__), 'members.csv')
    if os.path.exists(csv_path) and Member.query.count() == 0:
        print("--- Migrating members.csv to SQLite ---")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map CSV headers to Model fields
                    m = Member(
                        member_id=row.get('ID'),
                        full_name=row.get('Full Name'),
                        department=row.get('Department'),
                        year=row.get('Year'),
                        email=row.get('Email'),
                        phone=row.get('Phone'),
                        skills=row.get('Skills'),
                        interest_area=row.get('Interest Area'),
                        accept_oath=(row.get('Accept Oath') == 'Yes'),
                        accept_terms=(row.get('Accept Terms') == 'Yes'),
                        registered_at=datetime.strptime(row.get('Registered At'), '%Y-%m-%d %H:%M:%S') 
                                      if row.get('Registered At') else datetime.utcnow()
                    )
                    db.session.add(m)
                db.session.commit()
            print(f"Migration complete. Archiving members.csv...")
            os.rename(csv_path, csv_path + ".bak")
        except Exception as e:
            print(f"Migration error: {e}")
            db.session.rollback()

# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        
        # Verify if current session token matches the one in the DB
        # This prevents multiple concurrent logins (Single Session Enforcement)
        access = AdminAccess.query.first()
        current_token = session.get('admin_token')
        
        if not access or not current_token or access.active_token != current_token:
            # Token mismatch or stale session -> Force re-login
            session.clear()
            return redirect(url_for('admin_login'))
            
        return f(*args, **kwargs)
    return decorated

# ============================================================
# ROUTES – Frontend API
# ============================================================
@app.route('/')
def index():
    return jsonify({'status': 'CSSC Backend Running', 'version': '2.0 (SQLite)'})

@app.route('/register', methods=['POST'])
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request format.'}), 400

        required_fields = ['full_name', 'department', 'year', 'email', 'phone', 'interest']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'success': False, 'message': f'Field "{field}" is required.'}), 400

        # Sanitize
        full_name  = sanitize(data.get('full_name', ''), 100)
        department = sanitize(data.get('department', ''), 50)
        year       = sanitize(data.get('year', ''), 20)
        email      = sanitize(data.get('email', ''), 150).lower()
        phone      = sanitize(data.get('phone', ''), 20)
        skills     = sanitize(data.get('skills', ''), 300)
        interest   = sanitize(data.get('interest', ''), 100)
        accept_oath  = bool(data.get('accept_oath', False))
        accept_terms = bool(data.get('accept_terms', False))

        # Validate
        if len(full_name) < 2:
            return jsonify({'success': False, 'message': 'Full name is too short.'}), 400

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'success': False, 'message': 'Invalid email address.'}), 400

        if not re.match(r'^[+]?[0-9\s\-]{10,15}$', phone):
            return jsonify({'success': False, 'message': 'Invalid phone number.'}), 400

        if not accept_oath or not accept_terms:
            return jsonify({'success': False, 'message': 'You must accept the Club Oath and Terms & Conditions.'}), 400

        if Member.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'This email is already registered.'}), 409

        # Save
        member_id = generate_id()
        new_member = Member(
            member_id=member_id,
            full_name=full_name,
            department=department,
            year=year,
            email=email,
            phone=phone,
            skills=skills,
            interest_area=interest,
            accept_oath=accept_oath,
            accept_terms=accept_terms
        )
        db.session.add(new_member)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Registration successful! Your member ID is {member_id}.',
            'member_id': member_id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Registration error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error.'}), 500

# ============================================================
# ADMIN ROUTES (HTML TEMPLATES INCLUDED)
# ============================================================

# Simplified Templates (Keeping the previous design for now, will polish later)
ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSSC - Authorized Access</title>
<style>
  :root {
    --neon-green: #00ff88;
    --neon-blue: #00d4ff;
    --bg-dark: #020c14;
    --bg-card: #071e30;
    --border-glow: rgba(0, 255, 136, 0.4);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { 
    background: var(--bg-dark); 
    color: #e0f0ff; 
    font-family: 'Segoe UI', sans-serif; 
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center; 
    padding: 1rem;
    background-image: radial-gradient(circle at 50% 50%, #051525 0%, #020c14 100%);
  }
  .card { 
    background: var(--bg-card); 
    border: 1px solid var(--border-glow); 
    border-radius: 12px;
    padding: 3rem; width: 100%; max-width: 420px; 
    box-shadow: 0 0 50px rgba(0,255,136,0.1), inset 0 0 20px rgba(0,255,136,0.05);
    position: relative; overflow: hidden;
  }
  .card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--neon-green), transparent);
    animation: scan 3s linear infinite;
  }
  @keyframes scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  .icon { text-align: center; font-size: 3.5rem; margin-bottom: 1rem; filter: drop-shadow(0 0 10px var(--neon-green)); }
  h1 { text-align: center; font-size: 1.5rem; color: var(--neon-green); font-family: monospace; letter-spacing: 4px; margin-bottom: 0.5rem; text-transform: uppercase; }
  .sub { text-align: center; font-size: 0.75rem; color: #ff2d55; letter-spacing: 2px; font-family: monospace; margin-bottom: 2.5rem; }
  label { display: block; font-size: 0.85rem; color: #8ab0c8; margin-bottom: 0.6rem; font-family: monospace; text-transform: uppercase; letter-spacing: 1px; }
  input { 
    width: 100%; background: #051525; border: 1px solid rgba(0,255,136,0.2); border-radius: 6px;
    padding: 12px 16px; color: #e0f0ff; font-size: 1rem; margin-bottom: 1.5rem; outline: none;
    transition: all 0.3s;
  }
  input:focus { border-color: var(--neon-green); box-shadow: 0 0 15px rgba(0,255,136,0.2); background: #071e30; }
  button { 
    width: 100%; background: var(--neon-green); color: #020c14; border: none; border-radius: 6px;
    padding: 15px; font-size: 1.1rem; font-weight: 800; cursor: pointer; font-family: monospace;
    letter-spacing: 3px; transition: all 0.3s; text-transform: uppercase;
  }
  button:hover { background: #00ffaa; transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,255,136,0.5); }
  .error { 
    background: rgba(255,45,85,0.1); border: 1px solid rgba(255,45,85,0.3); border-radius: 6px;
    padding: 1rem; font-size: 0.9rem; color: #ff2d55; margin-bottom: 1.5rem; text-align: center;
    font-family: monospace; border-left: 4px solid #ff2d55;
  }
  .back { text-align: center; margin-top: 1.5rem; }
  .back a { color: var(--neon-blue); text-decoration: none; font-size: 0.9rem; font-family: monospace; transition: 0.3s; }
  .back a:hover { color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); }
</style>
</head>
<body>
<div class="card">
  <div class="icon">🛡️</div>
  <h1>Access Control</h1>
  <p class="sub">AUTHORIZATION REQUIRED</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <label>Operator ID</label><input type="text" name="username" required autocomplete="username" placeholder="ADMIN_USERNAME" />
    <label>Access Code</label><input type="password" name="password" required autocomplete="current-password" placeholder="********" />
    <button type="submit">Execute Login</button>
  </form>
  <div class="back"><a href="/">[ RETURN_TO_SYSTEM ]</a></div>
</div>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSSC Command Center</title>
<style>
  :root {
    --neon-green: #00ff88;
    --neon-blue: #00d4ff;
    --bg-dark: #020c14;
    --bg-panel: #051525;
    --bg-card: #071e30;
    --grid-line: rgba(0, 255, 136, 0.05);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { 
    background: var(--bg-dark); 
    color: #e0f0ff; 
    font-family: 'Segoe UI', sans-serif; 
    min-height: 100vh;
    background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), 
                      linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 30px 30px;
  }
  .header { 
    background: var(--bg-panel); 
    border-bottom: 2px solid var(--neon-green); 
    padding: 1.25rem 2.5rem;
    display: flex; align-items: center; justify-content: space-between; 
    flex-wrap: wrap; gap: 1rem;
    box-shadow: 0 5px 25px rgba(0,0,0,0.5);
    position: sticky; top: 0; z-index: 100;
  }
  .title { font-family: monospace; font-size: 1.4rem; color: var(--neon-green); letter-spacing: 3px; font-weight: 800; text-transform: uppercase; }
  .badge { background: rgba(0,212,255,0.1); border: 1px solid var(--neon-blue); padding: 4px 12px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; color: var(--neon-blue); text-transform: uppercase; }
  .actions { display: flex; gap: 1rem; flex-wrap: wrap; }
  .btn { 
    padding: 10px 20px; border-radius: 4px; font-size: 0.85rem; cursor: pointer;
    text-decoration: none; font-family: monospace; border: none; font-weight: 700; 
    transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px;
    text-transform: uppercase; letter-spacing: 1px;
  }
  .btn-green { background: var(--neon-green); color: #020c14; box-shadow: 0 0 15px rgba(0,255,136,0.3); }
  .btn-green:hover { background: #00ffaa; transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,255,136,0.5); }
  .btn-red { background: rgba(255,45,85,0.1); color: #ff2d55; border: 1px solid #ff2d55; }
  .btn-red:hover { background: #ff2d55; color: #fff; }

  .content { padding: 2.5rem; max-width: 1400px; margin: 0 auto; }
  .stats-row { display: flex; gap: 1.5rem; margin-bottom: 2.5rem; flex-wrap: wrap; }
  .stat-box { 
    background: var(--bg-card); 
    border: 1px solid rgba(0,255,136,0.15); 
    border-radius: 8px;
    padding: 1.5rem 2rem; flex: 1; min-width: 200px;
    border-left: 4px solid var(--neon-green);
    transition: 0.3s;
  }
  .stat-box:hover { transform: translateY(-5px); border-color: var(--neon-green); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
  .stat-num { font-family: monospace; font-size: 2.5rem; font-weight: 800; color: var(--neon-green); line-height: 1; }
  .stat-lbl { font-size: 0.75rem; color: #8ab0c8; font-family: monospace; letter-spacing: 2px; margin-top: 8px; text-transform: uppercase; }
  
  .table-wrap { 
    background: var(--bg-card);
    overflow-x: auto; 
    border-radius: 12px; 
    border: 1px solid rgba(0,255,136,0.1);
    box-shadow: 0 15px 50px rgba(0,0,0,0.4);
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th { 
    font-family: monospace; font-size: 0.8rem; color: var(--neon-blue); text-align: left;
    padding: 16px; background: rgba(0,212,255,0.03); border-bottom: 2px solid rgba(0,212,255,0.1);
    text-transform: uppercase; letter-spacing: 1px;
  }
  td { padding: 14px 16px; color: #8ab0c8; border-bottom: 1px solid rgba(255,255,255,0.03); vertical-align: middle; }
  tr:hover td { background: rgba(0,255,136,0.02); color: #e0f0ff; }
  .id-badge { font-family: monospace; color: var(--neon-green); background: rgba(0,255,136,0.05); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,255,136,0.1); }
  .date-lbl { font-size: 0.8rem; opacity: 0.7; font-family: monospace; }
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">🛡️ CSSC Operations</div>
    <div class="badge">Session Active: Operator Root</div>
  </div>
  <div class="actions">
    <a href="{{ url_for('admin_download') }}" class="btn btn-green"><span>📥</span> CSV_EXPORT</a>
    <a href="{{ url_for('admin_logout') }}" class="btn btn-red"><span>🔓</span> TERMINATE_SESSION</a>
  </div>
</div>
<div class="content">
  <div class="stats-row">
    <div class="stat-box"><div class="stat-num">{{ members|length }}</div><div class="stat-lbl">Registered Assets</div></div>
    <div class="stat-box"><div class="stat-num">{{ members|selectattr('accept_oath','equalto',True)|list|length }}</div><div class="stat-lbl">Oath Verified</div></div>
    <div class="stat-box"><div class="stat-num">{{ members|map(attribute='department')|unique|list|length }}</div><div class="stat-lbl">Divisions Active</div></div>
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Identifier</th><th>Asset Name</th><th>Division</th><th>Comm Link</th><th>Vector</th><th>Timestamp</th><th>Action</th></tr></thead>
      <tbody>
        {% for m in members %}
        <tr>
          <td><span class="id-badge">{{ m.member_id }}</span></td>
          <td style="font-weight:600; color:#fff">{{ m.full_name }}</td>
          <td>{{ m.department }}</td>
          <td>{{ m.email }}</td>
          <td><span style="color:var(--neon-blue)">{{ m.interest_area }}</span></td>
          <td class="date-lbl">{{ m.registered_at.strftime('%Y-%m-%d %H:%M') }}</td>
          <td>
            <form method="POST" action="{{ url_for('admin_delete', member_id=m.member_id) }}" onsubmit="return confirm('Confirm Deletion?')">
              <button type="submit" class="btn btn-red" style="padding:6px 10px; font-size:0.7rem;">DELE</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>
"""

@app.route('/admin')
@login_required
def admin_panel():
    members = Member.query.order_by(Member.registered_at.desc()).all()
    return render_template_string(ADMIN_PANEL_HTML, members=members)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        # Check if current session is still valid even if flag is set
        access = AdminAccess.query.first()
        if access and session.get('admin_token') == access.active_token:
            return redirect(url_for('admin_panel'))
        else:
            session.clear()

    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USERNAME and check_password_hash(ADMIN_PASS_HASH, pw):
            # Generate a new unique token for this session
            new_token = str(uuid.uuid4())
            
            # Update or create the globally active token in DB
            access = AdminAccess.query.first()
            if not access:
                access = AdminAccess()
                access.active_token = new_token
                db.session.add(access)
            else:
                access.active_token = new_token
                access.last_login = datetime.utcnow()
            
            db.session.commit()

            # Store token in user session
            session['admin_logged_in'] = True
            session['admin_token'] = new_token
            return redirect(url_for('admin_panel'))
        error = "Invalid credentials."
    return render_template_string(ADMIN_LOGIN_HTML, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/delete/<member_id>', methods=['POST'])
@login_required
def admin_delete(member_id):
    member = Member.query.filter_by(member_id=member_id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/download')
@login_required
def admin_download():
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Full Name', 'Department', 'Year', 'Email', 'Phone', 'Skills', 'Interest', 'Registered At'])
    members = Member.query.all()
    for m in members:
        writer.writerow([m.member_id, m.full_name, m.department, m.year, m.email, m.phone, m.skills, m.interest_area, m.registered_at])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'cssc_members_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_csv_to_db()
    
    port = int(os.environ.get('PORT', 5000))
    # debug=True for dev, change to False for prod
    app.run(debug=True, host='127.0.0.1', port=port)
