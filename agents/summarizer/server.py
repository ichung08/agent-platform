from fastapi import FastAPI
from pydantic import BaseModel

from agent import run_agent

app = FastAPI()

class RunRequest(BaseModel):
    message: str

class RunResponse(BaseModel):
    response: str

@app.post("/run", response_model=RunResponse)
def run(request: RunRequest) -> RunResponse:
    response = run_agent(request.message)
    return RunResponse(response=response or "")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)