import requests
import json

# Your API key
API_KEY = "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"

# For OpenAI API (if that's what you're using)
url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",  # or "gpt-4", "gpt-4-turbo", etc.
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Say 'API is working!' in 5 words."}
    ],
    "max_tokens": 50
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    print("✅ API Test Successful!")
    print(f"Response: {result['choices'][0]['message']['content']}")
    print(f"\nUsage: {result['usage']}")
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response body: {e.response.text}")