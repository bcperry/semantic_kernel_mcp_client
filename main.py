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



async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add Azure OpenAI chat completion
    chat_completion = OllamaChatCompletion(
        ai_model_id="gpt-oss:20b",
        host="http://ollama.home",
    )
    kernel.add_service(chat_completion)

    loglevel = logging.DEBUG  # Set the desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    # Set up logging to see detailed information
    setup_logging()
    
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

    
    ff_server = MCPStreamableHttpPlugin(
        name="ff_tools",
        url="http://192.168.86.103:8000/mcp",
    )
    await ff_server.connect()
    kernel.add_plugin(ff_server)

    
    sql_server = MCPSsePlugin(
        name="sql_tools",
        url="https://sql-mcp-demo.azurewebsites.us/sse",
    )
    await sql_server.connect()
    kernel.add_plugin(sql_server)


    print("✅ MCP plugins added to kernel")

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create a history of the conversation
    history = ChatHistory()

    history.add_system_message("Answer like a pirate")


    print("🤖 Assistant ready! You can ask me to use any of the MCP tools listed above.")
    print("💡 Example: 'Can you help me with fantasy football data?'")
    print("Type 'exit' to quit.\n")

    # Initiate a back-and-forth chat
    userInput = None
    while True:
        # Collect user input
        userInput = input("User > ")

        # Terminate the loop if the user says "exit"
        if userInput == "exit":
            break

        # Add user input to the history
        history.add_user_message(userInput)

        # Accumulate content so we can add a single message to history at the end
        full_response = {
            "thoughts": [],
            "tool_calls": [],
            "messages": [],
            "raw_chunks": [],
        }

        thread = None

        try:
            response = chat_completion.get_streaming_chat_message_content(
                messages=userInput,
                thread=thread,
                chat_history=history,
                settings=execution_settings,
                kernel=kernel,
            )

            thoughts = False
            tools = False
            message = False

            async for chunk in response:

                # thoughts
                if chunk.inner_content is not None and chunk.inner_content.get('message') is not None and chunk.inner_content['message'].thinking is not None:
                    if thoughts == False:
                        thoughts = True
                        tools = False
                        message = False
                        print("\n--- Agent Thoughts ---")
                    thinking = chunk.inner_content['message'].thinking
                    # preserve print behavior
                    print(thinking, end="")
                    # accumulate
                    try:
                        full_response['thoughts'].append(str(thinking))
                    except Exception:
                        full_response['thoughts'].append(repr(thinking))
                # tools
                elif chunk.inner_content is not None and chunk.inner_content.get('message') is not None and chunk.inner_content['message'].tool_calls is not None:
                    if tools == False:
                        tools = True
                        message = False
                        thoughts = False
                        print("\n--- Agent Tools ---")
                    tool_calls = chunk.inner_content['message'].tool_calls
                    for tool in tool_calls:
                        print(f"Tool: {tool.function.name}")
                        print(f"Arguments: {tool.function.arguments}")
                        # accumulate
                        try:
                            full_response['tool_calls'].append({tool.function.name: tool.function.arguments})
                        except Exception:
                            full_response['tool_calls'].append({"generic": str(tool_calls)})
                # messages
                else:
                    if message == False:
                        message = True
                        thoughts = False
                        tools = False
                        print("\n--- Agent Message ---")
                    print(chunk, end="")
                    # accumulate a best-effort message representation
                    try:
                        if chunk.inner_content is not None:
                            full_response['messages'].append(str(chunk.inner_content))
                        else:
                            full_response['messages'].append(str(chunk))
                    except Exception:
                        full_response['messages'].append(repr(chunk))
                    # keep raw chunk text too
                    try:
                        full_response['raw_chunks'].append(str(chunk))
                    except Exception:
                        full_response['raw_chunks'].append(repr(chunk))

            print()
            # Newline after stream finishes
            print()

            # Reconstruct a single assistant message from the accumulated pieces
            assistant_parts = []
            if full_response.get('thoughts'):
                assistant_parts.append("\n".join(full_response['thoughts']))
            if full_response.get('messages'):
                assistant_parts.append("\n".join(full_response['messages']))
            if full_response.get('tool_calls'):
                # represent tool calls as a stringified list/dict
                assistant_parts.append(str(full_response['tool_calls']))

            assistant_text = "\n\n".join([p for p in assistant_parts if p]).strip()
            if assistant_text:
                # Try to add as an assistant message; fall back to system message if method isn't available
                try:
                    history.add_assistant_message(assistant_text)
                except Exception:
                    history.add_system_message(assistant_text)

        except Exception as e:
            # Best-effort cleanup; ignore errors
            logging.exception(f"The chat message processing failed. {e}")
    await ff_server.close()
    await sql_server.close()
    return full_response


# Run the main function
if __name__ == "__main__":
    resp = asyncio.run(main())
    print(json.dumps(resp, indent=2, ensure_ascii=False))