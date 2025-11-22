from flask import Flask
from celery import Celery
import os
from .config import secret_key

# Initialize Celery without config first
celery = Celery(__name__, broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

def create_app():
    app = Flask(__name__)
    app.secret_key = secret_key
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

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
