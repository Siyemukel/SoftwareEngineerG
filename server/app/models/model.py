import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    student_number = db.Column(db.String(20), unique=True, nullable=True) # Unique identifier for students
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    faculty = db.Column(db.String(100), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    
    role = db.Column(db.String(20), nullable=False, default="student") # 'student' or 'staff'
    password_hash = db.Column(db.String(255), nullable=False)

    # Relationship to TestResult, StudentFollowUp, and StudentSurvey for easy data access
    test_results = db.relationship('TestResult', backref='student', lazy=True)
    follow_ups = db.relationship('StudentFollowUp', foreign_keys='StudentFollowUp.student_id', backref='student_user', lazy=True)
    staff_follow_ups = db.relationship('StudentFollowUp', foreign_keys='StudentFollowUp.staff_id', backref='staff_user', lazy=True)
    survey = db.relationship('StudentSurvey', backref='student', uselist=False, lazy=True)

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} ({self.student_number or self.email})>"

    def set_password(self, password):
        """Hash the password before storing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password."""
        return check_password_hash(self.password_hash, password)

# This table stores the details of each test.
class Test(db.Model):
    __tablename__ = "tests"

    test_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationship to questions and test sessions
    questions = db.relationship('Question', backref='test', lazy=True)
    test_sessions = db.relationship('StudentTestSession', backref='test', lazy=True)

# This table stores the individual questions for a test.
class Question(db.Model):
    __tablename__ = "questions"

    question_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = db.Column(db.String(36), db.ForeignKey('tests.test_id'), nullable=False)
    part = db.Column(db.String(20), nullable=False) # 'Numbers', 'Logic', 'Shapes'
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False) # 'multiple_choice', 'free_text'

    # Relationship to answer options and student answers
    answer_options = db.relationship('AnswerOption', backref='question', lazy=True)
    student_answers = db.relationship('StudentAnswer', backref='question', lazy=True)

# This table stores the answer options for multiple-choice questions.
class AnswerOption(db.Model):
    __tablename__ = "answer_options"

    option_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = db.Column(db.String(36), db.ForeignKey('questions.question_id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

# This table tracks a student's progress on a test.
class StudentTestSession(db.Model):
    __tablename__ = "student_test_sessions"

    session_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    test_id = db.Column(db.String(36), db.ForeignKey('tests.test_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress") # 'in_progress', 'completed'

    # Relationship to student answers and test results
    student_answers = db.relationship('StudentAnswer', backref='test_session', lazy=True)
    test_result = db.relationship('TestResult', backref='test_session', uselist=False, lazy=True)

# This table stores the student's answer to each question in a session.
class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    answer_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('student_test_sessions.session_id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('questions.question_id'), nullable=False)
    # For multiple-choice questions
    selected_option_id = db.Column(db.String(36), db.ForeignKey('answer_options.option_id'), nullable=True)
    # For free text questions
    free_text_answer = db.Column(db.Text, nullable=True)

# This table holds the calculated results for a completed test session.
class TestResult(db.Model):
    __tablename__ = "test_results"

    result_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('student_test_sessions.session_id'), nullable=False, unique=True)
    # Store scores broken down by part
    numbers_score = db.Column(db.Integer, nullable=True)
    logic_score = db.Column(db.Integer, nullable=True)
    shapes_score = db.Column(db.Integer, nullable=True)
    # Overall likelihood of a learning disability
    disability_likelihood = db.Column(db.String(20), nullable=False) # e.g., 'high', 'low'
    # Simple, clear outcome message for the student
    outcome_message = db.Column(db.String(255), nullable=False)
    # Detailed breakdown for professional staff review
    staff_breakdown = db.Column(db.JSON, nullable=False)
    
# This table stores recommended exercises and content.
class ExerciseContent(db.Model):
    __tablename__ = "exercise_content"

    exercise_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_link = db.Column(db.String(255), nullable=True)
    recommended_for_part = db.Column(db.String(20), nullable=False) # 'Numbers', 'Logic', 'Shapes'
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

# This table is used by staff to flag students and add notes for follow-up.
class StudentFollowUp(db.Model):
    __tablename__ = "student_follow_ups"

    followup_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    staff_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    flagged_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# This new table stores a student's initial survey data.
class StudentSurvey(db.Model):
    __tablename__ = "student_surveys"

    survey_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False, unique=True)
    survey_data = db.Column(db.JSON, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
