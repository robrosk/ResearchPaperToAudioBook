from openai import OpenAI
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, make_response, jsonify, session
from werkzeug.utils import secure_filename
import fitz
import os
from auth import validate_user, generate_token
from config import secret_key
from celeryconfig import celery

'''
Goals:

Make filenames delete out of the uploads folder after they are done -> implemented correctly
Also needs to delete audio files after they are done -> implemented correctly 
Make the audio file name the same as the pdf file name -> implemented correctly
Upload status in JS -> Not implemented correctly yet
Make it so only I can access this application and then upload to a server or GitHub -> Not implemented correctly yet

'''

app = Flask(__name__)
app.secret_key = secret_key
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Define your upload folder path
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)  # Open the PDF with fitz (PyMuPDF)
    text = ""
    for page in document:
        text += page.get_text()  # Extract text from each page
    document.close()
    return text

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Start the Celery task
        task = convert_pdf_to_audio.delay(file_path)
        
        # You can return the task id to the user or just a success message
        return jsonify({"message": "Conversion started", "task_id": task.id}), 202
    else:
        return 'No selected file', 400
    
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if validate_user(email, password):
        token = generate_token()
        return jsonify({'token': token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401  
    
@app.route('/status/<task_id>')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
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
            response['result'] = task.info.get('result', 0)  
    else:  # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Log the user out by removing them from the session
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@celery.task(bind=True)
def convert_pdf_to_audio(self, file_path):
    extracted_text = extract_text_from_pdf(file_path)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": """
        You are a helpful assistant tasked with providing a concise, multi-paragraph summary of the provided research paper. 
        Focus on preserving critical information and properly attributing key findings to the authors. 
        Make the summary engaging and accessible, explaining complex concepts in layman's terms. 
        Ensure the summary is suitable for an audiobook audience and retains all important content without requiring access to the full paper.
        Make an effort to explain keywords and avoid jargon."""},
        {"role": "user", "content": extracted_text}]
    )
    paper = response.choices[0].message.content
    file_name = file_path + ".mp3"
    audio_path = Path(__file__).parent / file_name
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=paper
    )
    with open(audio_path, 'wb') as file:
        file.write(response.content)
    return str(audio_path)




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)