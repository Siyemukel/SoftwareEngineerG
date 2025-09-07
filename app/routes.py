
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from .forms import SignupForm, StudentLoginForm, StaffLoginForm,StaffSignupForm, DiscalculiaSurveyForm
from .models import *
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from .extensions import db 
import json
import os

import mimetypes
from google import genai
from google.genai import types

main = Blueprint("main", __name__)

def setup_admin_account():
    form = StaffSignupForm()
    if form.validate_on_submit():
        try:
            # Create the first user and assign them the 'admin' role.
            new_admin = Staff(
                username=form.username.data,
                name=form.name.data,
                surname=form.surname.data,
                is_admin=True,
            )
            new_admin.set_password(form.password.data)
            
            db.session.add(new_admin)
            db.session.commit()

            flash("Admin account created successfully! Please log in.", "success")
            return redirect(url_for("main.home"))

        except IntegrityError:
            db.session.rollback()
            flash("That username is already taken. Please choose another.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")

    return render_template("admin_signup.html", form=form, title="Initial Admin Setup")

def setup_student_account():
    form = SignupForm()  
    if form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        course = form.course.data
        year_of_study = form.year_of_study.data
        faculty = form.faculty.data
        password = form.password.data

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

def login_user_account():
    username_or_email = request.form.get("username")
    password = request.form.get("password")

    student = Student.query.filter_by(student_email=username_or_email).first()
    if student and student.check_password(password):
        login_user(student)
        flash("Logged in as student!", "success")
        return redirect(url_for("main.student_dashboard"))

    staff = Staff.query.filter_by(username=username_or_email).first()
    if staff and staff.check_password(password):
        login_user(staff)
        flash("Logged in as staff!", "success")
        return redirect(url_for("main.staff_dashboard"))

    flash("Invalid credentials, please try again.", "danger")

#--------------------Home Page--------------------
@main.route("/", methods=["GET", "POST"]) 
def home():
    if not Staff.query.first():
        return setup_admin_account()

    student_count = Student.query.count()
    staff_count = Staff.query.count()
    print("Student count:", student_count)
    
    return render_template("home.html", student_count=student_count, staff_count=staff_count)


#--------------------Student Signup--------------------
@main.route("/signup", methods=["GET", "POST"])
def signup():
    if not Staff.query.first():
        return setup_admin_account()
    
    return setup_student_account()

#--------------------Login for both students and staff--------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if not Staff.query.first():
        return setup_admin_account()
    elif request.method == "POST":
        response = login_user_account()

        if response:
            return response

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
        # Determine the area of weakness based on scores
        # This is a simplified example; a more complex logic could be used
        scores = {
            "numbers": existing_test.numbers_score,
            "logic": existing_test.logic_score,
            "shapes": existing_test.shapes_score
        }
        
        # Find the lowest score and redirect to exercises for that part
        weakest_area = min(scores, key=scores.get)
        flash(f"You have already completed the test. Here are some exercises to help with your {weakest_area} skills.", "info")
        return redirect(url_for("main.exercises", part=weakest_area)) # Assuming an exercises route exists
    
    # If no test result exists, proceed to the test
    return redirect(url_for("main.test_part", part="numbers", difficulty="easy", q_num=1))

        
#--------------------Test Parts (students only)--------------------
from .services import get_next_question, ai_evaluate_answer

@main.route("/test/<part>/<int:q_num>/<difficulty>", methods=["GET", "POST"])
@login_required
def test_part(part, q_num, difficulty):
    if part not in ["numbers", "logic", "shapes"]:
        flash("Invalid test part.", "danger")
        return redirect(url_for("main.student_dashboard"))

    # POST: process student's answer
    if request.method == "POST":
        student_answer = request.form.get("answer")
        question_data = session.get(f"question_data_{part}_{q_num}")
        
        if not question_data or "answer" not in question_data:
            flash("Error: Question data not found or is incomplete.", "danger")
            return redirect(url_for("main.student_dashboard"))

        correct_answer = question_data["answer"]
        question_text = question_data["question"]
        
        correct = ai_evaluate_answer(student_answer, correct_answer, part, question_text)
        
        # Save score in session
        session[part + "_score"] = session.get(part + "_score", 0) + (1 if correct else 0)

        # Determine next question or part
        if q_num < 5:
            next_q = q_num + 1
            # Your difficulty logic here is a bit tricky. Let's simplify:
            if q_num == 1:
                next_diff = "easy"
            elif q_num == 2 or q_num == 3:
                next_diff = "medium"
            else:
                next_diff = "hard"
                
            return redirect(url_for("main.test_part", part=part, q_num=next_q, difficulty=next_diff))
        else:
            # Move to next part
            next_part = "logic" if part == "numbers" else "shapes" if part == "logic" else None
            if next_part:
                return redirect(url_for("main.test_part", part=next_part, q_num=1, difficulty="easy"))
            else:
                return redirect(url_for("main.test_results"))

    # GET: generate question dynamically
    question_data = get_next_question(part, difficulty)
    
    # Check if there was an error generating the question
    if "error" in question_data:
        flash(question_data["error"], "danger")
        return redirect(url_for("main.student_dashboard"))

    # Store the question and its answer in the session
    session[f"question_data_{part}_{q_num}"] = question_data

    return render_template("test_part.html", part=part.capitalize(), q_num=q_num, question=question_data["question"])

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

@main.route("/exercises/<string:part>", methods=["GET", "POST"])
@login_required
def exercises(part):
    # Check if the part is a valid category
    if part not in ["numbers", "logic", "shapes"]:
        flash("Invalid exercise category.", "danger")
        return redirect(url_for("main.student_dashboard"))
    
    # Generate the AI question
    exercise_data = get_next_question(part)
    
    if not exercise_data:
        flash("Could not generate an exercise. Please try again later.", "danger")
        return redirect(url_for("main.student_dashboard"))

    question_text = exercise_data.get("question")
    correct_answer = exercise_data.get("answer")

    # If the user is submitting an answer
    if request.method == "POST":
        student_answer = request.form.get("answer")
        is_correct = ai_evaluate_answer(student_answer, correct_answer, part, question_text)

        # Handle the answer (e.g., log completion, give feedback)
        if is_correct:
            flash("Correct! Great job!", "success")
            # Log the completion
            new_completion = ExerciseCompletion(
                student_id=current_user.id,
                exercise_id=None # Or link to a pre-generated exercise if you store them
            )
            db.session.add(new_completion)
            db.session.commit()
            
            # Redirect to the same page for a new question
            return redirect(url_for("main.exercises", part=part))
        else:
            flash(f"Incorrect. The correct answer was {correct_answer}.", "warning")
            # Log the attempt, but not a completion

    return render_template("exercise_page.html", question=question_text, part=part)


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

 
#--------------------Logout--------------------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))