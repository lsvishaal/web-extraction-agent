# web-extraction-agent

An AI agent that transforms unstructured web content into organized, structured data by combining Firecrawl's web scraping with Pydantic's structured output validation.

## Features

- **Dynamic Tool Management**: Add, enable, or disable MCP tools at runtime
- **Flexible Prompts**: Manage multiple prompts and switch between them dynamically
- **Configuration as Code**: Load and save agent configurations from JSON files
- **Mem0 Integration**: Built-in memory capabilities for context retention
- **GPT-5 Powered**: Uses OpenAI's GPT-5 model via OpenRouter for superior intelligence

## Quick Start

### Prerequisites

- Python 3.12+
- OpenRouter API key
- Mem0 API key

### Setup

```bash
# Clone and setup
cd web-extraction-agent
uv venv --python 3.12
source .venv/bin/activate
uv sync

# Configure environment
cp .env.example .env
```

Edit `.env` and add:
```
OPENROUTER_API_KEY=your_key_here
MEM0_API_KEY=your_key_here
```

### Run

```bash
# Install and check code quality
make install
make check

# Run the agent
python -m web_extraction_agent.main
```

## Configuration

The agent automatically creates a `config.json` file on first run with:

- **Tools**: Register and manage MCP tools
- **Prompts**: Define and activate different instruction sets
- **Model**: Powered by GPT-5 via OpenRouter
- **Settings**: Debug mode, timeouts, and more

Edit `web_extraction_agent/config.json` to customize your agent.

## Architecture

### Core Components

- **config_manager.py**: Configuration management for tools and prompts
- **tool_manager.py**: Dynamic MCP tool lifecycle management
- **main.py**: Agent initialization and request handling

### Dynamic Updates

The tool manager supports runtime updates:

```python
# Add a new tool
tool_manager.add_tool(ToolConfig(...))

# Enable/disable tools
tool_manager.enable_tool("tool_name")
tool_manager.disable_tool("tool_name")

# Reconnect with changes
await tool_manager.reconnect()
```

## Testing

Health check endpoint:
```bash
curl http://localhost:3773/health
```

Send a request to the agent:
```bash
curl -X POST http://localhost:3773/run \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Extract information from https://example.com"}
    ]
  }'
```

## Code Quality

```bash
make test              # Run tests
make format            # Format code
make lint              # Run linters
make check             # Run all checks
```

## Contributing

Contributions are welcome! Please follow PEP 8 and include tests for new features.

## License

MIT License - see LICENSE file for details
