# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort, send_from_directory
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


# === TELL FLASK WHERE TO FIND TEMPLATES AND STATIC FILES ===
app = Flask(__name__,
    template_folder='templates',
    static_folder='../frontend',
    static_url_path='/frontend'
)

@app.route('/favicon.ico')
def favicon():
    return '', 204

# === ADD ROUTES FOR RESOURCES ===
@app.route('/resources/<path:filename>')
def serve_resources(filename):
    """Serve resources from the frontend/resources folder"""
    return send_from_directory(os.path.join('..', 'frontend', 'resources'), filename)

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    """Serve frontend files"""
    return send_from_directory('..', 'frontend', filename)

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
    
    def __repr__(self):
        return '<Admin {}>'.format(self.username)

class SecretKey(db.Model):
    __tablename__ = 'secret_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_string = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)
    
    def is_valid(self):
        """Check if the key is active and not expired"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def __repr__(self):
        return '<SecretKey {}>'.format(self.id)

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

class Writing(db.Model):
    __tablename__ = 'writings'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='published')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Art(db.Model):
    __tablename__ = 'arts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Gallery(db.Model):
    __tablename__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    image_url = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    db.create_all()
    print("Tables created/verified!")
    print("Connected to database: " + str(app.config['SQLALCHEMY_DATABASE_URI']))

# === FLASK-LOGIN ===
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.before_request
def check_session_timeout():
    if current_user.is_authenticated:
        last_activity = session.get('last_activity')
        if last_activity and time.time() - last_activity > 3600:
            logout_user()
            session.clear()
            return redirect('/')
        session['last_activity'] = time.time()

# Simple rate limiting for login attempts
login_attempts = {}

@app.before_request
def rate_limit():
    if request.endpoint == 'admin_login':
        ip = request.remote_addr
        now = time.time()
        if ip in login_attempts:
            attempts, first_attempt = login_attempts[ip]
            if attempts >= 5 and now - first_attempt < 300:
                return jsonify({"error": "Too many attempts"}), 429
            elif now - first_attempt > 300:
                login_attempts[ip] = (1, now)
            else:
                login_attempts[ip] = (attempts + 1, first_attempt)
        else:
            login_attempts[ip] = (1, now)

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
    """Generate a unique, one-time admin slug"""
    slug = secrets.token_urlsafe(32)
    session['admin_slug'] = slug
    session['admin_slug_created'] = time.time()
    session['admin_slug_used'] = False
    return slug

def validate_admin_slug(slug):
    """Validate if the slug is valid and not expired"""
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
    """Mark the current slug as used (prevents reuse)"""
    session['admin_slug_used'] = True

def destroy_admin_slug():
    """Destroy the current admin slug"""
    session.pop('admin_slug', None)
    session.pop('admin_slug_created', None)
    session.pop('admin_slug_used', None)

# === ROUTES ===

@app.route('/')
def home():
    track_visit(request, '/')
    return render_template('main_page.html')

@app.route('/<page_name>.html')
def serve_static_page(page_name):
    allowed_pages = ['main_page', 'projects', 'art', 'gallery', 'writing', 'login']
    if page_name in allowed_pages:
        track_visit(request, '/{}'.format(page_name))
        
        if page_name == 'projects':
            projects = Project.query.order_by(Project.order).all()
            return render_template('projects.html', projects=projects)
        
        return render_template('{}.html'.format(page_name))
    abort(404)

def track_visit(request, page_url):
    try:
        visit = PageVisit(
            page_url=page_url,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200],
            referrer=request.headers.get('Referer', '')[:200],
            session_id=request.cookies.get('session', '')
        )
        db.session.add(visit)
        db.session.commit()
    except Exception as e:
        print("Error tracking visit: {}".format(e))
        db.session.rollback()

# === SECRET KEY VERIFICATION ===

def get_active_secret_keys():
    """Get all active secret keys from the database"""
    try:
        keys = SecretKey.query.filter_by(is_active=True).all()
        valid_keys = [key.key_string for key in keys if key.is_valid()]
        return valid_keys
    except Exception as e:
        print("Error fetching secret keys: {}".format(e))
        return ["supercalifragilisticexpialidocious12345"]

@app.route('/api/verify-keystroke', methods=['POST'])
def verify_keystroke():
    """Verify each keystroke against stored secret keys"""
    data = request.get_json() or {}
    current_position = data.get('position', 0)
    pressed_key = data.get('key', '').lower()
    
    active_keys = get_active_secret_keys()
    
    if not active_keys:
        active_keys = ["supercalifragilisticexpialidocious12345"]
    
    for secret_key in active_keys:
        if current_position < len(secret_key):
            expected_char = secret_key[current_position].lower()
            
            if pressed_key == expected_char:
                return jsonify({
                    "success": True,
                    "match": True,
                    "next_position": current_position + 1,
                    "is_complete": (current_position + 1) == len(secret_key)
                })
    
    return jsonify({
        "success": True,
        "match": False,
        "reset": True
    })

@app.route('/api/complete-secret', methods=['POST'])
def complete_secret():
    """Complete the secret key verification and generate admin slug"""
    data = request.get_json() or {}
    secret = data.get('secret', '')
    
    secret_key = SecretKey.query.filter_by(key_string=secret, is_active=True).first()
    
    if secret_key and secret_key.is_valid():
        admin_slug = generate_admin_slug()
        
        return jsonify({
            "success": True, 
            "redirectTo": "/admin/{}".format(admin_slug)
        })
    else:
        if secret == "supercalifragilisticexpialidocious12345":
            admin_slug = generate_admin_slug()
            
            return jsonify({
                "success": True, 
                "redirectTo": "/admin/{}".format(admin_slug)
            })
        
        return jsonify({"success": False}), 403

# === ADMIN LOGIN ===

@app.route('/admin/<slug>')
def dynamic_admin_login(slug):
    """Admin login page with one-time slug validation"""
    # Validate the slug
    if not validate_admin_slug(slug):
        # Destroy invalid slug
        destroy_admin_slug()
        abort(404)
    
    return render_template('admin_login.html', slug=slug)

@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    """Login with username and password"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    print("Login attempt: username='{}'".format(username))
    
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
        
        print("Login successful for: {}".format(username))
        
        return jsonify({
            "success": True,
            "redirectTo": "/dashboard"
        })
    else:
        print("Login failed for: {}".format(username))
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
    """Logout and destroy the admin slug"""
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

# === CATCH-ALL FOR ADMIN PATHS ===
@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/<path:path>')
def admin_catch_all(path=None):
    """Catch all admin paths and return 404"""
    abort(404)

# === PROJECT MANAGEMENT ===

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

@app.route('/api/projects', methods=['POST'])
@admin_required
def create_project():
    data = request.get_json() or {}
    
    project = Project(
        title=data.get('title'),
        description=data.get('description'),
        github_url=data.get('github_url'),
        live_url=data.get('live_url'),
        image_url=data.get('image_url'),
        category=data.get('category'),
        status=data.get('status', 'in_progress'),
        order=data.get('order', 0)
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({"success": True, "id": project.id})

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@admin_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    
    project.title = data.get('title', project.title)
    project.description = data.get('description', project.description)
    project.github_url = data.get('github_url', project.github_url)
    project.live_url = data.get('live_url', project.live_url)
    project.image_url = data.get('image_url', project.image_url)
    project.category = data.get('category', project.category)
    project.status = data.get('status', project.status)
    project.order = data.get('order', project.order)
    project.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({"success": True})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({"success": True})

# === ADMIN MANAGEMENT ===

@app.route('/api/admins', methods=['GET'])
@admin_required
def get_admins():
    admins = Admin.query.all()
    return jsonify([{
        'id': a.id,
        'username': a.username,
        'email': a.email,
        'is_active': a.is_active,
        'created_at': a.created_at.isoformat(),
        'last_login': a.last_login.isoformat() if a.last_login else None
    } for a in admins])

@app.route('/api/admins', methods=['POST'])
@admin_required
def create_admin():
    data = request.get_json() or {}
    
    admin = Admin(
        username=data.get('username'),
        email=data.get('email')
    )
    admin.set_password(data.get('password'))
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({"success": True, "id": admin.id})

# === RUN THE APP ===
if __name__ == '__main__':
    app.run(port=5000, debug=True)