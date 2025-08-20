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

    # Set up logging to see detailed information
    setup_logging()
    
    # Configure logging levels for different components
    logging.getLogger("semantic_kernel").setLevel(logging.DEBUG)
    logging.getLogger("semantic_kernel.kernel").setLevel(logging.DEBUG)
    logging.getLogger("semantic_kernel.connectors").setLevel(logging.DEBUG)
    
    # Set up a basic console handler if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.DEBUG,
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

        # Get the response from the AI
        result = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
        )

        # Print the results
        print("Assistant > " + str(result))

        # Add the message from the agent to the chat history
        history.add_message(result)
    await ff_server.close()


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())