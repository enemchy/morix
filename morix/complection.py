"""
Module for chat completion using the OpenAI API in the Morix project.

This module defines the function chat_completion_request which sends messages to the chat model
and returns the AI's response.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages.ai import AIMessage
from .helpers import DotSpinner
from .settings import config

logger = logging.getLogger(__name__)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


def chat_completion_request(messages, functions=None) -> AIMessage:
    """
    Sends a chat completion request to the OpenAI model and returns the response.
    Constructs a ChatOpenAI instance and invokes it with the provided messages (and functions if given),
    while displaying a spinner during the API call.

    Args:
        messages (list): A list of conversation messages to send to the model.
        functions (optional): Additional functions (tools) to bind to the model.

    Returns:
        AIMessage: The response message from the AI model containing metadata and content.
    """
    spinner = DotSpinner()
    spinner.start()
    response = None
    try:
        model = ChatOpenAI(model=config.llm.name, base_url=config.llm.base_url, api_key=config.llm.token)
        response = model.invoke(messages) if not functions else model.bind_tools(functions).invoke(messages)

    except Exception as e:
        logger.critical(f"Error generating response from API: {e}")
        logger.debug("Stack trace:", exc_info=True)
        exit(1)
    except KeyboardInterrupt:
        return None
    finally:
        spinner.stop()

    logger.debug("Chat completion request successfully executed.")
    return response
