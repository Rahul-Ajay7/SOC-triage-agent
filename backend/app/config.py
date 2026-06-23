"""Central config — loads backend/.env, safe defaults.

Goal: boots and runs with an EMPTY .env. Every external dep (LLMs,
threat intel) degrades to heuristics.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ---- Application ----
APP_NAME = os.getenv("APP_NAME", "SOC Triage Agent")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8001))

# ---- Paths ----
DATA_DIR = BASE_DIR / "data"
MITRE_DB_PATH = DATA_DIR / "mitre_attack.json"
SAMPLE_ALERTS_DIR = DATA_DIR / "sample_alerts"
# Historical log corpus the log_search tool queries (NOT auto-seeded as alerts).
HISTORY_DIR = DATA_DIR / "history"

# ---- Database ----
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'soc_triage.db'}")

# ---- LLM fallback chain (Groq -> Gemini -> Ollama) ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_CHAT_ENDPOINT = os.getenv("LLM_CHAT_ENDPOINT", "/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 120))

# ---- Threat intel ----
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")

# ---- Agent tuning ----
AGENT_CONFIDENCE_THRESHOLD = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", 0.7))
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", 2))

# ---- CORS ----
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8001"
).split(",")


def llm_available() -> bool:
    """True if at least one cloud LLM key configured."""
    return bool(GROQ_API_KEY or GEMINI_API_KEY)
