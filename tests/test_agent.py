import subprocess
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def test_agent_returns_json():
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / 'agent.py'), 'What is 2+2?'],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        timeout=70
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"

    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        assert False, f"Stdout is not valid JSON: {result.stdout}"

    assert 'answer' in data, "Missing 'answer' field"
    assert 'tool_calls' in data, "Missing 'tool_calls' field"
    assert isinstance(data['tool_calls'], list), "'tool_calls' must be a list"
