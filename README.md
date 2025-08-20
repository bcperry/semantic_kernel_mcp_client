# Semantic Kernel MCP Integration

A Python application that demonstrates integration between Microsoft's Semantic Kernel and Model Context Protocol (MCP), enabling AI assistants to interact with external tools and services through a standardized protocol.

## Features

- **Semantic Kernel Integration**: Leverages Microsoft's Semantic Kernel framework for AI orchestration
- **MCP Plugin Support**: Connects to MCP servers to access external tools and data sources
- **Ollama Chat Completion**: Uses local Ollama models for AI inference
- **Interactive Chat Interface**: Command-line chat interface for real-time interaction
- **Function Calling**: Automatic function calling capabilities with external MCP tools
- **Fantasy Football Example**: Includes example integration with fantasy football data tools

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.ai/) running locally with the `gpt-oss:20b` model
- An MCP server running at `http://192.168.86.103:8000/mcp` (or modify the URL in the code)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd semantic_kernel_mcp
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Ensure Ollama is running with the required model:
   ```bash
   ollama pull gpt-oss:20b
   ollama serve
   ```

## Configuration

The application is configured to connect to:
- **Ollama Server**: `http://ollama.home` (modify in `main.py` if different)
- **MCP Server**: `http://192.168.86.103:8000/mcp` (modify in `main.py` for your MCP server)

## Usage

Run the application:

```bash
uv run main.py
```

The application will:
1. Initialize the Semantic Kernel
2. Connect to the Ollama chat completion service
3. Establish connection to the MCP server
4. Start an interactive chat session

### Example Interaction

```
🤖 Assistant ready! You can ask me to use any of the MCP tools listed above.
💡 Example: 'Can you help me with fantasy football data?'
Type 'exit' to quit.

User > Can you help me with fantasy football data?
Assistant > [AI response using MCP tools to fetch fantasy football information]

User > exit
```

## Project Structure

```
semantic_kernel_mcp/
├── main.py              # Main application entry point
├── pyproject.toml       # Project configuration and dependencies
├── README.md           # This file
└── uv.lock            # Dependency lock file
```

## Key Components

### Semantic Kernel Setup
- Initializes a kernel instance for AI orchestration
- Configures Azure Chat Completion settings with automatic function calling
- Maintains chat history for conversational context

### MCP Integration
- Uses `MCPStreamableHttpPlugin` to connect to external MCP servers
- Enables the AI to call external tools and services
- Supports real-time streaming of tool responses

### Chat Interface
- Interactive command-line interface
- Maintains conversation history
- Supports graceful exit with 'exit' command

## Dependencies

- **semantic-kernel[mcp]**: Microsoft's Semantic Kernel with MCP support
- **ollama**: Python client for Ollama inference server

## Development

For development work, additional dependencies are available:

```bash
uv sync --group dev
```

This includes:
- **ipykernel**: For Jupyter notebook development

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**: Ensure Ollama is running and accessible at the configured host
2. **MCP Server Connection Error**: Verify the MCP server URL and that the server is running
3. **Model Not Found**: Make sure the `gpt-oss:20b` model is pulled in Ollama

### Logging

The application includes debug logging for the Semantic Kernel. Check the console output for detailed information about kernel operations and function calls.

## Acknowledgments

- [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)
- [Ollama](https://ollama.ai/)