# The System Agent (Task 3) - Documentation

## Provider Configuration

- Provider: Qwen Code API (self-hosted on VM)
- VM Address: 10.93.26.99:8080
- Model: qwen3-coder-plus
- API Base: http://10.93.26.99:8080/v1

## General Architecture

The agent is a Python script that interacts with the Qwen LLM via an OpenAI-compatible API. The agent has access to three tools that it can call based on the user's question type.

## Tools Available

### 1. list_files(path)
Lists all files and directories in the specified project directory. Used for exploring the wiki structure or source code directories.

### 2. read_file(filepath)
Reads and returns the contents of a file at the specified path. Used for retrieving documentation text or examining source code. The tool is protected from directory traversal attacks.

### 3. query_api(method, path, body)
Sends HTTP requests to the live backend API and returns the status code and response body. Used for questions about live data, system status, or API behavior.

Authentication: Uses the LMS_API_KEY via the Authorization: Bearer header.

## When to Use Each Tool

- Wiki/Documentation questions: Use list_files and read_file
- Source code questions: Use read_file
- Live data questions: Use query_api (e.g., item count, analytics)
- Bug diagnosis: Use query_api first to see the error, then read_file to find the bug

## Environment Variables

| Variable | Purpose | Source |
|----------|-------------|-----------|
| LLM_API_KEY | Qwen OAuth token | .env.agent.secret |
| LLM_API_BASE | Qwen API endpoint | .env.agent.secret |
| LLM_MODEL | Model name | .env.agent.secret |
| LMS_API_KEY | Backend API key | .env.docker.secret |
| AGENT_API_BASE_URL | Backend URL | Default: http://localhost:42002 |

## Lessons Learned

1. Authentication header format: The backend uses FastAPI's HTTPBearer which expects the Authorization header with Bearer scheme, not X-API-Key header.

2. Tool descriptions are critical: Clear and detailed tool descriptions help the LLM choose the appropriate tool for each question.

3. Error handling: API errors should be properly returned to the LLM so it can diagnose issues and potentially retry with different parameters.

4. None content handling: When the LLM returns tool calls, the content field is null (not missing). Use (msg.get('content') or '') instead of msg.get('content', '').

## Test Results

- test_agent_uses_read_file_for_framework_question: PASSED
- test_agent_uses_query_api_for_item_count: PASSED

Both regression tests verify that the agent correctly selects tools based on question type.

## Usage

```bash
uv run agent.py "question"
uv run pytest test_agent.py -v
```

## Acceptance Criteria Status

- [plans/task-3.md exists with implementation plan - DONE
- [agent.py defines query_api as function-calling schema - DONE
- [query_api authenticates with LMS_API_KEY from environment - DONE
- [Agent reads all LLM config from environment variables - DONE
- [Agent reads AGENT_API_BASE_URL from environment - DONE
- [Agent answers static system questions correctly - DONE
- [Agent answers data-dependent questions with plausible values - DONE
- [AGENT.md documents architecture and lessons learned - DONE
- [2 tool-calling regression tests exist and pass - DONE

