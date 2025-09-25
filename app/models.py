from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db 
from sqlalchemy import Index


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

    # Relationships
    test_results = db.relationship(
        "TestResult", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    exercises_completed = db.relationship(
        "ExerciseCompletion", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    staff_links = db.relationship(
        "StaffStudentLink", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    survey = db.relationship(
        "StudentSurvey", backref="student", uselist=False, cascade="all, delete-orphan"
    )
    medical_proofs = db.relationship(
        "MedicalProof", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    referrals = db.relationship(
        "StudentReferral", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    deletion_requests = db.relationship(
        "DeletionRequest", backref="student", lazy=True, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", backref="student", lazy=True, cascade="all, delete-orphan"
    )

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
    max_students = db.Column(db.Integer, default=5)

    # Relationships - Fixed with explicit foreign_keys
    students = db.relationship("StaffStudentLink", backref="staff", lazy=True)
    results_viewed = db.relationship("TestResultStaffView", backref="staff", lazy=True)
    surveys_viewed = db.relationship("StudentSurveyStaffView", backref="staff", lazy=True)
    exercises_reviewed = db.relationship("Exercise", backref="reviewed_by", lazy=True)
    
    # Fixed notification relationships with explicit foreign keys
    notifications = db.relationship(
        'Notification', 
        foreign_keys='Notification.staff_id',
        backref='staff', 
        lazy=True
    )
    admin_notifications = db.relationship(
        'Notification',
        foreign_keys='Notification.admin_id', 
        backref='admin',
        lazy=True
    )

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
    survey_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    staff_views = db.relationship("StudentSurveyStaffView", backref="survey", lazy=True)


class StudentSurveyStaffView(db.Model):
    __tablename__ = "student_survey_staff_views"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey("student_surveys.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate views
    __table_args__ = (db.UniqueConstraint('staff_id', 'survey_id', name='unique_staff_survey_view'),)


class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    numbers_score = db.Column(db.Integer)
    logic_score = db.Column(db.Integer)
    shapes_score = db.Column(db.Integer)
    disability_likelihood = db.Column(db.String(20), nullable=False)
    outcome_message = db.Column(db.String(255), nullable=False)
    staff_breakdown = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    staff_views = db.relationship("TestResultStaffView", backref="test_result", lazy=True)


class TestResultStaffView(db.Model):
    __tablename__ = "test_result_staff_views"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    test_result_id = db.Column(db.Integer, db.ForeignKey("test_results.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate views
    __table_args__ = (db.UniqueConstraint('staff_id', 'test_result_id', name='unique_staff_test_view'),)


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    video_link = db.Column(db.String(255))
    part = db.Column(db.String(20))  # Numbers, Logic, Shapes
    approved = db.Column(db.Boolean, default=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    completions = db.relationship("ExerciseCompletion", backref="exercise", lazy=True, cascade="all, delete-orphan")


class ExerciseCompletion(db.Model):
    __tablename__ = "exercise_completions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate completions
    __table_args__ = (db.UniqueConstraint('student_id', 'exercise_id', name='unique_student_exercise_completion'),)


class StaffStudentLink(db.Model):
    __tablename__ = "staff_student_links"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    status = db.Column(db.String(50), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint to prevent duplicate links
    __table_args__ = (db.UniqueConstraint('staff_id', 'student_id', name='unique_staff_student_link'),)


class DeletionRequest(db.Model):
    __tablename__ = "deletion_requests"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"))
    reviewed_at = db.Column(db.DateTime)

    # Relationships
    requested_by = db.relationship("Staff", foreign_keys=[requested_by_id], backref="deletion_requests_made")
    reviewed_by = db.relationship("Staff", foreign_keys=[reviewed_by_id], backref="deletion_requests_reviewed")


class NotificationSettings(db.Model):
    __tablename__ = "notification_settings"

    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=True)
    method_email = db.Column(db.Boolean, default=True)
    method_dashboard = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True) 
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50), nullable=True)  # For categorization
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id} - Staff {self.staff_id}>"


class ReportSettings(db.Model):
    __tablename__ = "report_settings"

    id = db.Column(db.Integer, primary_key=True)
    header_text = db.Column(db.String(255))
    footer_text = db.Column(db.String(255))
    include_student_email = db.Column(db.Boolean, default=True)
    include_name = db.Column(db.Boolean, default=True)
    include_surname = db.Column(db.Boolean, default=True)
    include_course = db.Column(db.Boolean, default=True)
    include_year = db.Column(db.Boolean, default=True)
    include_faculty = db.Column(db.Boolean, default=True)
    include_test_results = db.Column(db.Boolean, default=True)
    include_exercises_progress = db.Column(db.Boolean, default=True)
    report_format = db.Column(db.String(10), default="pdf")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MedicalProof(db.Model):
    __tablename__ = "medical_proofs"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Review info
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected
    rejection_reason = db.Column(db.String(500), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Assigned staff (before review)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    assigned_staff = db.relationship(
        "Staff",
        backref="assigned_medical_proofs",
        foreign_keys=[assigned_staff_id]
    )

    # Relationships
    reviewed_by = db.relationship("Staff", backref="reviewed_medical_proofs", foreign_keys=[reviewed_by_id])


class StudentReferral(db.Model):
    __tablename__ = "student_referrals"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    referred_by_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    referred_to_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="Pending")
    sent_to_department = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    referred_by = db.relationship("Staff", foreign_keys=[referred_by_id], backref="referrals_made")
    referred_to = db.relationship("Staff", foreign_keys=[referred_to_id], backref="referrals_received")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_type = db.Column(db.String(10), nullable=False)  # 'student' or 'staff'
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(10), nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_messages_sender', 'sender_type', 'sender_id'),
        db.Index('idx_messages_receiver', 'receiver_type', 'receiver_id'),
        db.Index('idx_messages_timestamp', 'timestamp'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sender_type": self.sender_type,
            "sender_id": self.sender_id,
            "receiver_type": self.receiver_type,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "is_read": self.is_read,
            "timestamp": self.timestamp.isoformat()
        }


class StaffFeedback(db.Model):
    __tablename__ = "staff_feedback"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    
    feedback_text = db.Column(db.Text, nullable=False)      # General feedback
    progress_notes = db.Column(db.Text, nullable=True)      # Optional progress notes (e.g., exercise completion, test areas)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship("Student", backref="feedbacks")
    staff = db.relationship("Staff", backref="given_feedbacks")


# Performance indexes
Index('idx_staff_student_link_staff_id', StaffStudentLink.staff_id)
Index('idx_staff_student_link_student_id', StaffStudentLink.student_id) 
Index('idx_medical_proof_student_status', MedicalProof.student_id, MedicalProof.status)
Index('idx_test_results_student_created', TestResult.student_id, TestResult.created_at)
Index('idx_notifications_staff_read', Notification.staff_id, Notification.is_read)
Index('idx_student_surveys_student', StudentSurvey.student_id)
Index('idx_exercise_completions_student', ExerciseCompletion.student_id)
Index('idx_student_referrals_status', StudentReferral.status, StudentReferral.created_at)