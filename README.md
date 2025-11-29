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

3. Trigger a quiz task via POST request:
   ```bash
   curl -X POST http://localhost:8000/run \
   -H "Content-Type: application/json" \
   -d '{
     "email": "your_email@example.com",
     "secret": "jules_secret_123",
     "url": "https://tds-llm-analysis.s-anand.net/demo"
   }'
   ```

### Running with Docker

1. Build the image:
   ```bash
   docker build -t quiz-solver .
   ```

2. Run the container (passing the API key):
   ```bash
   docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY quiz-solver
   # OR
   docker run -p 8000:8000 -e AIPROXY_TOKEN=$AIPROXY_TOKEN quiz-solver
   ```

## Deployment

To submit this project, you need a public HTTPS URL (e.g., `https://your-app.onrender.com/run`). Since the application requires system-level dependencies for Playwright (browsers), a **Docker-based deployment** is recommended.

### Option A: Deploy to Render (Recommended)

1. Push this repository to GitHub.
2. Create a new account/login at [Render.com](https://render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Select **Docker** as the Runtime.
6. Under **Environment Variables**, add:
   - Key: `GEMINI_API_KEY` (or `AIPROXY_TOKEN`)
   - Value: `your-actual-api-key`
7. Click **Create Web Service**.
8. Once deployed, your URL will be something like `https://project-name.onrender.com`.
9. Your API Endpoint URL for the form will be: `https://project-name.onrender.com/run`.

## How it Works

1. **Endpoint**: The `/run` endpoint accepts the initial quiz URL and user credentials.
2. **Solver**: The `solver.py` script runs as a background task.
   - It navigates to the quiz URL using Playwright.
   - It extracts the page content.
   - It uses the LLM (GPT-4o-mini or Gemini 1.5 Flash) to parse the question and determine the submission URL.
   - It uses the LLM to generate Python code to solve the specific data analysis question (e.g., scraping, parsing CSVs, calculating sums).
   - It executes the generated code in a subprocess.
   - It submits the answer and follows the next URL if provided.

### Fallback Mode
For the specific demo URL (`https://tds-llm-analysis.s-anand.net/demo`), the system includes fallback logic to solve the tasks (simple string posting and scraping) without requiring an API key. This allows for basic verification of the pipeline. **However, the real quiz tasks require the LLM and the API key.**
