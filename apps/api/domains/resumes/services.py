import json
from groq import Groq
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.config import settings
import os
import logging

groq_client = Groq(api_key=settings.GROQ_API_KEY)


def latex_escape(text) -> str:
    """Escape LaTeX special characters in dynamic text fields."""
    if not isinstance(text, str):
        text = str(text)
    # Backslash MUST be replaced first before we introduce new backslashes
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&',  r'\&'),
        ('%',  r'\%'),
        ('$',  r'\$'),
        ('#',  r'\#'),
        ('_',  r'\_'),
        ('{',  r'\{'),
        ('}',  r'\}'),
        ('~',  r'\textasciitilde{}'),
        ('^',  r'\textasciicircum{}'),
    ]
    for char, replacement in replacements:
        text = text.replace(char, replacement)
    return text

def url_format(text, platform=None) -> str:
    """Ensure a URL string starts with a proper schema. If only a username is provided, construct the full URL."""
    if not isinstance(text, str) or not text:
        return text
        
    text = text.strip()
    if text.startswith(('http://', 'https://')):
        return text
        
    if platform == 'github' and 'github.com' not in text:
        return f"https://github.com/{text.strip('/')}"
        
    if platform == 'linkedin' and 'linkedin.com' not in text:
        return f"https://linkedin.com/in/{text.strip('/')}"
        
    if not text.startswith(('http://', 'https://', 'mailto:')):
        return f"https://{text}"
    return text

# Jinja setup pointing to core/templates
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(disabled_extensions=(['j2', 'tex']))  # Don't HTML-escape LaTeX
)
env.filters['latex_escape'] = latex_escape
env.filters['url_format'] = url_format

def tailor_resume_latex(user_context: dict, job_description: str, custom_instructions: str = None) -> str:
    """
    Takes the UserContext and Job Description.
    Uses Llama-3 to generate the JSON mapping for Jake's Resume LaTeX template.
    Returns the rendered LaTeX string.
    """
    
    prompt = f"""
    You are an expert Executive Resume Writer. Your goal is to tailor the candidate's experience to perfectly match the target Job Description.
    
    CANDIDATE CONTEXT:
    {json.dumps(user_context, indent=2)}
    
    TARGET JOB DESCRIPTION:
    {job_description[:10000]}
    
    CRITICAL INSTRUCTIONS:
    1. Extract the candidate's base info (name, email, github, linkedin, phone) from their context.
    2. Rewrite their Experience and Projects into 3-4 powerful, highly-quantifiable bullet points each.
    3. DO NOT invent, hallucinate, or fabricate any experience, projects, or education that are not explicitly present in the CANDIDATE CONTEXT. If the candidate has no experience, leave the experience array empty `[]`.
    4. The bullet points MUST emphasize skills and achievements that directly match the TARGET JOB DESCRIPTION.
    5. Keep the bullet points concise but impactful (Action Verb + Context + Result).
    6. Return ALL text values as plain, unescaped strings. Do NOT escape any characters like %, &, $, #, _ yourself — the rendering pipeline handles that automatically.
    
    {f"USER CUSTOM PREFERENCES:\n{custom_instructions}\n(Please adhere to these preferences closely when tailoring the resume)" if custom_instructions else ""}
    
    OUTPUT SCHEMA (Return exactly this JSON structure and nothing else):
    {{
        "name": "string",
        "phone": "string",
        "email": "string",
        "github": "string (just the username/path, no https://)",
        "linkedin": "string (just the username/path, no https://)",
        "education": [
            {{ "school": "string", "date": "string", "degree": "string", "gpa": "string" }}
        ],
        "experience": [
            {{ "company": "string", "date": "string", "role": "string", "location": "string", "bullets": ["string", "string"] }}
        ],
        "projects": [
            {{ "title": "string", "tech": "string", "bullets": ["string", "string"] }}
        ],
        "skills": {{
            "languages": "string",
            "frameworks": "string",
            "tools": "string",
            "concepts": "string"
        }}
    }}
    """
    
    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    tailored_data = json.loads(completion.choices[0].message.content)
    
    # Render the LaTeX template using Jinja2
    template = env.get_template("jakes_resume.tex.j2")
    rendered_tex = template.render(**tailored_data)
    
    return rendered_tex

def generate_resume_from_pdf_text(raw_text: str) -> dict:
    """
    Parses raw PDF text into Jake's Resume JSON schema and returns the parsed JSON dict and rendered LaTeX string.
    Returns: {"latex": str, "name": str}
    """
    prompt = f"""
    You are an expert Executive Resume Writer. Your goal is to perfectly transcribe the provided unstructured resume text into the required structured JSON format.
    
    RAW RESUME TEXT:
    {raw_text[:15000]}
    
    CRITICAL INSTRUCTIONS:
    1. Extract the candidate's base info (name, email, github, linkedin, phone).
    2. Extract their Experience and Projects into 3-4 bullet points each.
    3. DO NOT invent or hallucinate any experience, projects, or education.
    4. Return ALL text values as plain, unescaped strings. Do NOT escape any characters like %, &, $, #, _ yourself.
    
    OUTPUT SCHEMA (Return exactly this JSON structure and nothing else):
    {{
        "name": "string",
        "phone": "string",
        "email": "string",
        "github": "string",
        "linkedin": "string",
        "education": [
            {{ "school": "string", "date": "string", "degree": "string", "gpa": "string" }}
        ],
        "experience": [
            {{ "company": "string", "date": "string", "role": "string", "location": "string", "bullets": ["string"] }}
        ],
        "projects": [
            {{ "title": "string", "tech": "string", "bullets": ["string"] }}
        ],
        "skills": {{
            "languages": "string",
            "frameworks": "string",
            "tools": "string",
            "concepts": "string"
        }}
    }}
    """
    
    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    parsed_data = json.loads(completion.choices[0].message.content)
    
    template = env.get_template("jakes_resume.tex.j2")
    rendered_tex = template.render(**parsed_data)
    
    return {"latex": rendered_tex, "name": parsed_data.get("name", "Untitled Resume")}



def analyze_resume_with_ai_enhanced(resume_text: str, job_description: str = None) -> dict:
    """Enhanced AI analysis with DETAILED, ACTIONABLE feedback - GUARANTEED 3 WEEKS"""

    if job_description and job_description.strip():
        prompt = f"""You are an expert ATS analyzer and career coach. Analyze this resume against the job description.

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:2000]}

Return ONLY valid JSON (no markdown, no explanation). Use EXACTLY this structure:

{{
  "analysis_type": "job_match",
  "match_score": 65,
  "potential_score": 85,
  "score_category": "Good Match",
  "ats_prediction": "✓ Moderate chance of passing ATS - add missing keywords to improve",
  "matched_skills": ["Python", "SQL", "React"],
  "missing_critical_skills": ["Docker", "AWS", "Kubernetes"],
  "missing_nice_to_have": ["GraphQL", "TypeScript"],
  "keyword_analysis": {{
    "resume_keywords": {{"Python": 3, "SQL": 2}},
    "required_keywords": {{"Docker": 5, "AWS": 4, "Python": 3}},
    "keyword_match_rate": 45
  }},
  "section_gaps": {{
    "skills": {{"status": "moderate", "issues": ["Missing cloud skills"]}},
    "experience": {{"status": "good", "issues": []}},
    "projects": {{"status": "critical", "issues": ["No relevant projects shown"]}},
    "education": {{"status": "good", "issues": []}}
  }},
  "before_after_examples": [
    {{
      "before": "Worked on backend systems",
      "after": "Built REST APIs using Python/FastAPI serving 10k+ requests/day on AWS EC2",
      "impact": "+8 points"
    }}
  ],
  "improvement_tips": [
    "Add Docker and AWS to your skills section immediately",
    "Rewrite experience bullets using action verbs + metrics",
    "Add a projects section with GitHub links",
    "Include a professional summary targeting this specific role",
    "Mirror exact keywords from the job description"
  ],
  "action_plan": [
    {{
      "week": 1,
      "priority": "critical",
      "title": "Close the Critical Skill Gaps",
      "tasks": [
        "□ Complete hands-on Docker tutorial and containerize one of your existing projects",
        "□ Create a free AWS account and deploy something live (even a static site counts)",
        "□ Add these to your GitHub with a README explaining what you built",
        "□ Update your resume Skills section with all newly learned technologies",
        "□ Rewrite 3 experience bullets with specific metrics (numbers, percentages)"
      ],
      "expected_result": "Resume now shows hands-on experience with the top missing skills",
      "expected_impact": "+20 points"
    }},
    {{
      "week": 2,
      "priority": "high",
      "title": "Build Portfolio Evidence & Get Certified",
      "tasks": [
        "□ Complete AWS Cloud Practitioner free course on AWS Skill Builder",
        "□ Build a project combining Python + Docker + AWS and push to GitHub",
        "□ Write a short LinkedIn post about what you built (shows communication skills)",
        "□ Add certifications (even in-progress) to resume and LinkedIn",
        "□ Tailor your professional summary to match this job description"
      ],
      "expected_result": "Certificates + portfolio + blog = credible candidate with proof",
      "expected_impact": "+15 points"
    }},
    {{
      "week": 3,
      "priority": "medium",
      "title": "Network, Apply & Track",
      "tasks": [
        "□ Connect with 5-10 people at target companies on LinkedIn",
        "□ Contribute to 1 open-source project using skills from this job posting",
        "□ Apply to 10 similar roles with a tailored cover letter referencing your new projects",
        "□ Ask for a referral from anyone in your network at target companies",
        "□ Follow up on applications after 5-7 business days"
      ],
      "expected_result": "Active pipeline with referrals and portfolio backing every application",
      "expected_impact": "+5 points"
    }}
  ],
  "overall_feedback": "Your resume shows strong fundamentals but is missing the cloud and DevOps keywords this role requires. Following this 3-week plan will close the gap from 65% to 85%+ match score."
}}

CRITICAL RULES:
- matched_skills: list skills that appear in BOTH the resume AND job description
- missing_critical_skills: skills mentioned in job description but NOT in resume
- keyword_analysis.resume_keywords: count how many times each important keyword appears in resume
- keyword_analysis.required_keywords: count how many times each keyword appears in job description
- action_plan MUST have exactly 3 items with week numbers 1, 2, 3
- All scores must be integers between 0-100
- Return ONLY JSON, nothing else"""

    else:
        prompt = f"""You are an expert resume coach. Analyze this resume thoroughly.

Resume:
{resume_text[:4000]}

Return ONLY valid JSON (no markdown, no explanation). Use EXACTLY this structure:

{{
  "analysis_type": "general",
  "score": 72,
  "section_scores": {{
    "summary": 60,
    "experience": 75,
    "skills": 80,
    "education": 70,
    "projects": 65,
    "formatting": 75
  }},
  "quick_wins": [
    {{
      "task": "Add a professional summary at the top",
      "time": "15 min",
      "impact": "High",
      "example": "Results-driven Software Engineer with 3+ years building scalable web applications...",
      "copy_paste": "Results-driven [Your Role] with [X] years of experience in [top skills]..."
    }},
    {{
      "task": "Add metrics to your top 3 experience bullets",
      "time": "20 min",
      "impact": "High",
      "example": "Reduced API response time by 40% through query optimization",
      "copy_paste": "Improved [metric] by [X%] through [specific action], resulting in [outcome]"
    }}
  ],
  "detailed_strengths": [
    {{
      "strength": "Strong technical skills section",
      "why_good": "Recruiters scan for keywords in the first 6 seconds - yours are easy to find",
      "example": "Your Python, SQL, React listing is clear and scannable"
    }}
  ],
  "detailed_weaknesses": [
    {{
      "weakness": "Experience bullets lack quantifiable impact",
      "why_bad": "Hiring managers want to see numbers - vague bullets get ignored",
      "current_text": "Worked on improving application performance",
      "improved_text": "Reduced page load time by 35% by implementing Redis caching, improving user retention by 12%",
      "impact": "Could increase your score by 15+ points"
    }}
  ],
  "specific_improvements": [
    {{
      "section": "Experience",
      "action": "Add metrics to every bullet point using the formula: Action Verb + What You Did + Measurable Result",
      "before": "Developed new features for the web application",
      "after": "Engineered 8 new React features adopted by 50K+ users, reducing support tickets by 23%",
      "time_needed": "30 minutes"
    }}
  ],
  "red_flags": [
    {{
      "issue": "No GitHub or portfolio link",
      "solution": "Add your GitHub profile URL next to your email in the header",
      "why_matters": "Tech recruiters check GitHub - missing it raises questions about your code quality"
    }}
  ],
  "format_issues": [
    "Resume may exceed 1 page for entry/mid-level candidates - trim to 1 page",
    "Use consistent bullet point style throughout"
  ],
  "ats_compatibility": [
    "✓ Standard section headers detected (ATS-friendly)",
    "✓ No tables or columns that confuse ATS parsers",
    "⚠ Avoid using headers/footers for contact info - ATS often misses them",
    "⚠ Save as PDF but confirm the job portal accepts PDFs"
  ],
  "overall_feedback": "This is a solid resume foundation. The biggest opportunity is adding measurable impact to your experience bullets - right now it reads like a job description rather than an achievement record. Implement the Quick Wins above and your score should jump to 85+."
}}

CRITICAL RULES:
- Be specific to the actual resume content provided
- quick_wins must have realistic time estimates and actual copy-paste templates
- detailed_weaknesses must have real before/after examples based on the resume
- All scores must be integers between 0-100
- Return ONLY JSON, nothing else"""

    client = groq_client

    if not client:
        # ==================== MOCK RESPONSE ====================
        if job_description and job_description.strip():
            jd_lower = job_description.lower()
            resume_lower = resume_text.lower()
            tech_keywords = {
                'docker': 'Docker', 'kubernetes': 'Kubernetes', 'aws': 'AWS',
                'python': 'Python', 'java': 'Java', 'react': 'React',
                'sql': 'SQL', 'git': 'Git', 'linux': 'Linux', 'node': 'Node.js'
            }
            required_in_jd = {}
            found_in_resume = {}
            for keyword, display_name in tech_keywords.items():
                jd_count = jd_lower.count(keyword)
                resume_count = resume_lower.count(keyword)
                if jd_count > 0:
                    required_in_jd[display_name] = jd_count
                if resume_count > 0:
                    found_in_resume[display_name] = resume_count

            matched_skills = [s for s in required_in_jd if s in found_in_resume]
            missing_critical = [s for s in required_in_jd if s not in found_in_resume][:6]
            match_score = min(85, max(30, int(len(matched_skills) / max(len(required_in_jd), 1) * 100)))
            potential_score = min(100, match_score + 25)

            return {
                "analysis_type": "job_match",
                "match_score": match_score,
                "potential_score": potential_score,
                "score_category": "Good Match" if match_score >= 60 else "Needs Work",
                "ats_prediction": f"{'✓ Good' if match_score >= 60 else '⚠ Low'} chance of passing ATS - {'keep applying' if match_score >= 60 else 'add missing keywords first'}",
                "matched_skills": matched_skills[:8],
                "missing_critical_skills": missing_critical,
                "missing_nice_to_have": ["GraphQL", "TypeScript"],
                "keyword_analysis": {
                    "resume_keywords": found_in_resume,
                    "required_keywords": required_in_jd,
                    "keyword_match_rate": int(len(matched_skills) / max(len(required_in_jd), 1) * 100)
                },
                "section_gaps": {
                    "skills": {"status": "critical" if len(missing_critical) > 3 else "moderate", "issues": [f"Missing: {', '.join(missing_critical[:3])}"]},
                    "experience": {"status": "moderate", "issues": ["Add metrics to bullets"]},
                    "projects": {"status": "moderate", "issues": ["Show projects using required tech"]},
                    "education": {"status": "good", "issues": []}
                },
                "before_after_examples": [{
                    "before": "Worked on software development projects",
                    "after": f"Built and deployed applications using {matched_skills[0] if matched_skills else 'Python'}, serving 10k+ users with 99.9% uptime",
                    "impact": "+10 points"
                }],
                "improvement_tips": [
                    f"Add these missing skills: {', '.join(missing_critical[:3])}" if missing_critical else "Your skills match well - focus on metrics",
                    "Mirror exact phrases from the job description",
                    "Add a tailored professional summary for this role",
                    "Include quantified achievements (numbers, percentages)",
                    "Add relevant projects that use the required tech stack"
                ],
                "action_plan": [
                    {
                        "week": 1, "priority": "critical",
                        "title": f"Close Critical Skill Gaps: {', '.join(missing_critical[:2]) if missing_critical else 'Polish & Quantify'}",
                        "tasks": [
                            f"□ Complete a hands-on {missing_critical[0] if missing_critical else 'Docker'} tutorial and build something real",
                            f"□ Deploy a project using {missing_critical[1] if len(missing_critical) > 1 else 'AWS'} (free tier is fine)",
                            "□ Push your work to GitHub with a clear README",
                            "□ Add all newly learned skills to your resume Skills section",
                            "□ Rewrite your top 3 experience bullets with specific numbers"
                        ],
                        "expected_result": f"Resume now demonstrates hands-on experience with {', '.join(missing_critical[:2]) if missing_critical else 'key technologies'}",
                        "expected_impact": f"+{min(20, potential_score - match_score)} points"
                    },
                    {
                        "week": 2, "priority": "high",
                        "title": "Build Portfolio Evidence & Certifications",
                        "tasks": [
                            f"□ Complete free certification course for {missing_critical[0] if missing_critical else 'a required skill'}",
                            "□ Build a project combining 2-3 skills from the job posting",
                            "□ Write a LinkedIn post about your project (signals communication skills)",
                            "□ Add certifications (even in-progress) to resume and LinkedIn",
                            "□ Tailor your professional summary to match this specific role"
                        ],
                        "expected_result": "Portfolio + certifications = credible candidate with demonstrable proof",
                        "expected_impact": f"+{min(15, potential_score - match_score - 5)} points"
                    },
                    {
                        "week": 3, "priority": "medium",
                        "title": "Network, Apply & Track Results",
                        "tasks": [
                            "□ Connect with 5-10 people at target company on LinkedIn",
                            "□ Contribute to 1 open-source project using required skills",
                            "□ Apply to 10 similar roles with a tailored cover letter",
                            "□ Ask for referrals from anyone in your network at target companies",
                            "□ Follow up on applications after 5-7 business days"
                        ],
                        "expected_result": "Active pipeline with referrals and strong portfolio backing applications",
                        "expected_impact": "+5 points + referral advantage"
                    }
                ],
                "overall_feedback": f"Your resume matches {match_score}% of this role's requirements. You're missing {len(missing_critical)} critical skills. Follow this 3-week action plan to reach {potential_score}% match score and significantly improve your chances."
            }
        else:
            return {
                "analysis_type": "general",
                "score": 70,
                "section_scores": {"summary": 60, "experience": 70, "skills": 75, "education": 70, "projects": 65, "formatting": 75},
                "quick_wins": [
                    {"task": "Add a professional summary", "time": "15 min", "impact": "High", "example": "Results-driven engineer with X years...", "copy_paste": "Results-driven [Role] with [X] years in [top 3 skills]..."},
                    {"task": "Add metrics to experience bullets", "time": "20 min", "impact": "High", "example": "Reduced load time by 40%", "copy_paste": "Improved [metric] by [X%] through [action]"}
                ],
                "detailed_strengths": [{"strength": "Technical skills listed", "why_good": "Easy for ATS to detect keywords", "example": "Skills section is clear"}],
                "detailed_weaknesses": [{"weakness": "Bullets lack metrics", "why_bad": "Vague bullets get ignored by hiring managers", "current_text": "Worked on projects", "improved_text": "Led 3 projects delivering $50K in cost savings", "impact": "+15 points"}],
                "specific_improvements": [{"section": "Experience", "action": "Add numbers to every bullet", "before": "Developed features", "after": "Engineered 5 features used by 10K+ users", "time_needed": "30 min"}],
                "red_flags": [{"issue": "No portfolio/GitHub link", "solution": "Add GitHub URL to resume header", "why_matters": "Tech recruiters check GitHub"}],
                "format_issues": ["Ensure consistent formatting throughout"],
                "ats_compatibility": ["✓ Standard headers detected", "⚠ Verify PDF renders correctly in ATS portals"],
                "overall_feedback": "Good foundation. Add metrics to bullets and a professional summary to push your score above 85."
            }

    # ==================== REAL AI CALL ====================
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=3000,
        )

        content = response.choices[0].message.content.strip()
        start = content.find('{')
        end = content.rfind('}') + 1

        if start != -1 and end > start:
            json_str = content[start:end]
            analysis = json.loads(json_str)

            if job_description and job_description.strip():
                analysis["analysis_type"] = "job_match"
                analysis["match_score"] = max(0, min(100, int(analysis.get("match_score", 70))))
                analysis["potential_score"] = max(analysis["match_score"], min(100, int(analysis.get("potential_score", min(100, analysis["match_score"] + 25)))))

                # ======= GUARANTEE 3-WEEK ACTION PLAN =======
                ai_plan = analysis.get("action_plan", [])
                missing = analysis.get("missing_critical_skills", ["Docker", "AWS"])
                ms = analysis["match_score"]
                ps = analysis["potential_score"]

                def get_week(plan, idx, default):
                    if idx < len(plan) and isinstance(plan[idx], dict):
                        w = plan[idx]
                        w.setdefault("week", idx + 1)
                        w.setdefault("priority", ["critical", "high", "medium"][idx])
                        w.setdefault("tasks", default["tasks"])
                        w.setdefault("expected_result", default["expected_result"])
                        w.setdefault("expected_impact", default["expected_impact"])
                        w.setdefault("title", default["title"])
                        return w
                    return {**default, "week": idx + 1}

                week1_default = {
                    "priority": "critical",
                    "title": f"Close Critical Gaps: {', '.join(missing[:2]) if missing else 'Build Skills'}",
                    "tasks": [
                        f"□ Complete hands-on {missing[0] if missing else 'Docker'} tutorial — build and deploy something real",
                        f"□ Set up free {missing[1] if len(missing) > 1 else 'AWS'} account and deploy a live project",
                        "□ Push work to GitHub with a clear README explaining what you built",
                        "□ Update your resume Skills section with all new technologies",
                        "□ Rewrite your top 3 experience bullets with specific metrics"
                    ],
                    "expected_result": f"Hands-on experience with {', '.join(missing[:2]) if missing else 'required skills'} now visible on resume",
                    "expected_impact": f"+{min(20, ps - ms)} points"
                }
                week2_default = {
                    "priority": "high",
                    "title": "Get Certified & Build Portfolio",
                    "tasks": [
                        f"□ Complete free certification for {missing[0] if missing else 'a required skill'} on Coursera/Udemy",
                        f"□ Build a project combining {', '.join(missing[:2]) if len(missing) >= 2 else 'required tech'}",
                        "□ Write a LinkedIn post about your project (demonstrates communication)",
                        "□ Add certifications (even in-progress) to resume and LinkedIn",
                        "□ Tailor your professional summary specifically for this role"
                    ],
                    "expected_result": "Certifications + portfolio prove commitment and capability to recruiters",
                    "expected_impact": f"+{min(15, ps - ms - 5)} points"
                }
                week3_default = {
                    "priority": "medium",
                    "title": "Network, Apply & Follow Up",
                    "tasks": [
                        "□ Connect with 5-10 people at target company on LinkedIn",
                        "□ Contribute to 1 open-source project using required skills",
                        "□ Apply to 10 similar roles with a tailored cover letter",
                        "□ Ask for referrals from your network at target companies",
                        "□ Follow up on all applications after 5-7 business days"
                    ],
                    "expected_result": "Active pipeline backed by strong portfolio and network referrals",
                    "expected_impact": f"+{max(5, ps - ms - 35)} points + referral advantage"
                }

                analysis["action_plan"] = [
                    get_week(ai_plan, 0, week1_default),
                    get_week(ai_plan, 1, week2_default),
                    get_week(ai_plan, 2, week3_default),
                ]

                # Guarantee all required fields exist
                analysis.setdefault("matched_skills", [])
                analysis.setdefault("missing_critical_skills", [])
                analysis.setdefault("missing_nice_to_have", [])
                analysis.setdefault("keyword_analysis", {"resume_keywords": {}, "required_keywords": {}, "keyword_match_rate": 0})
                analysis.setdefault("section_gaps", {})
                analysis.setdefault("improvement_tips", ["Add missing keywords", "Quantify achievements", "Tailor summary to role"])
                analysis.setdefault("ats_prediction", "⚠ Add missing keywords to improve ATS pass rate")
                analysis.setdefault("score_category", "Good Match" if analysis["match_score"] >= 60 else "Needs Work")
                analysis.setdefault("overall_feedback", f"Focus on closing the skill gaps to improve from {analysis['match_score']}% to {analysis['potential_score']}%.")

            else:
                analysis["analysis_type"] = "general"
                analysis["score"] = max(0, min(100, int(analysis.get("score", 70))))
                # Guarantee general fields
                analysis.setdefault("section_scores", {})
                analysis.setdefault("quick_wins", [])
                analysis.setdefault("detailed_strengths", [])
                analysis.setdefault("detailed_weaknesses", [])
                analysis.setdefault("specific_improvements", [])
                analysis.setdefault("red_flags", [])
                analysis.setdefault("format_issues", [])
                analysis.setdefault("ats_compatibility", [])
                analysis.setdefault("overall_feedback", "")

            return analysis
        else:
            raise ValueError("No JSON found in AI response")

    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        # Minimal fallback
        if job_description and job_description.strip():
            return {
                "analysis_type": "job_match",
                "match_score": 65,
                "potential_score": 85,
                "score_category": "Good Match",
                "ats_prediction": "⚠ Analysis limited - add missing keywords manually",
                "matched_skills": [],
                "missing_critical_skills": [],
                "missing_nice_to_have": [],
                "keyword_analysis": {"resume_keywords": {}, "required_keywords": {}, "keyword_match_rate": 0},
                "section_gaps": {},
                "improvement_tips": ["Add keywords from job description", "Quantify experience bullets", "Add professional summary"],
                "action_plan": [
                    {"week": 1, "priority": "critical", "title": "Add Missing Keywords", "tasks": ["□ List all skills from job description", "□ Add matching skills to resume", "□ Rewrite 3 bullets with metrics"], "expected_result": "Better keyword match", "expected_impact": "+20 points"},
                    {"week": 2, "priority": "high", "title": "Build & Certify", "tasks": ["□ Complete relevant certification", "□ Build a portfolio project", "□ Update LinkedIn"], "expected_result": "Certified with proof", "expected_impact": "+15 points"},
                    {"week": 3, "priority": "medium", "title": "Apply & Network", "tasks": ["□ Apply to 10 roles", "□ Connect with recruiters", "□ Follow up on applications"], "expected_result": "Active job pipeline", "expected_impact": "+5 points"}
                ],
                "overall_feedback": "Analysis service is temporarily limited. Review job description manually and add matching keywords."
            }
        return {
            "analysis_type": "general",
            "score": 65,
            "section_scores": {},
            "quick_wins": [],
            "detailed_strengths": [],
            "detailed_weaknesses": [],
            "specific_improvements": [],
            "red_flags": [],
            "format_issues": [],
            "ats_compatibility": [],
            "overall_feedback": "Analysis service temporarily unavailable. Please try again."
        }
