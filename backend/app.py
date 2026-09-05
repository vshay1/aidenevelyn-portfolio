import sys
import traceback
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    try:
        return jsonify({
            "status": "success",
            "message": "App is running!",
            "python_version": sys.version,
            "database_url": os.environ.get('DATABASE_URL', 'Not set')
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/test')
def test():
    return jsonify({"status": "ok"})

# Test database connection
@app.route('/api/test-db')
def test_db():
    try:
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import text
        import psycopg2
        
        # Try connecting directly
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return jsonify({"error": "DATABASE_URL not set"}), 500
        
        # Test connection
        conn = psycopg2.connect(db_url)
        conn.close()
        
        return jsonify({"status": "success", "message": "Database connected!"})
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)