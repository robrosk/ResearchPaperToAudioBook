from flask import Flask
from celery import Celery
import os
from .config import secret_key

import shutil

# Initialize Celery with modern configuration
# We set the backend and broker explicitly to avoid warnings about deprecated keys
celery = Celery(
    __name__, 
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    broker_connection_retry_on_startup=True
)

def create_app():
    app = Flask(__name__)
    app.secret_key = secret_key
    # Use absolute path to avoid confusion between app root and project root
    app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # app.config['CELERY_BROKER_URL'] is not strictly needed if we init Celery above,
    # but keeping it for consistency if other parts of the app need it.
    app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Update celery conf with app config
    celery.conf.update(app.config)

    # Subclassing Celery Task to ensure tasks run within the Flask application context.
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
