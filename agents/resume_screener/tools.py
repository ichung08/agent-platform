import json
import os
import re

import httpx
from openai import OpenAI

TOOLS = [
    {
        "type": "function",
        "name": "fetch_job_description",
        "description": "Fetch a job description from a URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the job description",
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "parse_pdf",
        "description": "Read a file and return its contents with line numbers. Paths are relative to the test_files directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the resume file relative to test_files (e.g. resume_alice.txt)",
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "score_candidate",
        "description": "Score a single candidate against a job description.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Candidate name"},
                "jd": {"type": "string", "description": "Job description text"},
                "resume_text": {"type": "string", "description": "Resume content"},
            },
            "required": ["name", "jd", "resume_text"],
            "additionalProperties": False,
        },
    },
]

BASE_DIR = os.environ.get("BASE_DIR", os.path.join(os.path.dirname(__file__), "test_files"))

def _resolve_path(path: str) -> str:
    """Resolve a user-provided path relative to BASE_DIR.

    Returns the resolved absolute path. Raises ValueError if the path
    escapes the base directory.
    """
    # Join with base dir, then resolve to an absolute path
    resolved = os.path.realpath(os.path.join(BASE_DIR, path))

    # Ensure the resolved path is within the base directory
    base_real = os.path.realpath(BASE_DIR)
    if not resolved.startswith(base_real + os.sep) and resolved != base_real:
        raise ValueError(f"Access denied: path '{path}' is outside the allowed directory.")

    return resolved

def fetch_job_description(url: str) -> str:
    """Fetch job description from a URL. Returns plain text, stripping HTML if present."""
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            text = resp.text
    except httpx.HTTPError as e:
        return f"Error fetching URL: {e}"
    except Exception as e:
        return f"Error: {e}"

    # Strip HTML tags if present
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

    return text[:15000] if len(text) > 15000 else text

def parse_pdf(file_path: str) -> str:
    """Read a .txt or .pdf file and return its contents with line numbers."""
    resolved = _resolve_path(file_path)

    if not os.path.isfile(resolved):
        return f"Error: '{file_path}' is not a file."

    suffix = os.path.splitext(resolved)[1].lower()

    if suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(resolved) as pdf:
                lines = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        lines.extend(text.splitlines())
        except ImportError:
            return "Error: pdfplumber not installed. Run: pip install pdfplumber"
        except Exception as e:
            return f"Error reading PDF: {e}"
    else:
        try:
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except PermissionError:
            return f"Error: permission denied reading '{file_path}'."

    if not lines:
        return "(empty file)"

    numbered = [f"{i + 1}: {line.rstrip()}" for i, line in enumerate(lines)]
    return "\n".join(numbered)

SCORE_PROMPT = """You are an expert resume screener. Score how well this candidate matches the job description.

Job description:
---
{jd}
---

Candidate: {name}

Resume:
---
{resume}
---

Respond with ONLY a valid JSON object (no markdown, no extra text) in this exact format:
{{"name": "{name}", "score": <0-100>, "notes": "<2-3 sentence summary of fit>"}}

Score 0-100 based on: required skills match, experience level, and overall fit. Be fair and role-agnostic."""


def score_candidate(name: str, jd: str, resume_text: str) -> str:
    """Use the LLM to score a candidate against the job description. Returns JSON with name, score (0-100), and notes."""
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    model = os.environ.get("MODEL", "gpt-4o-mini")

    # Truncate if very long to stay within context limits
    jd_trunc = jd[:8000] if len(jd) > 8000 else jd
    resume_trunc = resume_text[:8000] if len(resume_text) > 8000 else resume_text

    prompt = SCORE_PROMPT.format(jd=jd_trunc, name=name, resume=resume_trunc)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (response.choices[0].message.content or "").strip()
        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        return json.dumps({"name": parsed.get("name", name), "score": parsed.get("score", 0), "notes": parsed.get("notes", "")})
    except json.JSONDecodeError:
        return json.dumps({"name": name, "score": 0, "notes": f"Scoring failed: could not parse LLM output. Raw: {(raw or '')[:200]}..."})
    except Exception as e:
        return json.dumps({"name": name, "score": 0, "notes": f"Scoring failed: {e}"})

_TOOL_MAP = {
    "fetch_job_description": lambda params: fetch_job_description(params["url"]),
    "parse_pdf": lambda params: parse_pdf(params["file_path"]),
    "score_candidate": lambda params: score_candidate(params["name"], params["jd"], params["resume_text"])
}

def execute_tool(name: str, params: dict) -> str:
    handler = _TOOL_MAP.get(name)
    if handler is None:
        return f"Error: unknown tool '{name}'."
    
    try:
        return handler(params)
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error executing {name}: {e}"