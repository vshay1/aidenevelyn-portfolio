from flask import Flask, session, jsonify, request, send_from_directory
from supabase import create_client, Client
from datetime import timedelta
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='templates')

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Supabase Client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Get secret passkey from Supabase - NO FALLBACK!
def get_secret_passkey():
    try:
        response = supabase.table('secret_keys')\
            .select('key_value')\
            .eq('key_name', 'admin_passkey')\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['key_value']
        return None  # Return None if not found
    except:
        return None  # Return None on error

SECRET_PASSKEY = get_secret_passkey()

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

# API Routes with Supabase
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        response = supabase.table('projects').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/writings', methods=['GET'])
def get_writings():
    try:
        response = supabase.table('writings').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/art', methods=['GET'])
def get_art():
    try:
        response = supabase.table('art').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    try:
        data = request.get_json()
        page_url = data.get('page_url')
        visitor_ip = request.remote_addr
        
        supabase.table('visits').insert({
            'page_url': page_url,
            'visitor_ip': visitor_ip,
            'visited_at': datetime.now().isoformat()
        }).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Secret Passkey Verification - ONLY from Supabase
@app.route('/api/verify-keystroke', methods=['POST'])
def verify_keystroke():
    data = request.get_json()
    position = data.get('position', 0)
    key = data.get('key', '').lower()
    
    # Get passkey from Supabase
    try:
        response = supabase.table('secret_keys')\
            .select('key_value')\
            .eq('key_name', 'admin_passkey')\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Passkey not configured'}), 404
        
        secret_passkey = response.data[0]['key_value']
    except:
        return jsonify({'error': 'Failed to fetch passkey'}), 500
    
    if position < len(secret_passkey) and key == secret_passkey[position]:
        next_position = position + 1
        is_complete = next_position == len(secret_passkey)
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
    
    # Get passkey from Supabase
    try:
        response = supabase.table('secret_keys')\
            .select('key_value')\
            .eq('key_name', 'admin_passkey')\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Passkey not configured'}), 404
        
        secret_passkey = response.data[0]['key_value']
    except:
        return jsonify({'error': 'Failed to fetch passkey'}), 500
    
    if secret == secret_passkey:
        return jsonify({
            'success': True,
            'redirectTo': '/admin_login.html'
        })
    else:
        return jsonify({
            'success': False
        })

# Admin Login
@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    try:
        response = supabase.table('admins').select('*').eq('username', username).execute()
        if response.data and response.data[0]['password'] == password:
            session['user'] = username
            return jsonify({'success': True, 'redirectTo': '/admin_dashboard.html'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    except:
        if username == 'admin' and password == 'password':
            session['user'] = username
            return jsonify({'success': True, 'redirectTo': '/admin_dashboard.html'})
        return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/admin/logout', methods=['GET'])
def admin_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/settings/passkey', methods=['GET'])
def get_passkey():
    try:
        response = supabase.table('secret_keys')\
            .select('key_value')\
            .eq('key_name', 'admin_passkey')\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Passkey not configured'}), 404
        
        return jsonify({'passkey': response.data[0]['key_value']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/backend/templates/<page>.html')
def serve_backend_templates(page):
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

if __name__ == '__main__':
    app.run(debug=True, port=3000)