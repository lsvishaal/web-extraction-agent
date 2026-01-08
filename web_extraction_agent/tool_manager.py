"""Tool management system for recursive tool/prompt updates."""

import os

from agno.tools.mcp import MultiMCPTools
from agno.tools.mem0 import Mem0Tools

from web_extraction_agent.config_manager import AgentConfigManager, ToolConfig


class ToolManager:
    """Manages MCP tools with dynamic loading and updating capabilities."""

    def __init__(self, config: AgentConfigManager):
        """Initialize the tool manager.

        Args:
            config: The agent configuration manager
        """
        self.config = config
        self.mcp_tools: MultiMCPTools | None = None
        self.mem0_tools: Mem0Tools | None = None
        self._is_connected = False

    async def initialize(self, env: dict[str, str] | None = None) -> None:
        """Initialize and connect to MCP servers.

        Args:
            env: Environment variables dict for MCP servers
        """
        if self._is_connected:
            print("✅ Tool manager already connected")
            return

        env = env or dict(os.environ)
        enabled_tools = self.config.get_active_tools()

        if not enabled_tools:
            print("⚠️  No tools configured")
            return

        commands = [tool.command for tool in enabled_tools if tool.command]
        if commands:
            try:
                self.mcp_tools = MultiMCPTools(
                    commands=commands,
                    env=env,
                    allow_partial_failure=True,
                    timeout_seconds=max(tool.timeout for tool in enabled_tools),
                )
                await self.mcp_tools.connect()
                print(f"✅ Connected to {len(commands)} MCP servers")
            except Exception as e:
                print(f"⚠️  Error connecting to MCP servers: {e}")

        # Initialize Mem0 tools if API key is available
        mem0_api_key = os.getenv("MEM0_API_KEY")
        if mem0_api_key:
            self.mem0_tools = Mem0Tools(api_key=mem0_api_key)
            print("✅ Initialized Mem0 tools")

        self._is_connected = True

    async def shutdown(self) -> None:
        """Close all tool connections."""
        if self.mcp_tools:
            try:
                await self.mcp_tools.close()
                print("🔌 Disconnected from MCP servers")
            except Exception as e:
                print(f"⚠️  Error closing MCP tools: {e}")
        self._is_connected = False

    def add_tool(self, tool: ToolConfig) -> None:
        """Add a new tool configuration.

        Args:
            tool: The tool configuration to add
        """
        self.config.add_tool(tool)
        if self._is_connected:
            print(f"⚠️  Tool added but not connected. Reconnect to enable: {tool.name}")

    def enable_tool(self, tool_name: str) -> None:
        """Enable a tool dynamically.

        Args:
            tool_name: Name of the tool to enable
        """
        self.config.enable_tool(tool_name)
        if self._is_connected:
            print("⚠️  Tool enabled but not reconnected. Call reconnect() to apply changes")

    def disable_tool(self, tool_name: str) -> None:
        """Disable a tool dynamically.

        Args:
            tool_name: Name of the tool to disable
        """
        self.config.disable_tool(tool_name)

    async def reconnect(self) -> None:
        """Reconnect with updated tool configuration."""
        if self._is_connected:
            await self.shutdown()
        await self.initialize()

    def get_tools_list(self) -> list:
        """Get list of active tool instances for agent.

        Returns:
            List of tool instances
        """
        tools = []
        if self.mcp_tools:
            tools.append(self.mcp_tools)
        if self.mem0_tools:
            tools.append(self.mem0_tools)
        return tools

    def is_connected(self) -> bool:
        """Check if tools are connected.

        Returns:
            True if connected to at least one tool
        """
        return self._is_connected
