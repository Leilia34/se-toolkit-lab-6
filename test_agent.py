import pytest
import json
from agent import process_question
from unittest.mock import patch, MagicMock

def create_mock_llm_response(tool_name, tool_args):
    """Создаёт имитацию ответа LLM с вызовом инструмента."""
    mock_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args)
                    }
                }]
            }
        }]
    }
    return mock_response

@patch('agent.call_llm')
def test_agent_uses_read_file_for_framework_question(mock_call_llm):
    mock_call_llm.return_value = create_mock_llm_response("read_file", {"filepath": "some/file.py"})
    question = "What Python web framework does this project's backend use? Read the source code to find out."
    result = process_question(question)
    assert any(tc["tool"] == "read_file" for tc in result["tool_calls"])

@patch('agent.call_llm')
def test_agent_uses_query_api_for_item_count(mock_call_llm):
    mock_call_llm.return_value = create_mock_llm_response("query_api", {"method": "GET", "path": "/items/"})
    question = "How many items are currently stored in the database? Query the running API to find out."
    result = process_question(question)
    assert any(tc["tool"] == "query_api" for tc in result["tool_calls"]), "Должен быть вызван query_api"
