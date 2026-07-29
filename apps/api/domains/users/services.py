import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SCHEMA_PROMPT = """
You are an AI career assistant. Your job is to extract and intelligently MERGE professional information into a strict JSON schema.

THE SCHEMA:
{
  "contact": {"phone": "string", "email": "string", "github": "string", "linkedin": "string", "twitter": "string", "portfolio": "string"},
  "skills": ["string"],
  "experience": [{"role": "string", "company": "string", "duration": "string", "description": "string", "link": "string"}],
  "projects": [{"name": "string", "technologies": "string", "description": "string", "repo_link": "string", "live_link": "string"}],
  "education": [{"degree": "string", "institution": "string", "duration": "string", "gpa": "string"}],
  "certifications": [{"name": "string", "issuer": "string", "year": "string", "link": "string"}],
  "achievements": [{"title": "string", "description": "string", "link": "string"}]
}

RULES:
1. Return ONLY valid JSON matching this schema exactly. No markdown formatting like ```json, just the raw JSON.
2. Do not duplicate existing entries. Intelligently merge the new information into the existing context.
3. If an experience or project already exists but the new text has more details, update the existing entry.
4. For 'description', write a detailed, highly descriptive paragraph of all the work done, tools used, and impact. Do not use bullet points. We want maximum raw context so we can tailor resumes later.
5. IMPORTANT: The user's hidden PDF links are appended at the bottom under "--- EXTRACTED HYPERLINKS ---". You MUST intelligently map these URLs to the 'link', 'repo_link', and 'live_link' fields for Projects, Certifications, and Achievements based on their domains (e.g. udemy.com / linkedin.com/learning for certs, github.com for repos).
6. STRICT DURATION RULE: For 'duration' in experience and education, ONLY put a value if a specific time period (e.g. 'April 2023 - May 2025' or '2021-2023') is explicitly mentioned. DO NOT guess or infer. If no duration is explicitly stated, leave it as an empty string "".
"""

def merge_context_via_llm(current_context: dict, new_text: str) -> dict:
    prompt = f"""
CURRENT CONTEXT:
{json.dumps(current_context, indent=2)}

NEW INFORMATION TO MERGE:
{new_text}

Merge the NEW INFORMATION into the CURRENT CONTEXT. Return only the final merged JSON.
"""
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SCHEMA_PROMPT},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    return json.loads(response.choices[0].message.content)
