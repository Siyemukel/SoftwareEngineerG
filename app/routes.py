
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from .forms import SignupForm, StudentLoginForm, StaffLoginForm,StaffSignupForm, DiscalculiaSurveyForm
from .models import *
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from . import db 
import json
import google.generativeai as genai
import os


model = genai.GenerativeModel("gemini-1")  # or "gemini-1" if lighter

# Define the blueprint
main = Blueprint("main", __name__)

#--------------------Home Page--------------------
@main.route("/", methods=["GET", "POST"]) 
def home():
    # Check if any staff exists. If not, trigger the admin setup process.
    if not Staff.query.first():
        form = StaffSignupForm()
        if form.validate_on_submit():
            try:
                # Create the first user and assign them the 'admin' role.
                new_admin = Staff(
                    username=form.username.data,
                    name=form.name.data,
                    surname=form.surname.data,
                    is_admin=True, # Ensure the first user has admin privileges
                   
                )
                new_admin.set_password(form.password.data)
                
                db.session.add(new_admin)
                db.session.commit()

                flash("Admin account created successfully! Please log in.", "success")
                # Changed from "auth.login" to "main.login" to match your login_manager setup
                return redirect(url_for("main.login"))

            except IntegrityError:
                db.session.rollback()
                flash("That username is already taken. Please choose another.", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {e}", "danger")

        # Show the first-time admin setup page
        return render_template("admin_signup.html", form=form, title="Initial Admin Setup")

    # If an admin/staff already exists, render the normal home page
    student_count = Student.query.count()
    staff_count = Staff.query.count()
    return render_template("home.html", student_count=student_count, staff_count=staff_count)


#--------------------Student Signup--------------------
@main.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()  

    if form.validate_on_submit(): #Get data from the form

        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        course = form.course.data
        year_of_study = form.year_of_study.data
        faculty = form.faculty.data
        password = form.password.data

     # Check if email already exists
        existing_student = Student.query.filter_by(student_email=email).first()
        if existing_student:
            flash("Email already registered!", "danger")
            return redirect(url_for("main.signup"))

   
        new_student = Student(
            name=name,
            surname=surname,
            student_email=email,
            course=course,
            year_of_study=year_of_study,
            faculty=faculty
        )
        new_student.set_password(password)

        db.session.add(new_student)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("main.home"))


    return render_template("student_signup.html", form=form)


#--------------------Login for both students and staff--------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        # 1. Try to log in student (by email)
        student = Student.query.filter_by(student_email=username_or_email).first()
        if student and student.check_password(password):
            login_user(student)
            flash("Logged in as student!", "success")
            return redirect(url_for("main.student_dashboard"))

        # 2. Try to log in staff (by username)
        staff = Staff.query.filter_by(username=username_or_email).first()
        if staff and staff.check_password(password):
            login_user(staff)
            flash("Logged in as staff!", "success")
            return redirect(url_for("main.staff_dashboard"))

        flash("Invalid credentials, please try again.", "danger")

    return render_template("login.html")


#--------------------Student Dashboard--------------------
@main.route("/student_dashboard", methods=["GET", "POST"])
@login_required
def student_dashboard():
    student = current_user 
    
    # Get latest test results for this student
    student_results = TestResult.query.filter_by(student_id=student.id)\
                                      .order_by(TestResult.created_at.desc()).first()
    
    # Determine which test parts are completed
    numbers_done = student_results.numbers_score if student_results else None
    logic_done = student_results.logic_score if student_results else None
    shapes_done = student_results.shapes_score if student_results else None
    
    return render_template(
        "student_dashboard.html",
        student=student,
        student_results=student_results,
        numbers_done=numbers_done,
        logic_done=logic_done,
        shapes_done=shapes_done
    )


#--------------------Student Survey--------------------
@main.route("/survey", methods=["GET", "POST"])
@login_required
def survey():
    # Ensure only students access
    if not hasattr(current_user, "student_email"):
        flash("Access denied!", "danger")
        return redirect(url_for("main.home"))

    # Check if survey already submitted
    if StudentSurvey.query.filter_by(student_id=current_user.id).first():
        flash("You have already submitted the survey.", "info")
        return redirect(url_for("main.student_dashboard"))

    form = DiscalculiaSurveyForm()
    if form.validate_on_submit():
        survey_data = {
            "math_difficulty": form.math_difficulty.data,
            "reading_numbers": form.reading_numbers.data,
            "math_anxiety": form.math_anxiety.data,
            "time_management": form.time_management.data,
            "previous_diagnosis": form.previous_diagnosis.data,
            "support_needed": form.support_needed.data,
            "daily_challenges": form.daily_challenges.data
        }

        new_survey = StudentSurvey(
            student_id=current_user.id,
            survey_data=json.dumps(survey_data)
        )
        db.session.add(new_survey)
        db.session.commit()

        flash("Survey submitted successfully!", "success")
        return redirect(url_for("main.student_dashboard"))

    return render_template("survey.html", form=form)


#--------------------Staff Dashboard--------------------
@main.route("/staff_dashboard", methods=["GET", "POST"]) 
@login_required
def staff_dashboard(): 
    # Only allow staff to access
    if not hasattr(current_user, "username"):
        flash("Access denied!", "danger")
        return redirect(url_for("main.login")) 

    return render_template("staff_dashboard.html", staff=current_user)
 

#--------------------Start Test (students only)--------------------
@main.route("/start_test")
@login_required
def start_test():
    # Check if student already has a test result
    existing_test = TestResult.query.filter_by(student_id=current_user.id).first()
    if existing_test:
        flash("You have already completed the test.", "info")
        return redirect(url_for("main.student_dashboard"))

    # Redirect to first test part: Numbers
    return redirect(url_for("main.test_part", part="numbers", difficulty="easy", q_num=1))
 

        
#--------------------Test Parts (students only)--------------------

@main.route("/test/<part>/<int:q_num>/<difficulty>", methods=["GET", "POST"])
@login_required
def test_part(part, q_num, difficulty):
    if part not in ["numbers", "logic", "shapes"]:
        flash("Invalid test part.", "danger")
        return redirect(url_for("main.student_dashboard"))

    # POST: process student's answer
    if request.method == "POST":
        student_answer = request.form.get("answer")
        question_text = session.get(f"{part}_{q_num}_text")
        correct_answer = question_text  # For now assume AI will judge it
        correct = ai_evaluate_answer(student_answer, correct_answer, part, question_text)
        
        # Save score in session
        session[part + "_score"] = session.get(part + "_score", 0) + (1 if correct else 0)

        # Determine next question or part
        if q_num < 5:
            next_q = q_num + 1
            next_diff = "medium" if q_num == 2 else "hard" if q_num == 5 else "easy"
            return redirect(url_for("main.test_part", part=part, q_num=next_q, difficulty=next_diff))
        else:
            # Move to next part
            next_part = "logic" if part == "numbers" else "shapes" if part == "logic" else None
            if next_part:
                return redirect(url_for("main.test_part", part=next_part, q_num=1, difficulty="easy"))
            else:
                return redirect(url_for("main.test_results"))

    # GET: generate question dynamically
    question_text = get_next_question(part, difficulty)
    session[f"{part}_{q_num}_text"] = question_text
    return render_template("test_part.html", part=part.capitalize(), q_num=q_num, question=question_text)

# ------------------Display final results------------------
@main.route("/results")
@login_required
def test_results():

    numbers_score = session.get("numbers_score", 0)
    logic_score = session.get("logic_score", 0)
    shapes_score = session.get("shapes_score", 0)

    total_score = numbers_score + logic_score + shapes_score

    # Determine disability likelihood
    if total_score <= 7:  # Example threshold
        likelihood = "High"
        message = "You may need extra support with numbers and logic."
    else:
        likelihood = "Low"
        message = "Your results are within the expected range."

    # Save to database
    test_result = TestResult(
        student_id=current_user.id,
        numbers_score=numbers_score,
        logic_score=logic_score,
        shapes_score=shapes_score,
        disability_likelihood=likelihood,
        outcome_message=message,
        staff_breakdown={}  # optional
    )
    db.session.add(test_result)
    db.session.commit()

    # Clear session scores
    session.pop("numbers_score", None)
    session.pop("logic_score", None)
    session.pop("shapes_score", None)

    return render_template(
        "test_results.html",
        numbers_score=numbers_score,
        logic_score=logic_score,
        shapes_score=shapes_score,
        total_score=total_score,
        likelihood=likelihood,
        message=message
    )


#--------------------For managing staff accounts (admin only)------------------
@main.route("/manage_staff", methods=["GET", "POST"])
@login_required
def manage_staff():
    # Only allow admins
    if not getattr(current_user, "is_admin", False):
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    staff_list = Staff.query.all()  # Fetch all staff members
    return render_template("manage_staff.html", staff_list=staff_list)


#-------------------For adding new staff accounts (admin only)------------------
@main.route("/add_staff", methods=["GET", "POST"])
@login_required
def add_staff():
    # Only allow admins
    if not getattr(current_user, "is_admin", False):
        flash("You are not authorized to add staff.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    form = StaffSignupForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_staff = Staff.query.filter_by(username=form.username.data).first()
        if existing_staff:
            flash("Username already taken. Please choose another.", "danger")
            return redirect(url_for("main.add_staff"))

        new_staff = Staff(
            username=form.username.data,
            name=form.name.data,
            surname=form.surname.data,
            is_admin=form.is_admin.data or False  # Only if checkbox selected
        )
        new_staff.set_password(form.password.data)

        db.session.add(new_staff)
        db.session.commit()

        flash("Staff member added successfully!", "success")
        return redirect(url_for("main.manage_staff"))

    return render_template("add_staff.html", form=form)


# ----------------- Edit Staff -----------------
@main.route("/edit_staff/<int:staff_id>", methods=["GET", "POST"])
@login_required
def edit_staff(staff_id):
    # Only admin should edit staff
    if not getattr(current_user, "is_admin", False):
        flash("You do not have permission to edit staff!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    staff_member = Staff.query.get_or_404(staff_id)

    if request.method == "POST":
        staff_member.username = request.form.get("username")
        staff_member.name = request.form.get("name")
        staff_member.surname = request.form.get("surname")
        # Optionally: update password
        new_password = request.form.get("password")
        if new_password:
            staff_member.set_password(new_password)

        try:
            db.session.commit()
            flash("Staff updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating staff: {e}", "danger")

        return redirect(url_for("main.staff_dashboard"))

    return render_template("edit_staff.html", staff=staff_member)


#-------------------- Delete Staff -------------------
@main.route("/delete_staff/<int:staff_id>", methods=["POST"])
@login_required
def delete_staff(staff_id):
    if not getattr(current_user, "is_admin", False):
        flash("You do not have permission to delete staff!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    staff_member = Staff.query.get_or_404(staff_id)

    try:
        db.session.delete(staff_member)
        db.session.commit()
        flash("Staff deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting staff: {e}", "danger")

    return redirect(url_for("main.staff_dashboard"))


#--------------------Manage Students (staff only)--------------------
@main.route("/manage_students")
@login_required 
def manage_students():

    if not hasattr(current_user, "username"):
        flash("Access denied!", "danger")
        return redirect(url_for("main.login"))

    students = Student.query.all()
    return render_template("manage_students.html", students=students)


#--------------------Edit Student (staff only)--------------------
@main.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == "POST":
        student.name = request.form["name"]
        student.surname = request.form["surname"]
        student.student_email = request.form["email"]
        student.course = request.form["course"]
        student.year_of_study = request.form["year_of_study"]
        student.faculty = request.form["faculty"]
        db.session.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for("main.manage_students"))

    return render_template("edit_student.html", student=student)


#--------------------Delete Student (staff only)--------------------
@main.route("/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("main.manage_students"))




#-------------------staff view individual student results and surveys-------------------
@main.route("/staff/student/<int:student_id>/results")
@login_required
def staff_view_student_results(student_id):
    # Only staff can view
    if not hasattr(current_user, "is_staff") or not current_user.is_staff:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.index"))

    # Get the student and their results
    student = Student.query.get_or_404(student_id)
    results = TestResult.query.filter_by(student_id=student.id).all()

    # Log that staff viewed results
    for result in results:
        view = TestResultStaffView(staff_id=current_user.id, test_result_id=result.id)
        db.session.add(view)
    db.session.commit()

    return render_template("staff_view_results.html", student=student, results=results)

 

#-------------------staff view individual student surveys-------------------
@main.route("/staff/student/<int:student_id>/surveys")
@login_required
def staff_view_student_surveys(student_id):
    # Only staff can view
    if not hasattr(current_user, "is_staff") or not current_user.is_staff:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.index"))

    # Get the student and their surveys
    student = Student.query.get_or_404(student_id)
    surveys = StudentSurvey.query.filter_by(student_id=student.id).all()

    # Log staff view
    for survey in surveys:
        view = StudentSurveyStaffView(staff_id=current_user.id, survey_id=survey.id)
        db.session.add(view)
    db.session.commit()

    return render_template("staff_view_surveys.html", student=student, surveys=surveys)

 

# ---------------- AI Question Generator ----------------
def get_next_question(part, difficulty="easy"):
    """
    Generate one question per test part: numbers, logic, shapes.
    """
    if part == "numbers":
        prompt = f"""
        Generate one {difficulty} math multiple-choice question.
        Provide options A, B, C, D and specify the correct answer clearly.
        Format:
        Question: ...
        A) ...
        B) ...
        C) ...
        D) ...
        Answer: <letter>
        """
    elif part == "logic":
        prompt = f"""
        Generate one {difficulty} logic reasoning test question in plain text.
        Give a single correct short answer at the end.
        Format:
        Question: ...
        Answer: ...
        """
    elif part == "shapes":
        prompt = f"""
        Generate one {difficulty} spatial reasoning question using text description (like shapes, rotations, or sequences).
        Give a single correct short answer at the end.
        Format:
        Question: ...
        Answer: ...
        """
    else:
        return {"error": "Invalid test part"}

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Split into question and answer
        if "Answer:" in text:
            question, answer = text.split("Answer:", 1)
            return {"question": question.strip(), "answer": answer.strip()}
        else:
            return {"question": text, "answer": None}
    except Exception as e:
        print("Gemini question generation failed:", e)
        return {"question": "Error generating question", "answer": None}
    

# ---------------- AI Answer Evaluator ----------------
def ai_evaluate_answer(student_answer, correct_answer, part, question_text):
    """ 
    Evaluate student's answer with Gemini.
    """
    # For Numbers (MCQs), direct match with letter
    if part == "numbers" and student_answer.strip().upper() == correct_answer.strip().upper():
        return True

    # For text answers (logic & shapes), AI check
    prompt = f"""
    You are an examiner. Question: "{question_text}".
    Student answered: "{student_answer}".
    Expected correct answer: "{correct_answer}".
    Reply ONLY with 'yes' if correct or 'no' if incorrect.
    """

    try:
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        return "yes" in result
    except Exception as e:
        print("AI evaluation failed:", e)
        return False

#--------------------Logout--------------------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))