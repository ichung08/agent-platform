import os
from dotenv import load_dotenv

from openai import OpenAI
from tools import TOOLS, execute_tool
import json
import sys

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

    while True:
        response = client.responses.create(
            model=os.environ.get("MODEL"),
            tools=TOOLS,
            input=messages,
        )

        messages = list(messages) + list(response.output)

        has_tool_calls = False
        for item in response.output:
            if getattr(item, "type", None) == "function_call":
                has_tool_calls = True
                name = getattr(item, "name", None)
                arguments = getattr(item, "arguments", "{}")
                call_id = getattr(item, "call_id", None)

                params = json.loads(arguments) if isinstance(arguments, str) else arguments

                result = execute_tool(name, params)

                messages.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result,
                })
        
        if not has_tool_calls:
            return response.output_text

