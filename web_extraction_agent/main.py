# |---------------------------------------------------------|
# |                                                         |
# |                 Give Feedback / Get Help                |
# | https://github.com/getbindu/Bindu/issues/new/choose    |
# |                                                         |
# |---------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""web-extraction-agent - An Bindu Agent."""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from bindu.penguin.bindufy import bindufy
from dotenv import load_dotenv

from web_extraction_agent.config_manager import AgentConfigManager, create_default_config
from web_extraction_agent.tool_manager import ToolManager

# Load environment variables from .env file
load_dotenv()

# Global instances
config_manager: AgentConfigManager | None = None
tool_manager: ToolManager | None = None
agent: Agent | None = None
model_name: str | None = None
api_key: str | None = None
mem0_api_key: str | None = None
_initialized: bool = False
_init_lock: asyncio.Lock = asyncio.Lock()


def load_config() -> dict:
    """Load agent configuration from project root."""
    # Get path to agent_config.json in project root
    config_path = Path(__file__).parent / "agent_config.json"

    with open(config_path) as f:
        return json.load(f)


async def initialize_config() -> None:
    """Initialize configuration manager.

    Loads from config file if it exists, otherwise creates default config.
    """
    global config_manager

    config_file = Path(__file__).parent / "config.json"

    if config_file.exists():
        print(f"📋 Loading configuration from {config_file}")
        config_manager = AgentConfigManager.load_from_file(config_file)
    else:
        print("📋 Creating default configuration")
        config_manager = create_default_config()
        # Save it for future use
        config_manager.save_to_file(config_file)


# Create the agent instance
async def initialize_agent() -> None:
    """Initialize the agent once with current configuration."""
    global agent, model_name, tool_manager, config_manager

    if not model_name:
        msg = "model_name must be set before initializing agent"
        raise ValueError(msg)

    if not config_manager:
        msg = "config_manager must be initialized before initializing agent"
        raise ValueError(msg)
    if not tool_manager:
        msg = "tool_manager must be initialized before initializing agent"
        raise ValueError(msg)

    # Get active prompt
    active_prompt_config = config_manager.get_active_prompt()
    instructions = active_prompt_config.template if active_prompt_config else ""

    tools_list = tool_manager.get_tools_list()
    agent = Agent(
        name="web-extraction-agent",
        model=OpenRouter(id=model_name),
        tools=tools_list,
        instructions=instructions,
        add_datetime_to_context=True,
        markdown=True,
    )
    print("✅ Agent initialized")


async def cleanup_tools() -> None:
    """Close all tool connections."""
    global tool_manager

    if tool_manager:
        await tool_manager.shutdown()


async def run_agent(messages: list[dict[str, str]]) -> Any:
    """Run the agent with the given messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Agent response
    """
    global agent

    if not agent:
        msg = "Agent not initialized"
        raise ValueError(msg)

    # Run the agent and get response
    response = await agent.arun(messages)
    return response


async def handler(messages: list[dict[str, str]]) -> Any:
    """Handle incoming agent messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
                  e.g., [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Returns:
        Agent response (ManifestWorker will handle extraction)
    """  # Run agent with messages
    global _initialized

    # Lazy initialization on first call (in bindufy's event loop)
    async with _init_lock:
        if not _initialized:
            print("🔧 Initializing configuration, tools, and agent...")
            # Initialize configuration first
            await initialize_config()
            # Initialize tool manager
            await initialize_tools()
            # Then initialize agent
            await initialize_agent()
            _initialized = True

    # Run the async agent
    result = await run_agent(messages)
    return result


async def initialize_tools() -> None:
    """Initialize the tool manager with environment variables."""
    global tool_manager, config_manager

    if not config_manager:
        msg = "config_manager must be initialized before initializing tools"
        raise ValueError(msg)

    # Build environment with API keys
    env = {
        **os.environ,
    }

    tool_manager = ToolManager(config_manager)
    await tool_manager.initialize(env)


def main():
    """Start the web extraction agent server."""
    global model_name, api_key, mem0_api_key

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Bindu Agent with MCP Tools")
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("MODEL_NAME", "openai/gpt-5"),
        help="Model ID to use (default: openai/gpt-5, env: MODEL_NAME)",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key (env: OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--mem0-api-key",
        type=str,
        default=os.getenv("MEM0_API_KEY"),
        help="Mem0 API key (env: MEM0_API_KEY)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=os.getenv("CONFIG_FILE", "config.json"),
        help="Configuration file path (env: CONFIG_FILE)",
    )
    args = parser.parse_args()

    # Set global model name and API keys
    model_name = args.model
    api_key = args.api_key
    mem0_api_key = args.mem0_api_key

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY required")  # noqa: TRY003
    if not mem0_api_key:
        raise ValueError("MEM0_API_KEY required. Get your API key from: https://app.mem0.ai/dashboard/api-keys")  # noqa: TRY003

    print(f"🤖 Using model: {model_name}")
    print("🧠 Mem0 memory enabled")
    print(f"📋 Configuration file: {args.config}")

    # Load base configuration
    config = load_config()

    try:
        # Bindufy and start the agent server
        # Note: Configuration, tools and agent will be initialized lazily on first request
        print("🚀 Starting Bindu agent server...")
        bindufy(config, handler)
    finally:
        # Cleanup on exit
        print("\n🧹 Cleaning up...")
        asyncio.run(cleanup_tools())


# Bindufy and start the agent server
if __name__ == "__main__":
    main()
