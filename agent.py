#!/usr/bin/env python3
"""
Agent that calls an LLM via OpenRouter and returns a JSON answer.
Usage: uv run agent.py "Your question"
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.env.agent.secret')
if not env_path.exists():
    print("❌ .env.agent.secret not found. Please create it from .env.agent.example", file=sys.stderr)
    sys.exit(1)

load_dotenv(env_path)

API_KEY = os.getenv('LLM_API_KEY')
API_BASE = os.getenv('LLM_API_BASE', 'https://openrouter.ai/api/v1')
MODEL = os.getenv('LLM_MODEL')

if not API_KEY or not MODEL:
    print("❌ Missing LLM_API_KEY or LLM_MODEL in .env.agent.secret", file=sys.stderr)
    sys.exit(1)

def call_llm(question):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:42002',
        'X-Title': 'SE Toolkit Lab Agent',
    }
    payload = {
        'model': MODEL,
        'messages': [{'role': 'user', 'content': question}],
        'temperature': 0.7,
    }

    try:
        response = requests.post(
            f'{API_BASE}/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        answer = data['choices'][0]['message']['content']
        return answer
    except requests.exceptions.Timeout:
        print('{"error": "Request timeout"}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'{{"error": "{str(e)}"}}', file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run agent.py 'Your question'", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    answer = call_llm(question)

    output = {
        'answer': answer,
        'tool_calls': []
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == '__main__':
    main()
