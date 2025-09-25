from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "main.login"
mail = Mail()

# initialize SocketIO but don't attach app yet
socketio = SocketIO(cors_allowed_origins="*")
