import os

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
    return "Software Engineer"

def parse_pdf(file_path: str) -> str:
    """Read a file and return its contents with line numbers."""
    resolved = _resolve_path(file_path)

    if not os.path.isfile(resolved):
        return f"Error: '{file_path}' is not a file."

    try:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        return f"Error: permission denied reading '{file_path}'."

    if not lines:
        return "(empty file)"

    numbered = [f"{i + 1}: {line.rstrip()}" for i, line in enumerate(lines)]
    return "\n".join(numbered)

def score_candidate(name: str, jd: str, resume_text: str) -> str:
    return "6"

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