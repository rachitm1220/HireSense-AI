# HireSense-AI
HireSense AI is a full-stack, AI-powered career platform designed to help job seekers land roles faster. It leverages Llama-3 (via Groq) to automatically tailor resumes to specific job descriptions, conduct interactive mock interviews, and maintain a community job board with automated JD scraping.

🚀 Key Features
AI Resume Tailoring: Upload a master PDF resume and paste a target Job Description. The LLM extracts, intelligently rewrites, and formats your experience to match the role, exporting a compiled, ATS-compliant LaTeX PDF.
Interactive Mock Interviews: Practice technical, behavioral, or system design interviews in real-time against a strict AI agent. Receive a comprehensive scorecard and actionable feedback plan.
Community Job Board: Submit Greenhouse or Lever URLs. The backend uses the Tinyfish Fetch API and Llama-3 to bypass bot protections, scrape clean markdown, and extract structured data (Title, Company, Location) into a shared community pool.
Stateless Resume Analyzer: Get an instant 1-100 ATS score and critique on your resume without saving it to the database.
🏗️ Architecture & Tech Stack
HireSense AI is structured as a Monorepo implementing Domain-Driven Design (DDD).

🖥️ Frontend (apps/web)
Framework: Next.js 14, React, TypeScript
Styling: Tailwind CSS
Authentication: Google OAuth 2.0 (@react-oauth/google)
Networking: Axios with JWT Interceptors
⚙️ Backend (apps/api)
Framework: FastAPI (Python)
Database & ORM: PostgreSQL / SQLite via SQLModel (SQLAlchemy)
AI Models: Llama-3 (Served via Groq for ultra-low latency)
Scraping Proxy: Tinyfish Fetch API (Markdown extraction)
Document Processing: pypdf (Parsing), jinja2 (LaTeX Templating)
Architecture: Domain-Driven Design (separated by users, resumes, interviews, jobs, auth)
🛠️ Getting Started
Prerequisites
Node.js (v18+)
Python 3.10+
Groq API Key
Tinyfish API Key
Google OAuth Client ID
1. Clone the Repository
git clone https://github.com/Vallabh2909/HiresenseAI.git
cd HiresenseAI
2. Backend Setup
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Create a .env file in apps/api:

DATABASE_URL=sqlite:///./hiresense.db
GROQ_API_KEY=your_groq_api_key
TINYFISH_API_KEY=your_tinyfish_api_key
JWT_SECRET=your_jwt_secret
Run the backend:

uvicorn main:app --reload --port 8001
3. Frontend Setup
cd ../web
npm install
Create a .env.local file in apps/web:

NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
Run the frontend:

npm run dev
The frontend will be available at http://localhost:3000.

📁 Repository Structure
HireSenseAI/
├── apps/
│   ├── api/                 # FastAPI Backend
│   │   ├── core/            # Configs, Database, Templates (Jinja2/LaTeX)
│   │   ├── domains/         # DDD Modules (auth, users, resumes, jobs, interviews)
│   │   └── main.py          # FastAPI Entry Point
│   └── web/                 # Next.js Frontend
│       ├── src/
│       │   ├── app/         # Next.js App Router (Dashboard, Auth, Landing)
│       │   ├── components/  # Reusable UI Components
│       │   └── lib/         # Axios API Client
└── README.md
🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

