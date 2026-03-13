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
# Agent for Tasks 1–2

## General architecture
The agent is a Python script that interacts with LLM via OpenRouter. Task 2 adds tools and an agent loop.

## Tools
- **`list_files(path)`** – returns a list of files and folders in the specified project directory (relative to the root). Used to explore the wiki structure.
- **`read_file(path)`** – reads the contents of a file at the specified path. Used to retrieve documentation text.

Both tools are protected from going beyond the project: it is checked that the absolute path starts with the project root directory.

## Agent loop
1. The initial request to LLM includes a system prompt, a user question, and tool descriptions (in the format of `tools`).
2. If LLM returns `tool_calls`, the agent executes the corresponding tools, adds the results as messages with the role of `tool`, and sends the updated history back to LLM.
3. Step 2 is repeated until the LLM returns a final answer without invoking the tools
4. The final answer is parsed: the `source` field is extracted from the text (if it is present in the format `Source: ...`), and the rest is considered the `answer`. Then, a JSON is output with the `answer`, `source`, and `tool_calls` fields (the history of all calls).

##Promt 
You are a helpful documentation agent for a software project.
You have access to two tools:

list_files(path): lists files in a directory (use to explore the wiki)

read_file(path): reads a file from the project (use to get content of documentation files)

Your goal is to answer the user's question based on the wiki documentation.
Always start by exploring the wiki with list_files, then read relevant files to find the answer.
When you finally give the answer, include the source file path and section anchor in the 'source' field.
The source should be in the format: wiki/<filename>#section (e.g., wiki/git-workflow.md#resolving-merge-conflicts).
If you are uncertain about the exact section, you can omit the anchor, but the file path must be included.
Do not make up information. If you cannot find the answer, say so.
