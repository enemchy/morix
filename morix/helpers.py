"""
Module providing helper functions for the Morix project.

This module includes utility functions for terminal operations, token counting, file reading,
spinner animation, and other common tasks.
"""

import os
from pathlib import Path
import re
import subprocess
import threading
import time
import tiktoken
from typing import Any, Dict, List
from venv import logger
from prompt_toolkit.styles import Style
from .settings import config
from rich.console import Console
from rich.table import Table

style = Style.from_dict({
    'prompt': 'ansiblue bold',
    'rprompt': '#bcbcbc',
})

console = Console()

class DotSpinner:
    def __init__(self):
        """
        Initializes the DotSpinner for displaying a loading animation in the terminal.
        Sets up the spinner with a background thread to print dots periodically until stopped.
        """
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run)
        reset_terminal()

    def _run(self):
        """
        Runs the spinner animation in a separate thread.
        Continuously prints dots to the terminal until the stop event is set.
        """
        dot_count = 0
        while not self.stop_event.is_set():
            print('.', end='', flush=True)
            dot_count += 1
            if dot_count >= 15:
                print('\r', end='', flush=True)
                dot_count = 0
            time.sleep(1)

    def start(self):
        """
        Starts the spinner animation.
        Begins the background thread to display the spinner if it is not already running.
        """
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        """
        Stops the spinner animation.
        Signals the spinner thread to stop and waits for it to terminate.
        """
        print('\r', end='', flush=True)
        self.stop_event.set()
        self.thread.join(timeout=1)

def reset_terminal():
    """
    Resets the terminal to its default settings.
    Executes the 'stty sane' command to restore terminal settings.
    """
    subprocess.run(['stty', 'sane'])


def get_string_size_kb(string: str) -> float:
    """
    Calculates the size of a string in kilobytes.
    Returns the size of the provided string measured in kilobytes.

    Args:
        string (str): The input string to measure.

    Returns:
        float: The size of the string in kilobytes.
    """
    size_bytes = len(string.encode('utf-8'))
    size_kb = size_bytes / 1024
    return size_kb


def save_response_to_file(response: str, temp_dir: str) -> str:
    """
    Saves a response string to a file within the specified directory.
    Writes the provided response text to a file named 'response_{n}.md' in the given directory
    and returns the file path.

    Args:
        response (str): The response text to save.
        temp_dir (str): The directory where the response file should be saved.

    Returns:
        str: The path to the saved response file.
    """
    count = len(os.listdir(temp_dir)) + 1
    file_path = os.path.join(temp_dir, f"response_{count}.md")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(response)
        logger.info(f"Response saved in {temp_dir}")
    except IOError as e:
        logger.error(f"Error saving response to file: {file_path}: {e}", exc_info=True)
    return file_path


def read_file_content(file_path: str) -> str:
    """
    Reads the content of a file and returns it as a string.
    Opens the specified file in text mode and returns its content. Returns an empty string if reading fails.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file, or an empty string if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}", exc_info=True)
        return ""


def get_encoding_for_model(model: str):
    """
    Retrieves the token encoding for the specified model.
    Returns the appropriate encoding object for a given model name. Defaults to 'cl100k_base' if not found.

    Args:
        model (str): The model name.

    Returns:
        Encoding: The encoding object for the model.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return encoding


def tokens_from_messages(messages: List[Dict[str, Any]]):
    """
    Calculates total number of tokens in a list of messages.
    Iterates through each message and sums the token counts computed by tokens_from_message.

    Args:
        messages (List[Dict[str, Any]]): A list of message dictionaries.

    Returns:
        int: Total number of tokens across all messages.
    """
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_from_message(message)
    return num_tokens


def tokens_from_message(message):
    """
    Calculates the number of tokens in a single message.
    Uses the appropriate token encoding for the model to count tokens in the message content.

    Args:
        message: A message which can be a dictionary or a string.

    Returns:
        int: The number of tokens in the message.
    """
    encoding = get_encoding_for_model(config.llm.name)

    def encode_value(value):
        try:
            return len(encoding.encode(str(value), disallowed_special=()))
        except Exception as e:
            logger.error(f"Error encoding value: {value}, Exception: {e}")
            return 0

    if isinstance(message, dict):
        num_tokens = sum(encode_value(value) for value in message.values() if isinstance(value, str))
    else:
        num_tokens = encode_value(message)
    return num_tokens


def check_git_presence(work_folder: str) -> bool:
    """
    Checks if a .git directory exists in the given folder.
    Returns True if a .git directory is found in the specified working folder, otherwise False.

    Args:
        work_folder (str): The folder to check for a .git directory.

    Returns:
        bool: True if .git exists, False otherwise.
    """
    if not os.path.exists(os.path.join(work_folder, ".git")):
        return False
    return True


def console_print(left, right=''):
    """
    Prints a formatted message to the console using a table layout.
    Displays two pieces of text (left and right aligned) in a table for clear visualization in the console.

    Args:
        left: Text to display on the left side.
        right: Text to display on the right side (optional).
    """
    table = Table(show_header=False, show_edge=False, padding=0, expand=True, box=None)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row(f"{left}", f"[#bcbcbc]{right}[/#bcbcbc]")
    console.print(table)