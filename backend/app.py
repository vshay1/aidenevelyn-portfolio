cd /Users/aidenevelyn/Documents/Project/probable-octo-winner/backend
cat > app.py << 'EOF'
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# === CONFIGURATION ===
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

if not app.config['SQLALCHEMY_DATABASE_URI']:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# === INITIALIZE EXTENSIONS ===
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'dynamic_admin_login'

# === DATABASE MODELS ===

class Admin(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SecretKey(db.Model):
    __tablename__ = 'secret_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_string = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)
    
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

class AdminSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime)
    session_duration = db.Column(db.Integer)
    
    admin = db.relationship('Admin', backref='sessions')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    github_url = db.Column(db.String(200))
    live_url = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='in_progress')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = db.Column(db.Integer, default=0)

class PageVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_url = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    referrer = db.Column(db.String(200))
    visit_time = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.Text)

# === CREATE TABLES ===
with app.app_context():
    try:
        db.create_all()
        print("Tables created/verified!")
    except Exception as e:
        print("Database error (app will continue): {}".format(e))

# === FLASK-LOGIN ===
@login_manager.user_loader
def load_user(user_id):
    try:
        return Admin.query.get(int(user_id))
    except:
        return None

# === DECORATORS ===
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(404)
        return f(*args, **kwargs)
    return decorated_function

# === GENERATE ONE-TIME TOKEN ===
def generate_admin_slug():
    slug = secrets.token_urlsafe(32)
    session['admin_slug'] = slug
    session['admin_slug_created'] = time.time()
    session['admin_slug_used'] = False
    return slug

def validate_admin_slug(slug):
    stored_slug = session.get('admin_slug')
    created_at = session.get('admin_slug_created', 0)
    used = session.get('admin_slug_used', False)
    
    if not stored_slug or slug != stored_slug:
        return False
    if used:
        return False
    if time.time() - created_at > 60:
        return False
    return True

def mark_slug_used():
    session['admin_slug_used'] = True

def destroy_admin_slug():
    session.pop('admin_slug', None)
    session.pop('admin_slug_created', None)
    session.pop('admin_slug_used', None)

# === ROUTES ===

@app.route('/')
def home():
    return render_template('main_page.html')

@app.route('/<page_name>.html')
def serve_static_page(page_name):
    allowed_pages = ['main_page', 'projects', 'art', 'gallery', 'writing', 'login']
    if page_name in allowed_pages:
        return render_template('{}.html'.format(page_name))
    abort(404)

# === SECRET KEY VERIFICATION ===

def get_active_secret_keys():
    try:
        keys = SecretKey.query.filter_by(is_active=True).all()
        valid_keys = [key.key_string for key in keys if key.is_valid()]
        return valid_keys if valid_keys else ["supercalifragilisticexpialidocious12345"]
    except:
        return ["supercalifragilisticexpialidocious12345"]

@app.route('/api/verify-keystroke', methods=['POST'])
def verify_keystroke():
    data = request.get_json() or {}
    current_position = data.get('position', 0)
    pressed_key = data.get('key', '').lower()
    REAL_SECRET_KEY = "supercalifragilisticexpialidocious12345"
    
    if current_position < len(REAL_SECRET_KEY):
        expected_char = REAL_SECRET_KEY[current_position].lower()
        if pressed_key == expected_char:
            return jsonify({
                "success": True,
                "match": True,
                "next_position": current_position + 1,
                "is_complete": (current_position + 1) == len(REAL_SECRET_KEY)
            })
    return jsonify({"success": True, "match": False, "reset": True})

@app.route('/api/complete-secret', methods=['POST'])
def complete_secret():
    data = request.get_json() or {}
    secret = data.get('secret', '')
    REAL_SECRET_KEY = "supercalifragilisticexpialidocious12345"
    
    if secret.lower() == REAL_SECRET_KEY.lower():
        admin_slug = generate_admin_slug()
        return jsonify({
            "success": True,
            "redirectTo": "/admin/{}".format(admin_slug)
        })
    return jsonify({"success": False}), 403

# === ADMIN LOGIN ===

@app.route('/admin/<slug>')
def dynamic_admin_login(slug):
    if not validate_admin_slug(slug):
        destroy_admin_slug()
        abort(404)
    return render_template('admin_login.html', slug=slug)

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    admin = Admin.query.filter_by(username=username, is_active=True).first()
    
    if admin and admin.check_password(password):
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        admin_session = AdminSession(
            admin_id=admin.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200]
        )
        db.session.add(admin_session)
        db.session.commit()
        
        mark_slug_used()
        login_user(admin, remember=True)
        session['admin_username'] = admin.username
        
        return jsonify({
            "success": True,
            "redirectTo": "/dashboard"
        })
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

# === ADMIN DASHBOARD ===

@app.route('/dashboard')
@admin_required
def admin_dashboard():
    if not session.get('admin_slug_used'):
        return redirect('/')
    
    total_projects = Project.query.count()
    total_visits = PageVisit.query.count()
    total_admins = Admin.query.count()
    
    recent_sessions = AdminSession.query.order_by(
        AdminSession.login_time.desc()
    ).limit(10).all()
    
    recent_visits = PageVisit.query.order_by(
        PageVisit.visit_time.desc()
    ).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         username=current_user.username,
                         total_projects=total_projects,
                         total_visits=total_visits,
                         total_admins=total_admins,
                         recent_sessions=recent_sessions,
                         recent_visits=recent_visits)

@app.route('/admin/logout')
@admin_required
def admin_logout():
    admin_session = AdminSession.query.filter_by(
        admin_id=current_user.id
    ).order_by(AdminSession.login_time.desc()).first()
    
    if admin_session:
        admin_session.logout_time = datetime.utcnow()
        if admin_session.login_time:
            duration = (admin_session.logout_time - admin_session.login_time).total_seconds()
            admin_session.session_duration = int(duration)
        db.session.commit()
    
    destroy_admin_slug()
    logout_user()
    session.clear()
    return redirect('/')

@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/<path:path>')
def admin_catch_all(path=None):
    abort(404)

# === API ENDPOINTS ===

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.order_by(Project.order).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'github_url': p.github_url,
        'live_url': p.live_url,
        'image_url': p.image_url,
        'category': p.category,
        'status': p.status
    } for p in projects])

if __name__ == '__main__':
    app.run(port=5000, debug=True)
EOF