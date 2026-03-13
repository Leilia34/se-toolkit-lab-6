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

load_dotenv(env_path)

API_KEY = os.getenv('LLM_API_KEY')
API_BASE = os.getenv('LLM_API_BASE', 'https://openrouter.ai/api/v1')
MODEL = os.getenv('LLM_MODEL')

if not API_KEY or not MODEL:
    print("❌ Missing LLM_API_KEY or LLM_MODEL in .env.agent.secret", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.absolute()

# ---------- Tool implementations ----------
def read_file(path: str) -> str:
    """Read a file from the project directory."""
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        # Security: prevent directory traversal
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return "Error: Access denied (path outside project)"
        if not full_path.exists():
            return f"Error: File {path} does not exist"
        if not full_path.is_file():
            return f"Error: {path} is not a file"
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_files(path: str) -> str:
    """List contents of a directory."""
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return "Error: Access denied (path outside project)"
        if not full_path.exists():
            return f"Error: Directory {path} does not exist"
        if not full_path.is_dir():
            return f"Error: {path} is not a directory"
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
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root, e.g., 'wiki/git-workflow.md'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path. Use this to explore the wiki structure before reading files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root, e.g., 'wiki'"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

# ---------- System prompt ----------
SYSTEM_PROMPT = """You are a helpful documentation agent for a software project.
You have access to two tools:
- list_files(path): lists files in a directory (use to explore the wiki)
- read_file(path): reads a file from the project (use to get content of documentation files)

Your goal is to answer the user's question based on the wiki documentation.
Always start by exploring the wiki with list_files, then read relevant files to find the answer.
When you finally give the answer, include the source file path and section anchor in the 'source' field.
The source should be in the format: wiki/<filename>#section (e.g., wiki/git-workflow.md#resolving-merge-conflicts).
If you are uncertain about the exact section, you can omit the anchor, but the file path must be included.

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
        sys.exit(1)

def execute_tool_calls(tool_calls):
    results = []
    for tc in tool_calls:
        func_name = tc['function']['name']
        args = json.loads(tc['function']['arguments'])
        if func_name == 'read_file':
            result = read_file(**args)
        elif func_name == 'list_files':
            result = list_files(**args)
        else:
            result = f"Unknown tool: {func_name}"
        results.append({
            "tool_call_id": tc['id'],
            "role": "tool",
            "name": func_name,
            "content": result
        })
    return results

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run agent.py 'Your question'", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
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
                "content": message.get('content'),
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
            output = {
                "answer": final_content.strip(),
                "source": source,
                "tool_calls": tool_calls_history
            }
            print(json.dumps(output, ensure_ascii=False))
            return

    # If we exit the loop due to max iterations
    output = {
        "answer": "Maximum tool calls reached without final answer.",
        "source": "",
        "tool_calls": tool_calls_history
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == '__main__':
    main()
