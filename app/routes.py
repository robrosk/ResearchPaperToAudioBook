from flask import Blueprint, request, render_template, jsonify, session, current_app
from werkzeug.utils import secure_filename
import os
from .auth import validate_user, generate_token
from .tasks import convert_pdf_to_audio
from celery.result import AsyncResult

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('login.html')

@main_bp.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Start the Celery task
        task = convert_pdf_to_audio.delay(file_path)
        
        return jsonify({"message": "Conversion started", "task_id": task.id}), 202
    
@main_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if validate_user(email, password):
        token = generate_token()
        session['logged_in'] = True # Maintain simple session state if needed
        return jsonify({'token': token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401  
    
@main_bp.route('/status/<task_id>')
def task_status(task_id):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': 'Processing...'
        }
        if task.info:
            # If the task returns a result (file path), it might be in task.result or task.info depending on state
            # For SUCCESS state, result is the return value
            response['result'] = str(task.result) if task.state == 'SUCCESS' else task.info.get('result', 0)
    else:
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    return jsonify(response)

@main_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return render_template('login.html')

@main_bp.route('/index')
def index():
    return render_template('index.html')

