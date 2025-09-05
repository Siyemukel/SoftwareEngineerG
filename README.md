# Learning Disability Detection System

This project is a web-based system designed to help detect potential learning disabilities, specifically dyscalculia, through a series of interactive tests (Numbers, Logic, and Shapes). The application dynamically generates questions, evaluates responses using AI (Google Gemini), and provides results for students in a simple and accessible interface.

---

## Features

- **User Authentication**
  - Secure Sign Up and Login for Students and Staff
  - Student and Staff Dashboards
  - Admin management for staff accounts

- **Adaptive Testing**
  - Numbers, Logic, and Shapes Tests
  - Questions progress in difficulty (easy → medium → hard)
  - AI-generated questions for each test part

- **AI-Powered Evaluation**
  - Student answers are dynamically assessed using Google Gemini
  - Neutral, supportive feedback
  - No correction or diagnosis provided

- **Survey**
  - Students complete a dyscalculia-related survey
  - Survey results stored and viewable by staff

- **Test Results**
  - Scores tracked across test parts
  - Clear summary of performance
  - Disability likelihood estimation (non-diagnostic)
  - Results viewable by staff

- **Staff Management**
  - Admins can add, edit, and delete staff accounts
  - Staff can manage students and view individual results/surveys

---

## Project Structure

```
SoftwareEngineerG/
├── app
│   ├── extensions.py
│   ├── forms.py
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── services.py
│   ├── static
│   │   ├── images
│   │   ├── script.js
│   │   └── style.css
│   └── templates
│       ├── add_staff.html
│       ├── admin_signup.html
│       ├── base.html
│       ├── edit_staff.html
│       ├── home.html
│       ├── login.html
│       ├── manage_staff.html
│       ├── manage_students.html
│       ├── staff_dashboard.html
│       ├── staff_view_results.html
│       ├── staff_view_survey.html
│       ├── student_dashboard.html
│       ├── student_signup.html
│       ├── survey.html
│       ├── test_part.html
│       └── test_results.html
├── config.py
├── .env
├── README.md
└── run.py
```

---

## Setup Instructions

1. **Create a virtual environment**

   ```sh
   python -m venv venv
   source venv/bin/activate   # Mac/Linux
   # venv\Scripts\activate    # Windows
   ```

2. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   - Copy `.env.example` to .env and set your `GEMINI_API_KEY`, `SECRET_KEY`, and `DATABASE_URL`.

4. **Run the application**

   ```sh
   python run.py
   ```

---

## Notes

- The system uses Google Gemini for AI-powered question generation and answer evaluation.
- All assessments are preliminary and non-diagnostic.
- Only admins can manage staff accounts; staff can manage students and view results/surveys.
- Survey and test results are stored in the database and accessible via the dashboard.

---

For more details, see the code in routes.py, services.py, and models.py.