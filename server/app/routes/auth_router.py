from flask import Blueprint

from app.controllers.auth_controller import login, signup, check_email, check_username

auth_router_bp = Blueprint('auth_router', __name__, url_prefix='/auth')

@auth_router_bp.route('/login', methods=['POST'])
def login_route():
    return login()

@auth_router_bp.route('/signup', methods=['POST'])
def signup_route():
    return signup()

@auth_router_bp.route('/check-email', methods=['POST'])
def check_email_route():
    return check_email()

@auth_router_bp.route('/check-username', methods=['POST'])
def check_username_route():
    return check_username()

@auth_router_bp.route('/logout', methods=['POST'])
def logout_route():
    return {"message": "Logout successful"}, 200