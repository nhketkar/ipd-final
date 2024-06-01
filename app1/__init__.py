from flask import Flask
import os
from .routes import create_routes  # Ensure this import is correct

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'static/uploads/'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
    app.config['SECRET_KEY'] = 'ec9439cfc96c796ae2029594d'

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Set up routes
    create_routes(app)

    return app
