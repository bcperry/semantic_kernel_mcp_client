# 🚀 Semantic Kernel MCP Client

A powerful Python framework that bridges Microsoft's Semantic Kernel with Model Context Protocol (MCP) servers, enabling AI agents to seamlessly interact with external tools and services. Perfect for building intelligent agents that can access databases, APIs, and specialized services through standardized MCP connections.

## ✨ Features

- **🧠 Smart Agent Framework**: Define AI agents with custom personalities and behaviors using JSON configuration
- **🔌 Multi-MCP Server Support**: Connect to multiple MCP servers simultaneously (HTTP and SSE protocols)
- **🦙 Ollama Integration**: Uses local Ollama models for privacy-focused AI inference
- **📊 Interactive Notebooks**: Jupyter notebook support for agent development and testing
- **⚡ Async Architecture**: Built for performance with full async/await support
- **🎯 Function Calling**: Automatic tool discovery and execution from connected MCP servers
- **🏈 Real-world Examples**: Includes fantasy football and database integration examples

## 🛠️ Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** - Modern Python package manager
- **[Ollama](https://ollama.ai/)** - Local AI model server
- **MCP Servers** - One or more MCP-compatible tool servers

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/bcperry/semantic_kernel_mcp_client.git
cd semantic_kernel_mcp_client
uv sync
```

### 2. Setup Ollama

```bash
# Install and run Ollama
ollama pull gpt-oss:20b
ollama serve
```

### 3. Configure Your Agent

Edit `agent_definition.json` to customize your agent:

```json
{
  "ai_model_id": "gpt-oss:20b",
  "host": "http://ollama.home",
  "system_message": "You are a helpful assistant",
  "servers": {
    "your_server": {
      "url": "http://your-mcp-server:8000/mcp",
      "type": "http"
    }
  }
}
```

### 4. Run the Agent

```bash
# Interactive Jupyter notebook
uv run jupyter lab function.ipynb

# Or programmatically
uv run python -c "
from agent import Agent
import asyncio
import json

async def main():
    with open('agent_definition.json') as f:
        agent_def = json.load(f)
    
    agent = await Agent.create(agent_def)
    result = await agent.run_agent('Hello, what can you do?')
    print(result['messages'][-1]['content'])

asyncio.run(main())
"
```

## 📁 Project Structure

```
semantic_kernel_mcp_client/
├── 📄 agent.py              # Core Agent class with MCP integration
├── 📄 agent_definition.json # Agent configuration (AI model, servers, personality)
├── 📓 function.ipynb        # Interactive notebook for testing agents
├── 📄 pyproject.toml        # Project dependencies and metadata
├── 📄 README.md            # You are here! 👋
└── 🔒 uv.lock              # Dependency lock file
```

## 🔧 Core Components

### Agent Class
The `Agent` class is the heart of the framework:
- **Async Factory Pattern**: Use `Agent.create()` for proper initialization
- **Dynamic MCP Loading**: Automatically discovers and loads tools from MCP servers
- **Conversational Memory**: Maintains chat history with configurable system prompts
- **Error Handling**: Robust error handling for network and MCP server issues

### MCP Integration
- **Multiple Protocols**: Supports both HTTP and Server-Sent Events (SSE) MCP servers
- **Tool Discovery**: Automatically imports all available tools from connected servers
- **Streaming Support**: Real-time streaming responses for better user experience
- **Connection Pooling**: Efficient connection management for multiple servers

### Configuration System
- **JSON-based Config**: Simple JSON configuration for agent behavior and connections
- **Environment Flexibility**: Easy switching between development and production servers
- **Model Agnostic**: Works with any Ollama-compatible model

## 💡 Usage Examples

### Fantasy Football Agent
```python
# The included example shows how to query fantasy football data
result = await ff_agent.run_agent("what is the list of all players on Blaine's fantasy football team?")
print(result.get("messages")[-1]['content'])
```

### Database Integration
```python
# Example with SQL tools via MCP
db_result = await agent.run_agent("What tables are in my database?")
```

### Custom MCP Server
```json
{
  "servers": {
    "custom_tools": {
      "url": "http://localhost:3000/mcp",
      "type": "http"
    },
    "streaming_service": {
      "url": "https://api.example.com/sse",
      "type": "sse"
    }
  }
}
```

## 🔍 Advanced Configuration

### Custom System Messages
Personalize your agent's behavior:
```json
{
  "system_message": "Answer like a pirate",  // 🏴‍☠️ Arrr, matey!
  "system_message": "You are a SQL expert", // 📊 Database specialist
  "system_message": "Be concise and technical" // 🔧 Engineering focused
}
```

### Multiple Model Support
Switch between different Ollama models:
```json
{
  "ai_model_id": "llama3.2:latest",    // 🦙 Latest Llama
  "ai_model_id": "codellama:13b",      // 💻 Code specialist
  "ai_model_id": "mistral:latest"      // 🌟 Mistral model
}
```

## 🛠️ Development

### Jupyter Notebook Development
The included `function.ipynb` provides an interactive development environment:

```bash
uv run jupyter lab function.ipynb
```

### Adding Development Dependencies
```bash
uv sync --group dev
```

This includes:
- **ipykernel** - Jupyter notebook support
- **Additional dev tools** as needed

### Extending the Agent
1. **Add new MCP servers** to `agent_definition.json`
2. **Customize system messages** for different use cases
3. **Implement custom plugins** using the MCP specification
4. **Create specialized agents** for different domains

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **🔌 Ollama Connection Error** | Ensure Ollama is running: `ollama serve` |
| **🌐 MCP Server Timeout** | Check server URL and network connectivity |
| **🤖 Model Not Found** | Pull the model: `ollama pull gpt-oss:20b` |
| **📦 Import Errors** | Run `uv sync` to install dependencies |
| **🔄 Async Errors** | Use `Agent.create()` instead of `Agent()` |

### Debug Mode
Enable detailed logging by modifying the agent:
```python
agent._setup_logging(loglevel=logging.DEBUG)
```

### Performance Tips
- **Connection Pooling**: Reuse agent instances when possible
- **Model Selection**: Smaller models (7B) for faster responses
- **MCP Caching**: Implement caching in your MCP servers
- **Batch Operations**: Group related queries together

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup
```bash
git clone https://github.com/yourusername/semantic_kernel_mcp_client.git
cd semantic_kernel_mcp_client
uv sync --group dev
```

## 📚 Resources & Links

- **[Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)**
- **[Model Context Protocol Specification](https://modelcontextprotocol.io/docs/getting-started/intro)**
- **[Ollama Models](https://ollama.ai/library)**
- **[UV Package Manager](https://docs.astral.sh/uv/)**
- **[MCP Server Examples](https://github.com/modelcontextprotocol/servers)**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---