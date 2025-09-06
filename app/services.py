import os

import google.generativeai as genai
from google.generativeai import types

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

if __name__ == "__main__":
    generate()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash") 

def get_next_question(part, difficulty="easy"):
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
        
        if "Answer:" in text:
            question, answer = text.split("Answer:", 1)
            return {"question": question.strip(), "answer": answer.strip()}
        else:
            return {"question": text, "answer": None}
    except Exception as e:
        print("Gemini question generation failed:", e)
        return {"question": "Error generating question", "answer": None}

def ai_evaluate_answer(student_answer, correct_answer, part, question_text):
    if part == "numbers" and student_answer.strip().upper() == correct_answer.strip().upper():
        return True

    # For text answers (logic & shapes), AI check
    prompt = f"""
    You are an examiner.
    Question: "{question_text}".
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