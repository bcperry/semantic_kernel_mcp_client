import asyncio

from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent, FunctionCallContent, FunctionResultContent

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin, MCPSsePlugin

import logging
import json
import os
from dotenv import load_dotenv



class Agent:
    def __init__(self, agent_definition: dict):
        # Initialize the kernel
        self.kernel = Kernel()
        self._setup_chat_completion(agent_definition)
        self.kernel.add_service(self.chat_completion)


        self.mcp_server_objects = []

        self._setup_logging()
    # NOTE: _setup_mcp_plugins is an async coroutine because connecting to MCP
    # servers requires awaiting network operations. Do NOT call it here
    # synchronously to avoid 'coroutine was never awaited' warnings. Use the
    # async factory `Agent.create(...)` or call `await agent._setup_mcp_plugins(...)`
    # from async code after constructing the instance.
        self._setup_execution_settings()
        self.history = ChatHistory()
        self.history.add_system_message(agent_definition.get("system_message", "You are a helpful assistant. Use your tools to assist users."))


    def _setup_logging(self, loglevel = logging.INFO):


        # Configure logging levels for different components
        logging.getLogger("semantic_kernel").setLevel(loglevel)
        logging.getLogger("semantic_kernel.kernel").setLevel(loglevel)
        logging.getLogger("semantic_kernel.connectors").setLevel(loglevel)
    
        # Set up a basic console handler if not already configured
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=loglevel,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _setup_execution_settings(self):
        # Enable planning
        self.execution_settings = AzureChatPromptExecutionSettings()
        self.execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    async def _setup_mcp_plugins(self, mcp_plugins):
        """Setup MCP plugins from either a list of dicts or a dict of server configs"""

        # Handle if mcp_plugins is a dict (from agent_definition.json servers section)
        if isinstance(mcp_plugins, dict):
            servers_list = []
            for server_name, server_config in mcp_plugins.items():
                server_dict = {
                    "name": server_name,
                    **server_config
                }
                servers_list.append(server_dict)
            mcp_plugins = servers_list
        
        # Handle if mcp_plugins is already a list
        if not isinstance(mcp_plugins, list):
            logging.warning(f"mcp_plugins should be a list or dict, got {type(mcp_plugins)}")
            return
            
        for server in mcp_plugins:
            server_name = server.get("name", "unknown")
            server_type = server.get("type", "http")  # default to http
            server_url = server.get("url")
            
            if not server_url:
                logging.warning(f"No URL provided for server {server_name}, skipping")
                continue
            
            mcp_server = None
            if "/mcp" in server_url:
                mcp_server = MCPStreamableHttpPlugin(
                    name=server_name,
                    url=server_url,
                )
            elif "/sse" in server_url:
                mcp_server = MCPSsePlugin(
                    name=server_name,
                    url=server_url,
                )
            else:
                logging.warning(f"Unknown server type '{server_type}' for server {server_name}, skipping")
                continue
            
            if mcp_server:
                try:
                    await mcp_server.connect()
                    self.available_tools = await mcp_server.session.list_tools()
                    self.kernel.add_plugin(mcp_server)
                    self.mcp_server_objects.append(mcp_server)
                    logging.info(f"Successfully connected to MCP server: {server_name} ({server_type})")
                    await mcp_server.close()
                except Exception as e:
                    logging.error(f"Error connecting to {server_name} MCP server: {e}")


    @classmethod
    async def create(cls, agent_definition: dict):
        """Async factory that constructs an Agent and awaits MCP plugin setup.

        Usage:
            agent = await Agent.create(agent_definition)
        """
        inst = cls(agent_definition)
        
        # Use mcp_plugins parameter if provided, otherwise use servers from agent_definition
        servers_to_setup = agent_definition.get("servers", {})
        
        await inst._setup_mcp_plugins(servers_to_setup)
        return inst

    async def run_agent(self, userInput: str, streaming: bool = False):

        # Add user input to the history
        self.history.add_user_message(userInput)

        # Accumulate content so we can add a single message to history at the end
        full_response = {
            "thoughts": [],
            "tool_calls": [],
            "messages": []
        }

        try:
            logging.info(f"Running agent with user input: {userInput}")
            for server in self.mcp_server_objects:
                await server.connect()
            response = self.chat_completion.get_streaming_chat_message_content(
                messages=userInput,
                chat_history=self.history,
                settings=self.execution_settings,
                kernel=self.kernel,
            )

            thoughts = 0
            tools = 0
            message = 0

            async for chunk in response:
                if isinstance(self.chat_completion, AzureChatCompletion):

                                        # messages
                    if "message" in chunk.content_type and len(chunk.content) > 0:
                        if message == 0:
                            message = message + 1
                            thoughts = 0
                            tools = 0
                            if streaming: yield str("\n--- Agent Message ---")
                        if streaming: yield str(chunk.content)
                        # accumulate a best-effort message representation

                        if chunk.inner_content is not None:
                            full_response['messages'].append(str(chunk.content))
                    #  # thoughts
                    # if "thoughts" in chunk.tag:
                    #     if thoughts == 0:
                    #         thoughts = thoughts + 1
                    #         tools = 0
                    #         message = 0
                    #         if streaming: yield str("\n--- Agent Thoughts ---")
                    #     thinking = chunk.inner_content['message'].thinking
                    #     # preserve if streaming: yield str behavior
                    #     if streaming: yield str(thinking)
                    #     # accumulate
                    #     try:
                    #         full_response['thoughts'].append(str(thinking))
                    #     except Exception:
                    #         full_response['thoughts'].append(repr(thinking))

                    # tools
                    elif len(chunk.items) > 0:
                        if tools == 0:
                            tools = tools + len(chunk.items)
                            message = 0
                            thoughts = 0
                            if streaming: yield str("\n--- Agent Tools ---")
                        tool_calls = chunk.items
                        for tool in tool_calls:
                            if tool.content_type == "function_result":
                                try:
                                    full_response['tool_calls'].append(tool.inner_content)
                                except Exception as e:
                                    logging.error("Error occurred while processing tool calls: %s", e)
                    else:
                        if chunk.finish_reason == 'tool_calls':
                            # This is a special case where the Azure Chat Completion API returns a tool call
                            # as a separate chunk with no content, so we skip it.
                            continue
                        else:
                            logging.debug("somehow made it here: ", chunk)

                
                else: # Ollama Chat Completion
                    # thoughts
                    if chunk.inner_content is not None and chunk.inner_content.get('message') is not None and chunk.inner_content['message'].thinking is not None:
                        if thoughts == 0:
                            thoughts = thoughts + 1
                            tools = 0
                            message = 0
                            if streaming: yield str("\n--- Agent Thoughts ---")
                        thinking = chunk.inner_content['message'].thinking
                        # preserve if streaming: yield str behavior
                        if streaming: yield str(thinking)
                        # accumulate
                        try:
                            full_response['thoughts'].append(str(thinking))
                        except Exception:
                            full_response['thoughts'].append(repr(thinking))

                    # tools
                    elif chunk.inner_content is not None and chunk.inner_content.get('message') is not None and chunk.inner_content['message'].tool_calls is not None:
                        if tools == 0:
                            tools = tools + 1
                            message = 0
                            thoughts = 0
                            if streaming: yield str("\n--- Agent Tools ---")
                        tool_calls = chunk.inner_content['message'].tool_calls
                        for tool in tool_calls:
                            if streaming: yield str(f"Tool: {tool.function.name}")
                            if streaming: yield str(f"Arguments: {tool.function.arguments}")
                            # accumulate
                            try:
                                full_response['tool_calls'].append({tool.function.name: tool.function.arguments})
                            except Exception:
                                full_response['tool_calls'].append({"generic": str(tool_calls)})
                    # messages
                    elif len(chunk.content) > 0:
                        if message == 0:
                            message = message + 1
                            thoughts = 0
                            tools = 0
                            if streaming: yield str("\n--- Agent Message ---")
                        if streaming: yield str(chunk)
                        # accumulate a best-effort message representation

                        if chunk.inner_content is not None:
                            full_response['messages'].append(str(chunk.content))




            # Reconstruct a single assistant message from the accumulated pieces
            assistant_parts = []
            if full_response.get('thoughts'):
                full_response['thoughts'] = "".join(full_response['thoughts'])
                assistant_parts.append("\n".join(full_response['thoughts']))
            if full_response.get('messages'):
                full_response['messages'] = "".join(full_response['messages'])
                assistant_parts.append("\n".join(full_response['messages']))
            if full_response.get('tool_calls'):
                # represent tool calls as a stringified list/dict
                assistant_parts.append(str(full_response['tool_calls']))

            assistant_text = "\n\n".join([p for p in assistant_parts if p]).strip()
            if assistant_text:
                # Try to add as an assistant message; fall back to system message if method isn't available
                try:
                    self.history.add_assistant_message(assistant_text)
                except Exception:
                    self.history.add_system_message(assistant_text)
            for server in self.mcp_server_objects:
                # Attempt to close the server connection gracefully
                try:
                    logging.info(f"Closing MCP server connection: {server.name}")
                    await server.close()
                except Exception as e:
                    logging.exception(f"Failed to close server connection: {e}")
        except Exception as e:
            # Best-effort cleanup; ignore errors
            logging.exception(f"The chat message processing failed. {e}")

        if not streaming:
            yield str(full_response)
            # return full_response

    def _setup_chat_completion(self, agent_definition):
        """Setup the chat completion service based on agent definition."""
        try:
            if "env_file_path" in agent_definition:
                logging.info(f"Loading environment variables from {agent_definition['env_file_path']}")
                # Load environment variables from .env file
                load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), agent_definition['env_file_path']))

                # Override agent_definition with environment variables if they exist
                if os.getenv("AZURE_OPENAI_ENDPOINT"):
                    agent_definition["endpoint"] = os.getenv("AZURE_OPENAI_ENDPOINT")
                if os.getenv("AZURE_OPENAI_API_KEY"):
                    agent_definition["api_key"] = os.getenv("AZURE_OPENAI_API_KEY")
                if os.getenv("AZURE_OPENAI_MODEL"):
                    agent_definition["deployment_name"] = os.getenv("AZURE_OPENAI_MODEL")
                if os.getenv("OPENAI_API_VERSION"):
                    agent_definition["api_version"] = os.getenv("OPENAI_API_VERSION")\
                    
                logging.info(f"Azure OpenAI endpoint: {agent_definition.get('endpoint', None)}")
            if "azure" in agent_definition.get("endpoint", ""):
                logging.info("Configuring Azure OpenAI Chat Completion")
                
                self.chat_completion = AzureChatCompletion(
                    service_id=agent_definition.get("service_id", None),
                    api_key=agent_definition.get("api_key", None),
                    deployment_name=agent_definition.get("deployment_name", None),
                    endpoint=agent_definition.get("endpoint", None),
                    base_url=agent_definition.get("base_url", None),
                    api_version=agent_definition.get("api_version", None),
                    ad_token=agent_definition.get("ad_token", None),
                    ad_token_provider=agent_definition.get("ad_token_provider", None),
                    token_endpoint=agent_definition.get("token_endpoint", None),
                    default_headers=agent_definition.get("default_headers", None),
                    async_client=agent_definition.get("async_client", None),
                    env_file_path=agent_definition.get("env_file_path", None),
                    env_file_encoding=agent_definition.get("env_file_encoding", None),
                    instruction_role=agent_definition.get("instruction_role", None),
                )

            else:
                logging.info("Configuring Ollama Chat Completion")
                self.chat_completion = OllamaChatCompletion(
                    ai_model_id=agent_definition.get("deployment_name", "gpt-oss:20b"),
                    host=agent_definition.get("endpoint", "http://localhost:11434"), # Default to local Ollama Instance
                )
            logging.info(f"Chat completion service configured: {self.chat_completion.__class__.__name__}")
        except Exception as e:
            logging.error(f"Failed to setup chat completion: {e}")


# Run the main function
if __name__ == "__main__":
    resp = asyncio.run(Agent())
