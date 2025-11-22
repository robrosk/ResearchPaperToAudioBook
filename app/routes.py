from flask import Blueprint, request, render_template, jsonify, session, current_app, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import os
from .auth import validate_user, generate_token
from .tasks import convert_pdf_to_audio
from celery.result import AsyncResult
from app import celery

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('login.html')

@main_bp.route('/services')
def services():
    # In a real app, you'd check session['logged_in'] here
    return render_template('services.html')

@main_bp.route('/tool/audiobook')
def tool_audiobook():
    # In a real app, you'd check session['logged_in'] here
    return render_template('tool_audiobook.html')

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
        
        return jsonify({"message": "Conversion started", "task_id": task.id, "filename": filename}), 202
    
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
        if task.state == 'SUCCESS':
            # Return just the basename for the download link
            full_path = str(task.result)
            response['filename'] = os.path.basename(full_path)
    else:
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    return jsonify(response)

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    filename = os.path.basename(filename)
    
    mimetype = None
    if filename.lower().endswith('.mp3'):
        mimetype = 'audio/mpeg'
        
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True,
        mimetype=mimetype
    )

@main_bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    celery.control.revoke(task_id, terminate=True)
    return jsonify({'status': 'cancelled'})

@main_bp.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    # Filename could be the PDF (e.g., paper.pdf) or MP3 (e.g., paper.mp3)
    # We should try to clean up both if possible, or at least the requested one.
    # Security: ensure basename only
    filename = os.path.basename(filename)
    upload_dir = current_app.config['UPLOAD_FOLDER']
    
    # 1. Try to delete the exact file requested
    try:
        os.remove(os.path.join(upload_dir, filename))
    except OSError:
        pass # File might not exist
        
    # 2. Smart cleanup: 
    # If we deleted an MP3, check if original PDF exists and delete it?
    # Or if we deleted a PDF, delete the MP3?
    # Let's assume the frontend sends the MP3 filename for completed tasks, 
    # and PDF filename for pending ones.
    
    # If it's an MP3, try to find matching PDF (unreliable if names changed, but good effort)
    if filename.endswith('.mp3'):
        pdf_name = filename[:-4] + ".pdf" # simplistic guess based on task logic
        try:
            os.remove(os.path.join(upload_dir, pdf_name))
        except OSError:
            pass
            
    return jsonify({'status': 'deleted'})

@main_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return render_template('login.html')

@main_bp.route('/index')
def index():
    # Legacy route redirect
    return redirect(url_for('main.tool_audiobook'))
