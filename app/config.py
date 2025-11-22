from werkzeug.security import generate_password_hash
import os

password = os.environ['password']
secret_key = os.urandom(24)

hashed_password = generate_password_hash(password)

users = {
    "rob.roskowski@gmail.com": hashed_password
}