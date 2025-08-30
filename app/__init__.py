from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")


    db.init_app(app)
    login_manager.init_app(app)

 
    login_manager.login_view = "login"

    with app.app_context():
        from . import models  
        from .routes import register_routes  
        register_routes(app)  


        db.create_all()

    return app
