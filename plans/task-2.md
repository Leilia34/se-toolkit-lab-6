# Task 2: Documentation Agent Implementation Plan

## Tools
- `read_file(path)`: reads a file from the project, checks path to prevent directory traversal.
- `list_files(path)`: lists contents of a directory, also validates path.

## Tool schemas
Defined as OpenAI function-calling format with parameters and descriptions.

## Agentic loop
1. Send user question + tool definitions to LLM.
2. If LLM returns `tool_calls`:
   - Execute each tool.
   - Append results as `tool` messages.
   - Repeat (max 10 iterations).
3. If LLM returns a text message without `tool_calls`, treat it as final answer. Extract `source` if present, output JSON.

## System prompt strategy
Instruct LLM to first explore wiki using `list_files`, then read relevant files with `read_file`, and finally provide answer with `source` in format `wiki/file.md#section`.
