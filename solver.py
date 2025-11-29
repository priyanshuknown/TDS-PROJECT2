import os
import json
import requests
from playwright.sync_api import sync_playwright
from openai import OpenAI
import google.generativeai as genai
import base64
import re
import sys
from io import StringIO
import contextlib
import subprocess

# Initialize LLM Clients
openai_client = None
gemini_model = None

api_key = os.environ.get("AIPROXY_TOKEN")
gemini_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    openai_client = OpenAI(api_key=api_key)
elif gemini_key:
    genai.configure(api_key=gemini_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("WARNING: No valid API Token (AIPROXY_TOKEN or GEMINI_API_KEY) found. LLM features will be limited.")

def solve_quiz_task(email, secret, start_url):
    current_url = start_url

    while current_url:
        print(f"Solving quiz at: {current_url}")

        # 1. Get page content
        content = get_page_content(current_url)

        # 2. Parse task using LLM or Fallback
        task_data = parse_task_with_llm(content)

        if not task_data:
            print("Failed to parse task.")
            break

        print(f"Task parsed: {task_data}")

        # 3. Solve the question
        answer = solve_question(task_data['question'])

        if answer is None:
             print("Failed to solve question.")
             break

        # 4. Submit answer
        result = submit_answer(task_data['submit_url'], email, secret, current_url, answer, task_data.get('answer_key', 'answer'))

        print(f"Submission result: {result}")

        # 5. Check response for next URL or correction
        if result.get("correct"):
            current_url = result.get("url") # Next URL
        else:
            if result.get("reason"):
                 print(f"Incorrect: {result['reason']}")
            break

def get_page_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        try:
            page.wait_for_selector("body", timeout=5000)
            if page.locator("#result").count() > 0:
                 content = page.locator("#result").inner_text()
            else:
                 content = page.locator("body").inner_text()
        except:
            content = page.content()

        browser.close()
    return content

def parse_task_with_llm(content):
    prompt = f"""
    Analyze the following text from a quiz page:

    ---
    {content}
    ---

    Extract the following information in JSON format:
    1. "question": The question to be solved.
    2. "submit_url": The URL to post the answer to.
    3. "answer_key": The JSON key expected for the answer (e.g., "answer", "result").

    Return ONLY valid JSON.
    """

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing task with OpenAI: {e}")
            return None

    elif gemini_model:
        try:
            response = gemini_model.generate_content(prompt + "\n\nJSON:")
            # Extract JSON from potential markdown code blocks
            text = response.text
            text = clean_code(text) # Reusing clean_code as it handles removing backticks
            return json.loads(text)
        except Exception as e:
            print(f"Error parsing task with Gemini: {e}")
            return None

    else:
        # Fallback for demo without API key
        if "Scrape" in content and "secret code" in content:
            # Extract relative URL
            match = re.search(r"Scrape\s+([^\s]+)", content)
            if match:
                relative_url = match.group(1)
                return {
                    "question": f"Scrape {relative_url} and get the secret code.",
                    "submit_url": "https://tds-llm-analysis.s-anand.net/submit",
                    "answer_key": "answer"
                }
        elif "tds-llm-analysis.s-anand.net/demo" in content or "anything you want" in content:
             return {
                "question": "Post 'anything you want' as the answer.",
                "submit_url": "https://tds-llm-analysis.s-anand.net/submit",
                "answer_key": "answer"
            }

        print("No LLM client and regex fallback failed.")
        return None

def solve_question(question):
    print(f"Question: {question}")

    # Fallback for known demo tasks
    if "anything you want" in question.lower() or "post 'anything you want'" in question.lower():
         return "anything you want"

    if "Scrape" in question and "secret code" in question:
         # Handle scrape task fallback
         match = re.search(r"Scrape\s+([^\s]+)", question)
         if match:
             relative_url = match.group(1)
             base_url = "https://tds-llm-analysis.s-anand.net"
             full_url = base_url + relative_url

             print(f"Scraping {full_url}")
             try:
                 # Use Playwright instead of requests because the page renders with JS
                 content = get_page_content(full_url)
                 print(f"Scraped text: {content}")
                 # Extract code: "Secret code is 25511 and not 25535."
                 code_match = re.search(r"Secret code is\s*(\d+)", content)
                 if code_match:
                     print(f"Found code: {code_match.group(1)}")
                     return int(code_match.group(1))
                 else:
                     print("No code found in scraped text")
             except Exception as e:
                 print(f"Scrape error: {e}")

    if not openai_client and not gemini_model:
        print("Cannot solve complex question without LLM.")
        return None

    prompt = f"""
    Write a Python script to solve this question:
    "{question}"

    The script should:
    1. Be self-contained (imports are allowed).
    2. Print the result to stdout as the last line.
    3. Not ask for user input.
    4. Handle downloading files if mentioned (use requests).
    5. Be robust.

    Return ONLY the python code in a code block.
    """

    code = None
    try:
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.choices[0].message.content
        elif gemini_model:
            response = gemini_model.generate_content(prompt)
            code = response.text

        if code:
            code = clean_code(code)

            with open("temp_solution.py", "w") as f:
                f.write(code)

            result = subprocess.run(["python3", "temp_solution.py"], capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print("Execution error:", result.stderr)
                return None

            output = result.stdout.strip().split('\n')[-1]
            return parse_answer(output)

    except Exception as e:
        print(f"Error executing solution: {e}")
        return None

def clean_code(text):
    if "```python" in text:
        text = text.split("```python")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    # Handle cases where markdown is just ```
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
             text = parts[1]

    # Strip any leading 'python' if it was part of the block tag but not caught above
    if text.startswith("python"):
        text = text[6:]

    return text.strip()

def parse_answer(output):
    try:
        return json.loads(output)
    except:
        pass

    try:
        return int(output)
    except:
        pass

    try:
        return float(output)
    except:
        pass

    return output

def submit_answer(submit_url, email, secret, quiz_url, answer, answer_key):
    payload = {
        "email": email,
        "secret": secret,
        "url": quiz_url,
        answer_key: answer
    }

    print(f"Submitting payload to {submit_url}: {payload}")

    try:
        resp = requests.post(submit_url, json=payload, timeout=10)
        try:
             return resp.json()
        except:
             return {"correct": False, "reason": "Invalid JSON response", "raw": resp.text}
    except Exception as e:
        return {"correct": False, "reason": str(e)}
