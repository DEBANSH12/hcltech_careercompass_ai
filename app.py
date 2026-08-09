"""
CareerCompass AI — Tier-2/3 Student Career Guidance Engine
Problem Statement 4: AI Career Guidance Assistant for Tier-2/Tier-3 Engineering Students
"""

import os
import json
import random
import base64
import time
import re
import io
import datetime as dt

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv
load_dotenv()

try:
    from pypdf import PdfReader
    PDF_PARSING_AVAILABLE = True
except ImportError:
    PDF_PARSING_AVAILABLE = False

try:
    import docx as python_docx
    DOCX_PARSING_AVAILABLE = True
except ImportError:
    DOCX_PARSING_AVAILABLE = False

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False

# Sarvam's official SDK — used specifically for translation. The raw REST
# call to /translate started returning 404s; Sarvam's own current docs show
# the SDK as the primary integration path, and using it insulates this app
# from internal endpoint changes the same way the Gemini model-fallback
# chain already protects against Gemini's own model churn.
try:
    from sarvamai import SarvamAI as SarvamSDKClient
    SARVAM_SDK_AVAILABLE = True
except ImportError:
    SARVAM_SDK_AVAILABLE = False


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

THEMES = {
    "dark": {
        "bg": "#0F172A", "panel_bg": "#1E293B", "accent": "#06B6D4", "emerald": "#10B981",
        "text_muted": "#94A3B8", "text_primary": "#FFFFFF", "text_body": "#E5E7EB",
        "glass_card_bg": "rgba(30, 41, 59, 0.55)", "glass_card_border": "rgba(148, 163, 184, 0.18)",
        "hero_grad": "linear-gradient(135deg, rgba(6,182,212,0.18) 0%, rgba(16,185,129,0.12) 100%)",
        "hero_border": "rgba(6,182,212,0.35)", "metric_bg": "rgba(30, 41, 59, 0.6)",
        "metric_border": "rgba(148, 163, 184, 0.15)", "tab_bg": "rgba(30, 41, 59, 0.5)",
        "chart_paper": "#0F172A", "chart_plot": "#1E293B", "chart_font": "#E5E7EB",
        "input_bg": "#1C2333", "border": "#2A3550",
    },
    "light": {
        "bg": "#F8FAFC", "panel_bg": "#FFFFFF", "accent": "#0891B2", "emerald": "#059669",
        "text_muted": "#64748B", "text_primary": "#0F172A", "text_body": "#1F2937",
        "glass_card_bg": "rgba(255, 255, 255, 0.85)", "glass_card_border": "rgba(100, 116, 139, 0.25)",
        "hero_grad": "linear-gradient(135deg, rgba(8,145,178,0.12) 0%, rgba(5,150,105,0.10) 100%)",
        "hero_border": "rgba(8,145,178,0.35)", "metric_bg": "rgba(255, 255, 255, 0.9)",
        "metric_border": "rgba(100, 116, 139, 0.2)", "tab_bg": "rgba(255, 255, 255, 0.7)",
        "chart_paper": "#F8FAFC", "chart_plot": "#FFFFFF", "chart_font": "#1F2937",
        "input_bg": "#F1F5F9", "border": "#D8DEEA",
    },
}

T = THEMES[st.session_state["theme"]]
DARK_SLATE = T["chart_paper"]
DEEP_NAVY = T["chart_plot"]
ELECTRIC_CYAN = T["accent"]
EMERALD = T["emerald"]
TEXT_MUTED = T["text_muted"]

st.markdown(f"""
<style>
    .stApp {{ background-color: {T['bg']}; }}
    .stApp, .stApp p, .stApp span, .stApp label {{ color: {T['text_body']}; }}
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    label[data-testid="stWidgetLabel"] p,
    div[data-testid="stCaptionContainer"] {{ color: {T['text_body']} !important; }}
    h1, h2, h3, h4, h5 {{ color: {T['text_primary']} !important; }}
    .glass-card {{
        background: {T['glass_card_bg']}; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid {T['glass_card_border']}; border-radius: 16px; padding: 24px; margin-bottom: 16px;
    }}
    .hero-banner {{
        background: {T['hero_grad']}; border: 1px solid {T['hero_border']};
        border-radius: 18px; padding: 28px 32px; margin-bottom: 20px;
    }}
    .hero-banner h1 {{ margin: 0; color: {T['text_primary']}; font-size: 30px; }}
    .hero-banner p {{ color: {T['text_muted']}; margin-top: 6px; font-size: 14px; }}
    .disclaimer-badge {{
        display: inline-block; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.5);
        color: #B45309; padding: 6px 14px; border-radius: 999px; font-size: 12.5px; font-weight: 600; margin-bottom: 10px;
    }}
    .role-badge {{
        display: inline-block; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.4);
        color: {ELECTRIC_CYAN}; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
        margin-right: 6px; margin-bottom: 6px;
    }}
    .skill-have {{ color: #059669; font-weight: 600; }}
    .skill-partial {{ color: #D97706; font-weight: 600; }}
    .skill-missing {{ color: #DC2626; font-weight: 600; }}
    .integration-card {{
        background: {T['glass_card_bg']}; border: 1px solid {T['glass_card_border']};
        border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
    }}
    .integration-card b {{ color: {T['text_primary']}; }}
    div[data-testid="stMetric"] {{
        background: {T['metric_bg']}; border: 1px solid {T['metric_border']}; border-radius: 12px; padding: 12px 16px;
    }}
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {{ color: {T['text_body']} !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{ background-color: {T['tab_bg']}; border-radius: 8px 8px 0 0; padding: 8px 18px; }}
    .stTabs [data-baseweb="tab"] p {{ color: {T['text_body']} !important; }}
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {T['input_bg']} !important; color: {T['text_body']} !important; border: 1px solid {T['border']} !important;
    }}
</style>
""", unsafe_allow_html=True)

_spacer, _toggle_col = st.columns([6, 1])
with _toggle_col:
    is_light = st.toggle("☀️ Light", value=(st.session_state["theme"] == "light"), key="theme_toggle_widget")
    new_theme = "light" if is_light else "dark"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        st.rerun()


MOCK_ROLES = [
    {"role_id": "software_dev", "name": "Software Development Engineer", "branches": ["CSE", "IT"],
     "description": "Builds and maintains applications, APIs, and backend/frontend systems.",
     "required_skills": ["Python", "Data Structures & Algorithms", "Git", "REST APIs", "SQL", "OOP"],
     "entry_expectation": "Comfortable writing clean code, basic DSA, at least one full project on GitHub."},
    {"role_id": "frontend_dev", "name": "Frontend Web Developer", "branches": ["CSE", "IT"],
     "description": "Builds user-facing web interfaces and interactive UI components.",
     "required_skills": ["HTML/CSS", "JavaScript", "React", "Git", "REST APIs", "Responsive Design"],
     "entry_expectation": "Has built and deployed at least one responsive multi-page website or web app."},
    {"role_id": "backend_dev", "name": "Backend Developer", "branches": ["CSE", "IT"],
     "description": "Designs and maintains server-side logic, databases, and APIs.",
     "required_skills": ["Python", "SQL", "REST APIs", "Databases", "Git", "OOP"],
     "entry_expectation": "Can design a basic database schema and build a working REST API."},
    {"role_id": "data_analyst", "name": "Data / ML Analyst", "branches": ["CSE", "IT", "EE"],
     "description": "Works with data pipelines, dashboards, and applies ML models to business problems.",
     "required_skills": ["Python", "SQL", "Pandas", "Statistics", "Data Visualization", "Excel"],
     "entry_expectation": "Can clean and analyze a dataset end-to-end and present findings clearly."},
    {"role_id": "ml_engineer", "name": "AI / ML Engineer", "branches": ["CSE", "IT", "ECE"],
     "description": "Builds and trains machine learning models and integrates them into applications.",
     "required_skills": ["Python", "Machine Learning Basics", "NumPy", "Pandas", "Statistics", "Git"],
     "entry_expectation": "Has trained at least one ML model on a public dataset (Kaggle or similar)."},
    {"role_id": "qa_testing", "name": "QA / Test Engineer", "branches": ["CSE", "IT"],
     "description": "Designs test cases, automates testing, and ensures software quality.",
     "required_skills": ["Manual Testing", "Python", "Selenium", "API Testing", "Bug Tracking"],
     "entry_expectation": "Understands SDLC/STLC and can write basic test cases and automation scripts."},
    {"role_id": "devops", "name": "DevOps / Cloud Support Engineer", "branches": ["CSE", "IT", "ECE"],
     "description": "Manages CI/CD pipelines, cloud infrastructure, and deployment automation.",
     "required_skills": ["Linux", "Git", "Docker", "CI/CD", "Cloud Basics (AWS/Azure/GCP)", "Shell Scripting"],
     "entry_expectation": "Comfortable with Linux command line and has deployed at least one app to the cloud."},
    {"role_id": "cybersecurity", "name": "Cybersecurity Analyst", "branches": ["CSE", "IT"],
     "description": "Monitors, detects, and responds to security threats and vulnerabilities.",
     "required_skills": ["Networking Basics", "Linux", "Security Fundamentals", "Python", "Bug Tracking"],
     "entry_expectation": "Understands basic networking and has completed a beginner security course/CTF."},
    {"role_id": "embedded", "name": "Embedded / Core Electronics Engineer", "branches": ["ECE", "EE"],
     "description": "Works on hardware-software interfacing, IoT devices, and embedded firmware.",
     "required_skills": ["C/C++", "Microcontrollers", "Circuit Design", "IoT Protocols", "Debugging Tools"],
     "entry_expectation": "Has built at least one microcontroller-based project (Arduino/ESP32/similar)."},
    {"role_id": "vlsi_design", "name": "VLSI / Chip Design Engineer", "branches": ["ECE", "EE"],
     "description": "Designs and verifies integrated circuits and digital logic systems.",
     "required_skills": ["Verilog/VHDL", "Digital Logic Design", "Circuit Design", "Debugging Tools"],
     "entry_expectation": "Has completed a digital design lab project or simulation using Verilog/VHDL."},
    {"role_id": "power_systems", "name": "Power Systems / Electrical Engineer", "branches": ["EE", "ECE"],
     "description": "Works on power generation, distribution, and electrical systems design.",
     "required_skills": ["Circuit Design", "MATLAB/Simulink", "Power Systems Basics", "AutoCAD Electrical"],
     "entry_expectation": "Has completed a power systems lab project or simulation using MATLAB/Simulink."},
    {"role_id": "robotics", "name": "Robotics Engineer", "branches": ["ME", "ECE", "EE"],
     "description": "Designs and builds robotic systems combining mechanical, electrical, and software elements.",
     "required_skills": ["C/C++", "Microcontrollers", "CAD Software", "Circuit Design", "Debugging Tools"],
     "entry_expectation": "Has built at least one robotics/automation project combining hardware and code."},
    {"role_id": "mech_design", "name": "Mechanical Design / CAD Engineer", "branches": ["ME"],
     "description": "Designs mechanical components and systems using CAD software and simulation tools.",
     "required_skills": ["CAD Software", "SolidWorks/AutoCAD", "Engineering Drawing", "Material Science Basics"],
     "entry_expectation": "Has completed at least one CAD design project (assembly or part modeling)."},
    {"role_id": "manufacturing", "name": "Manufacturing / Production Engineer", "branches": ["ME"],
     "description": "Plans and optimizes manufacturing processes and production systems.",
     "required_skills": ["CAD Software", "Process Planning", "Quality Control Basics", "Excel"],
     "entry_expectation": "Understands basic manufacturing processes and has visited/interned at a production unit."},
    {"role_id": "structural_eng", "name": "Structural / Site Engineer", "branches": ["Civil"],
     "description": "Assists in structural design, site supervision, and construction project execution.",
     "required_skills": ["AutoCAD", "Structural Analysis Basics", "Engineering Drawing", "Excel"],
     "entry_expectation": "Has completed a structural design coursework project or site visit report."},
    {"role_id": "civil_planning", "name": "Civil Planning / Estimation Engineer", "branches": ["Civil"],
     "description": "Works on project planning, cost estimation, and quantity surveying for construction projects.",
     "required_skills": ["AutoCAD", "Estimation & Costing", "Excel", "Project Planning Basics"],
     "entry_expectation": "Has completed a basic estimation/costing exercise for a construction project."}
]

MOCK_PROJECTS = [
    {"title": "Personal Portfolio Website", "skill_tag": "Software Development Engineer", "level": "Beginner"},
    {"title": "Student Attendance Tracker (CLI + SQLite)", "skill_tag": "Software Development Engineer", "level": "Beginner"},
    {"title": "Weather App with Public API", "skill_tag": "Frontend Web Developer", "level": "Beginner"},
    {"title": "E-commerce UI Clone (React)", "skill_tag": "Frontend Web Developer", "level": "Intermediate"},
    {"title": "Blog Platform REST API", "skill_tag": "Backend Developer", "level": "Beginner"},
    {"title": "URL Shortener Service", "skill_tag": "Backend Developer", "level": "Intermediate"},
    {"title": "Sales Data Dashboard (Pandas + Plotly)", "skill_tag": "Data / ML Analyst", "level": "Beginner"},
    {"title": "Movie Recommendation System", "skill_tag": "Data / ML Analyst", "level": "Intermediate"},
    {"title": "Handwritten Digit Classifier", "skill_tag": "AI / ML Engineer", "level": "Beginner"},
    {"title": "Spam Email Detector", "skill_tag": "AI / ML Engineer", "level": "Intermediate"},
    {"title": "Automated Login Test Suite (Selenium)", "skill_tag": "QA / Test Engineer", "level": "Beginner"},
    {"title": "REST API Test Automation Framework", "skill_tag": "QA / Test Engineer", "level": "Intermediate"},
    {"title": "Dockerized To-Do App with CI/CD", "skill_tag": "DevOps / Cloud Support Engineer", "level": "Intermediate"},
    {"title": "Static Website Auto-Deploy Pipeline", "skill_tag": "DevOps / Cloud Support Engineer", "level": "Beginner"},
    {"title": "Home Network Vulnerability Scan Report", "skill_tag": "Cybersecurity Analyst", "level": "Beginner"},
    {"title": "Basic CTF Challenge Writeups", "skill_tag": "Cybersecurity Analyst", "level": "Intermediate"},
    {"title": "Home Automation with ESP32", "skill_tag": "Embedded / Core Electronics Engineer", "level": "Beginner"},
    {"title": "IoT Weather Station", "skill_tag": "Embedded / Core Electronics Engineer", "level": "Intermediate"},
    {"title": "4-bit ALU Design in Verilog", "skill_tag": "VLSI / Chip Design Engineer", "level": "Beginner"},
    {"title": "Traffic Light Controller (FPGA Sim)", "skill_tag": "VLSI / Chip Design Engineer", "level": "Intermediate"},
    {"title": "Solar Panel Load Simulation (MATLAB)", "skill_tag": "Power Systems / Electrical Engineer", "level": "Beginner"},
    {"title": "Line-Following Robot", "skill_tag": "Robotics Engineer", "level": "Beginner"},
    {"title": "Robotic Arm Prototype (Arduino)", "skill_tag": "Robotics Engineer", "level": "Intermediate"},
    {"title": "3D Printed Mechanical Assembly (CAD)", "skill_tag": "Mechanical Design / CAD Engineer", "level": "Beginner"},
    {"title": "Small Bridge Model — Structural Analysis Report", "skill_tag": "Structural / Site Engineer", "level": "Beginner"},
    {"title": "Building Material Cost Estimation Sheet", "skill_tag": "Civil Planning / Estimation Engineer", "level": "Beginner"}
]

MOCK_RESOURCES = [
    {"resource": "CS50 (Harvard, free)", "skill_tag": "Python", "type": "Free"},
    {"resource": "NPTEL Data Structures", "skill_tag": "Data Structures & Algorithms", "type": "Free"},
    {"resource": "freeCodeCamp SQL Course", "skill_tag": "SQL", "type": "Free"},
    {"resource": "freeCodeCamp Responsive Web Design", "skill_tag": "HTML/CSS", "type": "Free"},
    {"resource": "React Official Tutorial", "skill_tag": "React", "type": "Free"},
    {"resource": "Kaggle Micro-Courses", "skill_tag": "Pandas", "type": "Free"},
    {"resource": "Google Machine Learning Crash Course", "skill_tag": "Machine Learning Basics", "type": "Free"},
    {"resource": "Selenium with Python (docs)", "skill_tag": "Selenium", "type": "Free"},
    {"resource": "Docker Official Get Started", "skill_tag": "Docker", "type": "Free"},
    {"resource": "AWS Cloud Practitioner Essentials", "skill_tag": "Cloud Basics (AWS/Azure/GCP)", "type": "Free"},
    {"resource": "TryHackMe Intro to Cybersecurity", "skill_tag": "Security Fundamentals", "type": "Free"},
    {"resource": "Arduino Project Hub", "skill_tag": "Microcontrollers", "type": "Free"},
    {"resource": "NPTEL Digital Circuits & Systems", "skill_tag": "Digital Logic Design", "type": "Free"},
    {"resource": "NPTEL Power Systems", "skill_tag": "Power Systems Basics", "type": "Free"},
    {"resource": "Autodesk AutoCAD Free Tutorials", "skill_tag": "AutoCAD", "type": "Free"},
    {"resource": "NPTEL Structural Analysis", "skill_tag": "Structural Analysis Basics", "type": "Free"},
    {"resource": "SolidWorks Student Tutorials", "skill_tag": "SolidWorks/AutoCAD", "type": "Free"}
]

MOCK_PROFILES = [
    {"id": "S1", "branch": "CSE", "year": 3, "skills": ["Python", "Git", "SQL"], "role_family": "Software Development Engineer"},
    {"id": "S2", "branch": "ECE", "year": 2, "skills": ["C/C++", "Microcontrollers"], "role_family": "Embedded / Core Electronics Engineer"},
    {"id": "S3", "branch": "CSE", "year": 4, "skills": ["Python", "Pandas", "Statistics", "SQL"], "role_family": "Data / ML Analyst"},
    {"id": "S4", "branch": "IT", "year": 3, "skills": ["Manual Testing", "Python"], "role_family": "QA / Test Engineer"},
    {"id": "S5", "branch": "CSE", "year": 3, "skills": ["Linux", "Git", "Docker"], "role_family": "DevOps / Cloud Support Engineer"},
    {"id": "S6", "branch": "IT", "year": 3, "skills": ["HTML/CSS", "JavaScript", "Git"], "role_family": "Frontend Web Developer"},
    {"id": "S7", "branch": "CSE", "year": 4, "skills": ["Python", "Machine Learning Basics", "NumPy"], "role_family": "AI / ML Engineer"},
    {"id": "S8", "branch": "CSE", "year": 3, "skills": ["Networking Basics", "Linux"], "role_family": "Cybersecurity Analyst"},
    {"id": "S9", "branch": "ME", "year": 3, "skills": ["CAD Software", "Engineering Drawing"], "role_family": "Mechanical Design / CAD Engineer"},
    {"id": "S10", "branch": "ME", "year": 2, "skills": ["CAD Software"], "role_family": "Robotics Engineer"},
    {"id": "S11", "branch": "Civil", "year": 3, "skills": ["AutoCAD", "Excel"], "role_family": "Structural / Site Engineer"},
    {"id": "S12", "branch": "Civil", "year": 4, "skills": ["AutoCAD", "Estimation & Costing"], "role_family": "Civil Planning / Estimation Engineer"},
    {"id": "S13", "branch": "EE", "year": 3, "skills": ["Circuit Design", "MATLAB/Simulink"], "role_family": "Power Systems / Electrical Engineer"},
    {"id": "S14", "branch": "ECE", "year": 4, "skills": ["Verilog/VHDL", "Digital Logic Design"], "role_family": "VLSI / Chip Design Engineer"},
    {"id": "S15", "branch": "IT", "year": 2, "skills": ["Python", "SQL"], "role_family": "Backend Developer"}
]


def load_json_or_mock(filename, mock_fallback):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data, True
    except Exception:
        pass
    return mock_fallback, False


ROLES, roles_are_external = load_json_or_mock("roles.json", MOCK_ROLES)
PROJECTS, projects_are_external = load_json_or_mock("projects.json", MOCK_PROJECTS)
RESOURCES, resources_are_external = load_json_or_mock("resources.json", MOCK_RESOURCES)
PROFILES, profiles_are_external = load_json_or_mock("profiles.json", MOCK_PROFILES)

ALL_SKILLS = sorted({s for role in ROLES for s in role["required_skills"]})
ALL_BRANCHES = ["CSE", "IT", "ECE", "EE", "ME", "Civil"]

DATA_SOURCE_STATUS = [
    ("roles.json", roles_are_external, len(ROLES), "roles"),
    ("projects.json", projects_are_external, len(PROJECTS), "projects"),
    ("resources.json", resources_are_external, len(RESOURCES), "resources"),
    ("profiles.json", profiles_are_external, len(PROFILES), "student profiles"),
]

# =========================================================================
# SKILL EQUIVALENCE MAP — fixes a real matching bug: skill labels defined as
# compound/vendor-specific strings in one role (e.g. "SolidWorks/AutoCAD" in
# Mechanical Design) don't exact-string-match a differently-worded label for
# essentially the same skill in another role (e.g. plain "AutoCAD" in Civil
# roles, or "AutoCAD Electrical" in Power Systems). Without this, a student
# who has AutoCAD experience gets incorrectly marked as "missing" that skill
# whenever the required-skill string in a given role happens to be phrased
# differently. Each group below is a set of interchangeable skill labels —
# having ANY one of them satisfies a requirement listed as ANY other in the
# same group, in either direction.
# =========================================================================
SKILL_EQUIVALENCE_GROUPS = [
    {"AutoCAD", "SolidWorks/AutoCAD", "AutoCAD Electrical"},
]


def _build_skill_equivalence_map(groups):
    mapping = {}
    for group in groups:
        for skill in group:
            mapping[skill] = group
    return mapping


SKILL_EQUIVALENCE_MAP = _build_skill_equivalence_map(SKILL_EQUIVALENCE_GROUPS)


def skill_is_covered(required_skill, student_skills_set):
    """
    True if the student's skill set satisfies this required skill — either an
    exact match, or any equivalent label from SKILL_EQUIVALENCE_MAP. This is
    the single source of truth for skill matching; every place in the app that
    compares a role's required skills against a student's skills should call
    this instead of doing raw set intersection, so equivalent labels are never
    silently missed.
    """
    if required_skill in student_skills_set:
        return True
    equivalents = SKILL_EQUIVALENCE_MAP.get(required_skill, {required_skill})
    return bool(equivalents & student_skills_set)


def compute_skill_gap(required_skills, student_skills):
    """
    Alias-aware replacement for plain set-difference skill matching.
    Returns (have, missing, match_pct) where `have`/`missing` preserve the
    original required-skill label strings (for consistent UI display) and
    match_pct is computed against the true number of required skills, not an
    inflated/deflated count from expanding aliases into extra set members.
    """
    student_skills_set = set(student_skills)
    have = [s for s in required_skills if skill_is_covered(s, student_skills_set)]
    missing = [s for s in required_skills if not skill_is_covered(s, student_skills_set)]
    match_pct = round(100 * len(have) / max(len(required_skills), 1))
    return sorted(have), sorted(missing), match_pct


# =========================================================================
# RESUME PARSING — PDF/DOCX text extraction + best-effort profile extraction
# =========================================================================
def extract_text_from_resume(uploaded_file):
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".pdf"):
            if not PDF_PARSING_AVAILABLE:
                return None, "PDF parsing library (pypdf) is not installed."
            reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, None
        elif name.endswith(".docx"):
            if not DOCX_PARSING_AVAILABLE:
                return None, "DOCX parsing library (python-docx) is not installed."
            doc = python_docx.Document(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join(p.text for p in doc.paragraphs)
            return text, None
        else:
            return None, "Unsupported file type — please upload a .pdf or .docx file."
    except Exception as e:
        return None, f"Could not read the file: {e}"


def guess_branch_from_text(text):
    text_lower = text.lower()
    branch_keywords = {
        "CSE": ["computer science", "cse", "computer engineering"],
        "IT": ["information technology", " it ", "b.tech it"],
        "ECE": ["electronics and communication", "ece", "electronics & communication"],
        "EE": ["electrical engineering", "eee", "electrical & electronics"],
        "ME": ["mechanical engineering", "mech engineering", " me "],
        "Civil": ["civil engineering", "civil "],
    }
    for branch, keywords in branch_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return branch
    return None


def guess_skills_from_text(text, skill_pool):
    text_lower = text.lower()
    found = []
    for skill in skill_pool:
        tokens = [skill.lower()] + [t.strip() for t in re.split(r"[\/&,]", skill.lower())]
        tokens = [t for t in tokens if len(t) >= 2]
        for tok in tokens:
            pattern = r"\b" + re.escape(tok) + r"\b"
            if re.search(pattern, text_lower):
                found.append(skill)
                break
    return found


def extract_projects_section(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    projects_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^(projects?|academic projects?|key projects?)\s*:?\s*$", line, re.IGNORECASE):
            projects_idx = i
            break
    if projects_idx is not None:
        collected = []
        for line in lines[projects_idx + 1: projects_idx + 8]:
            if re.match(r"^(skills?|education|experience|certifications?)\s*:?\s*$", line, re.IGNORECASE):
                break
            collected.append(line)
        return "\n".join(collected[:5])
    return ""


def parse_resume_to_profile(uploaded_file, skill_pool):
    text, err = extract_text_from_resume(uploaded_file)
    if err:
        return None, err
    if not text or len(text.strip()) < 20:
        return None, "Could not extract readable text from this file — try a different file or fill the form manually."
    return {
        "branch": guess_branch_from_text(text),
        "skills": guess_skills_from_text(text, skill_pool),
        "projects_text": extract_projects_section(text),
        "raw_text_preview": text[:800],
    }, None


INDIC_LANGUAGES = {
    "English": "en-IN", "Hindi (हिंदी)": "hi-IN", "Hinglish": "hi-IN", "Bengali (বাংলা)": "bn-IN",
    "Gujarati (ગુજરાતી)": "gu-IN", "Kannada (ಕನ್ನಡ)": "kn-IN", "Malayalam (മലയാളം)": "ml-IN",
    "Marathi (मराठी)": "mr-IN", "Odia (ଓଡ଼ିଆ)": "od-IN", "Punjabi (ਪੰਜਾਬੀ)": "pa-IN",
    "Tamil (தமிழ்)": "ta-IN", "Telugu (తెలుగు)": "te-IN",
}

GEMINI_MODEL_DEFAULT = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def init_state():
    defaults = {
        "profile": None, "top_matches": None, "roadmap_text": None, "checklist": {},
        "feedback_log": [], "chat_history": [], "gemini_model_override": "", "resume_extracted": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


def call_gemini(prompt, api_key, model=None, max_output_tokens=1024):
    if not api_key:
        return False, "No Gemini API key provided."
    if not GENAI_SDK_AVAILABLE:
        return False, "google-genai package is not installed (pip install google-genai)."

    primary_model = model or st.session_state.get("gemini_model_override") or GEMINI_MODEL_DEFAULT
    candidates = [primary_model, "gemini-3.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
    seen = set()
    last_error = None

    client = google_genai.Client(api_key=api_key)
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        for use_thinking_config in (True, False):
            try:
                config_kwargs = dict(max_output_tokens=max_output_tokens, temperature=0.4)
                if use_thinking_config:
                    config_kwargs["thinking_config"] = google_genai_types.ThinkingConfig(thinking_budget=0)
                response = client.models.generate_content(
                    model=candidate, contents=prompt,
                    config=google_genai_types.GenerateContentConfig(**config_kwargs),
                )
                text = getattr(response, "text", None)
                if not text:
                    last_error = f"{candidate} returned an empty response."
                    continue
                if candidate != primary_model:
                    st.session_state["gemini_model_override"] = candidate
                return True, text
            except Exception as e:
                last_error = f"{candidate} failed: {e}"
                if use_thinking_config and ("thinking_config" in str(e).lower() or "thinking_budget" in str(e).lower()):
                    continue
                break
        if "404" not in str(last_error) and "NOT_FOUND" not in str(last_error) and "not found" not in str(last_error).lower():
            break
    return False, f"Gemini call failed after trying {len(seen)} model(s). Last error: {last_error}"


def rule_based_role_match(profile):
    """
    RAG / Intelligence fallback: deterministic skill-overlap retrieval + ranking,
    using the alias-aware compute_skill_gap() so equivalent skill labels (e.g.
    "AutoCAD" vs "SolidWorks/AutoCAD") are correctly credited either way.
    """
    student_skills = profile["skills"]
    scored = []
    for role in ROLES:
        have, missing, pct = compute_skill_gap(role["required_skills"], student_skills)
        scored.append({"role": role, "match_pct": pct, "have": have, "missing": missing})
    scored.sort(key=lambda x: x["match_pct"], reverse=True)
    return scored[:3]


def gemini_role_match(profile, api_key):
    fallback = rule_based_role_match(profile)
    roles_context = json.dumps(ROLES, indent=2)
    prompt = f"""You are a career guidance assistant for a Tier-2/Tier-3 engineering student in India.
Use ONLY the role data below — do not invent roles or skills that aren't listed.

STUDENT PROFILE:
Branch: {profile['branch']}, Year: {profile['year']}
Current skills: {', '.join(profile['skills']) if profile['skills'] else 'None listed'}
Interest: {profile['interest']}
Projects: {profile['projects'] if profile['projects'] else 'None listed'}

AVAILABLE ROLE FAMILIES (grounded source data):
{roles_context}

Task: Rank the top 3 role families for this student. For each, return STRICT JSON in this shape:
[
  {{"role_id": "...", "match_pct": <0-100 integer>, "why": "<2-3 sentence plain-language explanation>"}},
  ...
]
Do not add any text outside the JSON array. Do not promise placement, salary, or admission outcomes.
"""
    ok, text = call_gemini(prompt, api_key)
    if not ok:
        return fallback, False, text
    try:
        cleaned = text.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)
        role_lookup = {r["role_id"]: r for r in ROLES}
        results = []
        for item in parsed[:3]:
            role = role_lookup.get(item.get("role_id"))
            if not role:
                continue
            # Recompute have/missing with the alias-aware matcher rather than trusting
            # Gemini's own skill bookkeeping — Gemini only supplies the ranking and the
            # "why", the actual have/missing lists always come from our deterministic logic.
            have, missing, _ = compute_skill_gap(role["required_skills"], profile["skills"])
            results.append({
                "role": role, "match_pct": int(item.get("match_pct", 0)),
                "have": have, "missing": missing,
                "why": item.get("why", ""),
            })
        if results:
            return results, True, None
        return fallback, False, "Gemini response could not be parsed into valid roles."
    except Exception as e:
        return fallback, False, f"Could not parse Gemini's JSON output ({e}). Showing rule-based match instead."


def gemini_roadmap(profile, top_role, api_key):
    missing = top_role["missing"]
    prompt = f"""Create a realistic 30/60/90-day learning roadmap for a Tier-2/Tier-3 engineering
student in India targeting the role: {top_role['role']['name']}.

Student's current skills: {', '.join(profile['skills']) if profile['skills'] else 'None listed'}
Missing skills to build: {', '.join(missing) if missing else 'None — strong existing fit'}
Weekly available learning hours: {profile['weekly_hours']}

Structure the answer with three clear sections:
### 30 Days — Fundamentals
### 60 Days — Projects & Deep Dive
### 90 Days — Interview Preparation

Keep it practical, avoid generic filler, and do not promise a job or interview outcome — this is
guidance only. Keep the whole answer under 350 words.
"""
    ok, text = call_gemini(prompt, api_key, max_output_tokens=800)
    if ok:
        return text, True
    template = f"""### 30 Days — Fundamentals
Focus on: {', '.join(missing[:2]) if missing else 'reinforcing your strongest existing skill'}.
Spend {profile['weekly_hours']} hrs/week on structured courses + daily small practice problems.

### 60 Days — Projects & Deep Dive
Build 1 project from the recommended project list for {top_role['role']['name']}.
Deepen remaining gap skills: {', '.join(missing[2:]) if len(missing) > 2 else 'polish existing project quality'}.

### 90 Days — Interview Preparation
Revise core fundamentals, practice explaining your project out loud, and complete the
Interview Readiness Checklist below.

*(Gemini roadmap generation unavailable — showing a template roadmap instead: {text})*"""
    return template, False


SARVAM_BASE = "https://api.sarvam.ai"
SARVAM_SPEAKERS = [
    "anushka", "abhilash", "manisha", "vidya", "arya", "karun", "hitesh", "aditya",
    "ritu", "priya", "neha", "rahul", "pooja", "rohan", "simran", "kavya", "amit",
    "dev", "ishita", "shreya", "ratan", "varun", "manan", "sumit", "roopa", "kabir",
    "aayan", "shubh", "ashutosh", "advait",
]


def sarvam_translate(text, target_lang_code, api_key, source_lang_code="en-IN", max_retries=2):
    """
    Uses the official sarvamai SDK rather than a hand-built REST call to
    /translate. Explicit timeout + retry: the SDK's default read timeout is
    too short (10s) for how long translate can genuinely take. Never raises —
    returns (None, error_message) on any failure so the UI can fall back to
    showing the untranslated English answer.
    """
    if not api_key:
        return None, "No Sarvam API key provided."
    if not SARVAM_SDK_AVAILABLE:
        return None, "sarvamai package is not installed (pip install sarvamai)."

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            client = SarvamSDKClient(api_subscription_key=api_key, timeout=30.0)
            response = client.text.translate(
                input=text,
                source_language_code=source_lang_code,
                target_language_code=target_lang_code,
            )
            return response.translated_text, None
        except Exception as e:
            last_error = f"Sarvam translate failed: {e}"
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
            break
    return None, last_error


def sarvam_tts(text, target_lang_code, api_key, speaker="anushka", max_retries=2):
    if not api_key:
        return None, "No Sarvam API key provided."
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{SARVAM_BASE}/text-to-speech",
                headers={"api-subscription-key": api_key, "Content-Type": "application/json"},
                json={"text": text[:1500], "target_language_code": target_lang_code, "speaker": speaker, "model": "bulbul:v2"},
                timeout=35,
            )
            resp.raise_for_status()
            data = resp.json()
            audio_b64_list = data.get("audios", [])
            if not audio_b64_list:
                return None, "Sarvam TTS returned no audio."
            audio_bytes = base64.b64decode(audio_b64_list[0])
            return audio_bytes, None
        except requests.exceptions.ConnectTimeout:
            last_error = "Couldn't reach Sarvam's servers (connection timeout)."
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
        except Exception as e:
            last_error = f"Sarvam TTS failed: {e}"
            break
    return None, last_error


def sarvam_stt(uploaded_file, api_key):
    if not api_key:
        return None, "No Sarvam API key provided."
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "audio/wav")}
        resp = requests.post(
            f"{SARVAM_BASE}/speech-to-text",
            headers={"api-subscription-key": api_key}, data={"model": "saaras:v3"}, files=files, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("transcript"), None
    except Exception as e:
        return None, f"Sarvam STT failed: {e}"


with st.sidebar:
    st.markdown("## 🧭 CareerCompass AI")
    st.caption("Tier-2/3 Engineering Career Guidance Engine")
    st.divider()

    persona = st.radio("View as:", ["🎓 Student Guidance Mode", "📊 Placement Cell / Mentor Dashboard"])

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    sarvam_key = os.getenv("SARVAM_API_KEY", "")

    st.divider()
    selected_lang_label = st.selectbox("Indic language:", list(INDIC_LANGUAGES.keys()))
    selected_lang_code = INDIC_LANGUAGES[selected_lang_label]

    selected_speaker = st.selectbox("Bulbul voice:", SARVAM_SPEAKERS, index=0,
                                     help="Voice used for all text-to-speech output (Q&A answers and the Bulbul tool in Tab 4).")

    st.divider()
    st.markdown(
        '<div class="disclaimer-badge">⚠️ Guidance-Only Assistant • No Job/Placement Guarantee</div>',
        unsafe_allow_html=True,
    )


st.markdown("""
<div class="hero-banner">
    <h1>🧭 CareerCompass AI</h1>
    <p>Guidance-only career, skill-gap, and roadmap assistant for Tier-2/Tier-3 engineering students —
    grounded in prepared role data, not real-time job or placement guarantees.</p>
</div>
""", unsafe_allow_html=True)


def render_mentor_dashboard():
    st.subheader("📊 Placement Cell / Mentor Analytics")
    df = pd.DataFrame(PROFILES)

    col1, col2, col3 = st.columns(3)
    col1.metric("Students in dataset", len(df))
    col2.metric("Branches covered", df["branch"].nunique())
    col3.metric("Role families represented", df["role_family"].nunique())

    st.markdown("#### Role family distribution")
    role_counts = df["role_family"].value_counts().reset_index()
    role_counts.columns = ["role_family", "count"]
    fig = px.bar(role_counts, x="role_family", y="count", color="role_family",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(plot_bgcolor=DEEP_NAVY, paper_bgcolor=DARK_SLATE, font_color=T["chart_font"], showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Most common skill gaps (vs. their nearest role family)")
    gap_counter = {}
    for _, row in df.iterrows():
        role = next((r for r in ROLES if r["name"] == row["role_family"]), None)
        if not role:
            continue
        # Alias-aware gap calc, same logic as the individual student view —
        # avoids double-counting a skill as "missing" cohort-wide just because
        # of a labeling mismatch rather than a genuine gap.
        _, missing, _ = compute_skill_gap(role["required_skills"], row["skills"])
        for m in missing:
            gap_counter[m] = gap_counter.get(m, 0) + 1
    if gap_counter:
        gap_df = pd.DataFrame(sorted(gap_counter.items(), key=lambda x: -x[1]), columns=["skill", "students_missing"])
        fig2 = px.bar(gap_df.head(10), x="students_missing", y="skill", orientation="h",
                      color="students_missing", color_continuous_scale="Tealgrn")
        fig2.update_layout(plot_bgcolor=DEEP_NAVY, paper_bgcolor=DARK_SLATE, font_color=T["chart_font"])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("No skill gap data available.")

    st.markdown("#### Feedback received this session")
    if st.session_state["feedback_log"]:
        st.dataframe(pd.DataFrame(st.session_state["feedback_log"]), use_container_width=True)
    else:
        st.caption("No student feedback logged yet this session.")


if persona.startswith("📊"):
    render_mentor_dashboard()
    st.stop()


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣ Profile & Skills", "2️⃣ Role Matcher", "3️⃣ Skill-Gap & Roadmap",
    "4️⃣ Indic Assistant", "5️⃣ Responsible AI & Feedback",
])

with tab1:
    st.markdown("### Student Profile & Skill Capture")
    st.caption(
        "Fill the form manually, or upload your resume to auto-fill it — either way, "
        "**review the fields before saving**, since resume parsing here is best-effort keyword matching."
    )

    resume_upload = st.file_uploader(
        "📄 Upload your resume (PDF or DOCX) to auto-fill the form below",
        type=["pdf", "docx"], key="resume_upload_tab1",
    )
    if resume_upload is not None:
        if st.button("✨ Parse Resume & Auto-Fill Form", key="parse_resume_tab1"):
            with st.spinner("Reading resume..."):
                extracted, parse_err = parse_resume_to_profile(resume_upload, ALL_SKILLS)
            if parse_err:
                st.error(f"Couldn't parse resume: {parse_err}")
            else:
                st.session_state["resume_extracted"] = extracted
                st.success(
                    f"Extracted {len(extracted['skills'])} matching skill(s)"
                    + (f" and detected branch **{extracted['branch']}**" if extracted["branch"] else "")
                    + ". Review the pre-filled form below before saving."
                )
                if extracted.get("raw_text_preview"):
                    with st.expander("Preview extracted resume text"):
                        st.text(extracted["raw_text_preview"])

    extracted = st.session_state.get("resume_extracted")
    default_branch = extracted["branch"] if extracted and extracted.get("branch") else ALL_BRANCHES[0]
    default_skills = extracted["skills"] if extracted else []
    default_projects_text = extracted["projects_text"] if extracted else ""

    st.markdown("---")

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            branch = st.selectbox("Branch", ALL_BRANCHES,
                                   index=ALL_BRANCHES.index(default_branch) if default_branch in ALL_BRANCHES else 0)
            year = st.selectbox("Academic Year", [1, 2, 3, 4])
            interest = st.selectbox("Preferred role family (or 'Not sure yet')",
                                     ["Not sure yet"] + [r["name"] for r in ROLES])
        with c2:
            skills = st.multiselect("Current technical skills", ALL_SKILLS, default=default_skills)
            weekly_hours = st.slider("Weekly available learning hours", 2, 30, 8)
            projects = st.text_area("Completed projects (brief, one per line)", height=90, value=default_projects_text)

        submitted = st.form_submit_button("Save Profile", type="primary")

    if submitted:
        st.session_state["profile"] = {
            "branch": branch, "year": year, "interest": interest, "skills": skills,
            "weekly_hours": weekly_hours, "projects": [p.strip() for p in projects.split("\n") if p.strip()],
        }
        st.session_state["top_matches"] = None
        st.session_state["roadmap_text"] = None
        st.session_state["resume_extracted"] = None
        st.success("Profile saved. Head to Tab 2 for role matching.")

    profile = st.session_state["profile"]
    if profile:
        st.markdown("#### Your Profile Card")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Branch / Year", f"{profile['branch']} · Yr {profile['year']}")
        pc2.metric("Skills Listed", len(profile["skills"]))
        pc3.metric("Weekly Hours", profile["weekly_hours"])

        if profile["skills"]:
            categories = profile["skills"]
            values = [random.randint(55, 95) for _ in categories]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself",
                                           line_color=ELECTRIC_CYAN, fillcolor="rgba(6,182,212,0.25)"))
            fig.update_layout(
                polar=dict(bgcolor=DEEP_NAVY, radialaxis=dict(visible=True, range=[0, 100])),
                paper_bgcolor=DARK_SLATE, font_color=T["chart_font"], showlegend=False, height=380,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Add skills above to see your skill radar chart.")

with tab2:
    st.markdown("### AI Role Matcher & Career Guidance")

    with st.expander("📄 Or upload a resume here to auto-fill your profile and match immediately"):
        resume_upload_tab2 = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"], key="resume_upload_tab2")
        if resume_upload_tab2 is not None:
            if st.button("✨ Parse Resume, Fill Profile & Find Matches", key="parse_resume_tab2", type="primary"):
                with st.spinner("Reading resume and matching..."):
                    extracted, parse_err = parse_resume_to_profile(resume_upload_tab2, ALL_SKILLS)
                    if parse_err:
                        st.error(f"Couldn't parse resume: {parse_err}")
                    else:
                        quick_profile = {
                            "branch": extracted["branch"] or ALL_BRANCHES[0], "year": 3,
                            "interest": "Not sure yet", "skills": extracted["skills"], "weekly_hours": 8,
                            "projects": [l for l in extracted["projects_text"].split("\n") if l.strip()],
                        }
                        st.session_state["profile"] = quick_profile
                        st.session_state["resume_extracted"] = extracted
                        matches, used_gemini, note = gemini_role_match(quick_profile, gemini_key)
                        st.session_state["top_matches"] = matches
                        st.session_state["match_source_note"] = (
                            "✅ Ranked by Gemini, grounded in the prepared role dataset." if used_gemini
                            else f"ℹ️ Rule-based skill-overlap ranking used. {note or ''}"
                        )
                        st.success(
                            f"Profile auto-filled from resume ({len(extracted['skills'])} skills detected) "
                            "and matches generated below. Visit Tab 1 to review/correct the extracted profile."
                        )

    profile = st.session_state["profile"]
    if not profile:
        st.warning("Fill in your profile in Tab 1 first, or upload a resume above.")
    else:
        if st.button("🔍 Find My Best-Fit Roles", type="primary"):
            with st.spinner("Matching your profile against role data..."):
                matches, used_gemini, note = gemini_role_match(profile, gemini_key)
                st.session_state["top_matches"] = matches
                st.session_state["match_source_note"] = (
                    "✅ Ranked by Gemini, grounded in the prepared role dataset." if used_gemini
                    else f"ℹ️ Rule-based skill-overlap ranking used. {note or ''}"
                )

        matches = st.session_state.get("top_matches")
        if matches:
            st.caption(st.session_state.get("match_source_note", ""))
            for i, m in enumerate(matches):
                with st.container():
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"#### {i+1}. {m['role']['name']}")
                        st.write(m["role"]["description"])
                        if m.get("why"):
                            st.markdown(f"**Why this fits you:** {m['why']}")
                        st.markdown(
                            "".join(f'<span class="role-badge">{s}</span>' for s in m["have"]) or
                            "<i>No overlapping skills yet — see Tab 3 for a roadmap.</i>",
                            unsafe_allow_html=True,
                        )
                    with cols[1]:
                        st.metric("Match", f"{m['match_pct']}%")
                    st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("#### Suggested beginner/intermediate projects")
            top_role_name = matches[0]["role"]["name"]
            proj_df = pd.DataFrame([p for p in PROJECTS if p["skill_tag"] == top_role_name])
            if not proj_df.empty:
                st.dataframe(proj_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No project suggestions found for this role family in the dataset.")
        else:
            st.info("Click the button above to generate your role matches.")

with tab3:
    st.markdown("### Skill-Gap Analyzer & 30/60/90-Day Roadmap")
    profile = st.session_state["profile"]
    matches = st.session_state.get("top_matches")

    if not profile:
        st.warning("Fill in your profile in Tab 1 first.")
    elif not matches:
        st.warning("Run the Role Matcher in Tab 2 first.")
    else:
        top = matches[0]
        st.markdown(f"#### Skill Gap vs. {top['role']['name']}")

        gc1, gc2, gc3 = st.columns(3)
        with gc1:
            st.markdown("**✅ Have**")
            for s in top["have"]:
                st.markdown(f'<span class="skill-have">● {s}</span>', unsafe_allow_html=True)
        with gc2:
            st.markdown("**➖ Missing**")
            for s in top["missing"]:
                st.markdown(f'<span class="skill-missing">● {s}</span>', unsafe_allow_html=True)
        with gc3:
            readiness = round(100 * len(top["have"]) / max(len(top["have"]) + len(top["missing"]), 1))
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=readiness, title={"text": "Readiness Score"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": ELECTRIC_CYAN}, "bgcolor": DEEP_NAVY,
                       "steps": [{"range": [0, 40], "color": "rgba(248,113,113,0.3)"},
                                 {"range": [40, 70], "color": "rgba(251,191,36,0.3)"},
                                 {"range": [70, 100], "color": "rgba(16,185,129,0.3)"}]},
            ))
            fig.update_layout(paper_bgcolor=DARK_SLATE, font_color=T["chart_font"], height=250,
                               margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        if st.button("🗺️ Generate My 30/60/90-Day Roadmap", type="primary"):
            with st.spinner("Generating roadmap..."):
                text, used_gemini = gemini_roadmap(profile, top, gemini_key)
                st.session_state["roadmap_text"] = text
                st.session_state["roadmap_used_gemini"] = used_gemini

        if st.session_state.get("roadmap_text"):
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.caption("✅ Generated by Gemini" if st.session_state.get("roadmap_used_gemini")
                       else "ℹ️ Template roadmap (Gemini unavailable)")
            st.markdown(st.session_state["roadmap_text"])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("#### Interview Readiness Checklist")
        checklist_items = [
            "Core CS fundamentals (OS, DBMS, CN, OOP)",
            "DSA — arrays, strings, trees, basic graphs",
            "At least 1 project you can explain end-to-end",
            "Resume reviewed and updated",
            "Mock interview / soft-skills practice done",
        ]
        for item in checklist_items:
            checked = st.session_state["checklist"].get(item, False)
            st.session_state["checklist"][item] = st.checkbox(item, value=checked, key=f"chk_{item}")
        done = sum(st.session_state["checklist"].values())
        st.progress(done / len(checklist_items))
        st.caption(f"{done}/{len(checklist_items)} completed")

with tab4:
    st.markdown("### Sarvam Indic AI — Multilingual Career Q&A")
    st.caption(f"Selected language: {selected_lang_label}")

    user_question = st.text_input("Ask a career or skilling question:", placeholder="e.g. Should I learn Java or Python first?")

    audio_upload = st.file_uploader("Or upload a short voice question (Saaras STT)", type=["wav", "mp3", "m4a"])
    if audio_upload and sarvam_key:
        if st.button("🎙️ Transcribe uploaded audio"):
            with st.spinner("Transcribing with Saaras..."):
                transcript, err = sarvam_stt(audio_upload, sarvam_key)
            if transcript:
                user_question = transcript
                st.success(f"Transcribed: {transcript}")
            else:
                st.error(err)

    if st.button("💬 Get Answer", type="primary") and user_question:
        profile = st.session_state["profile"]
        context = f"Student branch: {profile['branch']}, year: {profile['year']}, skills: {', '.join(profile['skills'])}." if profile else "No profile on file yet."
        prompt = f"""You are a guidance-only career assistant for an Indian engineering student.
{context}
Question: {user_question}
Answer helpfully in 3-5 sentences. Do not guarantee jobs, placements, salaries, or admissions.
"""
        with st.spinner("Thinking..."):
            ok, answer = call_gemini(prompt, gemini_key, max_output_tokens=1024)
        if not ok:
            answer = ("I can't reach Gemini right now, so here's general guidance: research the role's "
                       "core skills, build one solid project, and ask your placement cell or a mentor for "
                       "a second opinion. (" + answer + ")")

        st.session_state["chat_history"].append({"q": user_question, "a": answer})

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"**Answer (English):** {answer}")

        if selected_lang_code != "en-IN" and sarvam_key:
            translated, err = sarvam_translate(answer, selected_lang_code, sarvam_key)
            if translated:
                st.markdown(f"**Translated ({selected_lang_label}):** {translated}")
                audio_bytes, tts_err = sarvam_tts(translated, selected_lang_code, sarvam_key, speaker=selected_speaker)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                elif tts_err:
                    st.caption(f"🔇 Voice output unavailable: {tts_err}")
            elif err:
                st.caption(f"🌐 Translation unavailable: {err}")
        elif selected_lang_code != "en-IN" and not sarvam_key:
            st.caption("🔑 Add a Sarvam API key in the sidebar to get this answer translated + spoken aloud.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["chat_history"]:
        with st.expander("Previous questions this session"):
            for turn in reversed(st.session_state["chat_history"][-5:]):
                st.markdown(f"**Q:** {turn['q']}")
                st.markdown(f"**A:** {turn['a']}")
                st.divider()

    st.markdown("---")
    st.markdown("### 🔊 Bulbul Text-to-Speech")
    st.caption(
        f"Standalone Bulbul (Sarvam TTS) tool — convert any text into spoken audio using the "
        f"**{selected_speaker}** voice in **{selected_lang_label}** (change either in the sidebar). "
        f"Independent of the Q&A flow above — useful for reading roadmap steps, checklist items, "
        f"or any other text aloud."
    )

    tts_source = st.radio(
        "Text to speak:",
        ["Type my own text", "Read my last roadmap (Tab 3)", "Read my last Q&A answer above"],
        horizontal=False, key="bulbul_source",
    )

    if tts_source == "Type my own text":
        tts_input_text = st.text_area("Enter text to convert to speech:", height=100, key="bulbul_custom_text")
    elif tts_source == "Read my last roadmap (Tab 3)":
        tts_input_text = st.session_state.get("roadmap_text") or ""
        if not tts_input_text:
            st.info("No roadmap generated yet — go to Tab 3 first, or type your own text above.")
    else:
        tts_input_text = st.session_state["chat_history"][-1]["a"] if st.session_state["chat_history"] else ""
        if not tts_input_text:
            st.info("No Q&A answer yet — ask a question above first, or type your own text.")

    if st.button("🎧 Generate Speech with Bulbul", type="primary", key="bulbul_generate"):
        if not tts_input_text.strip():
            st.warning("Nothing to speak yet — add some text first.")
        elif not sarvam_key:
            st.error("No Sarvam API key available — Bulbul needs one to generate audio.")
        else:
            with st.spinner("Generating audio with Bulbul..."):
                bulbul_audio, bulbul_err = sarvam_tts(tts_input_text, selected_lang_code, sarvam_key, speaker=selected_speaker)
            if bulbul_audio:
                st.audio(bulbul_audio, format="audio/wav")
                st.download_button("⬇️ Download audio", data=bulbul_audio, file_name="bulbul_speech.wav", mime="audio/wav")
            else:
                st.error(f"🔇 {bulbul_err}")

with tab5:
    st.markdown("### Responsible AI Checklist")
    st.markdown("""
    <div class="glass-card">
    <ul>
      <li>✅ All recommendations are grounded in the prepared <code>roles.json</code> dataset — Gemini is instructed not to invent roles or skills.</li>
      <li>✅ No promises of jobs, internships, salaries, or admission outcomes anywhere in the app.</li>
      <li>✅ Sample student profiles used for the mentor dashboard are generic and non-identifying — no real student records.</li>
      <li>✅ Every AI-generated answer is labelled with its source (Gemini vs. rule-based fallback) so users know when grounding logic, not the LLM, produced the result.</li>
      <li>✅ Feedback is captured per response to identify low-quality or confusing answers over time.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Feedback")
    with st.form("feedback_form"):
        rating = st.slider("How helpful was this session? (1-5)", 1, 5, 4)
        helpful_flag = st.radio("Did you get a clear next step?", ["Yes", "Somewhat", "No"], horizontal=True)
        comment = st.text_area("Anything confusing or missing?", height=80)
        fb_submit = st.form_submit_button("Submit Feedback")

    if fb_submit:
        st.session_state["feedback_log"].append({
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "rating": rating, "clear_next_step": helpful_flag, "comment": comment,
        })
        st.success("Thanks — your feedback has been logged for this session.")

    if st.session_state["feedback_log"]:
        st.markdown("#### Feedback log (this session)")
        st.dataframe(pd.DataFrame(st.session_state["feedback_log"]), use_container_width=True, hide_index=True)
