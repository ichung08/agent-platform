import os
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()


SYSTEM_PROMPT = """\
<role>
You are a document summarizer. Given text, produce a concise summary.
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
        tools=TOOLS,
        input=messages,
    )

    return response.output_text