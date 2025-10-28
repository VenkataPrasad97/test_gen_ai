import os
import requests

# Load Perplexity API Key from environment variable (set via GitHub Secrets!)
api_key = os.getenv("PERPLEXITY_API_KEY")

with open("pr.diff", "r") as f:
    diff = f.read()

prompt = f"""
Given this Python PR diff, generate suggested unit tests and doc explanations:
{diff[:3000]}
"""

response = requests.post(
    "https://api.perplexity.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "sonar",  # Optionally change model name if needed
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "max_tokens": 800
    },
    timeout=60
)
print("HTTP Status Code:", response.status_code)
print("Raw Response:", response.text)

result = response.json()
ai_text = result.get("choices", [{}])[0].get("message", {}).get("content", "No result!")

with open("suggestions.txt", "w") as sf:
    sf.write(ai_text)