# Learning Disability Detection System

This project is a web-based system designed to help detect potential learning disabilities through a series of interactive tests (Numbers, Logic, and Shapes). The application dynamically generates questions, evaluates responses using AI, and provides results for students in a simple and accessible interface.

---

##  Features

- **User Authentication**
  - Secure Sign Up and Login
  - Student Dashboard

- **Adaptive Testing**
  - Numbers Test
  - Logic Test
  - Shapes Test
  - Questions progress in difficulty (easy → medium → hard)

- **AI-Powered Evaluation**
  - Student answers are dynamically assessed
  - Tailored feedback is provided

- **Test Results**
  - Scores tracked across test parts
  - Clear summary of performance

---

## Project Structure


project/
│── app/
│ ├── init.py # App factory and initialization
│ ├── models.py # Database models
│ ├── routes.py # Application routes and logic
│ ├── templates/ # HTML templates for pages
│ ├── static/ # CSS, images, JavaScript
│
│── config.py # Configuration settings
│── requirements.txt # Dependencies
│── README.md # Project documentation
│── run.py # App entry point


Create a virtual environment

python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate 