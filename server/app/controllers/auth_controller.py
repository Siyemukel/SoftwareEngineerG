import re
import jwt
import uuid
import datetime
from flask import request, jsonify, current_app

from app.models.model import User
from app.extensions import db

def is_dut_email(email):
    return re.fullmatch(r"\d{8}@dut4life\.ac\.za", email) is not None

def is_full_name(name):
    return re.fullmatch(r"[A-Z][a-z]+ [A-Z][a-z]+", name) is not None

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"\d", password) and
        re.search(r"[@$!%*?&]", password)
    )

def signup():
    data = request.get_json()
    full_name = data.get('full_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([full_name, username, email, password]):
        return {"message": "Missing required fields"}, 400

    if not is_dut_email(email):
        return {"message": "Email must be a valid DUT email (e.g. 22289351@dut4life.ac.za)"}, 400

    if not is_full_name(full_name):
        return {"message": "Full name must be in format: Name Surname (capitalize first letters)"}, 400

    if not is_strong_password(password):
        return {"message": "Password must be at least 8 characters, include upper and lower case, a number, and a special character."}, 400

    if User.query.filter_by(email=email).first():
        return {"message": "Email already registered"}, 400

    if User.query.filter_by(username=username).first():
        return {"message": "Username already taken"}, 400

    user = User(
        user_id=str(uuid.uuid4()),
        full_name=full_name,
        username=username,
        email=email,
        role="student"
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return {
        "message": "Signup successful",
        "user": {
            "uid": user.user_id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }, 201

def check_email():
    data = request.get_json()
    email = data.get("email")
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({"exists": exists})

def check_username():
    data = request.get_json()
    username = data.get("username")
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({"exists": exists})

def login():
    data = request.get_json()
    identifier = data.get('email') or data.get('username')
    password = data.get('password')

    if not identifier or not password:
        return {"message": "Missing email/username or password"}, 400

    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if user and user.check_password(password):
        payload = {
            "uid": user.user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }
        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "uid": user.user_id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        }, 200

    return {"message": "Invalid credentials"}, 401