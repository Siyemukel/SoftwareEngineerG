from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    from .extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)

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

    return app