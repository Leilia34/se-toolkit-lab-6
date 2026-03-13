The agent `agent.py` calls the language model via OpenRouter and returns a JSON response. This is the base for the following tasks.

## The provider used
- **Provider:** OpenRouter
- **Model:** `qwen/qwen3-coder:free` (can be changed in `.env.agent.secret`)
- **API Base:** `https://openrouter.ai/api/v1`

## Configuration
1. Copy the file `.env.agent.example` to `.env.agent.secret`.
2. Edit `.env.agent.secret`:
 ```env
 LLM_API_KEY=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
 LLM_API_BASE=https://openrouter.ai/api/v1
 LLM_MODEL=qwen/qwen3-coder:free
