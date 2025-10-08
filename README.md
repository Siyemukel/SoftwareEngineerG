# SoftwareEngineerG

## Overview
SoftwareEngineerG is a web application built with Flask, SQLAlchemy, and Flask-SocketIO. It provides a platform for managing students and staff, handling referrals, generating and evaluating questions (including AI-powered features), and supporting real-time communication.

## Features
- User authentication and management (students, staff, admin)
- Student-staff assignment system
- AI-powered question generation and answer evaluation (Google Generative AI)
- Medical proof uploads and review
- Real-time communication via SocketIO
- Email notifications for referrals
- Admin and staff dashboards
- Survey and exercise tracking

## Project Structure
```
SoftwareEngineerG/
├── app/                # Main application package
│   ├── extensions.py   # Flask extensions (db, mail, login, etc.)
│   ├── forms.py        # WTForms definitions
│   ├── models.py       # SQLAlchemy models
│   ├── routes.py       # Flask routes/views
│   ├── services.py     # Business logic and AI helpers
│   ├── sockets.py      # SocketIO event handlers
│   ├── static/         # CSS, JS, images
│   └── templates/      # Jinja2 HTML templates
├── config.py           # App configuration
├── run.py              # Application entry point
├── requirements.txt    # Python dependencies
├── migrations/         # Alembic migration scripts
├── tests/              # Unit tests
├── uploads/            # Uploaded files (e.g., medical proofs)
└── instance/site.db    # SQLite database
```

## Setup & Installation
1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables:**
   - `GEMINI_API_KEY` or `GOOGLE_API_KEY` for AI features
   - `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`, etc. for email
4. **Run database migrations:**
   ```bash
   flask db upgrade
   ```
5. **Start the application:**
   ```bash
   python run.py
   ```
   The app will run on http://localhost:5000

## Main Modules
- **app/models.py**: Defines database models for users, staff, students, links, surveys, exercises, etc.
- **app/services.py**: Contains business logic, AI helpers, question generation, answer evaluation, and email functions.
- **app/routes.py**: Implements web routes for authentication, dashboards, student/staff management, and more.
- **app/sockets.py**: Handles real-time events and messaging.
- **app/extensions.py**: Initializes Flask extensions (db, mail, login manager).
- **app/forms.py**: Contains form definitions for user input.
- **app/static/**: Static assets (CSS, JS, images).
- **app/templates/**: HTML templates for all pages.
- **migrations/**: Database migration scripts managed by Alembic.
- **tests/**: Unit tests for services and business logic.
- **uploads/**: Stores uploaded files (e.g., medical proofs).

## AI Features
- AI-powered question generation and answer evaluation use Google Generative AI (Gemini).
- Configure your API key in environment variables to enable these features.

