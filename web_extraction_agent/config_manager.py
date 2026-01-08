"""Configuration management for dynamic prompt and tooling updates."""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolConfig(BaseModel):
    """Configuration for an MCP tool."""

    name: str = Field(..., description="Unique name for the tool")
    command: str = Field(..., description="MCP server command to execute")
    enabled: bool = Field(default=True, description="Whether this tool is enabled")
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables for this tool")
    timeout: int = Field(default=30, description="Timeout in seconds for this tool")
    description: str = Field(default="", description="Description of what this tool does")


class PromptConfig(BaseModel):
    """Configuration for agent instructions/prompts."""

    name: str = Field(..., description="Unique name for the prompt")
    template: str = Field(..., description="The prompt template text")
    enabled: bool = Field(default=True, description="Whether this prompt is enabled")
    version: str = Field(default="1.0", description="Version of this prompt")
    description: str = Field(default="", description="Description of this prompt")


class AgentConfigManager(BaseModel):
    """Manages agent configuration including tools and prompts."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tools: dict[str, ToolConfig] = Field(default_factory=dict, description="Registered tools")
    prompts: dict[str, PromptConfig] = Field(default_factory=dict, description="Registered prompts")
    active_tools: list[str] = Field(default_factory=list, description="List of active tool names")
    active_prompt: str = Field(default="default", description="Name of active prompt")
    model_id: str = Field(default="openai/gpt-5", description="Model ID to use")
    debug: bool = Field(default=False, description="Debug mode")

    def add_tool(self, tool: ToolConfig) -> None:
        """Add or update a tool configuration."""
        self.tools[tool.name] = tool
        if tool.enabled and tool.name not in self.active_tools:
            self.active_tools.append(tool.name)

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool configuration."""
        if tool_name in self.tools:
            del self.tools[tool_name]
        if tool_name in self.active_tools:
            self.active_tools.remove(tool_name)

    def enable_tool(self, tool_name: str) -> None:
        """Enable a tool."""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = True
            if tool_name not in self.active_tools:
                self.active_tools.append(tool_name)

    def disable_tool(self, tool_name: str) -> None:
        """Disable a tool."""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = False
        if tool_name in self.active_tools:
            self.active_tools.remove(tool_name)

    def add_prompt(self, prompt: PromptConfig) -> None:
        """Add or update a prompt configuration."""
        self.prompts[prompt.name] = prompt

    def set_active_prompt(self, prompt_name: str) -> None:
        """Set the active prompt."""
        if prompt_name in self.prompts:
            self.active_prompt = prompt_name

    def get_active_prompt(self) -> PromptConfig | None:
        """Get the currently active prompt."""
        return self.prompts.get(self.active_prompt)

    def get_active_tools(self) -> list[ToolConfig]:
        """Get list of enabled active tools."""
        return [self.tools[name] for name in self.active_tools if name in self.tools and self.tools[name].enabled]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfigManager":
        """Create from dictionary."""
        # Convert nested dicts to proper models
        if "tools" in data:
            data["tools"] = {k: ToolConfig(**v) if isinstance(v, dict) else v for k, v in data.get("tools", {}).items()}
        if "prompts" in data:
            data["prompts"] = {
                k: PromptConfig(**v) if isinstance(v, dict) else v for k, v in data.get("prompts", {}).items()
            }
        return cls(**data)

    def save_to_file(self, filepath: str | Path) -> None:
        """Save configuration to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            # Convert Pydantic models to dicts for JSON serialization
            data = self.to_dict()
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str | Path) -> "AgentConfigManager":
        """Load configuration from JSON file."""
        filepath = Path(filepath)
        if not filepath.exists():
            return cls()
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_default_config() -> AgentConfigManager:
    """Create default configuration for web extraction agent."""
    config = AgentConfigManager()

    # Add default tools - Firecrawl for web scraping
    config.add_tool(
        ToolConfig(
            name="firecrawl",
            command="npx -y firecrawl-mcp",
            description="Web scraping and content extraction using Firecrawl",
            environment={"FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")},
        )
    )

    # Add more tools based on environment
    if os.getenv("ENABLE_AIRBNB_MCP"):
        config.add_tool(
            ToolConfig(
                name="airbnb",
                command="npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
                description="Airbnb property search and information",
                enabled=True,
            )
        )

    if os.getenv("ENABLE_GOOGLE_MAPS_MCP"):
        config.add_tool(
            ToolConfig(
                name="google_maps",
                command="npx -y @modelcontextprotocol/server-google-maps",
                description="Google Maps location and routing information",
                enabled=True,
                environment={"GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", "")},
            )
        )

    # Add default prompt
    config.add_prompt(
        PromptConfig(
            name="default",
            template="""\
You are a helpful AI assistant specializing in web extraction and content analysis.
Your capabilities include:
- Extracting structured data from web pages
- Analyzing web content and organizing it
- Providing detailed information from web sources

Always:
- Be accurate and precise in your extraction
- Maintain data structure and hierarchy
- Ask for clarification if needed
- Format responses clearly
""",
            description="Default web extraction assistant prompt",
        )
    )

    return config
