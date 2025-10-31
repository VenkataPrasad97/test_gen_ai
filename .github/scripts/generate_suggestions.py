import os
import argparse
import requests
from pathlib import Path

# --- Configuration ---
# Load Perplexity API Key from environment variable (set via GitHub Secrets!)
API_KEY = os.getenv("PERPLEXITY_API_KEY")
API_URL = "https://api.perplexity.ai/chat/completions"
MODEL_NAME = "sonar" # Using a fast and capable model

# --- Main Functions ---

def call_llm(prompt, max_tokens=800):
    """
    Sends a prompt to the Perplexity API and returns the text response.
    """
    if not API_KEY:
        return "Error: PERPLEXITY_API_KEY not set."
        
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "max_tokens": max_tokens
            },
            timeout=60
        )
        response.raise_for_status() # Raise an exception for bad status codes
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "No result!")
        return content
    except requests.RequestException as e:
        return f"Error calling Perplexity API: {e}"
    except (KeyError, IndexError):
        return f"Error parsing API response: {response.text}"

def get_file_content(file_path):
    """
    Safely reads the content of a file.
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def handle_python_changes(diff_content, changed_files, openapi_content):
    """
    Generates suggestions for Python code changes (Pytest, DRF tests).
    """
    py_files = [f for f in changed_files if f.endswith(".py") and ("backend/" in f or "server/" in f)]
    if not py_files:
        return ""

    # Simple logic: just find diff sections for Python files
    # A more advanced version would parse the diff per file
    py_diff_sections = []
    for line in diff_content.splitlines():
        if any(line.startswith(f"+++ b/{py_file}") for py_file in py_files):
            py_diff_sections.append(f"\n--- Changes for {line.split('/')[-1]} ---\n")
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            if py_diff_sections: # Only add diff content if we're in a relevant file section
                py_diff_sections.append(line)
    
    if not py_diff_sections:
        return ""
        
    py_diff = "\n".join(py_diff_sections)

    # Truncate if diff is too large
    if len(py_diff) > 4000:
        py_diff = py_diff[:4000] + "\n... (diff truncated)"

    # --- THIS IS THE FIX ---
    # Build the context string separately to avoid backslash in f-string expression
    api_context = ""
    if openapi_content:
        # We create the string with \n here, outside the main prompt's {expression}
        api_context = f"Context from openapi.yaml:\n{openapi_content[:1000]}"
    # --- END FIX ---

    prompt = f"""
    You are a senior Python SWE reviewing a PR. Given the following git diff for Python files, generate suggested Pytest unit tests.
    
    - Focus *only* on the changed code.
    - If API endpoints (views.py, serializers.py) are touched, include DRF API tests using APIClient.
    - Cover edge cases and error conditions implied by the code.
    - Return *only* the test code blocks, formatted in Markdown, with suggested file paths.
    
    {api_context}
    
    Git Diff:
    {py_diff}
    """
    
    suggestions = call_llm(prompt)
    return f"### 🐍 Backend Test Suggestions\n\n{suggestions}\n\n"


def handle_frontend_changes(diff_content, changed_files):
    """
    Generates suggestions for React/TS code changes (Vitest, RTL).
    """
    fe_files = [f for f in changed_files if ("web/src/" in f) and (f.endswith((".tsx", ".jsx", ".ts")))]
    if not fe_files:
        return ""

    # Simple logic to find diff sections for frontend files
    fe_diff_sections = []
    for line in diff_content.splitlines():
        if any(line.startswith(f"+++ b/{fe_file}") for fe_file in fe_files):
            fe_diff_sections.append(f"\n--- Changes for {line.split('/')[-1]} ---\n")
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            if fe_diff_sections:
                fe_diff_sections.append(line)
                
    if not fe_diff_sections:
        return ""

    fe_diff = "\n".join(fe_diff_sections)

    if len(fe_diff) > 4000:
        fe_diff = fe_diff[:4000] + "\n... (diff truncated)"

    prompt = f"""
    You are a senior Frontend Engineer. Given the following git diff for React/TypeScript files, generate suggested Vitest + React Testing Library (RTL) tests.
    
    - Focus *only* on the changed components or hooks.
    - Mock any API calls or external dependencies.
    - Cover new UI states, user interactions, or logic.
    - Return *only* the test code blocks, formatted in Markdown, with suggested file paths.
    
    Git Diff:
    {fe_diff}
    """
    
    suggestions = call_llm(prompt)
    return f"### ⚛️ Frontend Test Suggestions\n\n{suggestions}\n\n"

def main():
    parser = argparse.ArgumentParser(description="Generate AI suggestions for a PR.")
    parser.add_argument("--diff", required=True, help="Path to the pr.diff file")
    parser.add_argument("--changed-files", required=True, help="Path to the changed_files.list file")
    parser.add_argument("--out", required=True, help="Path to the output markdown file")
    parser.add_argument("--openapi", help="Optional path to the openapi.yaml file")
    
    args = parser.parse_args()

    # Read all necessary files
    diff_content = get_file_content(args.diff)
    changed_files_list = get_file_content(args.changed_files)
    openapi_content = get_file_content(args.openapi) if args.openapi else None
    
    if not diff_content or not changed_files_list:
        print("Error: Could not read diff or changed files list.")
        return

    changed_files = changed_files_list.splitlines()
    
    # --- Routing Logic ---
    all_suggestions = []
    
    # 1. Handle Python/Backend changes
    py_suggestions = handle_python_changes(diff_content, changed_files, openapi_content)
    if py_suggestions:
        all_suggestions.append(py_suggestions)

    # 2. Handle React/Frontend changes
    fe_suggestions = handle_frontend_changes(diff_content, changed_files)
    if fe_suggestions:
        all_suggestions.append(fe_suggestions)
    
    # 3. Add more handlers here (e.g., for documentation, changelogs, etc.)

    # --- Write Output ---
    output_content = "Here are some AI-generated suggestions based on your changes:\n\n"
    if not all_suggestions:
        output_content = "AI analysis complete. No specific test suggestions for this diff."
    else:
        output_content += "\n---\n".join(all_suggestions)
        
    with open(args.out, "w") as f:
        f.write(output_content)
        
    print(f"Suggestions written to {args.out}")

if __name__ == "__main__":
    main()