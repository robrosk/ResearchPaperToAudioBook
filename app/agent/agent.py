import os
from openai import OpenAI

class Agent:
    def __init__(self):
        # Initialize the client using the API key from environment variables
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    def chat(self, prompt, system_prompt="You are a helpful assistant.", model="gpt-4o-mini"):
        """
        Sends a chat completion request to OpenAI.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content

    def speak(self, text, output_path, model="tts-1", voice="shimmer"):
        """
        Converts text to speech and saves it to the specified output path.
        """
        response = self.client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Write the binary content to the file
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        return output_path

