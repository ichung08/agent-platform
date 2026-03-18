"""End-to-end test for step 1d. Run from agents/resume_screener/ with: python test_e2e.py"""

import sys
from pathlib import Path

# Ensure we can import agent and tools
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import run_agent

PROMPT = "Score the candidates in the test_files directory against the job description in sample_jd.txt"

if __name__ == "__main__":
    print("Running agent with prompt:")
    print(f"  {PROMPT!r}\n")
    print("--- Agent response ---")
    result = run_agent(PROMPT)
    print(result)
    print("\n--- Done ---")
