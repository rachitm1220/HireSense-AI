import httpx
import json
from groq import Groq
from core.config import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)

async def scrape_job_url(url: str) -> dict:
    """
    1. Uses Tinyfish to fetch the raw Markdown.
    2. Uses Llama-3 to extract structured fields.
    """
    # 1. Fetch from Tinyfish
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.fetch.tinyfish.ai/",
            headers={
                "X-API-Key": settings.TINYFISH_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "urls": [url],
                "format": "markdown"
            },
            timeout=30.0
        )
        
    if response.status_code != 200:
        raise Exception(f"Tinyfish API failed: {response.text}")
        
    data = response.json()
    if data.get("errors") and len(data["errors"]) > 0:
        raise Exception(f"Scrape failed: {data['errors'][0].get('error')}")
        
    markdown_text = data["results"][0]["text"]
    
    # 2. Extract structured data via Llama-3
    prompt = f"""
    You are an expert HR data extractor. Your ONLY job is to accurately identify the specific Job Title, the Hiring Company, and the Job Location from the provided Job Description markdown.
    
    CRITICAL INSTRUCTIONS:
    1. Do NOT extract generic website text like 'Careers', 'Home', 'Apply Now', or 'Open Roles' as the Job Title.
    2. Look for the main heading (e.g., # Software Engineer, ## Senior Product Manager) which represents the actual role being hired for.
    3. If the Company name is missing from the headers, infer it from the context (e.g., "Welcome to Google").
    4. Keep the Title clean (e.g. "Software Engineer" instead of "Software Engineer - Remote").
    
    Return ONLY a valid JSON object matching this schema:
    {{
        "title": "string or null",
        "company": "string or null",
        "location": "string or null"
    }}
    
    JOB DESCRIPTION:
    {markdown_text[:20000]}
    """
    
    completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    extracted = json.loads(completion.choices[0].message.content)
    extracted["description"] = markdown_text # Keep the raw markdown
    return extracted
