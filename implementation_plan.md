# NextStep: Career Path & Market Insight Platform

This document outlines the architectural blueprint, technology stack, project structure, and methodology needed to build the **NextStep** platform. The goal is to create a professional, production-ready system to offer career recommendation, skill gap analysis, and geo-location job market trends based on real-time ATS data.

## Goal Description
A comprehensive web application that integrates intelligent data pipelines from ATS platforms (Greenhouse, Lever, Ashby) to provide users with visual, actionable insights regarding their career trajectory and learning path.

---

## 🛠️ Technology Stack & Packages

### 1. Frontend (Client-Side)
- **Core Library**: React.js (Bootstrapped with Vite for instant server start & fast bundles).
- **Styling**: Vanilla CSS with CSS Modules for scoped, highly customized, and modern UI (glassmorphism, micro-animations, fast performant styling without external clutter).
- **Routing**: `react-router-dom` for application navigation.
- **State Management**: Context API (or `Zustand` for lightweight global state).
- **Data Visualization**: `Recharts` or `Chart.js` for rendering professional, interactive analysis graphs.
- **Authentication Forms**: `react-hook-form` coupled with `yup` for clean and robust user inputs.

### 2. Backend (Server-Side)
- **Framework**: Python with Flask (Lightweight, robust, excellent for integrating with data-science models).
- **Database Connectors**: `PyMySQL` and **SQLAlchemy** (ORM model handling).
- **Auth Integrations**: `Flask-JWT-Extended` (for secure session tokens), `Google-Auth` / `Authlib` (for Google Gmail integration).
- **Data Acquisition**: `requests`, ATS official SDKs, and potentially `BeautifulSoup` (for open-source scraping when API boundaries are hit).
- **Data Processing**: `pandas` and `numpy` to format and aggregate job trend metrics. `spacy` or `nltk` for basic NLP to extract skills from job descriptions.
- **Report Generation**: `reportlab` or `pdfkit` to convert analysis dashboards into downloadable PDF reports.

### 3. Database
- **Engine**: MySQL (hosted locally via XAMPP for initial development).

### 4. Testing & Dev Tools
- **API Testing**: Postman.
- **Package Managers**: `npm` (Frontend), `pip` with `virtualenv` (Backend).

---

## 🏗️ Code Structure Recommendation

To ensure scalability, the repository will be separated into strict frontend and backend domains:

```text
NextStep/
├── frontend/                   # React Application
│   ├── src/
│   │   ├── assets/             # Images, Global fonts & Styles
│   │   ├── components/         # Reusable UI (Buttons, Cards, Modals, Nav)
│   │   ├── pages/              # Main Views (Dashboard, SignIn, Analysis, Reports)
│   │   ├── services/           # Axios API calls to the Flask backend
│   │   ├── context/            # Global State (Auth context, User profile)
│   │   ├── utils/              # Helper functions (date formatting, validators)
│   │   ├── App.jsx             # Main Router wrapper
│   │   └── index.css           # Global design system (colors, typography)
│   ├── package.json
│   └── vite.config.js
│
├── backend/                    # Python Flask Application
│   ├── app/
│   │   ├── __init__.py         # Flask App & Extension Initializer
│   │   ├── config.py           # Environment variables & DB settings
│   │   ├── controllers/        # Business Logic (e.g., auth_controller, analysis_controller)
│   │   ├── models/             # Database Schemas (SQLAlchemy Entities)
│   │   ├── routes/             # API Endpoints exposed to frontend
│   │   ├── services/           # ATS API integrations, Data processing scripts
│   │   └── utils/              # JWT Helpers, NLP/ML logic, Error handlers
│   ├── requirements.txt        # Python Dependencies
│   └── run.py                  # Server Entry Point
```

---

## 🚀 Recommended Approach (Phased Rollout)

### Phase 1: Foundation Setup & DB Schema
- Initialize React + Vite and establish the aesthetic design system.
- Set up Flask + MySQL (XAMPP) with SQLAlchemy models for `Users`, `Profiles`, and `SavedReports`.
- Ensure bidirectional communication between React and Flask (CORS, JSON standards).

### Phase 2: Authentication & Profile Engine
- Implement traditional Email/Password Auth (hashing with bcrypt).
- Integrate Google Sign-In for friction-less onboarding.
- Build the User Profile page where users input their existing skills and career goals.

### Phase 3: ATS Data Aggregation Pipeline
- Create background scripts or manual refresh endpoints in Flask to securely call Greenhouse, Lever, and Ashby APIs.
- Cleanse raw JSON data, standardizing job titles, extracting explicit skills required, and mapping them to geo-locations. 

### Phase 4: Analysis & Recommendation Engine
- **Skill Gap**: Compare User Profile Array vs. Aggregated Job Description Array. Compute match percentages.
- **Learning Path**: Suggest missing links/skills mapped directly from the Gap Analysis.
- **Trend Engine**: Cross-match time-series data of job openings vs. skill keyword frequencies.

### Phase 5: Dashboard Visualization & Reports
- Wire data endpoints to Recharts in React to generate beautiful, interactive displays.
- Set up a Flask report endpoint to capture the analytics as a branded PDF.

### Phase 6: Deployment (100% Free Strategy)
To achieve a completely free deployment without sacrificing the background worker or database, we will use a "fragmented" hosting approach utilizing the best free tiers available across the web:

1. **Frontend**: **Vercel** or **Netlify** (Permanent free hosting for React, very fast).
2. **Database**: **Supabase** (Permanent free PostgreSQL database up to 500MB).
3. **Redis**: **Upstash** (Permanent free serverless Redis, 10k requests/day).
4. **Backend + Worker**: **Render** (Free Web Service). We will modify the Dockerfile to run both the Flask API and the Celery worker inside the *same* free container to avoid paying for a separate worker instance.

---

## 💡 Other Professional Recommendations

1. **ORM vs Raw SQL**: While you are using XAMPP/MySQL, I highly recommend using **SQLAlchemy** (Python's leading ORM) instead of raw SQL strings. It makes handling relationships and preventing syntax errors infinitely smoother.
2. **Background Tasks**: Scraping/pulling data from multiple ATS providers during an active user request takes too long (the browser might timeout). I suggest we cache trends in the MySQL database nightly/weekly, so the user experience is lightning fast.
3. **Design System First**: To make it feel premium, we will define a strong, curated color palette (Dark mode, glassmorphism layers, modern typography like 'Inter' or 'Outfit') within `index.css` before spamming UI components. 

---

> [!IMPORTANT]
> ## User Review Required & Open Questions
> 
> You requested a **100% free** hosting setup. Because platforms like Render charge for background workers and delete free databases after 90 days, we have to split the services across a few platforms.
> 
> **Are you okay with signing up for a few different services to keep this entirely free?**
> 1. **Supabase.com** (For the Database)
> 2. **Upstash.com** (For Redis)
> 3. **Render.com** (For the Backend API & Worker combo)
> 4. **Vercel.com** (For the Frontend)
> 
> *Alternatively*, if you have a credit card you can use for verification (it won't be charged), you can sign up for **Oracle Cloud's Always Free Tier**, which gives you a massive 24GB RAM server for free forever. If we use that, we can just run your `docker-compose.yml` and host everything in one place. 
> 
> **Which completely free route do you prefer: The Multi-Platform approach, or Oracle Cloud?**
