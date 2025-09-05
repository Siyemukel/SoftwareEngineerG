from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db 



class Student(UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    test_results = db.relationship("TestResult", backref="student", lazy=True)
    exercises_completed = db.relationship("ExerciseCompletion", backref="student", lazy=True)
    staff_links = db.relationship("StaffStudentLink", backref="student", lazy=True)
    survey = db.relationship("StudentSurvey", backref="student", uselist=False)

    def get_id(self):
        return f"student-{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Staff(UserMixin, db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    students = db.relationship("StaffStudentLink", backref="staff", lazy=True)
    results_viewed = db.relationship("TestResultStaffView", backref="staff", lazy=True)
    surveys_viewed = db.relationship("StudentSurveyStaffView", backref="staff", lazy=True)
    exercises_reviewed = db.relationship("Exercise", backref="reviewed_by", lazy=True)

    def get_id(self):
        return f"staff-{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class StudentSurvey(db.Model):
    __tablename__ = "student_surveys"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, unique=True)
    survey_data = db.Column(db.JSON, nullable=False)  # Store responses as JSON
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_views = db.relationship("StudentSurveyStaffView", backref="survey", lazy=True)



class StudentSurveyStaffView(db.Model):
    __tablename__ = "student_survey_staff_views"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey("student_surveys.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)



class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    numbers_score = db.Column(db.Integer)
    logic_score = db.Column(db.Integer)
    shapes_score = db.Column(db.Integer)
    disability_likelihood = db.Column(db.String(20), nullable=False)  # high / low
    outcome_message = db.Column(db.String(255), nullable=False)
    staff_breakdown = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_views = db.relationship("TestResultStaffView", backref="test_result", lazy=True)


class TestResultStaffView(db.Model):
    __tablename__ = "test_result_staff_views"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    test_result_id = db.Column(db.Integer, db.ForeignKey("test_results.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)



class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    video_link = db.Column(db.String(255))
    part = db.Column(db.String(20))  # Numbers, Logic, Shapes
    approved = db.Column(db.Boolean, default=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"))



class ExerciseCompletion(db.Model):
    __tablename__ = "exercise_completions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)



class StaffStudentLink(db.Model):
    __tablename__ = "staff_student_links"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
