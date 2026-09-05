from flask import Flask, session, jsonify, request, send_from_directory
import os
from datetime import timedelta

app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='templates')

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Serve static files from frontend
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/resources/<path:filename>')
def serve_resources(filename):
    return send_from_directory('../frontend/resources', filename)

# API Routes
@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'password':
        session['user'] = username
        return jsonify({'success': True, 'redirectTo': '/admin_dashboard.html'})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/verify-keystroke', methods=['POST'])
def verify_keystroke():
    data = request.get_json()
    position = data.get('position', 0)
    key = data.get('key', '').lower()
    
    SECRET_PASSKEY = "aiden"  # Change this to your secret
    
    if position < len(SECRET_PASSKEY) and key == SECRET_PASSKEY[position]:
        next_position = position + 1
        is_complete = next_position == len(SECRET_PASSKEY)
        return jsonify({
            'match': True,
            'next_position': next_position,
            'is_complete': is_complete,
            'reset': False
        })
    else:
        return jsonify({
            'match': False,
            'next_position': 0,
            'is_complete': False,
            'reset': True
        })

@app.route('/api/complete-secret', methods=['POST'])
def complete_secret():
    data = request.get_json()
    secret = data.get('secret', '').lower()
    
    SECRET_PASSKEY = "aiden"  # Change this to your secret
    
    if secret == SECRET_PASSKEY:
        return jsonify({
            'success': True,
            'redirectTo': '/admin_login.html'
        })
    else:
        return jsonify({
            'success': False
        })

@app.route('/api/admin/logout', methods=['GET'])
def admin_logout():
    session.clear()
    return jsonify({'success': True})

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/<page>.html')
def serve_html(page):
    try:
        return send_from_directory('templates', f'{page}.html')
    except:
        return send_from_directory('templates', 'index.html')

# Fallback route
@app.route('/<path:path>')
def catch_all(path):
    if path.endswith('.html'):
        try:
            return send_from_directory('templates', path)
        except:
            pass
    
    try:
        return send_from_directory('../frontend', path)
    except:
        return send_from_directory('templates', 'index.html')

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=3000)