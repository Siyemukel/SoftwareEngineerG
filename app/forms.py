from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, SubmitField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
import re

#---- Custom validator for DUT email ----
def dut_email_check(form, field):
    pattern = r"^\d{8}@dut4life\.ac\.za$" 
    if not re.match(pattern, field.data):
        raise ValidationError("Email must be 8 digits followed by @dut4life.ac.za")


#---- Student signup form ---
#basic info
class SignupForm(FlaskForm):
    name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=50)])
    surname = StringField("Surname", validators=[DataRequired(), Length(min=2, max=50)])  
    email = StringField("Email", validators=[DataRequired(), dut_email_check])
#academic details
    course = StringField("Course", validators=[DataRequired(), Length(max=100)])
    year_of_study = StringField("Year of Study", validators=[DataRequired(), Length(min=1, max=2)])
    faculty = StringField("Faculty", validators=[DataRequired(), Length(max=100)])
    
# password
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Sign Up")



#----Student login form----
class StudentLoginForm(FlaskForm):
    email = StringField("Student Email", validators=[DataRequired(), dut_email_check])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login")



#----Staff Signup forms----
class StaffSignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=100)])
    surname = StringField("Surname", validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", 
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    is_admin = BooleanField("Admin User")  # optional, defaults to True in your model
    submit = SubmitField("Sign Up")



#----Staff Login form----
class StaffLoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(message="Username is required"), Length(min=3, max=80)]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required"), Length(min=6)]
    )
    submit = SubmitField("Login")



#----Assign Staff to Students Form----
class AssignStaffForm(FlaskForm):
    staff = SelectField('Select Staff', coerce=int)
    students = SelectMultipleField('Select Students', coerce=int)
    submit = SubmitField('Assign')



#----------Student Survey Form---------------
class DiscalculiaSurveyForm(FlaskForm):
    # Numbers / math
    math_difficulty = SelectField(
        "Rate your difficulty with numbers and calculations",
        choices=[("1", "1 - No difficulty"), ("2", "2"), ("3", "3 - Moderate"), ("4", "4"), ("5", "5 - Severe")],
        validators=[DataRequired()]
    )
    reading_numbers = RadioField(
        "Do you confuse numbers easily (e.g., 6 vs 9)?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    math_anxiety = RadioField(
        "Do you feel anxious or stressed during math tasks?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    time_management = RadioField(
        "Do you struggle with timing tasks or estimating durations?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    previous_diagnosis = RadioField(
        "Have you been diagnosed with any learning difficulty before?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )

    # Reading / writing / memory
    reading_difficulty = RadioField(
        "Do you find it difficult to read or understand numbers in text or word problems?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    writing_numbers = RadioField(
        "Do you make mistakes when writing numbers or performing calculations?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    memory_issues = RadioField(
        "Do you often forget steps in calculations or math procedures?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    attention_difficulty = RadioField(
        "Do you find it hard to concentrate during math tasks or problem solving?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )

    # Real-life challenges
    daily_math_challenges = TextAreaField(
        "Describe challenges you face in daily activities that involve numbers (shopping, time, money, etc.)",
        validators=[DataRequired()]
    )
    daily_challenges = TextAreaField(
        "Briefly describe any challenges you face in daily school activities related to numbers.",
        validators=[DataRequired()]
    )

    # Support & accommodations
    support_needed = TextAreaField(
        "What kind of support do you think would help you succeed in math?",
        validators=[DataRequired()]
    )

    # Additional key areas for disability evaluation
    processing_speed = RadioField(
        "Do you often feel slow when completing math tasks compared to peers?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    problem_solving_difficulty = RadioField(
        "Do you find it difficult to plan or solve multi-step problems?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    visual_confusion = RadioField(
        "Do you confuse symbols, shapes, or numbers when looking at them quickly?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    anxiety_other_subjects = RadioField(
        "Do you feel anxious or stressed in subjects other than math?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )
    fatigue = RadioField(
        "Do you get tired or mentally exhausted quickly when working on math tasks?",
        choices=[("Yes", "Yes"), ("No", "No")],
        validators=[DataRequired()]
    )

    # Submit
    submit = SubmitField("Submit Survey")




