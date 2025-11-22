from werkzeug.security import check_password_hash
from flask import session
from .config import users


def validate_user(email, password):
    if email in users and check_password_hash(users[email], password):
        session['logged_in'] = True
        return True
    return False

def generate_token():
    return "simple_token"  # This should be more secure and meaningful in production
    



