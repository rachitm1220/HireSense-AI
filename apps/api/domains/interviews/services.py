import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def get_system_prompt(interview_type: str, difficulty: str, company_name: str, job_description: str, resume_latex: str) -> str:
    base_prompt = f"""You are an expert technical interviewer and hiring manager conducting a mock interview with a candidate for a role at {company_name}.
Your goal is to evaluate the candidate based on the provided Job Description and their Tailored Resume.

PERSONA ({difficulty}):
"""
    if difficulty == "Friendly Recruiter":
        base_prompt += "Act like a friendly, encouraging recruiter. Focus heavily on culture fit, high-level experience, and soft skills. Be supportive and conversational.\n"
    else:
        base_prompt += "Act like a strict, rigorous Hiring Manager. Focus heavily on technical implementation, grill the candidate on edge cases, expect highly detailed answers, and push back if their answer is vague.\n"

    base_prompt += f"""
IMPORTANT RULE 1: Calibrate the difficulty of your questions based on the candidate's experience level shown in their resume. If they are a fresher or junior, ask fundamental and appropriate questions. If they are senior, you may grill them on advanced system design or edge cases. Do not unnecessarily grill a junior candidate.
IMPORTANT RULE 2: Act realistically. Do not be overly polite or robotic. Ask probing follow-up questions if their answer is superficial.
IMPORTANT RULE 3: Only ask ONE question at a time. Keep your responses concise (1-3 paragraphs max).

--- JOB DESCRIPTION ---
{job_description}

--- CANDIDATE'S TAILORED RESUME (LaTeX format) ---
{resume_latex}
"""
    
    # Company Specific Frameworks
    company_lower = company_name.lower() if company_name else ""
    if "amazon" in company_lower or "aws" in company_lower:
        base_prompt += "\nCOMPANY FRAMEWORK (AMAZON): You MUST evaluate the candidate strictly against Amazon's 14 Leadership Principles (e.g., Customer Obsession, Ownership, Bias for Action, Dive Deep). Grade their answers implicitly on these principles.\n"
    elif "google" in company_lower or "alphabet" in company_lower:
        base_prompt += "\nCOMPANY FRAMEWORK (GOOGLE): You MUST evaluate the candidate for 'Googlyness'—doing the right thing, striving for excellence, keeping an eye on the goals, being proactive, and working well in ambiguity.\n"

    type_prompts = {
        "HR": "\n\nFOCUS: Behavioral and Culture Fit.\nSTRICT RULE 1: For behavioral questions, strictly enforce the STAR method. If the candidate misses the 'Result' or 'Action' part of their story, explicitly reply and prompt them for the missing part.\nSTRICT RULE 2: Occasionally, initiate a LIVE ROLE-PLAY scenario instead of asking a standard question (e.g., 'Let's roleplay. I am your angry Product Manager. I just walked to your desk and told you we are cutting the deadline in half. Walk me through exactly what you say to me right now.'). Start the interview by welcoming them.",
        "DSA": "\n\nFOCUS: Data Structures & Algorithms. STRICT RULE: DO NOT ask any behavioral, HR, or culture fit questions. Stay strictly focused on coding, algorithms, and data structures. Propose a classic Big-Tech / LeetCode-style algorithmic coding problem. Ask them to explain their approach, time/space complexity, and write code. NOTE: The candidate will be typing code in a live editor. Their current code will be passed to you inside [CANDIDATE'S WORKSPACE] blocks. You MUST review their code and point out bugs, infinite loops, or inefficiencies.",
        "SYSTEM_DESIGN": "\n\nFOCUS: System Design. STRICT RULE: DO NOT ask any behavioral, HR, or simple coding questions. Ask them to design a scalable architecture for a core feature mentioned in the JD.\nSUDDEN CONSTRAINT CURVEBALL: After the candidate answers your initial design question, you MUST introduce a sudden, massive constraint (e.g., 'Traffic just spiked 100x', 'The main database region went completely down') and ask how their architecture pivots or handles it.",
        "CORE_FUNDAMENTALS": "\n\nFOCUS: Core Fundamentals & Language specifics. STRICT RULE: Stay strictly focused on deep language features and mechanics based on their resume.\nSUDDEN CONSTRAINT CURVEBALL: After they answer, throw a curveball scenario (e.g., 'What if you run out of memory doing that?', 'What happens if a race condition occurs?') to see if they understand the fundamentals."
    }
    
    return base_prompt + type_prompts.get(interview_type, type_prompts["HR"])

def generate_interview_reply(interview_type: str, difficulty: str, company_name: str, job_description: str, resume_latex: str, message_history: list) -> str:
    system_prompt = get_system_prompt(interview_type, difficulty, company_name, job_description, resume_latex)
    
    clean_history = [{"role": m["role"], "content": m.get("content", "")} for m in message_history]
    messages = [{"role": "system", "content": system_prompt}] + clean_history
    
    response = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        temperature=0.7,
        max_tokens=1000,
    )
    return response.choices[0].message.content

def get_interview_hint(message_history: list) -> str:
    hint_prompt = "You are a helpful 'training wheels' AI assistant analyzing an ongoing mock interview. Look at the last question the interviewer asked. Provide a brief, concise hint to the candidate on how to structure their answer (e.g., 'Try structuring your answer around the CAP theorem here' or 'Use the STAR method to describe a specific conflict'). Do not answer the question for them, just guide them."
    
    clean_history = [{"role": m["role"], "content": m.get("content", "")} for m in message_history]
    messages = [{"role": "system", "content": hint_prompt}] + clean_history
    
    response = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        temperature=0.7,
        max_tokens=200,
    )
    return response.choices[0].message.content

def generate_scorecard(interview_type: str, message_history: list) -> dict:
    # Define dynamic rubrics based on interview type
    if interview_type == "HR":
        metrics = '"behavioral_competency": 8, "communication": 6, "culture_fit": 9'
        rubric = "Grade them on STAR method usage, confidence, and culture fit."
    elif interview_type == "DSA":
        metrics = '"algorithmic_efficiency": 8, "problem_solving": 6, "communication": 9'
        rubric = "Grade them on optimal Big-O complexity, handling edge cases, and code correctness."
    elif interview_type == "SYSTEM_DESIGN":
        metrics = '"system_architecture": 8, "scalability": 6, "communication": 9'
        rubric = "Grade them on identifying bottlenecks, database choices, and handling the constraint curveballs."
    else:
        metrics = '"technical_depth": 8, "accuracy": 6, "communication": 9'
        rubric = "Grade them on deep language knowledge and factual accuracy of their answers."

    scorecard_prompt = f"""You are an expert AI Interview Evaluator. Analyze the full transcript of this {interview_type} mock interview.
{rubric}

Output a strict JSON object with the following schema:
{{
  {metrics},
  "overall_score": 7.5,
  "summary": "Brief overall summary of their performance.",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "red_flags_and_filler_words": ["Identify phrases like 'I guess', 'Maybe', or any red flags like blaming others"],
  "detailed_critiques": [
    {{
      "user_message_snippet": "The vague answer they gave...",
      "critique": "Why it was bad.",
      "improved_answer": "A perfect 10/10 example of how they should have answered it."
    }}
  ]
}}
IMPORTANT RULE 1: Do NOT critique every single answer. Identify ONLY the top 2 to 3 weakest or most impactful answers where the candidate struggled, and provide a 'detailed_critique' only for those specific instances.
IMPORTANT RULE 2: Actively scan the transcript for 'red flags' (lack of accountability, toxicity) or 'filler words' (I guess, Maybe) and list them in 'red_flags_and_filler_words'.
Return ONLY the raw JSON without markdown backticks.
"""
    clean_history = [{"role": m["role"], "content": m.get("content", "")} for m in message_history]
    messages = [{"role": "system", "content": scorecard_prompt}] + clean_history
    
    response = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content)
