
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from .forms import SignupForm, StudentLoginForm, StaffLoginForm,StaffSignupForm, DiscalculiaSurveyForm, AssignStaffForm
from .models import *
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from .extensions import db 
import json
import os

import mimetypes
import google.generativeai as genai
from .services import get_next_question, ai_evaluate_answer


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

    return render_template("/auth/admin_signup.html", form=form, title="Initial Admin Setup")

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
        return redirect(url_for("main.student_dashboard"))

    return render_template("auth/signup.html", form=form)

def login_user_account():
    username_or_email = request.form.get("username")
    password = request.form.get("password")

    # ----------- STUDENT LOGIN -----------
    student = Student.query.filter_by(student_email=username_or_email).first()
    if student and student.check_password(password):
        login_user(student)

        # Check if survey exists
        survey_exists = StudentSurvey.query.filter_by(student_id=student.id).first()

        if not survey_exists:
            flash("Welcome! Let’s get started with a quick setup, shall we? ", "info")
            return redirect(url_for("main.student_onboarding"))  # send to onboarding page

        flash("Logged in as student!", "success")
        return redirect(url_for("main.student_dashboard"))

    # ----------- STAFF LOGIN -----------
    staff = Staff.query.filter_by(username=username_or_email).first()
    if staff and staff.check_password(password):
        login_user(staff)
        flash("Logged in as staff!", "success")
        return redirect(url_for("main.staff_dashboard"))

    # ----------- INVALID CREDENTIALS -----------
    flash("Invalid credentials, please try again.", "danger")
    return redirect(url_for("main.login"))




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

    return render_template("/auth/login.html")


#--------------------Logout for both students and staff--------------------
@main.route("/student/onboarding")
@login_required
def student_onboarding():
    if not isinstance(current_user, Student):
        flash("Access denied!", "danger")
        return redirect(url_for("main.home"))

    return render_template("/student/student_onboarding.html", student=current_user)
 

   

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
        "/student/student_dashboard.html",
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
        # Convert responses to numeric scores
        def score_yes_no(ans):
            return 1 if ans == "Yes" else 0

        survey_scores = {
            "math_difficulty": int(form.math_difficulty.data),
            "reading_numbers": score_yes_no(form.reading_numbers.data),
            "math_anxiety": score_yes_no(form.math_anxiety.data),
            "time_management": score_yes_no(form.time_management.data),
            "previous_diagnosis": score_yes_no(form.previous_diagnosis.data),
            # Add other questions if present
            "reading_difficulty": score_yes_no(getattr(form, "reading_difficulty", "No")),
            "writing_numbers": score_yes_no(getattr(form, "writing_numbers", "No")),
            "memory_issues": score_yes_no(getattr(form, "memory_issues", "No")),
            "attention_difficulty": score_yes_no(getattr(form, "attention_difficulty", "No")),
            "processing_speed": score_yes_no(getattr(form, "processing_speed", "No")),
            "problem_solving_difficulty": score_yes_no(getattr(form, "problem_solving_difficulty", "No")),
            "visual_confusion": score_yes_no(getattr(form, "visual_confusion", "No")),
            "anxiety_other_subjects": score_yes_no(getattr(form, "anxiety_other_subjects", "No")),
            "fatigue": score_yes_no(getattr(form, "fatigue", "No"))
        }

        # Save survey numeric scores
        new_survey = StudentSurvey(
            student_id=current_user.id,
            survey_data=json.dumps(survey_scores)
        )
        db.session.add(new_survey)
        db.session.commit()

        flash("Survey submitted successfully!", "success")
        return redirect(url_for("main.student_dashboard"))

    return render_template("/student/survey.html", form=form)


 
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
        # Handle None values properly by providing default empty string and strip
        student_answer = request.form.get("answer", "").strip()
        question_data = session.get(f"question_data_{part}_{q_num}")

        # Safety check for missing question data
        if not question_data or "answer" not in question_data or "question" not in question_data:
            flash("Error: Question data not found or is incomplete.", "danger")
            return redirect(url_for("main.student_dashboard"))

        correct_answer = question_data.get("answer", "")
        question_text = question_data.get("question", "")

        # Debugging prints (now safe from AttributeError)
        print("student_answer:", student_answer)
        print("correct_answer:", correct_answer)

        # Safely evaluate the answer
        correct = ai_evaluate_answer(student_answer, correct_answer, part, question_text)

        # Save score in session
        session[part + "_score"] = session.get(part + "_score", 0) + (1 if correct else 0)

        # Determine next question or part
        if q_num < 5:
            next_q = q_num + 1
            # Simplified difficulty logic
            if q_num == 1:
                next_diff = "easy"
            elif q_num in [2, 3]:
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
    if not question_data or "error" in question_data:
        flash(question_data.get("error", "Failed to generate question."), "danger")
        return redirect(url_for("main.student_dashboard"))

    # Store the question and its answer in the session
    session[f"question_data_{part}_{q_num}"] = question_data

    return render_template(
        "/student/test_part.html",
        part=part.capitalize(),
        q_num=q_num,
        **question_data
    )


# ------------------Display final results------------------
@main.route("/results")
@login_required
def test_results():
    # --- Get test scores ---
    numbers_score = session.get("numbers_score", 0)
    logic_score = session.get("logic_score", 0)
    shapes_score = session.get("shapes_score", 0)
    max_test_score = 5  # per section

    # --- Invert test score for risk ---
    test_risk_score = (max_test_score * 3) - (numbers_score + logic_score + shapes_score)

    # --- Load survey scores ---
    survey = StudentSurvey.query.filter_by(student_id=current_user.id).first()
    survey_scores = {}
    survey_struggles = []
    if survey:
        survey_scores = json.loads(survey.survey_data)
        for key, value in survey_scores.items():
            if value > 0:
                survey_struggles.append(key.replace("_", " ").capitalize())

    # --- Identify low-performing test sections ---
    low_test_sections = []
    if numbers_score < 3:
        low_test_sections.append("Numbers")
    if logic_score < 3:
        low_test_sections.append("Logic")
    if shapes_score < 3:
        low_test_sections.append("Shapes")

    # --- Combine risk areas ---
    risk_areas = set(low_test_sections + survey_struggles)

    # --- Combine risk score ---
    total_survey_score = sum(survey_scores.values()) if survey_scores else 0
    combined_risk_score = test_risk_score + total_survey_score

    # --- Determine likelihood ---
    if combined_risk_score >= 15:
        likelihood = "High"
        message = f"You may need extra support in: {', '.join(risk_areas)}. A staff member will review your results."
    elif combined_risk_score >= 8:
        likelihood = "Moderate"
        message = f"You show some areas that could use support: {', '.join(risk_areas)}. Staff may follow up if needed."
    else:
        likelihood = "Low"
        message = "Your results are within the expected range. Keep up the good work!"

    # --- Save result to DB ---
    test_result = TestResult(
        student_id=current_user.id,
        numbers_score=numbers_score,
        logic_score=logic_score,
        shapes_score=shapes_score,
        disability_likelihood=likelihood,
        outcome_message=message,
        staff_breakdown={
            "test_scores": {
                "numbers": numbers_score,
                "logic": logic_score,
                "shapes": shapes_score
            },
            "survey_scores": survey_scores
        }
    )
    db.session.add(test_result)
    db.session.commit()

    # --- Clear session ---
    session.pop("numbers_score", None)
    session.pop("logic_score", None)
    session.pop("shapes_score", None)

    return render_template(
        "/student/test_results.html",
        numbers_score=numbers_score,
        logic_score=logic_score,
        shapes_score=shapes_score,
        total_test_score=numbers_score + logic_score + shapes_score,
        total_survey_score=total_survey_score,
        combined_risk_score=combined_risk_score,
        likelihood=likelihood,
        message=message
    )

@main.route("/exercises", methods=["GET", "POST"])
@login_required
def exercises():
    part = request.args.get("part")
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

    return render_template("exercises.html", question=question_text, part=part)


#--------------------Staff Dashboard--------------------
@main.route("/staff_dashboard")
@login_required
def staff_dashboard():
    user = current_user

    # Admin sees all students
    if user.is_admin:
        students_query = Student.query.all()
        total_staff = Staff.query.count()
    else:
        links = StaffStudentLink.query.filter_by(staff_id=user.id).all()
        students_query = [link.student for link in links]
        total_staff = None

    total_students = len(students_query)

    # Precompute student stats to avoid ORM calls in template
    students = []
    total_exercises = Exercise.query.count()

    for student in students_query:
        # Exercises progress
        completed_count = len(student.exercises_completed)
        if completed_count == 0:
            exercises_progress = "Not Started"
        elif completed_count < total_exercises:
            exercises_progress = "In Progress"
        else:
            exercises_progress = "Completed"

        # Test progress
        test_results = student.test_results
        if not test_results:
            test_progress = "Not Taken"
        elif all(result.staff_views for result in test_results):
            test_progress = "Reviewed"
        else:
            test_progress = "Pending Review"

        # Flagged students
        flagged = any(result.disability_likelihood == "high" for result in test_results) if test_results else False

        # Assigned staff names (for admin)
        assigned_staff = [link.staff.name for link in student.staff_links] if user.is_admin else None

        students.append({
            "id": student.id,
            "name": student.name,
            "student_email": student.student_email,
            "created_at": student.created_at,
            "exercises_progress": exercises_progress,
            "test_progress": test_progress,
            "flagged": flagged,
            "assigned_staff": assigned_staff
        })

    # Count exercises in progress
    exercises_in_progress = sum(1 for s in students if s["exercises_progress"] == "In Progress")

    # Count tests pending review
    tests_pending_review = sum(1 for s in students if s["test_progress"] == "Pending Review")

    # Count flagged students
    flagged_students = sum(1 for s in students if s["flagged"])

    return render_template(
        "/staff/staff_dashboard.html",
        user=user,
        students=students,
        total_students=total_students,
        total_staff=total_staff,
        exercises_in_progress=exercises_in_progress,
        tests_pending_review=tests_pending_review,
        flagged_students=flagged_students
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
    return render_template("/staff/manage_staff.html", staff_list=staff_list)



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

    return render_template("/staff/add_staff.html", form=form)
 

   
#-------------------- Edit Staff (admin only)--------------------
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

    return render_template("/staff/edit_staff.html", staff=staff_member)



#-------------------- Delete Staff (admin only)--------------------
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



#-------------------Assign Staff to Students (admin only)-------------------
@main.route('/assign_staff', methods=['GET', 'POST'])
@login_required
def assign_staff():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('main.staff_dashboard'))

    form = AssignStaffForm()
    form.staff.choices = [(s.id, s.name) for s in Staff.query.all()]

    # Only include students who might need staff (optional automation)
    students = Student.query.all()
    active_students = []
    for student in students:
        # Skip students who completed all exercises and have all tests reviewed
        def all_tests_reviewed(student):
            results = student.test_results
            return all(len(result.staff_views) > 0 for result in results)
        
        if len(student.exercises_completed) < Exercise.query.count() or not all_tests_reviewed(student):
            active_students.append(student)
        else:
            # Remove from any existing staff assignment
            StaffStudentLink.query.filter_by(student_id=student.id).delete()
    db.session.commit()

    form.students.choices = [(s.id, s.name) for s in active_students]

    if form.validate_on_submit():
        staff = Staff.query.get(form.staff.data)
        selected_student_ids = form.students.data

        # Remove any previous links for this staff
        StaffStudentLink.query.filter_by(staff_id=staff.id).delete()

        # Create new links
        for student_id in selected_student_ids:
            link = StaffStudentLink(staff_id=staff.id, student_id=student_id)
            db.session.add(link)

        db.session.commit()
        flash(f"Assigned {len(selected_student_ids)} student(s) to {staff.name}", "success")
        return redirect(url_for('main.staff_dashboard'))

    return render_template('/staff/assign_staff.html', form=form)



#--------------------Review Deletion Requests (admin only)--------------------
@main.route("/review_deletion_requests")
@login_required 
def review_deletion_requests(): 
    if not getattr(current_user, "is_admin", False):
        flash("Access denied!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    requests = DeletionRequest.query.filter_by(status="Pending").all()
    return render_template("/staff/review_deletion_requests.html", requests=requests)



#--------------------Handle Deletion Request (admin only)--------------------
@main.route("/handle_deletion_request/<int:request_id>/<string:action>")
@login_required
def handle_deletion_request(request_id, action):
    if not getattr(current_user, "is_admin", False):
        flash("Access denied!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    deletion_request = DeletionRequest.query.get_or_404(request_id)

    if action == "approve":
        # Mark request as approved BEFORE deleting the student
        deletion_request.status = "Approved"
        deletion_request.reviewed_by_id = current_user.id
        deletion_request.reviewed_at = datetime.utcnow()

        student = Student.query.get(deletion_request.student_id)
        if student:
            db.session.delete(student)

    elif action == "reject":
        deletion_request.status = "Rejected"
        deletion_request.reviewed_by_id = current_user.id
        deletion_request.reviewed_at = datetime.utcnow()
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for("main.review_deletion_requests"))

    db.session.commit()

    flash(f"Request {action}d successfully.", "success")
    return redirect(url_for("main.review_deletion_requests"))





 


#--------------------Manage Students (staff only)--------------------
@main.route("/manage_students")
@login_required
def manage_students():
    # Only logged-in staff/admin can access
    if not hasattr(current_user, "id"):
        flash("Access denied!", "danger") 
        return redirect(url_for("main.login"))

    # Optional: show all students (admins) or assigned students (if you implement assignments)
    students = Student.query.all()

    return render_template("/staff/manage_students.html", students=students)
 
 

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

    return render_template("/staff/edit_student.html", student=student)



#--------------------Delete Student (staff only)--------------------
@main.route("/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("main.manage_students"))


  
#-------------------staff view individual student results-------------------
@main.route("/staff/student/<int:student_id>/results")
@login_required
def staff_view_student_results(student_id):
    if not isinstance(current_user, Staff):
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.index"))

    student = Student.query.get_or_404(student_id)
    results = student.test_results  # use relationship

    # Avoid duplicate views
    for result in results:
        if not TestResultStaffView.query.filter_by(
            staff_id=current_user.id, test_result_id=result.id
        ).first():
            view = TestResultStaffView(staff_id=current_user.id, test_result_id=result.id)
            db.session.add(view)
    db.session.commit()

    return render_template("/staff/staff_view_results.html", student=student, results=results)

 

#-------------------staff request deletion of student-------------------
@main.route("/request_delete_student/<int:student_id>", methods=["GET", "POST"])
@login_required
def request_delete_student(student_id):
    if not isinstance(current_user, Staff) or current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for("main.manage_students"))

    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        reason = request.form.get("reason")
        if not reason:
            flash("You must provide a reason for deletion.", "warning")
            return redirect(request.url)

        # Create deletion request
        new_request = DeletionRequest(
            student_id=student.id,
            requested_by_id=current_user.id,
            reason=reason
        )
        db.session.add(new_request)
        db.session.commit()

        flash("Deletion request submitted to admin for approval.", "success")
        return redirect(url_for("main.manage_students"))

    return render_template("/staff/request_delete_student.html", student=student)

 

#-------------------staff view individual student surveys-------------------
@main.route("/staff/student/<int:student_id>/surveys")
@login_required
def staff_view_student_surveys(student_id):
    if not isinstance(current_user, Staff):
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.index"))

    student = Student.query.get_or_404(student_id)
    surveys = StudentSurvey.query.filter_by(student_id=student.id).all()

    import json
    for survey in surveys: 
        # convert from str to dict if needed 
        if isinstance(survey.survey_data, str):
            survey.survey_data = json.loads(survey.survey_data)
        
        # Convert numeric values to readable form
        readable_data = {} 
        for key, value in survey.survey_data.items():
            if value == 1:
                readable_data[key] = "Struggle"
            else:
                readable_data[key] = "No struggle"
        survey.readable_data = readable_data  # attach new attribute for template

        # log staff view
        if not any(view.staff_id == current_user.id for view in survey.staff_views):
            view = StudentSurveyStaffView(staff_id=current_user.id, survey_id=survey.id)
            db.session.add(view)

    db.session.commit()
    return render_template("/staff/staff_view_surveys.html", student=student, surveys=surveys)

 
 
 
#-------------------staff view individual student exercises-------------------
@main.route("/staff/student/<int:student_id>/exercises")
@login_required
def staff_view_student_exercises(student_id):
    student = Student.query.get_or_404(student_id)
    exercises = Exercise.query.all()  # could also filter by exercises completed by this student
    completed_ex_ids = [ex.exercise_id for ex in student.exercises_completed]

    return render_template(
        "/staff/staff_view_student_exercises.html",
        student=student,
        exercises=exercises,
        completed_ex_ids=completed_ex_ids
    )




#--------------------Logout--------------------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))