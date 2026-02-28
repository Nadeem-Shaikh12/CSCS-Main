"""
CSSC - Cyber Security Students Club
Backend Member Management System
Flask Application (app.py)

Run: python app.py
Admin Panel: http://127.0.0.1:5000/admin
"""

import os
import csv
import json
import hashlib
import secrets
from datetime import datetime
from functools import wraps

from flask import (Flask, request, jsonify, render_template_string,
                   redirect, url_for, session, send_file, abort)
from flask_cors import CORS

# ============================================================
# APP SETUP
# ============================================================
app = Flask(__name__)

# IMPORTANT: Change this secret key in production!
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Allow CORS from the frontend (localhost during development)
CORS(app, origins=["http://127.0.0.1:5500", "http://localhost:5500",
                   "http://127.0.0.1:8080", "http://localhost:8080",
                   "http://localhost:3000", "null"])

# ============================================================
# CONFIGURATION
# ============================================================
DATA_DIR    = os.path.dirname(os.path.abspath(__file__))
CSV_FILE    = os.path.join(DATA_DIR, 'members.csv')

# Admin credentials — CHANGE THESE before deploying!
ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'cssc@2026')  # Change this!

# CSV field headers
CSV_HEADERS = [
    'ID', 'Full Name', 'Department', 'Year', 'Email', 'Phone',
    'Skills', 'Interest Area', 'Accept Oath', 'Accept Terms',
    'Registered At'
]

# ============================================================
# HELPERS
# ============================================================
def ensure_csv():
    """Create CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def read_members():
    """Read all members from CSV. Returns list of dicts."""
    ensure_csv()
    members = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            members.append(dict(row))
    return members

def write_members(members):
    """Write all members list back to CSV."""
    ensure_csv()
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(members)

def sanitize(value, max_len=500):
    """Basic sanitization: strip whitespace, limit length, remove dangerous chars."""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()[:max_len]
    # Remove potential script injection chars
    dangerous = ['<', '>', '"', "'", '=', ';', '(', ')', '{', '}', '\\']
    for ch in dangerous:
        value = value.replace(ch, '')
    return value

def generate_id():
    """Generate a simple unique member ID."""
    members = read_members()
    if not members:
        return 'CSSC-001'
    last_id = members[-1].get('ID', 'CSSC-000')
    try:
        num = int(last_id.split('-')[1]) + 1
    except (IndexError, ValueError):
        num = len(members) + 1
    return f'CSSC-{num:03d}'

def is_duplicate_email(email):
    """Check if email already registered."""
    members = read_members()
    return any(m.get('Email','').lower() == email.lower() for m in members)


# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated


# ============================================================
# ROUTES – Frontend API
# ============================================================

@app.route('/')
def index():
    return jsonify({'status': 'CSSC Backend Running', 'version': '1.0'})


@app.route('/register', methods=['POST'])
def register():
    """
    Accept member registration from the frontend form.
    Validates input and saves to CSV.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request format.'}), 400

        # --- Required field validation ---
        required_fields = ['full_name', 'department', 'year', 'email', 'phone', 'interest']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'success': False, 'message': f'Field "{field}" is required.'}), 400

        # --- Sanitize inputs ---
        full_name  = sanitize(data.get('full_name', ''), 100)
        department = sanitize(data.get('department', ''), 50)
        year       = sanitize(data.get('year', ''), 20)
        email      = sanitize(data.get('email', ''), 150).lower()
        phone      = sanitize(data.get('phone', ''), 20)
        skills     = sanitize(data.get('skills', ''), 300)
        interest   = sanitize(data.get('interest', ''), 100)
        accept_oath  = bool(data.get('accept_oath', False))
        accept_terms = bool(data.get('accept_terms', False))

        # --- Field-level validation ---
        import re
        if len(full_name) < 2:
            return jsonify({'success': False, 'message': 'Full name is too short.'}), 400

        email_re = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_re, email):
            return jsonify({'success': False, 'message': 'Invalid email address.'}), 400

        phone_re = r'^[+]?[0-9\s\-]{10,15}$'
        if not re.match(phone_re, phone):
            return jsonify({'success': False, 'message': 'Invalid phone number.'}), 400

        if not accept_oath or not accept_terms:
            return jsonify({'success': False, 'message': 'You must accept the Club Oath and Terms & Conditions.'}), 400

        # --- Check duplicate email ---
        if is_duplicate_email(email):
            return jsonify({'success': False, 'message': 'This email is already registered. Contact us if you need help.'}), 409

        # --- Save to CSV ---
        member_id = generate_id()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        member_row = {
            'ID':           member_id,
            'Full Name':    full_name,
            'Department':   department,
            'Year':         year,
            'Email':        email,
            'Phone':        phone,
            'Skills':       skills or 'Not specified',
            'Interest Area': interest,
            'Accept Oath':  'Yes' if accept_oath else 'No',
            'Accept Terms': 'Yes' if accept_terms else 'No',
            'Registered At': timestamp
        }

        ensure_csv()
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writerow(member_row)

        print(f"[{timestamp}] New member registered: {full_name} ({email}) — ID: {member_id}")

        return jsonify({
            'success': True,
            'message': f'Registration successful! Your member ID is {member_id}.',
            'member_id': member_id
        }), 201

    except Exception as e:
        print(f"[ERROR] Registration error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error. Please try again.'}), 500


# ============================================================
# ADMIN ROUTES
# ============================================================

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSSC Admin Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #020c14; color: #e0f0ff; font-family: 'Segoe UI', sans-serif; min-height: 100vh;
         display: flex; align-items: center; justify-content: center; padding: 1rem; }
  .card { background: #071e30; border: 1px solid rgba(0,255,136,0.4); border-radius: 12px;
          padding: 3rem; width: 100%; max-width: 400px; box-shadow: 0 0 40px rgba(0,255,136,0.1); }
  .icon { text-align: center; font-size: 3rem; margin-bottom: 1rem; }
  h1 { text-align: center; font-size: 1.3rem; color: #00ff88; font-family: monospace; letter-spacing: 2px; margin-bottom: 0.25rem; }
  .sub { text-align: center; font-size: 0.75rem; color: #ff2d55; letter-spacing: 2px; font-family: monospace; margin-bottom: 2rem; }
  label { display: block; font-size: 0.82rem; color: #8ab0c8; margin-bottom: 0.4rem; font-family: monospace; }
  input { width: 100%; background: #051525; border: 1px solid rgba(0,255,136,0.2); border-radius: 6px;
          padding: 11px 14px; color: #e0f0ff; font-size: 0.92rem; margin-bottom: 1.25rem; outline: none; }
  input:focus { border-color: #00ff88; box-shadow: 0 0 0 3px rgba(0,255,136,0.1); }
  button { width: 100%; background: #00ff88; color: #020c14; border: none; border-radius: 6px;
           padding: 13px; font-size: 1rem; font-weight: 700; cursor: pointer; font-family: monospace;
           letter-spacing: 2px; transition: all 0.3s; }
  button:hover { background: #00cc6a; box-shadow: 0 0 20px rgba(0,255,136,0.4); }
  .error { background: rgba(255,45,85,0.1); border: 1px solid rgba(255,45,85,0.3); border-radius: 6px;
           padding: 0.75rem 1rem; font-size: 0.88rem; color: #ff2d55; margin-bottom: 1rem; text-align: center; }
  .back { text-align: center; margin-top: 1rem; }
  .back a { color: #00ff88; text-decoration: none; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="card">
  <div class="icon">🔐</div>
  <h1>ADMIN ACCESS</h1>
  <p class="sub">⚠ RESTRICTED ZONE ⚠</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST" action="/admin/login">
    <label>Username</label>
    <input type="text" name="username" placeholder="admin" required autocomplete="username" />
    <label>Password</label>
    <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password" />
    <button type="submit">🔓 LOGIN</button>
  </form>
  <div class="back"><a href="/">← Back to API</a></div>
</div>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSSC Admin Panel</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #020c14; color: #e0f0ff; font-family: 'Segoe UI', sans-serif; min-height: 100vh; }
  .header { background: #051525; border-bottom: 2px solid #00ff88; padding: 1rem 2rem;
            display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
  .title { font-family: monospace; font-size: 1.1rem; color: #00ff88; letter-spacing: 2px; }
  .badge { background: rgba(255,45,85,0.1); border: 1px solid #ff2d55; padding: 4px 14px;
           border-radius: 3px; font-family: monospace; font-size: 0.75rem; color: #ff2d55; }
  .actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }
  .btn { padding: 8px 18px; border-radius: 4px; font-size: 0.85rem; cursor: pointer;
         text-decoration: none; font-family: monospace; border: none; font-weight: 600; transition: all 0.3s; display: inline-block; }
  .btn-green { background: #00ff88; color: #020c14; }
  .btn-green:hover { background: #00cc6a; }
  .btn-red { background: rgba(255,45,85,0.15); color: #ff2d55; border: 1px solid #ff2d55; }
  .btn-red:hover { background: rgba(255,45,85,0.3); }
  .content { padding: 2rem; max-width: 1400px; margin: 0 auto; }
  .stats-row { display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
  .stat-box { background: #071e30; border: 1px solid rgba(0,255,136,0.2); border-radius: 8px;
              padding: 1.25rem 1.5rem; flex: 1; min-width: 150px; }
  .stat-num { font-family: monospace; font-size: 2rem; font-weight: 700; color: #00ff88; }
  .stat-lbl { font-size: 0.8rem; color: #4a6a7a; font-family: monospace; letter-spacing: 1px; margin-top: 4px; }
  .search-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
  .search-input { flex: 1; background: #071e30; border: 1px solid rgba(0,255,136,0.2); border-radius: 6px;
                  padding: 10px 14px; color: #e0f0ff; font-size: 0.9rem; outline: none; }
  .search-input:focus { border-color: #00ff88; }
  .table-wrap { overflow-x: auto; border-radius: 8px; border: 1px solid rgba(0,255,136,0.15); }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { font-family: monospace; font-size: 0.75rem; color: #00ff88; letter-spacing: 1px; text-align: left;
       padding: 12px 14px; background: rgba(0,255,136,0.05); white-space: nowrap; border-bottom: 1px solid rgba(0,255,136,0.2); }
  td { padding: 11px 14px; color: #8ab0c8; border-bottom: 1px solid rgba(0,255,136,0.06); vertical-align: middle;
       max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  tr:hover td { background: rgba(0,255,136,0.03); }
  td.id { font-family: monospace; color: #00ff88; font-size: 0.8rem; }
  td.timestamp { font-family: monospace; font-size: 0.78rem; color: #4a6a7a; }
  .empty { text-align: center; padding: 3rem; color: #4a6a7a; font-family: monospace; }
  .count { font-family: monospace; font-size: 0.82rem; color: #4a6a7a; margin-top: 1rem; }
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">🛡️ CSSC ADMIN PANEL</div>
    <div class="badge">⚠ RESTRICTED ACCESS</div>
  </div>
  <div class="actions">
    <a href="/admin/download" class="btn btn-green">📥 Download CSV</a>
    <a href="/admin/logout" class="btn btn-red">🔓 Logout</a>
  </div>
</div>

<div class="content">
  <div class="stats-row">
    <div class="stat-box">
      <div class="stat-num">{{ members|length }}</div>
      <div class="stat-lbl">TOTAL MEMBERS</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">{{ members|selectattr('Accept Oath','equalto','Yes')|list|length }}</div>
      <div class="stat-lbl">OATH ACCEPTED</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">{{ members|groupby('Department')|list|length }}</div>
      <div class="stat-lbl">DEPARTMENTS</div>
    </div>
  </div>

  <div class="search-row">
    <input class="search-input" type="text" id="searchInput" placeholder="🔍 Search by name, email, department, ID..." oninput="filterTable()" />
  </div>

  {% if members %}
  <div class="table-wrap">
    <table id="membersTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Full Name</th>
          <th>Department</th>
          <th>Year</th>
          <th>Email</th>
          <th>Phone</th>
          <th>Skills</th>
          <th>Interest</th>
          <th>Oath</th>
          <th>Terms</th>
          <th>Registered At</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for m in members %}
        <tr>
          <td class="id">{{ m['ID'] }}</td>
          <td>{{ m['Full Name'] }}</td>
          <td>{{ m['Department'] }}</td>
          <td>{{ m['Year'] }}</td>
          <td>{{ m['Email'] }}</td>
          <td>{{ m['Phone'] }}</td>
          <td title="{{ m['Skills'] }}">{{ m['Skills'][:40] }}{% if m['Skills']|length > 40 %}...{% endif %}</td>
          <td>{{ m['Interest Area'] }}</td>
          <td style="color:{% if m['Accept Oath']=='Yes' %}#00ff88{% else %}#ff2d55{% endif %}">{{ m['Accept Oath'] }}</td>
          <td style="color:{% if m['Accept Terms']=='Yes' %}#00ff88{% else %}#ff2d55{% endif %}">{{ m['Accept Terms'] }}</td>
          <td class="timestamp">{{ m['Registered At'] }}</td>
          <td>
            <form method="POST" action="/admin/delete/{{ m['ID'] }}"
                  onsubmit="return confirm('Delete {{ m['Full Name'] }}? This cannot be undone.')">
              <button type="submit" class="btn btn-red" style="padding:5px 12px; font-size:0.78rem;">🗑 Delete</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <p class="count">Showing <span id="visibleCount">{{ members|length }}</span> of {{ members|length }} members.</p>
  {% else %}
  <div class="empty">
    <p>📭 No members registered yet.</p>
    <p style="margin-top:0.5rem; font-size:0.85rem;">Members will appear here after registration.</p>
  </div>
  {% endif %}
</div>

<script>
function filterTable() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  const rows  = document.querySelectorAll('#membersTable tbody tr');
  let visible = 0;
  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    if (text.includes(query)) { row.style.display = ''; visible++; }
    else row.style.display = 'none';
  });
  const vc = document.getElementById('visibleCount');
  if (vc) vc.textContent = visible;
}
</script>
</body>
</html>
"""


@app.route('/admin')
@login_required
def admin_panel():
    members = read_members()
    return render_template_string(ADMIN_PANEL_HTML, members=members)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect('/admin')

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = False
            return redirect('/admin')
        else:
            error = '❌ Invalid credentials. Access denied.'

    return render_template_string(ADMIN_LOGIN_HTML, error=error)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')


@app.route('/admin/download')
@login_required
def admin_download():
    """Download the full members CSV."""
    ensure_csv()
    if not os.path.exists(CSV_FILE):
        abort(404)
    return send_file(
        CSV_FILE,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'cssc_members_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    )


@app.route('/admin/delete/<member_id>', methods=['POST'])
@login_required
def admin_delete(member_id):
    """Delete a member by ID."""
    members = read_members()
    original_len = len(members)
    members = [m for m in members if m.get('ID') != member_id]

    if len(members) < original_len:
        write_members(members)
        print(f"[ADMIN] Deleted member: {member_id}")

    return redirect('/admin')


@app.route('/admin/api/members')
@login_required
def admin_api_members():
    """JSON API endpoint for members (optional: for AJAX admin UIs)."""
    members = read_members()
    return jsonify({'success': True, 'count': len(members), 'members': members})


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/health')
def health():
    members = read_members()
    return jsonify({
        'status': 'healthy',
        'server': 'CSSC Backend v1.0',
        'members_count': len(members),
        'timestamp': datetime.now().isoformat()
    })


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Route not found'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    ensure_csv()
    print("=" * 50)
    print("  CSSC Backend Server Starting...")
    print("=" * 50)
    print(f"  API:    http://127.0.0.1:5000")
    print(f"  Admin:  http://127.0.0.1:5000/admin")
    print(f"  Health: http://127.0.0.1:5000/health")
    print(f"  Data:   {CSV_FILE}")
    print("=" * 50)
    print("  [!] Change ADMIN_PASS in production!")
    print("=" * 50)

    # Debug=False in production
    app.run(debug=True, host='127.0.0.1', port=5000)
