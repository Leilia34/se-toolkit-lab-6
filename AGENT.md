# The System Agent (Task 3)

## Provider

- Provider: OpenRouter
- Model: Qwen/Qwen2.5-Coder-32B-Instruct
- API Base: https://openrouter.ai/api/v1

## Tools

### 1. list_files(path)
Lists files in a directory.

### 2. read_file(filepath)
Reads file contents.

### 3. query_api(method, path, body)
Sends HTTP requests to backend API.
- method: GET, POST, PUT, DELETE
- path: API endpoint
- body: Optional JSON

Authentication: X-API-Key header with LMS_API_KEY.

## Environment Variables

- LLM_API_KEY, LLM_API_BASE, LLM_MODEL from .env.agent.secret
- LMS_API_KEY from .env.docker.secret
- AGENT_API_BASE_URL (default: http://localhost:42002)

## Lessons Learned

1. Tool descriptions must be clear for LLM
2. Authentication critical for query_api
3. Handle API errors properly
4. Handle None content correctly

## Usage

uv run agent.py "question"
uv run run_eval.py
