"""Integration tests for the web extraction agent."""

import os
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


def wait_for_agent(max_retries: int = 30, retry_delay: float = 1.0) -> bool:
    """Wait for agent to be available with retries.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        True if agent is ready, False if timeout
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{AGENT_URL}/.well-known/agent.json", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt < max_retries - 1:
            time.sleep(retry_delay)

    return False


@pytest.fixture(scope="module")
def agent_process():
    """Start the agent for testing.

    This fixture:
    1. Starts the agent process with environment variables
    2. Waits for it to be ready with retries
    3. Cleans up on test completion

    In CI/CD environments without necessary environment variables,
    integration tests are skipped automatically.
    """
    # Start the agent in the background
    cmd = "python -m web_extraction_agent"
    project_root = Path(__file__).parent.parent

    # Build environment with required variables for CI/CD
    env = os.environ.copy()

    # Check for required environment variables
    required_vars = ["OPENROUTER_API_KEY", "MEM0_API_KEY"]
    missing_vars = [var for var in required_vars if not env.get(var)]

    if missing_vars:
        pytest.skip(f"Skipping integration tests: missing environment variables {missing_vars}")

    # Start the agent process
    try:
        process = subprocess.Popen(  # noqa: S603
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            env=env,
        )
    except Exception as e:
        pytest.skip(f"Failed to start agent process: {e}")

    # Wait for agent to start with retries
    if not wait_for_agent(max_retries=30, retry_delay=1.0):
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:  # noqa: S110
            pass
        pytest.skip("Agent failed to start within timeout period")

    yield process

    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except Exception:  # noqa: S110
        pass


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
