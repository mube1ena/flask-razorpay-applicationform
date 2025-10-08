import os
import sqlite3
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import razorpay
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('applications.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT NOT NULL,
            dob TEXT NOT NULL,
            bio TEXT NOT NULL,
            resume_filename TEXT NOT NULL,
            payment_id TEXT,
            payment_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        data = request.json
        
        # Validate all fields
        required_fields = ['full_name', 'email', 'phone', 'gender', 'dob', 'bio']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create Razorpay order
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order_data = {
            'amount': 5000,  # 50 INR in paise
            'currency': 'INR',
            'payment_capture': 1
        }
        order = client.order.create(data=order_data)
        
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': RAZORPAY_KEY_ID
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    try:
        data = request.json
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        # Verify payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Validate and sanitize resume filename to prevent path traversal
        resume_filename = data.get('resume_filename', '')
        if not resume_filename:
            return jsonify({'error': 'Resume filename is required'}), 400
        
        # Re-sanitize the filename to prevent path traversal attacks
        sanitized_filename = secure_filename(resume_filename)
        
        # Ensure sanitized filename is not empty and has valid extension
        if not sanitized_filename or not allowed_file(sanitized_filename):
            return jsonify({'error': 'Invalid resume filename'}), 400
        
        # Verify the file exists in the uploads folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return jsonify({'error': 'Resume file not found'}), 400
        
        # Save application to database
        conn = sqlite3.connect('applications.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO applications (full_name, email, phone, gender, dob, bio, resume_filename, payment_id, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['full_name'],
            data['email'],
            data['phone'],
            data['gender'],
            data['dob'],
            data['bio'],
            sanitized_filename,
            data['razorpay_payment_id'],
            'success'
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Payment verified and application submitted'})
    except razorpay.errors.SignatureVerificationError:
        return jsonify({'error': 'Payment verification failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF, DOC, and DOCX files are allowed'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/admin')
def admin():
    conn = sqlite3.connect('applications.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM applications ORDER BY created_at DESC')
    applications = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template('admin.html', applications=applications)

@app.route('/download-resume/<filename>')
def download_resume(filename):
    # Sanitize filename to prevent path traversal
    safe_filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    # Ensure the resolved path is within the uploads folder
    uploads_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    resolved_path = os.path.abspath(filepath)
    
    if not resolved_path.startswith(uploads_folder):
        return jsonify({'error': 'Invalid file path'}), 403
    
    if os.path.exists(resolved_path):
        return send_file(resolved_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
