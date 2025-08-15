from flask import Blueprint

from app.routes.auth_router import auth_router_bp

router_bp = Blueprint('router', __name__, url_prefix='/api')

@router_bp.route('/', methods=['GET'])
def index():
    return {"message": "Hello, World! This an API"}, 200 

router_bp.register_blueprint(auth_router_bp)