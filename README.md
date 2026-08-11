# 🧭 CareerCompass AI

**AI Career Guidance Assistant for Tier-2/Tier-3 Engineering Students**
Problem Statement 4 — HCLTech GET Hackathon Submission

A guidance-only career, skill-gap, and roadmap assistant for engineering students across CSE, IT, ECE, EE, ME, and Civil — grounded in prepared role data, not real-time job or placement guarantees.

---

## 🎯 What it does

Students often get generic career advice that ignores their branch, actual skills, or realistic entry points. CareerCompass AI takes a student's profile (filled manually or extracted from a resume) and:

- Matches them against curated role families with a plain-language explanation of *why*
- Diffs their current skills against a target role to show what's missing
- Generates a practical 30/60/90-day learning roadmap
- Answers open-ended career questions in English or a regional Indian language, with spoken audio output
- Gives placement cells a lightweight analytics view of skill gaps across a student cohort

Every AI-generated response is explicitly labelled with its source (Gemini-generated vs. rule-based fallback) and carries a "guidance-only, no guarantee" disclaimer — this is a decision-support tool, not an admissions or placement authority.

---

## 🏗️ Five-Layer Architecture

| Layer | Implementation |
|---|---|
| **Data Layer** | `roles.json`, `profiles.json`, `projects.json`, `resources.json` — external files with automatic fallback to built-in mock data if a file is missing or unreadable |
| **RAG / Retrieval Layer** | Lightweight full-context retrieval — the entire curated `ROLES` dataset is injected into every Gemini prompt, which is explicitly instructed not to invent roles or skills outside it. (Not embeddings-based semantic search — a deliberate right-sizing choice at the current dataset scale; see Known Limitations.) |
| **Intelligence Layer** | `call_gemini()` — role matching, skill-gap explanation, and roadmap generation, with an automatic multi-model fallback chain and a deterministic rule-based fallback if no key is present or every model call fails |
| **Application Layer** | Streamlit, 5 tabs: Profile & Skills · Role Matcher · Skill-Gap & Roadmap · Indic Assistant · Responsible AI & Feedback, plus a separate Mentor Dashboard persona, with a light/dark theme toggle |
| **Responsible AI Layer** | Disclaimer badges, source-of-answer labelling, a 1–5 star feedback log, and a Responsible AI checklist visible in-app |

---

## ✨ Key Features

- **Resume upload (PDF/DOCX)** — auto-fills branch, skills, and a projects summary via best-effort keyword extraction; always presented for review before saving, never auto-submitted. Available in both the Profile tab (careful review flow) and the Role Matcher tab (fast one-click match).
- **16 role families across all 6 branches** — CSE/IT-leaning roles (Software Dev, Frontend, Backend, Data/ML, DevOps, QA, Cybersecurity) alongside ECE/EE (Embedded, VLSI, Power Systems), ME (Mechanical Design, Manufacturing, Robotics), and Civil (Structural, Planning/Estimation)
- **Alias-aware skill matching** — a normalization layer (`compute_skill_gap`, `SKILL_EQUIVALENCE_GROUPS`) resolves differently-worded labels for the same real skill (e.g. "AutoCAD" vs. "SolidWorks/AutoCAD" vs. "AutoCAD Electrical") so a student isn't falsely marked as missing a skill they actually have, in either direction.
- **Gemini-powered reasoning** — via the current `google-genai` SDK, with an automatic fallback chain across multiple model candidates that continues past both "model retired" (404) *and* quota-exhaustion (429) errors, since each model has its own separate free-tier quota bucket. Gemini error messages are always simplified into short, human-readable text before ever reaching the UI, translation, or spoken output — raw API error JSON is never shown or read aloud to a user.
- **Sarvam AI Indic integration**, via the official `sarvamai` SDK:
  - **Translate** — answers translated into 11 Indian languages + Hinglish, using `sarvam-translate:v1` (2000-character limit) with defensive input truncation and retry-on-timeout
  - **Bulbul (TTS)** — 29 selectable voices, available as a standalone tool to read roadmaps, answers, or custom text aloud, with downloadable audio and retry-on-timeout
  - **Saaras (STT)** — upload a voice question, transcribed automatically
- **Interactive visualizations** — skill radar chart, readiness gauge, role-match cards, mentor-side skill-gap bar charts (Plotly)
- **Feedback loop** — every session logs a 1–5 rating, a "got a clear next step?" flag, and free-text comments
- **Mentor Dashboard** — persona switch showing role-family distribution and aggregate skill gaps across the student profile dataset (uses illustrative sample data, not live usage — see Known Limitations)

---

## 🛠️ Tech Stack

| Component | Choice |
|---|---|
| Framework | Streamlit |
| LLM | Google Gemini (`google-genai` SDK) |
| Indic AI | Sarvam AI — Chat, Translate, Bulbul TTS, Saaras STT (`sarvamai` SDK) |
| Data | JSON (roles, profiles, projects, resources) |
| Visualization | Plotly (radar, gauge, bar charts) |
| Resume parsing | `pypdf`, `python-docx` |
| Config | `python-dotenv` |

---

## 🚀 Setup

### 1. Clone and install dependencies
```bash
git clone <your-repo-url>
cd careercompass-ai
pip install -r requirements.txt
```

### 2. Configure API keys
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_key_here
SARVAM_API_KEY=your_sarvam_key_here
```
- Gemini key: [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (free tier available, daily quota per model)
- Sarvam key: [dashboard.sarvam.ai](https://dashboard.sarvam.ai) (free credit on signup)

> The app runs without either key — it falls back to rule-based role matching and template roadmaps, with a clear on-screen note that Gemini/Sarvam features are unavailable. Nothing crashes on a missing key.

### 3. Run
```bash
streamlit run app.py
```

### 4. (Optional) Hide the developer toolbar for a clean demo
Add to `.streamlit/config.toml`:
```toml
[client]
toolbarMode = "viewer"
```

---

## 📁 Project Structure

```
careercompass-ai/
├── app.py              # Main Streamlit application
├── requirements.txt
├── roles.json           # Role families, required skills, branch mapping
├── profiles.json         # Sample student profiles (mentor dashboard)
├── projects.json         # Suggested beginner/intermediate projects per role
├── resources.json        # Free learning resources per skill
├── .env                 # API keys (not committed — see .gitignore)
├── .streamlit/
│   └── config.toml       # Theme + toolbar visibility settings
└── README.md
```

Editing the JSON files directly changes what the app teaches and recommends — no code changes needed to expand role coverage, add resources, or update the sample student cohort.

---

## 🔐 Responsible AI Notes

- **No unsupported claims.** The assistant is explicitly instructed never to promise jobs, internships, salaries, or admission outcomes — enforced in every Gemini prompt and restated as a persistent UI badge.
- **Source transparency.** Every AI response states whether it came from Gemini (grounded in the role dataset) or a deterministic rule-based fallback, so a low-confidence answer is never mistaken for a verified one.
- **No sensitive data.** Sample student profiles are generic and non-identifying — no real names, marksheets, or personal records.
- **Resume data stays in-session.** Uploaded resumes are parsed in memory for the current session only; nothing is persisted to disk or a database.
- **Clean failure messages.** API failures (rate limits, timeouts, model deprecation) are always simplified into short, human-readable text — raw JSON error dumps are never surfaced to the user, translated, or read aloud.
- **Feedback loop.** A visible, low-friction feedback mechanism (rating + comment) is built in from the start, not bolted on — supporting iterative improvement of answer quality.

---

## ⚠️ Known Limitations

- **Resume parsing is best-effort keyword matching**, not true NLP/NER extraction — always surfaced for user review before being saved as a profile, never auto-submitted.
- **Retrieval is full-context injection, not embeddings-based RAG.** At 16 roles, the entire dataset fits in a single prompt; this is a deliberate scale-appropriate choice. A larger role dataset (hundreds+) would need a vector store (FAISS/ChromaDB) for genuine semantic retrieval instead.
- **Skill-gap radar chart values are illustrative**, not a precisely measured proficiency score.
- **No authentication or persistent storage across sessions** — every session starts fresh; the Mentor Dashboard uses sample data, not live usage data.
- **Gemini's free tier has a real daily quota per model.** The app's fallback chain tries multiple models automatically, but all models can be exhausted simultaneously under heavy testing — there is no unlimited fallback.
- **Sarvam API calls depend on network reachability** to `api.sarvam.ai`; translate and TTS both retry automatically on timeout and fail gracefully with a clear message rather than crashing.

---

## 🔭 Future Scope

- True per-user authentication so the Mentor Dashboard reflects real, not sample, student data
- Persistent storage (database) for tickets/feedback across sessions, replacing in-memory session state
- Embeddings-based retrieval (FAISS/ChromaDB) once the role dataset grows beyond what fits comfortably in a single prompt
- A dedicated NLP/NER pipeline for higher-confidence resume extraction
- Closing the loop on collected feedback data to actually influence future recommendations

---

## 📜 License

Built as a hackathon prototype for educational/demonstration purposes. Not an official career, admissions, or placement advisory tool.
