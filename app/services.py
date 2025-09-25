import os, json
import random
import base64
from io import BytesIO
import google.generativeai as genai
from google.generativeai import types
from .models import *
from sqlalchemy import func
from flask_mail import Message
from flask_login import current_user
from .extensions import mail


# For generating fallback shape images
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


# IMAGE GENERATION (AI + FALLBACK)


def generate_shape_image_ai(shape_type, question_data):
    """
    Use Gemini to generate an image for shapes.
    """
    try:
        prompt = f"Draw a simple black outline of a {shape_type}. No background, plain white canvas."
        
        response = model.generate_images(
            prompt=prompt,
            generation_config=genai.types.GenerationConfig(
                size="512x512"
            )
        )
        
        if not response or not response.images:
            return None

        # Convert first image to base64
        image_data = response.images[0].image_bytes
        img_str = base64.b64encode(image_data).decode()
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        print(f"AI shape generation failed: {e}")
        return None


def generate_shape_image_pil(shape_type, question_data):
    """Generate a simple shape image using PIL (fallback)."""
    if not PIL_AVAILABLE:
        return None
    
    try:
        width, height = 400, 300
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        center_x, center_y = width // 2, height // 2
        
        if shape_type == "circle":
            radius = question_data.get('radius', 60)
            draw.ellipse([center_x - radius, center_y - radius, 
                         center_x + radius, center_y + radius], 
                        outline='black', width=3)
                        
        elif shape_type == "square":
            side = question_data.get('side', 100)
            half_side = side // 2
            draw.rectangle([center_x - half_side, center_y - half_side,
                           center_x + half_side, center_y + half_side], 
                          outline='black', width=3)
                          
        elif shape_type == "rectangle":
            width_rect = question_data.get('width', 120)
            height_rect = question_data.get('height', 80)
            draw.rectangle([center_x - width_rect//2, center_y - height_rect//2,
                           center_x + width_rect//2, center_y + height_rect//2], 
                          outline='black', width=3)
                          
        elif shape_type == "triangle":
            points = [
                (center_x, center_y - 60),  # top
                (center_x - 60, center_y + 60),  # bottom left
                (center_x + 60, center_y + 60)   # bottom right
            ]
            draw.polygon(points, outline='black', width=3)
            
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"PIL fallback failed: {e}")
        return None


def generate_shape_image(shape_type, question_data):
    """
    Try AI first, fallback to PIL if AI fails.
    """
    img = generate_shape_image_ai(shape_type, question_data)
    if img:
        return img
    return generate_shape_image_pil(shape_type, question_data)



# QUESTION GENERATION


def get_varied_question_seed(part, q_num, difficulty):
    seeds = {
        "numbers": {
            1: ["addition with single digits", "subtraction basics", "counting objects"],
            2: ["two-digit addition", "simple multiplication", "number patterns"],
            3: ["division problems", "fractions introduction", "place value"],
            4: ["word problems", "decimals", "percentage basics"],
            5: ["mixed operations", "estimation", "number sequences"]
        },
        "logic": {
            1: ["simple patterns", "basic sequences", "sorting"],
            2: ["if-then logic", "categorization", "simple reasoning"],
            3: ["pattern completion", "logical deduction", "problem solving"],
            4: ["complex patterns", "multi-step reasoning", "analogies"],
            5: ["advanced logic", "spatial reasoning", "critical thinking"]
        },
        "shapes": {
            1: ["basic shape recognition", "counting sides", "simple geometry"],
            2: ["shape properties", "symmetry", "shape comparison"],
            3: ["area and perimeter", "shape transformation", "angles"],
            4: ["3D shapes", "geometric patterns", "shape relationships"],
            5: ["complex geometry", "spatial visualization", "shape puzzles"]
        }
    }
    
    question_types = seeds.get(part, {}).get(q_num, ["general question"])
    return random.choice(question_types)


def get_next_question(part, difficulty="easy", q_num=1):
    """Generate questions with better error handling and variety"""
    seed_topic = get_varied_question_seed(part, q_num, difficulty)
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if part == "numbers":
                prompt = f"""
                Generate one {difficulty} level math question about {seed_topic}.
                Create a multiple-choice question with 4 options.
                
                Format EXACTLY like this:
                Question: [your question here]
                A) [option A]
                B) [option B]
                C) [option C]
                D) [option D]
                Answer: [A/B/C/D]
                """
            elif part == "logic":
                prompt = f"""
                Generate one {difficulty} level logic reasoning question about {seed_topic}.
                
                Format EXACTLY like this:
                Question: [your question here]
                Answer: [short correct answer]
                """
            elif part == "shapes":
                shape_types = ["circle", "square", "rectangle", "triangle"]
                chosen_shape = random.choice(shape_types)
                
                prompt = f"""
                Generate one {difficulty} level spatial/geometric question about {seed_topic}.
                Focus on {chosen_shape}.
                
                Format EXACTLY like this:
                Question: [your question here]
                Answer: [short correct answer]
                Shape: {chosen_shape}
                """
            else:
                return {"error": "Invalid test part"}

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500
                )
            )
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
                
            text = response.text.strip()
            result = parse_question_response(text, part)
            
            if result and "error" not in result:
                if part == "shapes" and "Shape:" in text:
                    shape_line = [line for line in text.split('\n') if line.startswith('Shape:')]
                    if shape_line:
                        shape_type = shape_line[0].split('Shape:')[1].strip().lower()
                        shape_image = generate_shape_image(shape_type, {})
                        if shape_image:
                            result["shape_image"] = shape_image
                            result["shape_type"] = shape_type
                return result
            else:
                retry_count += 1
                
        except Exception as e:
            print(f"Attempt {retry_count + 1} failed: {e}")
            retry_count += 1
    
    return get_fallback_question(part, difficulty, q_num)



# PARSING & FALLBACKS


def parse_question_response(text, part):
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        question_line = None
        answer_line = None
        
        for line in lines:
            if line.startswith('Question:'):
                question_line = line.replace('Question:', '').strip()
            elif line.startswith('Answer:'):
                answer_line = line.replace('Answer:', '').strip()
        
        if question_line and answer_line:
            result = {"question": question_line, "answer": answer_line}
            if part == "numbers":
                options = {}
                for line in lines:
                    for option in ['A)', 'B)', 'C)', 'D)']:
                        if line.startswith(option):
                            options[option[0]] = line.replace(option, '').strip()
                if options:
                    result["options"] = options
            return result
        else:
            return {"error": "Could not parse question"}
            
    except Exception as e:
        return {"error": f"Parse error: {str(e)}"}


def get_fallback_question(part, difficulty, q_num):
    fallbacks = {
        "numbers": {
            "easy": {
                1: {"question": "What is 3 + 4?", "answer": "B", "options": {"A": "6", "B": "7", "C": "8", "D": "9"}},
                2: {"question": "What is 12 - 5?", "answer": "A", "options": {"A": "7", "B": "8", "C": "6", "D": "9"}},
            }
        },
        "logic": {
            "easy": {
                1: {"question": "What comes next in this pattern: 2, 4, 6, 8, ?", "answer": "10"},
            }
        },
        "shapes": {
            "easy": {
                1: {"question": "How many sides does a triangle have?", "answer": "3", "shape_type": "triangle"},
            }
        }
    }
    
    try:
        fallback = fallbacks[part][difficulty][q_num]
        if part == "shapes" and "shape_type" in fallback:
            shape_image = generate_shape_image(fallback["shape_type"], {})
            if shape_image:
                fallback["shape_image"] = shape_image
        return fallback
    except KeyError:
        return {"error": "No fallback question available"}



# ANSWER EVALUATION


def ai_evaluate_answer(student_answer, correct_answer, part, question_text):
    if not student_answer or not correct_answer:
        return False
    
    student_clean = student_answer.strip().upper()
    correct_clean = correct_answer.strip().upper()
    
    if student_clean == correct_clean:
        return True
    
    if part == "numbers" and correct_clean in "ABCD":
        return student_clean == correct_clean
    
    try:
        prompt = f"""
        You are evaluating a student's answer.
        Question: "{question_text}"
        Student answered: "{student_answer}"
        Expected answer: "{correct_answer}"
        
        Reply ONLY 'YES' if correct, 'NO' if incorrect.
        """
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=10
            )
        )
        
        if response and response.text:
            return "YES" in response.text.strip().upper()
    except Exception:
        return basic_answer_similarity(student_answer, correct_answer)
    
    return False


def basic_answer_similarity(student, correct):
    student_words = set(student.lower().split())
    correct_words = set(correct.lower().split())
    
    if not correct_words:
        return False
    
    overlap = len(student_words.intersection(correct_words))
    similarity = overlap / len(correct_words)
    return similarity >= 0.6



#system to assign students to staff with least load
def assign_student_to_staff(student):
    # Check if student is already assigned to avoid duplicates
    existing_assignment = StaffStudentLink.query.filter_by(student_id=student.id).first()
    if existing_assignment:
        return Staff.query.get(existing_assignment.staff_id)
    
    # This single query efficiently finds all NON-ADMIN staff, counts their current
    # students, and sorts them by that count in ascending order.
    # This avoids the "N+1" query problem.
    staff_with_counts = db.session.query(
        Staff,
        func.count(StaffStudentLink.student_id)
    ).outerjoin(StaffStudentLink, Staff.id == StaffStudentLink.staff_id) \
     .filter(Staff.is_admin == False) \
     .group_by(Staff.id) \
     .order_by(func.count(StaffStudentLink.student_id).asc()) \
     .all()
    
    # The result is a list of tuples: [(staff_member_1, count_1), (staff_member_2, count_2), ...]
    for staff_member, student_count in staff_with_counts:
        # The max_students value from the database record is used.
        # The model's default=5 handles cases where it's not explicitly set.
        if student_count < staff_member.max_students:
            # Create the link object
            link = StaffStudentLink(staff_id=staff_member.id, student_id=student.id)
            
            # Add the link to the session, but DO NOT commit here
            db.session.add(link)
            
            return staff_member  # Return the assigned staff member
    
    # If the loop finishes, no non-admin staff with available slots were found
    return None


#email function to send student referral details to departments
def send_department_email(student, department, referral=None):
    """
    Send an email to the department with all details of the student referral:
    - Basic info
    - Survey results
    - Test results
    - Exercises completed
    """
    # Map department to email addresses
    department_emails = {
        "Finance": "finance@university.com",
        "Academics": "academics@university.com",
        "Counselling": "counselling@university.com"
    }

    recipient = department_emails.get(department)
    if not recipient:
        return

    # --- Basic info ---
    student_info = f"""
Name: {student.name} {student.surname}
Email: {student.student_email}
Course: {student.course}
Year: {student.year_of_study}
Faculty: {student.faculty}
Joined On: {student.created_at.strftime('%b %d, %Y')}
"""

    # --- Referral reason ---
    reason_text = f"\nReason for referral: {referral.reason}" if referral and referral.reason else "\nReason for referral: Not specified"

    # --- Test results ---
    test_results_text = "\nTest Results:\n"
    for result in student.test_results:
        test_results_text += f"- {result.created_at.strftime('%b %d, %Y')}: Numbers={result.numbers_score}, Logic={result.logic_score}, Shapes={result.shapes_score}, Outcome={result.outcome_message}\n"

    # --- Surveys ---
    surveys_text = "\nSurveys:\n"
    for survey in student.survey if student.survey else []:
        # if JSON stored as string
        survey_data = survey.survey_data
        if isinstance(survey_data, str):
            survey_data = json.loads(survey_data)
        readable_data = {k: ("Struggle" if v==1 else "No struggle") for k, v in survey_data.items()}
        surveys_text += f"- Survey {survey.id} ({survey.created_at.strftime('%b %d, %Y')}): {readable_data}\n"

    # --- Exercises completed ---
    exercises_text = "\nExercises Completed:\n"
    for completion in student.exercises_completed:
        ex = completion.exercise
        exercises_text += f"- {ex.title} ({ex.part}): Completed on {completion.completed_at.strftime('%b %d, %Y')}\n"

    # --- Compose email ---
    msg = Message(
        subject=f"Student Referral: {student.name} {student.surname}",
        recipients=[recipient],
        body=f"""
Dear {department} Team,

The following student has been referred for your attention:

{student_info}
{reason_text}
{test_results_text}
{surveys_text}
{exercises_text}

Please review and take the necessary actions.

Regards,
{current_user.name}
"""
    )

    mail.send(msg)







