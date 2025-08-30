import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'staff'

    # Relationships
    test_sessions = db.relationship("StudentTestSession", backref="user", lazy=True)
    follow_ups_as_student = db.relationship("StudentFollowUp", foreign_keys="StudentFollowUp.student_id", backref="student", lazy=True)
    follow_ups_as_staff = db.relationship("StudentFollowUp", foreign_keys="StudentFollowUp.staff_id", backref="staff", lazy=True)
    survey = db.relationship("StudentSurvey", backref="user", uselist=False, lazy=True)

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} ({self.email})>"

    def set_password(self, password):
        """Hash the password before storing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password."""
        return check_password_hash(self.password_hash, password)


# ✅ Instead of separate Staff/Student models, keep one User table with `role`.
#    If you want separate tables, you’d need joined-table inheritance. But one table is simpler.

class Test(db.Model):
    __tablename__ = "tests"

    test_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    questions = db.relationship("Question", backref="test", lazy=True)
    test_sessions = db.relationship("StudentTestSession", backref="test", lazy=True)


class Question(db.Model):
    __tablename__ = "questions"

    question_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = db.Column(db.String(36), db.ForeignKey("tests.test_id"), nullable=False)
    part = db.Column(db.String(20), nullable=False)  # 'Numbers', 'Logic', 'Shapes'
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # 'multiple_choice', 'free_text'

    answer_options = db.relationship("AnswerOption", backref="question", lazy=True)
    student_answers = db.relationship("StudentAnswer", backref="question", lazy=True)


class AnswerOption(db.Model):
    __tablename__ = "answer_options"

    option_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = db.Column(db.String(36), db.ForeignKey("questions.question_id"), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)


class StudentTestSession(db.Model):
    __tablename__ = "student_test_sessions"

    session_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)
    test_id = db.Column(db.String(36), db.ForeignKey("tests.test_id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress")

    student_answers = db.relationship("StudentAnswer", backref="test_session", lazy=True)
    test_result = db.relationship("TestResult", backref="test_session", uselist=False, lazy=True)


class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    answer_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("student_test_sessions.session_id"), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey("questions.question_id"), nullable=False)
    selected_option_id = db.Column(db.String(36), db.ForeignKey("answer_options.option_id"), nullable=True)
    free_text_answer = db.Column(db.Text, nullable=True)


class TestResult(db.Model):
    __tablename__ = "test_results"

    result_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("student_test_sessions.session_id"), nullable=False, unique=True)
    numbers_score = db.Column(db.Integer, nullable=True)
    logic_score = db.Column(db.Integer, nullable=True)
    shapes_score = db.Column(db.Integer, nullable=True)
    disability_likelihood = db.Column(db.String(20), nullable=False)
    outcome_message = db.Column(db.String(255), nullable=False)
    staff_breakdown = db.Column(db.JSON, nullable=False)


class ExerciseContent(db.Model):
    __tablename__ = "exercise_content"

    exercise_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_link = db.Column(db.String(255), nullable=True)
    recommended_for_part = db.Column(db.String(20), nullable=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)


