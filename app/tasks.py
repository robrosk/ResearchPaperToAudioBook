from celery import shared_task
import fitz
import os
from pathlib import Path
from app.agent import Agent

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page in document:
        text += page.get_text()
    document.close()
    return text

@shared_task(bind=True)
def convert_pdf_to_audio(self, file_path):
    # Initialize our new Agent
    agent = Agent()
    
    extracted_text = extract_text_from_pdf(file_path)
    
    # Use the agent to chat (summarize)
    system_prompt = """
    You are a helpful assistant tasked with providing a concise, multi-paragraph summary of the provided research paper. 
    Focus on preserving critical information and properly attributing key findings to the authors. 
    Make the summary engaging and accessible, explaining complex concepts in layman's terms. 
    Ensure the summary is suitable for an audiobook audience and retains all important content without requiring access to the full paper.
    Make an effort to explain keywords and avoid jargon."""
    
    paper_summary = agent.chat(extracted_text, system_prompt=system_prompt)
    
    file_name = Path(file_path).stem + ".mp3"

    audio_path = Path(file_path).parent / file_name
    
    agent.speak(paper_summary, str(audio_path))
        
    # Return just the filename so the frontend can request it from the uploads folder
    return str(file_name)
