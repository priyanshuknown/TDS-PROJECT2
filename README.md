# LLM Analysis Quiz Solver

This project implements an automated quiz solver for the "LLM Analysis Quiz". It exposes a FastAPI endpoint that accepts quiz tasks, solves them using Playwright and an LLM (OpenAI or Google Gemini), and submits the results.

## Prerequisites

- **Python 3.12+**
- **Playwright Browsers** (`playwright install chromium`)
- **LLM API Key** (OpenAI `AIPROXY_TOKEN` OR Google `GEMINI_API_KEY`)

## Setup & Running

### Environment Variables

The application requires **one** of the following environment variables to function correctly for the actual quiz.

**Option 1: OpenAI (via Proxy)**
```bash
export AIPROXY_TOKEN="your-api-key-here"
```

**Option 2: Google Gemini**
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Start the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   *The server logs will appear directly in your terminal.*

3. Trigger a quiz task via POST request (in a new terminal):
   ```bash
   curl -X POST http://localhost:8000/run \
   -H "Content-Type: application/json" \
   -d '{
     "email": "your_email@example.com",
     "secret": "UNKNOWN",
     "url": "https://tds-llm-analysis.s-anand.net/demo"
   }'
   ```
   *You should see "Solving quiz at..." messages in the server terminal.*

### Running with Docker

1. Build the image:
   ```bash
   docker build -t quiz-solver .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY quiz-solver
   ```

## Deployment & Logs

To submit this project, you need a public HTTPS URL (e.g., `https://your-app.onrender.com/run`).

### Deploy to Render

1. Push this repository to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com).
3. Connect your GitHub repository.
4. Select **Docker** as the Runtime.
5. Add Environment Variable: `GEMINI_API_KEY` (or `AIPROXY_TOKEN`).
6. Deploy.

### Viewing Logs in Render

Since the quiz solving happens in the background, you **must** check the logs to see if it worked or failed.

1. Go to your **Render Dashboard**.
2. Click on your **Web Service**.
3. Click on the **Logs** tab on the left sidebar.
4. When you send a request (via the Form or curl), watch these logs. You will see output like:
   ```text
   INFO:     ... POST /run HTTP/1.1" 200 OK
   Solving quiz at: https://...
   Task parsed: ...
   Submission result: ...
   ```

## How it Works

1. **Endpoint**: The `/run` endpoint accepts the initial quiz URL and user credentials.
2. **Solver**: The `solver.py` script runs as a background task.
   - It navigates to the quiz URL using Playwright.
   - It extracts the page content.
   - It uses the LLM to parse the question and determine the submission URL.
   - It uses the LLM to generate Python code to solve the specific data analysis question.
   - It executes the generated code in a subprocess.
   - It submits the answer and follows the next URL.

### Fallback Mode
For the specific demo URL (`https://tds-llm-analysis.s-anand.net/demo`), the system includes fallback logic to solve the tasks without requiring an API key. This allows for basic verification of the pipeline. **However, the real quiz tasks require the LLM and the API key.**
