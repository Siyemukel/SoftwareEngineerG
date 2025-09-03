from flask import Blueprint
from app.controllers import test_controller

# Create a Blueprint for test routes
test_bp = Blueprint('test_bp', __name__)

@test_bp.route('/tests', methods=['GET'])
def get_tests():
    """
    API endpoint to get a list of all available tests.
    """
    return test_controller.get_available_tests()

@test_bp.route('/tests/<test_id>/questions', methods=['GET'])
def get_questions(test_id):
    """
    API endpoint to get questions for a specific test.
    """
    return test_controller.get_test_questions(test_id)

@test_bp.route('/sessions/start', methods=['POST'])
def start_session():
    """
    API endpoint to start a new test session.
    """
    return test_controller.start_test_session()

@test_bp.route('/sessions/submit', methods=['POST'])
def submit_session():
    """
    API endpoint to submit test answers and get results.
    """
    return test_controller.submit_answers()
