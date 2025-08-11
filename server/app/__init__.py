from flask import Flask

from app.routes import router_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(router_bp)

    return app
