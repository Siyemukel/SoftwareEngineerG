import os
import random
import base64
from io import BytesIO
import google.generativeai as genai
from google.generativeai import types

# For generating shape images
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text="""Persona: You are a professional assessor specializing in learning disabilities, specifically dyscalculia. Your tone is supportive, encouraging, and neutral. You are not a teacher or a therapist in this role; you are a data collector.

Objective: Your task is to conduct a preliminary, non-diagnostic assessment for potential indicators of dyscalculia in a student. The assessment will be conducted through a series of questions.

Rules of Engagement:

Assessment Flow: Present a single question at a time. Do not ask multiple questions simultaneously.

Question Categories: The questions will be related to one or more of the following categories:

Numbers: Mental arithmetic, number sequencing, place value, and estimation.

Logic: Pattern recognition, spatial reasoning, and problem-solving that requires sequential steps.

Shapes: Recognizing, manipulating, and understanding the properties of geometric shapes.

Student Interaction:

Introduction: Begin the assessment with a friendly, reassuring welcome that explains the purpose is to understand their thinking, not to test them.

Response Handling: Acknowledge the student's answer neutrally and with encouragement. For example, \"Thank you for that answer. Let's move on to the next question,\" or \"That's helpful. Here is the next one.\"

Avoid Correction: Absolutely do not correct the student's answers, hint at the correct response, or explain why an answer is right or wrong. Your role is to gather uninfluenced responses.

Conclusion: Once all questions have been asked (or a pre-determined number of questions has been completed by you), you must not provide a diagnosis or any definitive conclusion. Instead, state that the assessment is complete and that the results should be shared with a qualified professional for review."""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_shape_image(shape_type, question_data):
    """Generate a simple shape image using PIL"""
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Create a white background image
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
            
        # Convert to base64 for HTML embedding
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"Error generating shape image: {e}")
        return None

def get_varied_question_seed(part, q_num, difficulty):
    """Generate a unique seed for question variation"""
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
    
    # Add variety to questions
    seed_topic = get_varied_question_seed(part, q_num, difficulty)
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if part == "numbers":
                prompt = f"""
                Generate one {difficulty} level math question about {seed_topic}.
                Create a multiple-choice question with 4 options.
                Make it appropriate for dyscalculia assessment.
                
                Format EXACTLY like this:
                Question: [your question here]
                A) [option A]
                B) [option B]
                C) [option C]
                D) [option D]
                Answer: [correct letter only - A, B, C, or D]
                """
                
            elif part == "logic":
                prompt = f"""
                Generate one {difficulty} level logic reasoning question about {seed_topic}.
                Make it suitable for dyscalculia assessment focusing on logical thinking.
                Provide a clear, short answer.
                
                Format EXACTLY like this:
                Question: [your question here]
                Answer: [short correct answer]
                """
                
            elif part == "shapes":
                shape_types = ["circle", "square", "rectangle", "triangle"]
                chosen_shape = random.choice(shape_types)
                
                prompt = f"""
                Generate one {difficulty} level spatial/geometric question about {seed_topic}.
                Focus on {chosen_shape} shapes. Make it suitable for dyscalculia assessment.
                Ask about properties like sides, corners, or basic measurements.
                
                Format EXACTLY like this:
                Question: [your question here]
                Answer: [short correct answer]
                Shape: {chosen_shape}
                """
            else:
                return {"error": "Invalid test part"}

            # Generate content with timeout
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # Add some randomness
                    max_output_tokens=500,
                    top_p=0.8
                )
            )
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
                
            text = response.text.strip()
            
            # Parse the response more robustly
            result = parse_question_response(text, part)
            
            if result and "error" not in result:
                # For shapes, add image generation
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
            print(f"Attempt {retry_count + 1} - Gemini generation failed: {e}")
            retry_count += 1
    
    # Fallback questions if all retries fail
    return get_fallback_question(part, difficulty, q_num)

def parse_question_response(text, part):
    """Parse Gemini response more robustly"""
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        question_line = None
        answer_line = None
        
        for line in lines:
            if line.startswith('Question:'):
                question_line = line.replace('Question:', '').strip()
            elif line.startswith('Answer:'):
                answer_line = line.replace('Answer:', '').strip()
        
        if not question_line:
            # Try to find question without prefix
            for line in lines:
                if '?' in line and not line.startswith(('A)', 'B)', 'C)', 'D)')):
                    question_line = line
                    break
        
        if not answer_line:
            # Try to find answer without prefix
            for line in reversed(lines):
                if part == "numbers" and line in ['A', 'B', 'C', 'D']:
                    answer_line = line
                    break
                elif part in ["logic", "shapes"] and len(line.split()) <= 5:
                    answer_line = line
                    break
        
        if question_line and answer_line:
            result = {
                "question": question_line,
                "answer": answer_line
            }
            
            # For multiple choice, include options
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
            return {"error": "Could not parse question format"}
            
    except Exception as e:
        print(f"Parse error: {e}")
        return {"error": f"Parse error: {str(e)}"}

def get_fallback_question(part, difficulty, q_num):
    """Provide fallback questions when Gemini fails"""
    fallbacks = {
        "numbers": {
            "easy": {
                1: {"question": "What is 3 + 4?", "answer": "B", "options": {"A": "6", "B": "7", "C": "8", "D": "9"}},
                2: {"question": "What is 12 - 5?", "answer": "A", "options": {"A": "7", "B": "8", "C": "6", "D": "9"}},
                3: {"question": "What is 2 × 3?", "answer": "C", "options": {"A": "5", "B": "8", "C": "6", "D": "7"}},
                4: {"question": "What is 10 ÷ 2?", "answer": "B", "options": {"A": "4", "B": "5", "C": "6", "D": "3"}},
                5: {"question": "What is 6 + 9?", "answer": "D", "options": {"A": "14", "B": "16", "C": "13", "D": "15"}}
            }
        },
        "logic": {
            "easy": {
                1: {"question": "What comes next in this pattern: 2, 4, 6, 8, ?", "answer": "10"},
                2: {"question": "If all cats have tails, and Fluffy is a cat, what can we say about Fluffy?", "answer": "Fluffy has a tail"},
                3: {"question": "Complete the sequence: A, B, C, ?", "answer": "D"},
                4: {"question": "What is the odd one out: apple, banana, car, orange?", "answer": "car"},
                5: {"question": "If today is Monday, what day will it be in 3 days?", "answer": "Thursday"}
            }
        },
        "shapes": {
            "easy": {
                1: {"question": "How many sides does a triangle have?", "answer": "3", "shape_type": "triangle"},
                2: {"question": "How many corners does a square have?", "answer": "4", "shape_type": "square"},
                3: {"question": "What shape has no corners?", "answer": "circle", "shape_type": "circle"},
                4: {"question": "How many sides does a rectangle have?", "answer": "4", "shape_type": "rectangle"},
                5: {"question": "Which shape has 3 sides and 3 corners?", "answer": "triangle", "shape_type": "triangle"}
            }
        }
    }
    
    try:
        fallback = fallbacks[part][difficulty][q_num]
        # Add shape image for shapes questions
        if part == "shapes" and "shape_type" in fallback:
            shape_image = generate_shape_image(fallback["shape_type"], {})
            if shape_image:
                fallback["shape_image"] = shape_image
        return fallback
    except KeyError:
        return {"error": "No fallback question available"}

def ai_evaluate_answer(student_answer, correct_answer, part, question_text):
    """Evaluate answers with better error handling"""
    if not student_answer or not correct_answer:
        return False
    
    # Clean inputs
    student_clean = student_answer.strip().upper()
    correct_clean = correct_answer.strip().upper()
    
    # Direct comparison for exact matches
    if student_clean == correct_clean:
        return True
    
    # For multiple choice (numbers), just compare letters
    if part == "numbers" and len(correct_clean) == 1 and correct_clean in 'ABCD':
        return student_clean == correct_clean
    
    # For text answers, use AI with fallback
    max_retries = 2
    for attempt in range(max_retries):
        try:
            prompt = f"""
            You are evaluating a student's answer. Be lenient with minor spelling or phrasing differences.
            
            Question: "{question_text}"
            Student answered: "{student_answer}"
            Expected answer: "{correct_answer}"
            
            Reply with ONLY 'YES' if the student's answer is essentially correct, or 'NO' if incorrect.
            Consider synonyms and alternative phrasings as correct.
            """
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=10
                )
            )
            
            if response and response.text:
                result = response.text.strip().upper()
                return "YES" in result
                
        except Exception as e:
            print(f"AI evaluation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                # Final fallback: basic string similarity
                return basic_answer_similarity(student_answer, correct_answer)
    
    return False

def basic_answer_similarity(student, correct):
    """Basic fallback for answer comparison"""
    if not student or not correct:
        return False
    
    student_words = set(student.lower().split())
    correct_words = set(correct.lower().split())
    
    if not correct_words:
        return False
    
    # Calculate overlap
    overlap = len(student_words.intersection(correct_words))
    similarity = overlap / len(correct_words)
    
    return similarity >= 0.6  # 60% word overlap threshold