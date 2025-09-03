from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, SubmitField, SelectField
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



#----------Student Survey Form---------------
class DiscalculiaSurveyForm(FlaskForm):
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
    support_needed = TextAreaField(
        "What kind of support do you think would help you succeed in math?",
        validators=[DataRequired()]
    )
    daily_challenges = TextAreaField(
        "Briefly describe any challenges you face in daily school activities related to numbers.",
        validators=[DataRequired()]
    )
    submit = SubmitField("Submit Survey")



