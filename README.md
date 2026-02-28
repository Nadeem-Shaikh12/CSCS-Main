# 🛡️ CSSC – Cyber Security Students Club Website

A professional, fully functional cybersecurity-themed website for the **Cyber Security Students Club (CSSC)** — built with HTML/CSS/JavaScript (frontend) and Python Flask (backend).

---

## 📁 Project Structure

```
cssc-website/
│
├── frontend/
│   ├── index.html          ← Home page (hero, stats, events, vision)
│   ├── about.html          ← About CSSC, Vision, Mission, Objectives, Faculty Mentor
│   ├── ethics.html         ← Cyber Ethics, Laws, Responsible Disclosure
│   ├── policies.html       ← Terms, Code of Ethics, Social Media, Legal (accordion)
│   ├── team.html           ← Team cards (President, Tech Head, Core Members)
│   ├── register.html       ← Member registration form
│   ├── styles.css          ← Full dark cybersecurity theme CSS
│   ├── script.js           ← Animations, form validation, background canvas
│   └── assets/
│       └── logo.png        ← CSSC logo (replace with official logo)
│
├── backend/
│   ├── app.py              ← Flask backend (API + Admin Panel)
│   ├── members.csv         ← Member data storage (auto-created)
│   └── requirements.txt    ← Python dependencies
│
└── README.md               ← This file
```

---

## 🚀 Quick Start — Running Locally

### Step 1: Open the Frontend

1. Navigate to the `frontend/` folder
2. Open `index.html` directly in your browser  
   **OR** use VS Code's **Live Server** extension for better experience:
   - Install: [Live Server Extension](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)
   - Right-click `index.html` → **Open with Live Server**

### Step 2: Set Up and Run the Backend

```bash
# Navigate to the backend folder
cd cssc-website/backend

# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py
```

The backend will start at: **http://127.0.0.1:5000**

### Step 3: Access the Admin Panel

Open your browser and go to:
```
http://127.0.0.1:5000/admin
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `cssc@2026`

> ⚠️ **Change the password in `app.py` before deploying!**

---

## 🔧 How to Customize

### Change the Club Logo
1. Replace `frontend/assets/logo.png` with your official CSSC logo
2. Recommended size: **200×200 pixels**, circular/square format
3. The logo appears automatically in: Navbar, Hero section, Footer

### Add/Update Team Members
Edit `frontend/team.html`:
```html
<div class="team-card reveal">
  <div class="team-avatar">XX</div>          <!-- Initials -->
  <h3 class="team-name">Your Name Here</h3>
  <p class="team-role">Your Role</p>
  <p class="team-dept">Department · Year</p>
  <button class="team-contact-toggle" onclick="toggleEmail(this)">Show Contact</button>
  <div class="team-email">📧 email@university.edu</div>
</div>
```

### Add Events
Edit the events section in `frontend/index.html`:
```html
<div class="event-card reveal">
  <span class="event-badge badge-upcoming">UPCOMING</span>
  <div class="event-date">📅 DATE HERE</div>
  <h3 class="event-title">Event Title</h3>
  <p class="event-desc">Event description...</p>
</div>
```

### Change Club Name/Info
- Open each `.html` file
- Search for `CSSC` and replace with your club acronym
- Update the tagline in `index.html` hero section (also in `script.js` → `taglines` array)

### Change Admin Password
Open `backend/app.py` and find:
```python
ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'cssc@2026')
```
Change `'cssc@2026'` to your secure password.  
**Better practice:** Set as environment variable:
```bash
# Windows PowerShell
$env:ADMIN_PASS="YourSecurePassword123!"
python app.py
```

### Update Backend URL
When deploying, update the `BACKEND_URL` in `frontend/script.js`:
```javascript
const BACKEND_URL = 'https://your-deployed-backend.com'; // Change this!
```

---

## 📥 How to Download Member Data

**Via Admin Panel:**
1. Go to `http://your-server/admin`
2. Log in with admin credentials
3. Click **"📥 Download CSV"** button

**Via File System:**
The data is stored in `backend/members.csv` — you can open it in Excel directly.

---

## 🔐 Security Notes

- All form inputs are sanitized server-side (strips HTML, limits length)
- Duplicate email registration is prevented
- Admin panel uses session-based authentication
- Input validation runs on both frontend and backend
- **Never deploy with debug=True** (already set to True for development only)
- Use HTTPS in production (via Render/Railway/Heroku free SSL)

---

## 🌐 Deployment Instructions

### Option A: Render (Recommended for Students — Free Tier)

1. Push your project to GitHub
2. Go to [render.com](https://render.com) → Sign up free
3. Click **"New Web Service"** → Connect GitHub repo
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add environment variables in Render dashboard:
   - `SECRET_KEY` = any random string
   - `ADMIN_USER` = your admin username
   - `ADMIN_PASS` = your secure password
6. Deploy! Render gives you a URL like `https://cssc-backend.onrender.com`
7. Update `BACKEND_URL` in `frontend/script.js` with this URL

**For the frontend:** Deploy to [GitHub Pages](https://pages.github.com/) (free static hosting)

```bash
# Install gunicorn for production
pip install gunicorn
pip freeze > requirements.txt
```

---

### Option B: Railway (Also Free)

1. Go to [railway.app](https://railway.app)
2. Deploy from GitHub → select `backend/` as root
3. Set environment variables
4. Railway auto-detects Flask and deploys

---

### Option C: Local Network (LAN)

Run Flask accessible on your local network:
```python
# In app.py, change the last line to:
app.run(debug=False, host='0.0.0.0', port=5000)
```
Access from other devices: `http://YOUR_IP:5000`

---

## 📊 Admin Panel Features

| Feature | Description |
|---------|-------------|
| 👁️ View Members | See all registered members in a table |
| 🔍 Search | Filter by name, email, department, ID |
| 📥 Download CSV | Export all data to CSV (opens in Excel) |
| 🗑️ Delete Record | Remove a member (with confirmation prompt) |
| 📈 Stats | Total members, oath acceptance count, departments |

---

## 🎨 Design System

| Element | Color |
|---------|-------|
| Background | `#020c14` (deep navy) |
| Cards | `#071e30` (dark blue) |
| Neon Green (primary) | `#00ff88` |
| Neon Blue (accent) | `#00d4ff` |
| Alert Red | `#ff2d55` |
| Fonts | Orbitron (headings), Rajdhani (body), Share Tech Mono (code) |

---

## 🛠️ Tech Stack

### Frontend
- HTML5 (semantic)
- CSS3 (custom properties, grid, animations)
- Vanilla JavaScript (ES6+)
- Google Fonts (Orbitron, Rajdhani, Share Tech Mono)

### Backend
- Python 3.8+
- Flask 3.0+
- Flask-CORS (cross-origin requests)
- CSV (lightweight data storage)

---

## 🤝 Contributing / Maintaining

This website is designed to be beginner-friendly. Here's how students can contribute:

1. **Fork** the repository on GitHub
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and test locally
4. **Submit a PR** for review by the Technical Head

For major changes (like adding a new page), coordinate with the Technical Head first.

---

## 📞 Support

For technical issues, contact:
- **Technical Head:** rahul.nair@university.edu
- **Club Email:** cssc@university.edu

---

## ⚖️ Legal

This project is maintained by CSSC members. All cybersecurity activities conducted using this club's resources must comply with:
- Information Technology Act, 2000 (India)
- University IT Usage Policy
- CSSC Code of Ethics

---

*Built with 💚 by the CSSC Technical Team · 2026*
