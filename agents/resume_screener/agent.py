import os
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = """\
<role>
You are a Resume Screener Assistant. Your job is to analyze, search and understand
the contents of a resume.
</role>

"""

def run_agent(user_message: str) -> str:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    response = client.responses.create(
        model=os.environ.get("MODEL"),
        input=messages,
    )

    return response.output_text

print(run_agent("hi"))