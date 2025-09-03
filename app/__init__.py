from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro") 
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Redirect unauthorized users to the login page
    login_manager.login_view = "main.login"
    
    # Import models
    from .models import Student, Staff
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("student-"):
            student_id = int(user_id.split("-")[1])
            return Student.query.get(student_id)
        elif user_id.startswith("staff-"):
            staff_id = int(user_id.split("-")[1])
            return Staff.query.get(staff_id)
        return None
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    return app