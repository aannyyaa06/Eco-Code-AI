"""Google Gemini AI integration for sustainability analysis and code optimization."""

from __future__ import annotations

import os
import time
import logging

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()
logger = logging.getLogger(__name__)

# Configure once at module level
def _get_api_key() -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except StreamlitSecretNotFoundError:
        return None


_API_KEY = _get_api_key()
if _API_KEY:
    genai.configure(api_key=_API_KEY)

# Singleton model instance
_MODEL: genai.GenerativeModel | None = None


def _get_model() -> genai.GenerativeModel:
    """Return a cached GenerativeModel instance."""
    global _MODEL
    if _MODEL is None:
        _MODEL = genai.GenerativeModel("gemini-2.5-flash")
    return _MODEL


def _call_gemini(prompt: str, retries: int = 2) -> str:
    """Send a prompt to Gemini with basic retry logic."""
    if not _API_KEY:
        return (
            "Error: `GEMINI_API_KEY` is not configured. "
            "Set it in your environment, `.env` file, or Streamlit Secrets."
        )
    model = _get_model()
    for attempt in range(retries + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.warning("Gemini API error (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
            else:
                return f"Error communicating with Gemini API after {retries + 1} attempts: {e}"
    return "Unexpected error in Gemini API call."


def analyze_code(code_input: str) -> str:
    """Analyze Python code for sustainability, performance, and efficiency."""
    prompt = (
        "Analyze the following Python code for sustainability, performance, and efficiency.\n"
        "Provide a report with the following sections in Markdown format:\n"
        "## Issues Found\n"
        "## Sustainability Score (out of 100)\n"
        "## Optimization Suggestions\n"
        "## Estimated Improvements\n"
        "## Green Coding Recommendation\n\n"
        "Code to analyze:\n"
        "```python\n"
        f"{code_input}\n"
        "```\n"
    )
    return _call_gemini(prompt)


def optimize_code(code_input: str) -> str:
    """Generate an optimized version of the given Python code."""
    prompt = (
        "Optimize the following Python code for sustainability, performance, "
        "and memory efficiency.\n"
        "Return ONLY the optimized Python code (with ```python ... ``` block "
        "if needed), followed by a brief summary of the improvements in "
        "Markdown format under the heading '## Improvements'.\n"
        "Do not include any other conversational text.\n\n"
        "Code to optimize:\n"
        "```python\n"
        f"{code_input}\n"
        "```\n"
    )
    return _call_gemini(prompt)
