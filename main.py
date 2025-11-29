from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from solver import solve_quiz_task

app = FastAPI()

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

# Define the secret for the API endpoint verification
MY_SECRET = "UNKNOWN"

@app.post("/run")
async def run_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    if request.secret != MY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Start the quiz solver in the background
    background_tasks.add_task(solve_quiz_task, request.email, request.secret, request.url)

    return {"message": "Quiz started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
