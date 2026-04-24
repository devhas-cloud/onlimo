from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from functools import wraps
import sqlite3
import os
import traceback
from datetime import datetime
import requests
import json
from datetime import datetime, timedelta

from config import loadConfig, CONFIG_DB_PATH

# Get the directory paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')

app = Flask(__name__, static_folder=frontend_dir, static_url_path='', template_folder=frontend_dir)
app.secret_key = 'onlimo_secret_key_2026'
CORS(app)

# ==================== AUTHENTICATION ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Default credentials - bisa diubah sesuai kebutuhan
    if username == 'admin' and password == 'has123456':
        session['user'] = username
        session['login_time'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Login berhasil'}), 200
    
    return jsonify({'success': False, 'message': 'Username atau password salah'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logout berhasil'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': 'user' in session}), 200

# ==================== CONFIG ENDPOINTS ====================


@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    config = loadConfig()
    
    # Format response - include all config fields
    response = {
        
        # general
        'parameter': config.get('parameter', ''),

        # dlh api
        'dlh_status': config.get('dlh_status', ''),
        'dlh_api_url': config.get('dlh_api_url', ''),
        'dlh_api_key': config.get('dlh_api_key', ''),
        'dlh_api_secret': config.get('dlh_api_secret', ''),
        'dlh_uid': config.get('dlh_uid', ''),
        
        # has api
        'has_status': config.get('has_status', ''),
        'has_api_url': config.get('has_api_url', ''),
        'has_logs_api_url': config.get('has_logs_api_url', ''),
        'has_token_api': config.get('has_token_api', ''),
        'has_fields': config.get('has_fields', ''),
        
        
        # device info
        'device_id': config.get('device_id', ''),
        'location_name': config.get('location_name', ''),
        'software_version': config.get('software_version', ''),
        'geo_latitude': config.get('geo_latitude', ''),
        'geo_longitude': config.get('geo_longitude', ''),
    }
    
    print(f"[{datetime.now()}] Config loaded from DB: device_id={response.get('device_id')}, location_name={response.get('location_name')}")
    
    return jsonify(response), 200

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    data = request.get_json()
    
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        
        # List of valid config fields to prevent SQL injection
        valid_fields = {
            'parameter',
            'dlh_status', 'dlh_api_url', 'dlh_api_key', 'dlh_api_secret', 'dlh_uid',
            'has_status', 'has_api_url', 'has_logs_api_url', 'has_token_api', 'has_fields',
            'device_id', 'location_name', 'software_version', 'geo_latitude', 'geo_longitude'
        }
        
        # Update each field safely using parameterized queries
        for key, value in data.items():
            # Only update valid fields
            if key not in valid_fields:
                continue
                
            if key == 'parameters' and isinstance(value, list):
                value = ','.join(value)
            
            # Use parameterized query with double quotes for SQLite column names
            cursor.execute(f'UPDATE config SET "{key}"=? WHERE id=1', (value,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[{datetime.now()}] Config updated successfully: {list(data.keys())}")
        
        return jsonify({'success': True, 'message': 'Konfigurasi berhasil diperbarui'}), 200
    
    except Exception as e:
        import traceback
        print(f"[{datetime.now()}] Error updating config: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== MONITORING ENDPOINTS ====================


# Data Stats
@app.route('/api/data/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        
        
        # Get total data count
        cursor.execute('SELECT COUNT(*) FROM data')
        total_data = cursor.fetchone()[0]
        
        # Get pending data count (not sent to DLH)
        cursor.execute('SELECT COUNT(*) FROM data WHERE dlh=0')
        pending_data = cursor.fetchone()[0]
        
        # Get sent to DLH count
        cursor.execute('SELECT COUNT(*) FROM data WHERE dlh=1')
        sent_dlh = cursor.fetchone()[0]
        
        # Get sent to HAS count
        cursor.execute('SELECT COUNT(*) FROM data WHERE has=1')
        sent_has = cursor.fetchone()[0]

        cursor.execute('SELECT MAX(dlh_sent_at) FROM data WHERE dlh=1')
        dlh_sent_at = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_data': total_data,
                'pending_data': pending_data,
                'sent_dlh': sent_dlh,
                'sent_has': sent_has,
                'dlh_sent_at': dlh_sent_at  # Placeholder, bisa diisi dengan timestamp terakhir data dikirim ke DLH            
            }
        }), 200
    
    except Exception as e:
        import traceback
        print(f"[{datetime.now()}] Error fetching stats: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


# 
@app.route('/api/data/all', methods=['GET'])
@login_required
def get_all_data():
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        conn.row_factory = sqlite3.Row  # ✅ supaya hasil jadi dict-like
        cursor = conn.cursor()

        query = """
        SELECT * FROM data
        ORDER BY date DESC
        LIMIT 1000
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert ke list of dict
        data = []
        for row in rows:
            row_dict = dict(row)

            # Convert datetime jika ada
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()

            data.append(row_dict)

        # Get config
        config = loadConfig()
        params = config.get('parameter', 'datetime,pH,cod,tss,nh3n,flow')

        return jsonify({
            'success': True,
            'count': len(data),
            'data': data,
            'params': params
        }), 200

    except Exception as e:
        import traceback
        print(f"Error in get_all_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        # ✅ pastikan selalu ditutup
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ==================== SEND ENDPOINTS ====================

@app.route('/api/send/manual', methods=['POST'])
@login_required
def manual_send():
    """Manual send to DLH and HAS API"""
    try:
        from send import send_dlh, send_has
        
        send_date = datetime.now()
        
        results = {
            'dlh_sent': False,
            'has_sent': False,
            'dlh_message': '',
            'has_message': '',
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to DLH
        try:
            dlh_result = send_dlh(send_date)
            results['dlh_sent'] = dlh_result
            results['dlh_message'] = 'Data DLH berhasil dikirim' if dlh_result else 'Tidak ada data untuk dikirim ke DLH'
        except Exception as e:
            results['dlh_message'] = f'Error DLH: {str(e)}'
            print(f"[{datetime.now()}] Error sending to DLH: {e}")
            traceback.print_exc()
        
        # Send to HAS
        try:
            has_result = send_has(send_date)
            results['has_sent'] = has_result
            results['has_message'] = 'Data HAS berhasil dikirim' if has_result else 'Tidak ada data untuk dikirim ke HAS'
        except Exception as e:
            results['has_message'] = f'Error HAS: {str(e)}'
            print(f"[{datetime.now()}] Error sending to HAS: {e}")
            traceback.print_exc()
        
        success = results['dlh_sent'] or results['has_sent']
        
        print(f"[{datetime.now()}] Manual send triggered: DLH={results['dlh_sent']}, HAS={results['has_sent']}")
        
        return jsonify({
            'success': success,
            'results': results
        }), 200
        
    except Exception as e:
        print(f"[{datetime.now()}] Error in manual_send: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs/<log_type>', methods=['GET'])
@login_required
def get_logs(log_type):
    """Mendapatkan log files dari folder logs"""
    try:
        # Validasi log_type
        valid_logs = ['web','main', 'send']
        if log_type not in valid_logs:
            return jsonify({'success': False, 'error': 'Invalid log type'}), 400
        
        logs_dir = '/app/logs'
        log_file = os.path.join(logs_dir, f'{log_type}.log')
        
        # Check if file exists
        if not os.path.exists(log_file):
            return jsonify({
                'success': True,
                'count': 0,
                'data': [],
                'message': f'Log file {log_type}.log not found'
            }), 200
        
        # Read log file - last N lines
        lines = []
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # Get last 1000 lines
                lines = all_lines[-1000:]
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error reading log file: {str(e)}'}), 500
        
        # Format log lines with timestamp and sequence number
        formatted_logs = []
        for idx, line in enumerate(lines):
            formatted_logs.append({
                'no': len(lines) - idx,  # Reverse numbering (highest first)
                'message': line.strip(),
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(formatted_logs),
            'data': formatted_logs,
            'log_type': log_type
        }), 200
    
    except Exception as e:
        print(f"[{datetime.now()}] Error in get_logs: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500



# ==================== STATIC ROUTES ====================

@app.route('/', methods=['GET'])
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    return send_from_directory(frontend_dir, 'login.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/config', methods=['GET'])
def config_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/logs.html', methods=['GET'])
def logs_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return send_from_directory(frontend_dir, 'logs.html')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return send_from_directory(frontend_dir, '404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    # Load config dan jalankan app
    config = loadConfig()
    port = int(config.get('port_number_app', 5010))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
