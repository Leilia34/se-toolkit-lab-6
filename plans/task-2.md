# Task 2: The Documentation Agent

### Tools to implement
- `read_file(path)` – reads a file from the project.  
  **Security**: use `os.path.abspath` to prevent directory traversal.
- `list_files(path)` – lists contents of a directory.  
  **Security**: same as above.

### Tool schemas
I will define them in OpenAI-compatible format as required by the LLM API.

### Agentic loop
1. Send the user question + tool definitions to the LLM.
2. If the response contains `tool_calls`:
   - Execute each tool.
   - Append the results as new messages with role `tool`.
   - Go back to step 1.
3. If the response is a plain text message, treat it as the final answer.
   - Extract `answer` and `source`.
   - Output JSON with `answer`, `source`, and `tool_calls`.

### System prompt strategy
I will instruct the LLM to:
- First explore the wiki using `list_files`.
- Then read relevant files with `read_file`.
- When answering, include the source in the format `wiki/<file>#section`.
- If uncertain, state so.

### Path security
- Always resolve paths relative to project root.
- Reject paths that try to go outside using `os.path.abspath` and prefix check.

### Testing
- Add 2 regression tests to verify tool usage and source extraction.
