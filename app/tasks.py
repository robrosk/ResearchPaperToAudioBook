from celery import shared_task
from openai import OpenAI
import fitz
import os
from pathlib import Path

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page in document:
        text += page.get_text()
    document.close()
    return text

@shared_task(bind=True)
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
    
    # Ensure we have a string for the path
    file_name = str(file_path) + ".mp3"
    # Use absolute path to avoid relative path issues in worker
    audio_path = Path(file_name).resolve()
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=paper
    )
    
    with open(audio_path, 'wb') as file:
        file.write(response.content)
        
    return str(audio_path)

