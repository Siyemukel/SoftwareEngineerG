from flask import jsonify, request
from app.extensions import db
from app.models.model import Test, Question, StudentTestSession, StudentAnswer, TestResult, User
import uuid

def get_available_tests():
    """
    Retrieves a list of all available tests.
    """
    try:
        tests = Test.query.all()
        test_list = [{
            "test_id": test.test_id,
            "name": test.name,
            "description": test.description
        } for test in tests]
        return jsonify(test_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_test_questions(test_id):
    """
    Retrieves all questions for a specific test.
    """
    try:
        test = Test.query.get(test_id)
        if not test:
            return jsonify({"error": "Test not found"}), 404
            
        questions = Question.query.filter_by(test_id=test_id).order_by(Question.part).all()
        question_list = []
        for q in questions:
            question_data = {
                "question_id": q.question_id,
                "part": q.part,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": []
            }
            if q.question_type == 'multiple_choice':
                options = [{"option_id": opt.option_id, "option_text": opt.option_text} for opt in q.answer_options]
                question_data["options"] = options
            question_list.append(question_data)
        
        return jsonify(question_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_test_session():
    """
    Starts a new test session for a student.
    """
    data = request.json
    user_id = data.get('user_id')
    test_id = data.get('test_id')

    if not user_id or not test_id:
        return jsonify({"error": "User ID and Test ID are required"}), 400
    
    user = User.query.get(user_id)
    test = Test.query.get(test_id)
    if not user or not test:
        return jsonify({"error": "User or Test not found"}), 404

    try:
        new_session = StudentTestSession(user_id=user_id, test_id=test_id)
        db.session.add(new_session)
        db.session.commit()
        return jsonify({"message": "Test session started successfully", "session_id": new_session.session_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def submit_answers():
    """
    Submits a batch of answers for a test session.
    """
    data = request.json
    session_id = data.get('session_id')
    answers = data.get('answers')

    if not session_id or not answers:
        return jsonify({"error": "Session ID and answers are required"}), 400

    session = StudentTestSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Test session not found"}), 404
    
    try:
        for answer in answers:
            new_answer = StudentAnswer(
                session_id=session_id,
                question_id=answer.get('question_id'),
                selected_option_id=answer.get('selected_option_id'),
                free_text_answer=answer.get('free_text_answer')
            )
            db.session.add(new_answer)
        
        # This is a placeholder for the result calculation logic.
        # In a real-world scenario, you would perform the classification here.
        test_result = TestResult(
            session_id=session_id,
            numbers_score=5,  # Placeholder score
            logic_score=7,    # Placeholder score
            shapes_score=8,   # Placeholder score
            disability_likelihood="high",
            outcome_message="Your results suggest a high likelihood of a learning difficulty.",
            staff_breakdown={"notes": "Detailed breakdown for staff review"}
        )
        db.session.add(test_result)
        
        db.session.commit()
        return jsonify({"message": "Answers submitted and results calculated successfully", "result": test_result.outcome_message}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
