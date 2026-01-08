"""Integration tests for the web extraction agent."""

import shlex
import subprocess
import time
import uuid
from pathlib import Path

import pytest
import requests

AGENT_URL = "http://localhost:3773"


def send_a2a_message(text: str, timeout: int = 30) -> dict:
    """Send a message to the agent via A2A protocol."""
    msg_id = str(uuid.uuid4())
    ctx_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "message/send",
        "params": {
            "configuration": {"acceptedOutputModes": ["text/plain", "application/json"]},
            "message": {
                "messageId": msg_id,
                "contextId": ctx_id,
                "taskId": task_id,
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
            },
        },
    }

    response = requests.post(
        f"{AGENT_URL}/", json=payload, headers={"Content-Type": "application/json"}, timeout=timeout
    )
    return response.json()


@pytest.fixture(scope="module")
def agent_process():
    """Start the agent for testing."""
    # Start the agent in the background
    cmd = "python -m web_extraction_agent"
    # Use the directory containing this test file as the reference point
    project_root = Path(__file__).parent.parent
    process = subprocess.Popen(  # noqa: S603
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root),
    )

    # Wait for agent to start
    time.sleep(5)

    yield process

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


@pytest.mark.integration
def test_agent_manifest(agent_process):
    """Test that the agent manifest endpoint works."""
    response = requests.get(f"{AGENT_URL}/.well-known/agent.json", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "web-extraction-agent"
    assert "capabilities" in data


@pytest.mark.integration
def test_docs_endpoint(agent_process):
    """Test that the docs endpoint works."""
    response = requests.get(f"{AGENT_URL}/docs", timeout=10)
    assert response.status_code == 200
    assert "Bindu" in response.text


@pytest.mark.integration
def test_send_message(agent_process):
    """Test sending a message to the agent."""
    result = send_a2a_message("Hello, what can you do?")
    assert "result" in result
    # Task can be submitted or working depending on processing speed
    assert result["result"]["status"]["state"] in ("submitted", "working", "completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
