# LLM Analysis Quiz Solver

This project implements an automated quiz solver for the "LLM Analysis Quiz". It exposes a FastAPI endpoint that accepts quiz tasks, solves them using Playwright and an LLM (OpenAI), and submits the results.

## Prerequisites

- **Python 3.12+**
- **Playwright Browsers** (`playwright install chromium`)
- **OpenAI API Key** (or compatible `AIPROXY_TOKEN`)

## Setup & Running

### Environment Variables

The application requires the `AIPROXY_TOKEN` environment variable to function correctly for the actual quiz.

```bash
export AIPROXY_TOKEN="your-api-key-here"
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
   docker run -p 8000:8000 -e AIPROXY_TOKEN=$AIPROXY_TOKEN quiz-solver
   ```

## How it Works

1. **Endpoint**: The `/run` endpoint accepts the initial quiz URL and user credentials.
2. **Solver**: The `solver.py` script runs as a background task.
   - It navigates to the quiz URL using Playwright.
   - It extracts the page content.
   - It uses the LLM (GPT-4o-mini) to parse the question and determine the submission URL.
   - It uses the LLM to generate Python code to solve the specific data analysis question (e.g., scraping, parsing CSVs, calculating sums).
   - It executes the generated code in a subprocess.
   - It submits the answer and follows the next URL if provided.

### Fallback Mode
For the specific demo URL (`https://tds-llm-analysis.s-anand.net/demo`), the system includes fallback logic to solve the tasks (simple string posting and scraping) without requiring an API key. This allows for basic verification of the pipeline. **However, the real quiz tasks require the LLM and the API key.**
