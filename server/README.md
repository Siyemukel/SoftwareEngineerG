# Backend (Flask)

This directory contains the Flask backend for the SoftwareEngineerG project, a Learning Disability Detector and Classifier System.

## Overview

- **Framework:** Flask
- **Database:** SQLite (via SQLAlchemy)
- **Structure:** Modular with Blueprints for routing and controllers for logic
- **Purpose:** Provides API endpoints for authentication, user management, and learning disability assessment

---

## Project Structure

```bash
server/
├── main.py                # Application entrypoint
├── requirements.txt       # Python dependencies
├── app/
│   ├── __init__.py        # App factory
│   ├── config.py          # Configuration settings
│   ├── extensions.py      # Extensions (e.g., SQLAlchemy)
│   ├── controllers/
│   │   └── auth_controller.py   # Authentication logic
│   ├── instance/
│   │   └── database.db    # SQLite database file
│   ├── models/
│   │   └── model.py       # SQLAlchemy models
│   └── routes/
│       ├── __init__.py
│       └── auth_router.py # Authentication routes
```

---

## Key Components

- **main.py:** Starts the Flask application using the app factory pattern.
- **app/config.py:** Contains configuration variables (e.g., secret key, database URI).
- **app/extensions.py:** Initializes Flask extensions like SQLAlchemy.
- **app/models/model.py:** Defines database models (e.g., User).
- **app/controllers/auth_controller.py:** Contains authentication logic (login, signup, etc.).
- **app/routes/auth_router.py:** Defines authentication API endpoints using Flask Blueprints.

---

## API Endpoints

All endpoints are prefixed as needed (e.g., `/api/auth/`):

- `POST /api/auth/login` – User login
- `POST /api/auth/signup` – User registration
- `POST /api/auth/check-email` – Check if email is registered
- `POST /api/auth/check-username` – Check if username is taken
- `POST /api/auth/logout` – Logout (stateless, for client-side cleanup)

> All endpoints expect and return JSON.

---

## Development

### Setup

1. Create and activate a virtual environment (optional but recommended):

    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install dependencies:

    ```sh
    pip install -r requirements.txt
    ```

3. Run the Flask server:

    ```sh
    python main.py
    ```

4. The API will be available at `http://localhost:5000` by default.

---

## Configuration

- Edit `app/config.py` to change environment variables, secret keys, or database URI.
- The SQLite database is stored at `app/instance/database.db` by default.

---

## Useful References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/)

---
