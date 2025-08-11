from flask import Blueprint

from app.controllers.auth_controller import login, signup

auth_router_bp = Blueprint('auth_router', __name__, url_prefix='/auth')

@auth_router_bp.route('/login', methods=['GET'])
def login_route():
    return login()

@auth_router_bp.route('/signup', methods=['GET'])
def signup_route():
    return signup()
