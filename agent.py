#!/usr/bin/env python3
"""
Agent with tools: read_file and list_files.
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
load_dotenv('.env.agent.secret')
load_dotenv('.env.docker.secret')

LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_API_BASE = os.getenv('LLM_API_BASE')
LLM_MODEL = os.getenv('LLM_MODEL')
LMS_API_KEY = os.getenv('LMS_API_KEY')
AGENT_API_BASE_URL = os.getenv('AGENT_API_BASE_URL', 'http://localhost:42002')

API_KEY = LLM_API_KEY
API_BASE = LLM_API_BASE
MODEL = LLM_MODEL

if not API_KEY or not MODEL:
    print("❌ Missing LLM_API_KEY or LLM_MODEL in .env.agent.secret", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path.cwd()

def query_api(method: str, path: str, body: str = None) -> str:
    """Выполняет запрос к бэкенду и возвращает статус и тело ответа."""
    url = f"{AGENT_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {LMS_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=body if body else None,
            timeout=10
        )
        try:
            body_content = response.json()
        except:
            body_content = response.text
        return json.dumps({"status_code": response.status_code, "body": body_content})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": f"Request failed: {str(e)}"})

def read_file(filepath: str) -> str:
    """Read a file from the project directory."""
    try:
        full_path = (PROJECT_ROOT / filepath).resolve()
        # Security: prevent directory traversal
        if not str(full_path).lower().startswith(str(PROJECT_ROOT).lower()):
            return "Error: Access denied (path outside project)"
        if not full_path.exists():
            return f"Error: File {filepath} does not exist"
        if not full_path.is_file():
            return f"Error: {filepath} is not a file"
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_files(dirpath: str) -> str:
    """List contents of a directory."""
    try:
        full_path = (PROJECT_ROOT / dirpath).resolve()
        if not str(full_path).lower().startswith(str(PROJECT_ROOT).lower()):
            return "Error: Access denied (path outside project)"
        if not full_path.exists():
            return f"Error: Directory {dirpath} does not exist"
        if not full_path.is_dir():
            return f"Error: {dirpath} is not a directory"
        items = [p.name for p in full_path.iterdir()]
        return "\n".join(sorted(items))
    except Exception as e:
        return f"Error listing directory: {str(e)}"
# ---------- Tool schemas (OpenAI format) ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project repository. Use this to get detailed information from documentation files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string", "description": "Directory path"}
                },
                "required": ["dirpath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Send HTTP request to the backend API. Use for questions about live data, system status, or API behavior. Returns status code and response body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "description": "HTTP method"
                    },
                    "path": {
                        "type": "string",
                        "description": "API endpoint path (e.g., '/items/')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST/PUT"
                    }
                },
                "required": ["method", "path"]
            }
        }
    }
]

# ---------- System prompt ----------
SYSTEM_PROMPT = """You are a helpful documentation agent for a software project.
You have access to tools:
- list_files(path): lists files in a directory (use to explore the wiki or source code)
- read_file(path): reads a file from the project (use to get content of documentation files or source code)
- query_api(method, path, body): sends HTTP request to the live backend API (use for questions about live data, system status, or API behavior). Returns status code and response body.
Guidelines:
- For questions about the wiki, documentation, or source code, use list_files and read_file.
- For questions about live data (e.g., item count, analytics), query the appropriate API endpoint using query_api.
- If you get an error from the API, read the relevant source code to diagnose the bug.
- When giving the final answer, include the source file path and section anchor in the 'source' field if the answer came from documentation. The source should be in the format: wiki/<filename>#section (e.g., wiki/git-workflow.md#resolving-merge-conflicts). If the answer came from the API, the source field can be empty.

Do not make up information. If you cannot find the answer, say so.
"""

# ---------- Agent helpers ----------
def call_llm(messages, tools=None):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:42002',
        'X-Title': 'SE Toolkit Lab Agent',
    }
    payload = {
        'model': MODEL,
        'messages': messages,
        'temperature': 0.7,
    }
    if tools:
        payload['tools'] = tools
    try:
        response = requests.post(
            f'{API_BASE}/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'Error calling LLM: {e}', file=sys.stderr)
        raise RuntimeError(f"LLM call failed: {e}") from e

def execute_tool_calls(tool_calls):
    results = []
    for tc in tool_calls:
        func_name = tc['function']['name']
        args = json.loads(tc['function']['arguments'])
        if func_name == 'read_file':
            result = read_file(**args)
        elif func_name == 'list_files':
            result = list_files(**args)
        elif func_name == 'query_api':
            result = query_api(**args)
        else:
            result = f"Unknown tool: {func_name}"
        results.append({
            "tool_call_id": tc['id'],
            "role": "tool",
            "name": func_name,
            "content": result
        })
    return results

def process_question(question: str) -> dict:
    """Обрабатывает вопрос и возвращает словарь с ответом, source и tool_calls."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]
    tool_calls_history = []
    max_iter = 10
    for _ in range(max_iter):
        data = call_llm(messages, tools=tools)
        choice = data['choices'][0]
        message = choice['message']

        if message.get('tool_calls'):
            tool_calls = message['tool_calls']
            # Record the calls (without results yet)
            for tc in tool_calls:
                tool_calls_history.append({
                    "tool": tc['function']['name'],
                    "args": json.loads(tc['function']['arguments']),
                    "result": None
                })
            # Append assistant message with tool_calls
            messages.append({
                "role": "assistant",
                "content": message.get('content') or '',
                "tool_calls": tool_calls
            })
            # Execute tools and get results
            tool_results = execute_tool_calls(tool_calls)
            messages.extend(tool_results)
            # Update history with results
            for i, tr in enumerate(tool_results):
                tool_calls_history[-len(tool_results) + i]["result"] = tr['content']
        else:
            # No tool calls – this is the final answer
            final_content = message.get('content', '')
            # Try to extract source (simple heuristic: look for "Source:" line)
            source = ""
            lines = final_content.split('\n')
            for line in lines:
                if line.lower().startswith('source:'):
                    source = line[7:].strip()
                    final_content = '\n'.join(l for l in lines if not l.lower().startswith('source:'))
                    break
            return {
                "answer": final_content.strip(),
                "source": source,
                "tool_calls": tool_calls_history
            }
    # If we exit the loop due to max iterations
    return {
        "answer": "Maximum tool calls reached without final answer.",
        "source": "",
        "tool_calls": tool_calls_history
    }

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run agent.py 'Your question'", file=sys.stderr)
        sys.exit(1)
    question = sys.argv[1]
    output = process_question(question)
    print(json.dumps(output, ensure_ascii=False))
 
if __name__ == '__main__':
    main()
