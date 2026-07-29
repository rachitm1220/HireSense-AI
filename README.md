<div align="center">

# 🚀 HireSense AI

**An end-to-end, AI-powered career accelerator designed to help job seekers land roles faster.**

[![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq_Llama--3-F05032?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

[Key Features](#-key-features) • [Tech Stack](#-architecture--tech-stack) • [Getting Started](#-getting-started) • [Project Structure](#-repository-structure) • [Contributing](#-contributing)

</div>

---

## 💡 Overview

**HireSense AI** automates the tedious, time-consuming parts of the modern job search. Leveraging ultra-low latency inference via **Llama-3 on Groq**, it dynamically tailors resumes, runs real-time technical & behavioral mock interviews, and builds a community-driven job board powered by smart web scraping.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **📄 AI Resume Tailoring** | Upload a master PDF resume and paste a target Job Description. The system rewrites, aligns, and compiles your experience into an **ATS-compliant LaTeX PDF**. |
| **🎙️ Interactive Mock Interviews** | Practice technical, behavioral, or system design interviews in real-time against a strict AI interviewer. Get detailed scorecards and actionable improvement plans. |
| **🌐 Community Job Board** | Submit Greenhouse or Lever job links. The backend uses **Tinyfish Fetch API** and **Llama-3** to bypass bot blocks, parse markdown, and index structured listings. |
| **📊 Stateless Resume Analyzer** | Get instant 1–100 ATS scores and targeted critiques on your resume on-the-fly, without saving data to the database. |

---

## 🏗️ Architecture & Tech Stack

HireSense AI is architected as a **Monorepo** following **Domain-Driven Design (DDD)** principles to ensure high maintainability and modular scalability.

### **Frontend** (`apps/web`)
* **Framework:** Next.js 14 (App Router, React, TypeScript)
* **Styling:** Tailwind CSS
* **Authentication:** Google OAuth 2.0 (`@react-oauth/google`)
* **Networking:** Axios with custom JWT Interceptors

### **Backend** (`apps/api`)
* **Framework:** FastAPI (Python)
* **Database & ORM:** PostgreSQL / SQLite managed via SQLModel (SQLAlchemy)
* **AI Engine:** Llama-3 (Served via Groq for ultra-low latency)
* **Web Scraping:** Tinyfish Fetch API (Automated markdown extraction)
* **Document Processing:** `pypdf` for parsing, `jinja2` for dynamic LaTeX templating
* **Architecture Pattern:** Domain-Driven Design (auth, users, resumes, jobs, interviews)

---

## 🛠️ Getting Started

### Prerequisites

Ensure you have the following installed locally:
* **Node.js** (v18 or higher)
* **Python** (v3.10 or higher)
* **API Keys:**
  * Groq API Key
  * Tinyfish API Key
  * Google OAuth Client ID

---

### 📥 1. Clone the Repository

```bash
git clone [https://github.com/Vallabh2909/HiresenseAI.git](https://github.com/Vallabh2909/HiresenseAI.git)
cd HiresenseAI
