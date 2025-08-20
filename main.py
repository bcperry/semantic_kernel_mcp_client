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
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

import logging



async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add Azure OpenAI chat completion
    chat_completion = OllamaChatCompletion(
        ai_model_id="gpt-oss:20b",
        host="http://ollama.home",
    )
    kernel.add_service(chat_completion)

    loglevel = logging.ERROR

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

    
    ff_server =  MCPStreamableHttpPlugin(
        name="ff_tools",
        url="http://192.168.86.103:8000/mcp",
    )
    await ff_server.connect()  

    kernel.add_plugin(ff_server)
    print("✅ MCP plugin added to kernel")

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create a history of the conversation
    history = ChatHistory()

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

        # Try streaming responses if the client supports it; otherwise fall back
        thread = None

                # This callback function will be called for each intermediate message,
        # which will allow one to handle FunctionCallContent and FunctionResultContent.
        # If the callback is not provided, the agent will return the final response
        # with no intermediate tool call steps.
        async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
            print("\n--- Intermediate Step ---")
            print(message)
            for item in message.items or []:
                if isinstance(item, FunctionResultContent):
                    print(f"Function Result:> {item.result} for function: {item.name}")
                elif isinstance(item, FunctionCallContent):
                    print(f"Function Call:> {item.name} with arguments: {item.arguments}")
                else:
                    print(f"{item}")

        # Accumulate content so we can add a single message to history at the end
        full_response = ""

        # Enforce streaming-only mode: require invoke_stream on the client
        if not hasattr(chat_completion, "get_streaming_chat_message_contents"):
            raise RuntimeError(
                "The configured chat_completion client does not support streaming (invoke_stream).\n"
                "This script is running in streaming-only mode. Use a streaming-capable client."
            )

        thread = None

        try:
            response = chat_completion.get_streaming_chat_message_content(
                messages=userInput,
                thread=thread,
                on_intermediate_message=handle_streaming_intermediate_steps,
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
                    print(chunk.inner_content['message'].thinking, end="")

                # tools
                elif chunk.inner_content is not None and chunk.inner_content.get('message') is not None and chunk.inner_content['message'].tool_calls is not None:
                    if tools == False:
                        message = False
                        thoughts = False
                        print("\n--- Agent Tools ---")
                    print(chunk.inner_content['message'].tool_calls)
                # messages

                else:
                    if message == False:
                        message = True
                        thoughts = False
                        tools = False
                        print("\n--- Agent Message ---")
                    print(chunk, end="")

            print()
            # Newline after stream finishes
            print()

            if full_response:
                history.add_message(full_response)
        finally:
            # Clean up the thread on the remote service if provided
            if thread:
                try:
                    await thread.delete()
                except Exception:
                    # Best-effort cleanup; ignore errors
                    pass
    await ff_server.close()


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())