"""
Module for managing the conversation flow in Morix.

This module handles initialization of messages, user interaction, and conversation logic
with calls to the chat completion model.
"""

import os
import logging
import json
from rich.markdown import Markdown
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from colorama import init
from .run_functions import process_tool_calls
from .scan import scan, get_project_structure
from .keys import bindings
from .helpers import get_string_size_kb, style, tokens_from_messages, console_print
from .settings import config
from .complection import chat_completion_request
from prompt_toolkit.formatted_text import HTML

# Initialize colorama for Windows
init()

console = Console()
logger = logging.getLogger(__name__)
history = InMemoryHistory()


def initialize_messages(scan_result: str, initial_message: str = None) -> list:
    """
    Initializes conversation messages with system and user messages.
    Creates the initial list of messages including system prompt and scan result information.

    Args:
        scan_result (str): The result from scanning the project.
        initial_message (str, optional): An optional initial user message.

    Returns:
        list: A list of message dictionaries for the conversation.
    """
    messages = []
    if config.role_system_content:
        messages.append({"role": "system", "content": config.role_system_content})
        if logger.getEffectiveLevel() == logging.DEBUG:
            console.print(f"[green][bold]SYSTEM MESSAGE[/bold]\n-------------\n{config.role_system_content}[/green]")
    if scan_result:
        messages.append({"role": "system", "content": f"Working on the project: {scan_result}."})
    if initial_message:
        messages.append({"role": "user", "content": initial_message})
    return messages


def handle_user_interaction(messages: list) -> str:
    """
    Handles user interaction by prompting for input and appending it to messages.
    Uses prompt_toolkit to gather user input and add it to the conversation history.

    Args:
        messages (list): The list of current conversation messages.

    Returns:
        str: The user's input string.
    """
    tokens = tokens_from_messages(messages)
    user_prompt = prompt(
        [('class:prompt', 'User: ')],
        multiline=True,
        key_bindings=bindings,
        style=style,
        rprompt=HTML('<rprompt>{} tokens</rprompt>').format(tokens),
        history=history
    )
    messages.append({"role": "user", "content": user_prompt})
    history.append_string(user_prompt)
    return user_prompt


def conversation(work_folder: str, full_scan: bool = False, structure_only: bool = False, initial_message: str = None, is_interactive: bool = True) -> None:
    """
    Manages the conversation flow with user interaction and chat completions.
    Conducts the conversation by scanning the project, initializing messages, and processing user and assistant messages.

    Args:
        work_folder (str): Path to the working directory.
        full_scan (bool, optional): If true, scans file contents.
        structure_only (bool, optional): If true, scans directory structure only.
        initial_message (str, optional): An optional initial user message.
        is_interactive (bool, optional): Flag to enable interactive mode.
    """
    try:
        scan_result = None
        if structure_only:
            scan_result = get_project_structure(work_folder)
        elif full_scan:
            scan_result = scan(work_folder)
            logger.debug(f"Scanning completed. Size in kilobytes: {get_string_size_kb(scan_result):.2f} KB.")
        project_abspath = os.path.abspath(work_folder)
        messages = initialize_messages(scan_result, initial_message)
        is_skip_user_question = bool(initial_message)

        while True:
            if not is_skip_user_question and is_interactive:
                handle_user_interaction(messages)
            assistant_message = chat_completion_request(messages, config.functions)
            if not assistant_message:
                is_skip_user_question = False
                continue
            messages.append(assistant_message)
            finish_reason = assistant_message.response_metadata['finish_reason']

            console_print(f"[red][bold]GPT[/bold][/red] Finish reason: {finish_reason}", f"{assistant_message.response_metadata['token_usage']['total_tokens']} tokens")
            thoughts, response, tool_args = content_parse(assistant_message.content)
            if assistant_message.content and is_interactive:
                if thoughts: console.print(thoughts)
                console.print(Markdown(response))
                if tool_args: console.print(tool_args)
            if finish_reason == 'length':
                is_skip_user_question = True
            elif finish_reason == 'tool_calls':
                is_skip_user_question = process_tool_calls(messages, assistant_message, project_abspath)
            else:
                is_skip_user_question = False
                if not is_interactive:
                    return assistant_message
    except KeyboardInterrupt:
        logger.info("Finished")
    finally:
        logger.info("Session completed")


def content_parse(content):
    """
    Parses content from assistant message as JSON if possible.
    Attempts to parse the given content string into a dictionary and extract thoughts, response, and tool_args.

    Args:
        content (str): The content string from the assistant message.

    Returns:
        tuple: (thoughts, response, tool_args) extracted from the content. If parsing fails, returns (None, content, None).
    """
    try:
        j_response = json.loads(content)
        return j_response.get('thoughts'), j_response.get('response'), j_response.get('tool_args')
    except:
        return None, content, None
