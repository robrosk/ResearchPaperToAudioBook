from dotenv import load_dotenv
load_dotenv() 

from app import create_app, celery

app = create_app()
app.app_context().push()
