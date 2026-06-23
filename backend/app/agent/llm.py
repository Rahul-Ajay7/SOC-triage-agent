"""LLM client — reused fallback chain from HealthAI: Groq -> Gemini -> Ollama.

Single entry point: call_llm(system, user) -> (text, source).
If every provider is unavailable, returns ("", "unavailable") so callers
can fall back to deterministic heuristics — the agent never hard-fails.

Also json_llm() for structured nodes (assess/classify): asks for JSON,
parses defensively.
"""
import json
import logging
import re
from typing import Any, Optional

import requests

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_API_URL,
    GROQ_MODEL,
    LLM_BASE_URL,
    LLM_CHAT_ENDPOINT,
    LLM_MODEL,
    LLM_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _call_groq(system: str, user: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    resp = requests.post(
        GROQ_API_URL,
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        },
        headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                 "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(system: str, user: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
        json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return (
        resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    )


def _call_ollama(system: str, user: str) -> str:
    resp = requests.post(
        f"{LLM_BASE_URL}{LLM_CHAT_ENDPOINT}",
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
            "stream": False,
        },
        timeout=LLM_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def call_llm(system: str, user: str) -> tuple[str, str]:
    """Try each provider in order. Returns (answer, source)."""
    for name, caller in (
        ("groq", _call_groq),
        ("gemini", _call_gemini),
        ("ollama", _call_ollama),
    ):
        try:
            answer = caller(system, user)
            if answer:
                logger.info("LLM answered by %s", name)
                return answer, name
        except ValueError as e:
            logger.info("%s skipped: %s", name, e)
        except Exception as e:  # noqa: BLE001 — try next provider
            logger.warning("%s failed: %s — trying next", name, e)
    logger.warning("All LLM providers unavailable — caller should use heuristics")
    return "", "unavailable"


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM reply (handles code fences)."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if not candidate:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace.group(0) if brace else None
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def json_llm(system: str, user: str) -> tuple[Optional[dict[str, Any]], str]:
    """Call the LLM expecting JSON. Returns (parsed_or_None, source)."""
    answer, source = call_llm(system, user)
    if source == "unavailable":
        return None, source
    return _extract_json(answer), source
