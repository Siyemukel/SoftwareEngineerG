from flask import Flask
from .extensions import db, socketio, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    from .extensions import db, login_manager, socketio, mail, migrate
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)

    from .models import Student, Staff
    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("student-"):
            student_id = int(user_id.split("-")[1])
            return Student.query.get(student_id)
        elif user_id.startswith("staff-"):
            staff_id = int(user_id.split("-")[1])
            return Staff.query.get(staff_id)
        return None
    
    from .routes import main
    app.register_blueprint(main)
     
    from . import sockets 

    
    return app