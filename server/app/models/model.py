import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    
    role = db.Column(db.String(20), nullable=False, default="student")
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    def set_password(self, password):
        """Hash the password before storing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password."""
        return check_password_hash(self.password_hash, password)
    