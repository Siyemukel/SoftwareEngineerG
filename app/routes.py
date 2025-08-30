from flask import Blueprint


main = Blueprint("main", __name__)

@main.route("/")
def home():
    return "Hello, World!"

def register_routes(app):
    app.register_blueprint(main)