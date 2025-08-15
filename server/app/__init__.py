from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db
from app.routes import router_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=["http://localhost:5173"])  

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(router_bp)

    return app
