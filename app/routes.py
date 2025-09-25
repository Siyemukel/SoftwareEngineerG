import json, os

from flask import Blueprint, render_template, redirect, url_for, request, session, flash, send_from_directory, current_app, abort,send_file
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from .models import *
from .extensions import db
from .services import get_next_question, ai_evaluate_answer , assign_student_to_staff,send_department_email
from .forms import  * 
from .extensions import mail  
from sqlalchemy import or_, and_
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd


main = Blueprint("main", __name__)

def setup_admin_account():
    form = StaffSignupForm()
    if form.validate_on_submit():
        try:
            new_admin = Staff(
                username=form.username.data,
                name=form.name.data,
                surname=form.surname.data,
                is_admin=True,
            )
            new_admin.set_password(form.password.data)
            
            db.session.add(new_admin)
            db.session.commit()

            print("Admin account created successfully! Please log in.", "success")
            return redirect(url_for("main.home"))

        except IntegrityError:
            db.session.rollback()
            print("That username is already taken. Please choose another.", "danger")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}", "danger")

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
            print("Email already registered!", "danger")
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

        print("Account created successfully!", "success")

        student = Student.query.filter_by(student_email=email).first()
        if student and student.check_password(password):
            login_user(student)

            survey_exists = StudentSurvey.query.filter_by(student_id=student.id).first()

            if not survey_exists:
                return redirect(url_for("main.student_onboarding"))

            print("Signed in as student!", "success")
            return redirect(url_for("main.student_dashboard"))
        
        return redirect(url_for("main.student_dashboard"))

    return render_template("auth/signup.html", form=form)

def login_user_account():
    username_or_email = request.form.get("username")
    password = request.form.get("password")

    # --- Check student login ---
    student = Student.query.filter_by(student_email=username_or_email).first()
    if student and student.check_password(password):
        login_user(student)

        # Check if the student has done the survey
        survey_exists = StudentSurvey.query.filter_by(student_id=student.id).first()

        if not survey_exists:
            # New student: force onboarding -> survey
            flash("Welcome! Let's get started with onboarding.", "info")
            return redirect(url_for("main.student_onboarding"))

        # Survey exists: straight to dashboard
        flash(f"Welcome back, {student.name}!", "success")
        return redirect(url_for("main.student_dashboard"))

    # --- Check staff login ---
    staff = Staff.query.filter_by(username=username_or_email).first()
    if staff and staff.check_password(password):
        login_user(staff)
        flash(f"Logged in as {staff.name}!", "success")
        return redirect(url_for("main.staff_dashboard"))

    # Invalid credentials
    flash("Invalid credentials, please try again.", "danger")
    return redirect(url_for("main.login"))




@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_path = os.path.join(current_app.root_path, '..', 'uploads')
    return send_from_directory(upload_path, filename)



#------------ Messaging / Chat ------------- #
@main.route("/messages/<int:student_id>/<int:staff_id>")
@login_required
def conversation(student_id, staff_id):
   
    is_student_user = (hasattr(current_user, "student_email") and current_user.id == student_id)
    is_staff_user = (hasattr(current_user, "name") and current_user.id == staff_id)
    is_admin_user = getattr(current_user, "is_admin", False)

    if not (is_student_user or is_staff_user or is_admin_user):
        abort(403)  


    student = Student.query.get(student_id)
    staff = Staff.query.get(staff_id)
    if not student or not staff:
        abort(404)

    Message.query.filter(
        or_(
            and_(
                Message.sender_type == "staff",
                Message.sender_id == staff_id,
                Message.receiver_type == "student",
                Message.receiver_id == student_id
            ),
            and_(
                Message.sender_type == "student",
                Message.sender_id == student_id,
                Message.receiver_type == "staff",
                Message.receiver_id == staff_id
            )
        ),
        Message.is_read == False
    ).update({"is_read": True})
    db.session.commit()

  
    messages = Message.query.filter(
        or_(
            and_(
                Message.sender_id == student_id,
                Message.receiver_id == staff_id
            ),
            and_(
                Message.sender_id == staff_id,
                Message.receiver_id == student_id
            )
        )
    ).order_by(Message.timestamp.asc()).all()

    return render_template(
        "conversation.html",
        student=student,
        staff=staff,
        student_id=student_id,
        staff_id=staff_id,
        messages=[m.to_dict() for m in messages]
    )


#------------ Notifications creation ------------- #
def create_notification(message, student_id=None, staff_id=None, notify_admins=True):
    # Notify a specific student
    if student_id:
        db.session.add(Notification(student_id=student_id, message=message, notification_type="system"))

    # Notify a specific staff member
    if staff_id:
        db.session.add(Notification(staff_id=staff_id, message=message, notification_type="system"))

    # Notify all admins
    if notify_admins:
        admins = Staff.query.filter_by(is_admin=True).all()
        for admin in admins:
            db.session.add(Notification(admin_id=admin.id, message=message, notification_type="system"))

    db.session.commit()


#------------ Inject unread notification count into templates ------------- #
@main.context_processor
def inject_notifications():
    unread_count = 0
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        unread_count = Notification.query.filter_by(admin_id=current_user.id, is_read=False).count()
    elif hasattr(current_user, "id") and hasattr(current_user, "staff_role"):  # regular staff
        unread_count = Notification.query.filter_by(staff_id=current_user.id, is_read=False).count()
    elif hasattr(current_user, "student_email"):  # student
        unread_count = Notification.query.filter_by(student_id=current_user.id, is_read=False).count()
    return dict(unread_notifications=unread_count)


#------------ Notifications read------------- #
@main.route("/notifications/mark_read", methods=["POST"])
@login_required
def mark_notifications_read():
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        Notification.query.filter_by(admin_id=current_user.id, is_read=False).update({"is_read": True})
    elif hasattr(current_user, "staff_role"):
        Notification.query.filter_by(staff_id=current_user.id, is_read=False).update({"is_read": True})
    elif hasattr(current_user, "student_email"):
        Notification.query.filter_by(student_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return ("", 204)





@main.route("/", methods=["GET", "POST"]) 
def home():
    if not Staff.query.first():
        return setup_admin_account()

    if current_user.is_authenticated:
        if isinstance(current_user, Student):
            return redirect(url_for("main.student_dashboard"))
        elif isinstance(current_user, Staff):
            return redirect(url_for("main.staff_dashboard"))

    return render_template("home.html")


# ------------  Authentication  ------------ #
@main.route("/signup", methods=["GET", "POST"])
def signup():
    if not Staff.query.first():
        return setup_admin_account()
    
    return setup_student_account()


#login page for all memebers
@main.route("/login", methods=["GET", "POST"])
def login():
    if not Staff.query.first():
        return setup_admin_account()
    elif request.method == "POST":
        response = login_user_account()

        if response:
            return response

    return render_template("/auth/login.html")


@main.route("/student/onboarding", methods=["GET", "POST"])
@login_required
def student_onboarding():
    if not isinstance(current_user, Student):
        flash("Access denied!", "danger")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        # After onboarding, redirect student to survey
        return redirect(url_for("main.survey"))

    # Render onboarding page for new students
    return render_template("/student/student_onboarding.html", student=current_user)



   

#--------------------Student Dashboard--------------------
@main.route("/student_dashboard", methods=["GET", "POST"])
@login_required
def student_dashboard():
    # 1. Fetch the full Student object from the database, as current_user is a proxy.
    student = Student.query.get(current_user.id)
    
    if not student:
        # Redirect to logout if the student object isn't found in the database.
        return redirect(url_for('auth.logout'))

    # 2. Get the latest test results for the student.
    student_results = TestResult.query.filter_by(student_id=student.id)\
                                    .order_by(TestResult.created_at.desc()).first()

    # 3. Find the assigned staff member's ID from the StaffStudentLink table.
    assigned_staff_link = StaffStudentLink.query.filter_by(student_id=student.id).first()
    
    assigned_staff_id = None
    if assigned_staff_link:
        assigned_staff_id = assigned_staff_link.staff_id

    # 4. Fetch the messages for the conversation if a staff member is assigned.
    messages_data = []
    if assigned_staff_id:
        msgs = Message.query.filter(
            ((Message.sender_type == 'student') & (Message.sender_id == student.id) & (Message.receiver_type == 'staff') & (Message.receiver_id == assigned_staff_id)) |
            ((Message.sender_type == 'staff') & (Message.sender_id == assigned_staff_id) & (Message.receiver_type == 'student') & (Message.receiver_id == student.id))
        ).order_by(Message.timestamp.asc()).all()
        
        # Convert messages to a list of dictionaries for the template.
        messages_data = [m.to_dict() for m in msgs]
    
    # 5. Prepare data for the charts and other dashboard elements.
    #    Use the fetched student_results; provide defaults if none exist.
    numbers_score = student_results.numbers_score if student_results else 0
    logic_score = student_results.logic_score if student_results else 0
    shapes_score = student_results.shapes_score if student_results else 0
    
    disability_likelihood = student_results.disability_likelihood if student_results else 'low'
    
    numbers_time = student_results.numbers_time if student_results and hasattr(student_results, 'numbers_time') else 0
    logic_time = student_results.logic_time if student_results and hasattr(student_results, 'logic_time') else 0
    shapes_time = student_results.shapes_time if student_results and hasattr(student_results, 'shapes_time') else 0

    student_scores = {'numbers': numbers_score, 'logic': logic_score, 'shapes': shapes_score}
    test_times = {'numbers': numbers_time, 'logic': logic_time, 'shapes': shapes_time}

    # 6. Pass all the prepared data to the template.
    return render_template(
        "student/student_dashboard.html",
        student=student,
        student_results=student_results,
        messages=messages_data,
        assigned_staff_id=assigned_staff_id,  # Pass the staff ID for the chat link
        studentScores=student_scores,         # Data for the chart script
        studentLikelihood=disability_likelihood, # Data for the chart script
        testTimes=test_times                  # Data for the chart script
    )

 
#--------------------Student Survey--------------------
@main.route("/survey", methods=["GET", "POST"])
@login_required
def survey():
    # Ensure only students access
    if not hasattr(current_user, "student_email"):
        print("Access denied!", "danger")
        return redirect(url_for("main.home"))

    # Check if survey already submitted
    if StudentSurvey.query.filter_by(student_id=current_user.id).first():
        print("You have already submitted the survey.", "info")
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

        print("Survey submitted successfully!", "success")
        return redirect(url_for("main.student_dashboard"))

    return render_template("/student/survey.html", form=form)


 
#--------------------Start Test (students only)--------------------
@main.route("/start_test")
@login_required
def start_test():
    # Check if student already has a test result
    existing_test = TestResult.query.filter_by(student_id=current_user.id).first()
    if existing_test:
        print("You have already completed the test.", "info")
        return redirect(url_for("main.student_dashboard"))

    # Redirect to first test part: Numbers
    return redirect(url_for("main.test_part", part="numbers", difficulty="easy", q_num=1))
 
 
        
#--------------------Test Parts (students only)--------------------
@main.route("/test/<part>/<int:q_num>/<difficulty>", methods=["GET", "POST"])
@login_required
def test_part(part, q_num, difficulty):
    if part not in ["numbers", "logic", "shapes"]:
        print("Invalid test part.", "danger")
        return redirect(url_for("main.student_dashboard"))

    # POST: process student's answer
    if request.method == "POST": 
        # Handle None values properly by providing default empty string and strip
        student_answer = request.form.get("answer", "").strip()
        question_data = session.get(f"question_data_{part}_{q_num}")

        # Safety check for missing question data
        if not question_data or "answer" not in question_data or "question" not in question_data:
            print("Error: Question data not found or is incomplete.", "danger")
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
        print(question_data.get("error", "Failed to generate question."), "danger")
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


#--------------------Exercises (students only)--------------------
@main.route("/exercises/<part>", methods=["GET", "POST"])
@login_required
def exercises(part):
    # Retrieve current difficulty and question number from session, or set defaults
    difficulty = session.get("exercise_difficulty", "easy")
    q_num = session.get("exercise_q_num", 1)

    # If the user is submitting an answer
    if request.method == "POST":
        student_answer = request.form.get("answer")
        # Retrieve the correct answer from the session to evaluate
        correct_answer = session.get("correct_answer")
        question_text = session.get("question_text")
        
        if not correct_answer:
            flash("Error: No question data found. Please restart the exercise.", "danger")
            return redirect(url_for("main.student_dashboard"))

        # NOTE: ai_evaluate_answer and get_next_question must be imported or defined elsewhere
        is_correct = ai_evaluate_answer(student_answer, correct_answer, part, question_text)

        if is_correct:
            flash("Correct! Great job!", "success")
            
            # 1. Log the dynamically generated exercise to the database
            # Ensure `Exercise` and `db` are imported
            new_exercise = Exercise(
                title=f"AI-generated {part} exercise",
                description=question_text,
                video_link=None, # You can add a link if your AI generates one
                part=part.capitalize(),
                approved=False # Since it's AI-generated, it's not pre-approved
            )
            db.session.add(new_exercise)
            db.session.commit()

            # 2. Now log the ExerciseCompletion with the new exercise ID
            # Ensure `ExerciseCompletion` is imported
            new_completion = ExerciseCompletion(
                student_id=current_user.id,
                exercise_id=new_exercise.id
            )
            db.session.add(new_completion)
            
            # Increment the question number and commit the session
            session["exercise_q_num"] = q_num + 1
            db.session.commit()
            
            return redirect(url_for("main.exercises", part=part))
        else:
            flash(f"Incorrect. The correct answer was: {correct_answer}.", "warning")
            # For incorrect answers, don't increment q_num, allow a retry
            return redirect(url_for("main.exercises", part=part))

    # For a GET request, generate a new question
    # Ensure `get_next_question` is imported
    exercise_data = get_next_question(part, difficulty=difficulty, q_num=q_num)
    
    if "error" in exercise_data:
        flash(f"Could not generate an exercise: {exercise_data['error']}", "danger")
        return redirect(url_for("main.student_dashboard"))

    # Store question data in the session for later evaluation
    session["question_text"] = exercise_data["question"]
    session["correct_answer"] = exercise_data["answer"]

    # Render the exercises template
    return render_template(
        "exercises.html",
        part=part,
        question=exercise_data["question"],
        options=exercise_data.get("options"),
        shape_image=exercise_data.get("shape_image")
    )


 
#--------------------Upload Medical Proof (students only)--------------------

@main.route("/upload_medical_proof", methods=["GET", "POST"])
@login_required
def upload_medical_proof():
    form = MedicalProofForm()
    if form.validate_on_submit():
        try:
            file = form.medical_file.data
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(upload_path)

            # Assign student to staff (skip admins)
            assigned_staff = assign_student_to_staff(current_user)

            # Create the MedicalProof record
            proof = MedicalProof(
                student_id=current_user.id,
                file_name=filename,
                file_path=upload_path,
                status="pending",
                assigned_staff_id=assigned_staff.id if assigned_staff else None
            )
            db.session.add(proof)
            db.session.commit()

            if assigned_staff:
                flash(f"Medical proof uploaded and assigned to {assigned_staff.name} {assigned_staff.surname}!", "success")
            else:
                flash("Medical proof uploaded but no staff are currently available.", "warning")

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while uploading: {str(e)}", "danger")
            return render_template("student/upload_medical_proof.html", form=form)

        return redirect(url_for("main.student_dashboard"))

    return render_template("student/upload_medical_proof.html", form=form)





  



#--------------------Staff Dashboard--------------------
@main.route("/staff_dashboard")
@login_required
def staff_dashboard():
    user = current_user

 
    unread_notifications = Notification.query.filter(
        ((Notification.staff_id == user.id) |
         (Notification.admin_id == user.id) |
         (Notification.student_id == user.id)),
        Notification.is_read == False
    ).count()
    Notification.query.filter_by(staff_id=user.id, is_read=False).update({"is_read": True})

 
    if getattr(user, "is_admin", False):
        students_query = Student.query.all()
        total_staff = Staff.query.count()
    else:
        links = StaffStudentLink.query.filter_by(staff_id=user.id).all()
        students_query = [link.student for link in links]
        total_staff = None

    total_students = len(students_query)
    total_exercises = Exercise.query.count()

    students = []
    unread_per_student = {}

    for student in students_query:
      
        completed_count = len(student.exercises_completed)
        if completed_count == 0:
            exercises_progress = "Not Started"
        elif completed_count < total_exercises:
            exercises_progress = "In Progress"
        else:
            exercises_progress = "Completed"


        test_results = student.test_results
        if not test_results:
            test_progress = "Not Taken"
        elif all(result.staff_views for result in test_results):
            test_progress = "Reviewed"
        else:
            test_progress = "Pending Review"

        flagged = any(result.disability_likelihood == "high" for result in test_results) if test_results else False


        assigned_staff = [link.staff.name for link in student.staff_links] if getattr(user, "is_admin", False) else None


        unread_count = Message.query.filter_by(
            sender_id=student.id,
            receiver_id=user.id,
            is_read=False
        ).count()
        unread_per_student[student.id] = unread_count

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

    exercises_in_progress = sum(1 for s in students if s["exercises_progress"] == "In Progress")
    tests_pending_review = sum(1 for s in students if s["test_progress"] == "Pending Review")
    flagged_students = sum(1 for s in students if s["flagged"])

    return render_template(
        "/staff/staff_dashboard.html",
        user=user,
        students=students,
        total_students=total_students,
        total_staff=total_staff,
        exercises_in_progress=exercises_in_progress,
        tests_pending_review=tests_pending_review,
        flagged_students=flagged_students,
        unread_notifications=unread_notifications,  
        unread_per_student=unread_per_student       
    )



#--------------------Profile Management for Staff/Admin--------------------
@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name")
        current_user.surname = request.form.get("surname")
        current_user.username = request.form.get("username")

        # Handle password update (with confirm check)
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password:
            if password != confirm_password:
                flash("Passwords do not match. Please try again.", "danger")
                return redirect(url_for("main.profile"))
            current_user.password_hash = generate_password_hash(password)

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "danger")

        return redirect(url_for("main.profile"))

    return render_template("/staff/staff_profile.html", user=current_user)



#------Notification Settings for staff------
@main.route("/notification_settings", methods=["GET", "POST"])
@login_required
def notification_settings():
    if not getattr(current_user, "is_admin", False):
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    notifications = NotificationSettings.query.all()

    if request.method == "POST":
        for notification in notifications:
            # Checkbox values will exist only if checked
            notification.enabled = bool(request.form.get(f"enabled_{notification.id}"))
            notification.method_email = bool(request.form.get(f"email_{notification.id}"))
            notification.method_dashboard = bool(request.form.get(f"dashboard_{notification.id}"))
        try:
            db.session.commit()
            flash("Notification settings updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {e}", "danger")
        return redirect(url_for("main.notification_settings"))

    return render_template("/staff/staff_notification_settings.html", notifications=notifications)


#--------------------For managing staff accounts (admin only)------------------
@main.route("/manage_staff", methods=["GET", "POST"])
@login_required
def manage_staff():
    # Only allow admins
    if not getattr(current_user, "is_admin", False):
        print("You are not authorized to view this page.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    staff_list = Staff.query.all()  # Fetch all staff members
    return render_template("/staff/manage_staff.html", staff_list=staff_list)



#-------------------For adding new staff accounts (admin only)------------------
@main.route("/add_staff", methods=["GET", "POST"])
@login_required
def add_staff():
    # Only allow admins
    if not getattr(current_user, "is_admin", False):
        print("You are not authorized to add staff.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    form = StaffSignupForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_staff = Staff.query.filter_by(username=form.username.data).first()
        if existing_staff:
            print("Username already taken. Please choose another.", "danger")
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

        print("Staff member added successfully!", "success")
        return redirect(url_for("main.manage_staff"))

    return render_template("/staff/add_staff.html", form=form)
 

   
#-------------------- Edit Staff (admin only)--------------------
@main.route("/edit_staff/<int:staff_id>", methods=["GET", "POST"])
@login_required
def edit_staff(staff_id):
    # Only admin should edit staff
    if not getattr(current_user, "is_admin", False):
        print("You do not have permission to edit staff!", "danger")
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
            print("Staff updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating staff: {e}", "danger")

        return redirect(url_for("main.staff_dashboard"))

    return render_template("/staff/edit_staff.html", staff=staff_member)



#-------------------- Delete Staff (admin only)--------------------
@main.route("/delete_staff/<int:staff_id>", methods=["POST"])
@login_required
def delete_staff(staff_id):
    if not getattr(current_user, "is_admin", False):
        print("You do not have permission to delete staff!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    staff_member = Staff.query.get_or_404(staff_id)

    try: 
        db.session.delete(staff_member)
        db.session.commit()
        print("Staff deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting staff: {e}", "danger")

    return redirect(url_for("main.manage_staff"))


#--------------------Report Settings (admin only)--------------------
@main.route("/report_settings", methods=["GET", "POST"])
@login_required
def report_settings():
    if not getattr(current_user, "is_admin", False):
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    # Get current settings or create default
    settings = ReportSettings.query.first()
    if not settings:
        settings = ReportSettings()
        db.session.add(settings)
        db.session.commit()

    form = ReportSettingsForm(obj=settings)

    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash("Report settings updated successfully!", "success")
        return redirect(url_for("main.staff_dashboard"))

    return render_template("/staff/admin_report_settings.html", form=form)
 


#--------------------Review Medical Proof Applications (staff only)--------------------
"""
@main.route("/staff/applications", methods=["GET"])
@login_required
def staff_applications():
    # More robust check for staff permissions
    if not hasattr(current_user, "students") and not getattr(current_user, "is_staff", False):
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    # Get all medical proofs assigned to this staff and pending review
    assigned_proofs = (
        MedicalProof.query
        .join(StaffStudentLink, StaffStudentLink.student_id == MedicalProof.student_id)
        .join(Student, Student.id == MedicalProof.student_id)  # Join to get student info
        .filter(StaffStudentLink.staff_id == current_user.id)
        .filter(MedicalProof.status == "pending")
        .order_by(MedicalProof.uploaded_at.desc())  # Most recent first
        .all()
    )
    
    return render_template("staff/staff_applications.html", applications=assigned_proofs)

"""

@main.route("/staff/applications", methods=["GET"])
@login_required
def staff_applications():
    if not hasattr(current_user, "students") and not getattr(current_user, "is_admin", False):
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    print(f"\n=== STAFF APPLICATIONS DEBUG ===")
    print(f"Current staff: {current_user.name} (ID: {current_user.id})")
    
    # Check how many students are assigned to this staff
    assigned_count = StaffStudentLink.query.filter_by(staff_id=current_user.id).count()
    print(f"Students assigned to this staff: {assigned_count}")
    
    # Get assigned students
    assigned_students = db.session.query(Student)\
        .join(StaffStudentLink)\
        .filter(StaffStudentLink.staff_id == current_user.id)\
        .all()
    
    print(f"Assigned students: {[s.name for s in assigned_students]}")
    
    # Get medical proofs for assigned students
    assigned_proofs = (
        MedicalProof.query
        .join(StaffStudentLink, StaffStudentLink.student_id == MedicalProof.student_id)
        .join(Student, Student.id == MedicalProof.student_id)
        .filter(StaffStudentLink.staff_id == current_user.id)
        .filter(MedicalProof.status == "pending")
        .order_by(MedicalProof.uploaded_at.desc())
        .all()
    )
    
    
    return render_template("staff/staff_applications.html", applications=assigned_proofs)




#--------------------Review Individual Medical Proof Application (staff only)--------------------
@main.route("/staff/application/<int:proof_id>", methods=["GET", "POST"])
@login_required
def review_medical_proof(proof_id):
    proof = MedicalProof.query.get_or_404(proof_id)

    # Check if the proof is assigned to this staff
    if proof.assigned_staff_id != current_user.id:
        flash("You are not authorized to review this application.", "danger")
        return redirect(url_for("main.staff_applications"))

    if request.method == "POST":
        action = request.form.get("action")
        reason = request.form.get("reason", "").strip()

        try:
            if action == "approve":
                proof.status = "approved"
                proof.rejection_reason = None
                flash("Application approved successfully!", "success")
            elif action == "reject":
                if not reason:
                    flash("Rejection reason is required.", "danger")
                    return render_template("staff/review_medical_proof.html", proof=proof)

                proof.status = "rejected"
                proof.rejection_reason = reason
                flash("Application rejected.", "info")
            else:
                flash("Invalid action.", "danger")
                return render_template("staff/review_medical_proof.html", proof=proof)

            proof.reviewed_by_id = current_user.id
            proof.reviewed_at = datetime.now()
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template("staff/review_medical_proof.html", proof=proof)

        return redirect(url_for("main.staff_applications"))

    return render_template("staff/review_medical_proof.html", proof=proof)


 
#--------------------Review Deletion Requests (admin only)--------------------
@main.route("/review_deletion_requests")
@login_required 
def review_deletion_requests(): 
    if not getattr(current_user, "is_admin", False):
        print("Access denied!", "danger")
        return redirect(url_for("main.staff_dashboard"))

    requests = DeletionRequest.query.filter_by(status="Pending").all()
    return render_template("/staff/review_deletion_requests.html", requests=requests)



#--------------------Handle Deletion Request (admin only)--------------------
@main.route("/handle_deletion_request/<int:request_id>/<string:action>")
@login_required
def handle_deletion_request(request_id, action):
    if not getattr(current_user, "is_admin", False):
        print("Access denied!", "danger")
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
        print("Invalid action.", "danger")
        return redirect(url_for("main.review_deletion_requests"))

    db.session.commit()

    print(f"Request {action}d successfully.", "success")
    return redirect(url_for("main.review_deletion_requests"))



#--------------------Manage Students (staff only)--------------------
@main.route("/manage_students")
@login_required
def manage_students():
    # Only logged-in staff/admin can access
    if not hasattr(current_user, "id"):
        print("Access denied!", "danger") 
        return redirect(url_for("main.login"))

    # Admin sees all students
    if getattr(current_user, "is_admin", False):
        students = Student.query.all()
    else:
        # Staff sees only students assigned to them
        assigned_links = StaffStudentLink.query.filter_by(staff_id=current_user.id).all()
        student_ids = [link.student_id for link in assigned_links]
        students = Student.query.filter(Student.id.in_(student_ids)).all()

    return render_template("/staff/manage_students.html", students=students, user=current_user)

 
   
 
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
        print("Student updated successfully!", "success")
        return redirect(url_for("main.manage_students"))

    return render_template("/staff/edit_student.html", student=student)



#--------------------Delete Student (staff only)--------------------
@main.route("/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    print("Student deleted successfully!", "success")
    return redirect(url_for("main.manage_students"))


  
#-------------------staff view individual student results-------------------
@main.route("/staff/student/<int:student_id>/results")
@login_required
def staff_view_student_results(student_id):
    if not isinstance(current_user, Staff):
        print("Unauthorized access", "danger")
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
        print("Access denied!", "danger")
        return redirect(url_for("main.manage_students"))

    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        reason = request.form.get("reason")
        if not reason:
            print("You must provide a reason for deletion.", "warning")
            return redirect(request.url)

        # Create deletion request
        new_request = DeletionRequest(
            student_id=student.id,
            requested_by_id=current_user.id,
            reason=reason
        )
        db.session.add(new_request)
        db.session.commit()

        print("Deletion request submitted to admin for approval.", "success")
        return redirect(url_for("main.manage_students"))

    return render_template("/staff/request_delete_student.html", student=student)

 

#-------------------staff view individual student surveys-------------------
@main.route("/staff/student/<int:student_id>/surveys")
@login_required
def staff_view_student_surveys(student_id):
    if not isinstance(current_user, Staff):
        print("Unauthorized access", "danger")
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


#-------------------staff refer student to department-------------------
@main.route("/staff/student/<int:student_id>/refer_department", methods=["GET", "POST"])
@login_required
def refer_student_department(student_id):
    if not isinstance(current_user, Staff):
        return redirect(url_for("main.index"))

    student = Student.query.get_or_404(student_id)
    departments = ["Finance", "Academics", "Counselling"]

    if request.method == "POST":
        department = request.form.get("department")
        reason = request.form.get("reason")

        if not department or not reason:
            flash("You must select a department and provide a reason.", "warning")
            return redirect(request.url)

        # Create referral record
        referral = StudentReferral(
            student_id=student.id,
            referred_by_id=current_user.id,
            department=department,
            reason=reason,
            sent_to_department=True
        )
        db.session.add(referral)
        db.session.commit()

        # Pass the referral object, not strings
        send_department_email(student, referral)

        flash(f"Student referred to {department} successfully.", "success")
        return redirect(url_for("main.staff_view_student_results", student_id=student.id))

    return render_template("/staff/staff_refer_department.html", student=student, departments=departments)

  
 
@main.route("/staff/student/<int:student_id>/feedback", methods=["GET", "POST"])
@login_required
def staff_feedback(student_id):
    # Ensure only staff can access
    if not hasattr(current_user, "id") or not hasattr(current_user, "is_admin"):
        flash("Unauthorized access.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    student = Student.query.get_or_404(student_id)
    form = StaffFeedbackForm()

    if form.validate_on_submit():
        try:
            feedback = StaffFeedback(
                student_id=student.id,
                staff_id=current_user.id,
                feedback_text=form.feedback_text.data,
                progress_notes=form.progress_notes.data
            )
            db.session.add(feedback)
            db.session.commit()
            flash("Feedback submitted successfully!", "success")
            return redirect(url_for("main.staff_view_student_results", student_id=student.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("staff/staff_feedback.html", student=student, form=form)

 
#-------------------staff view individual student progress-------------------
@main.route("/staff/student/<int:student_id>")
@login_required
def staff_view_student(student_id):
    student = Student.query.get_or_404(student_id)
    exercises = ExerciseCompletion.query.filter_by(student_id=student_id).all()
    tests = TestResult.query.filter_by(student_id=student_id).all()
    surveys = StudentSurvey.query.filter_by(student_id=student_id).all()
    medical_proofs = MedicalProof.query.filter_by(student_id=student_id).all()
    referrals = StudentReferral.query.filter_by(student_id=student_id).all()

    return render_template(
        "staff/student_progress.html",
        student=student,
        exercises=exercises,
        tests=tests,
        surveys=surveys,
        medical_proofs=medical_proofs,
        referrals=referrals
    )
   


@main.route("/generate_student_report/<int:student_id>", methods=["GET"])
@login_required
def generate_student_report(student_id):
    # Only staff (non-admin) can generate student reports
    if getattr(current_user, "is_admin", False):
        flash("Admins cannot generate student reports.", "danger")
        return redirect(url_for("main.staff_dashboard"))

    # Get report settings
    settings = ReportSettings.query.first()
    if not settings:
        flash("Report settings have not been configured by admin.", "warning")
        return redirect(url_for("main.staff_dashboard"))

    # Get the student
    student = Student.query.get_or_404(student_id)

    # Prepare student data based on settings
    report_data = {}
    if settings.include_name:
        report_data["Name"] = student.name
    if settings.include_surname:
        report_data["Surname"] = student.surname
    if settings.include_student_email:
        report_data["Email"] = student.student_email
    if settings.include_course:
        report_data["Course"] = student.course
    if settings.include_year:
        report_data["Year"] = student.year_of_study
    if settings.include_faculty:
        report_data["Faculty"] = student.faculty
    if settings.include_test_results:
        test_scores = [f"{t.numbers_score}-{t.logic_score}-{t.shapes_score}" for t in student.test_results]
        report_data["Test Results"] = ", ".join(test_scores) if test_scores else "-"
    if settings.include_exercises_progress:
        exercises_done = [ex.exercise.title for ex in student.exercises_completed]
        report_data["Exercises Completed"] = ", ".join(exercises_done) if exercises_done else "-"

    # Generate PDF
    if settings.report_format.lower() == "pdf":

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y = 750

        # Header
        if settings.header_text:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, settings.header_text)
            y -= 30

        # Write student data
        for key, value in report_data.items():
            line = f"{key}: {value}"
            p.setFont("Helvetica", 10)
            p.drawString(50, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                y = 750

        # Footer
        if settings.footer_text:
            p.setFont("Helvetica-Oblique", 10)
            p.drawString(50, 30, settings.footer_text)

        p.save()
        buffer.seek(0)
        filename = f"{student.name}_{student.surname}_report.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

    # Generate Excel
    elif settings.report_format.lower() == "excel":


        buffer = BytesIO()
        df = pd.DataFrame([report_data])
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        filename = f"{student.name}_{student.surname}_report.xlsx"
        return send_file(buffer, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        flash("Unsupported report format.", "danger")
        return redirect(url_for("main.staff_dashboard"))


#--------------------Logout--------------------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    print("You have been logged out.", "success")
    return redirect(url_for("main.home"))