# Plan: The System Agent (Task 3)

## Implementation Plan

### 1. query_api Tool Schema

The query_api tool is defined in agent.py:
- method: GET, POST, PUT, DELETE
- path: API endpoint (e.g., /items/)
- body: Optional JSON for POST/PUT

### 2. Authentication

query_api uses LMS_API_KEY from .env.docker.secret via X-API-Key header.

### 3. System Prompt

The system prompt guides LLM to choose:
- Wiki/documentation questions -> list_files, read_file
- Live data questions -> query_api
- Bug diagnosis -> query_api first, then read_file

### 4. Environment Variables

| Variable | Purpose | Source |
|----------|---------|--------|
| LLM_API_KEY | LLM API key | .env.agent.secret |
| LLM_API_BASE | LLM endpoint | .env.agent.secret |
| LLM_MODEL | Model name | .env.agent.secret |
| LMS_API_KEY | Backend key | .env.docker.secret |
| AGENT_API_BASE_URL | Backend URL | Default: http://localhost:42002 |

### 5. Benchmark Strategy

1. Run uv run run_eval.py
2. Analyze failures
3. Fix issues (tool descriptions, endpoints, auth)
4. Re-run until 10/10 pass

---

## Benchmark Results

### Initial Run

- Score: _/10
- First failures: TBD

### Final Score

- Score: _/10
