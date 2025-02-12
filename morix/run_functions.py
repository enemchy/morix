"""
Module for executing core functions in the Morix project.

This module defines the Functions class which provides various utility methods
for file operations, console command execution, task status reporting, and reading
the project directory structure.
"""

import logging
import os
from typing import Any
from . import plugin_loader
from .scan import get_project_structure
from .functions.file_operations import FileOperations
from .functions.execute_shell_command import ShellExecutor
from .functions.report_task_status import TaskStatusReporter

logger = logging.getLogger(__name__)

plugin_loader = plugin_loader.PluginLoader()
plugin_loader.load_plugins()

class Functions:
    def __init__(self, project_abspath: str):
        """
        Initializes the Functions class with necessary utilities.
        Sets up the absolute project path, file operations, shell executor, and task status reporter.

        Args:
            project_abspath (str): The absolute path to the project directory.
        """
        self.project_abspath = project_abspath
        self.file_ops = FileOperations(project_abspath)
        self.shell_exec = ShellExecutor(project_abspath)
        self.status = TaskStatusReporter()

    def crud_files(self, arguments: Any):
        """
        Manages CRUD operations on files.
        Performs create, read, update, or delete operations on files based on the provided arguments.

        Args:
            arguments (Any): A dictionary containing file operation details.

        Returns:
            str: Result message from the file operations.
        """
        return self.file_ops.manage_files_on_disk(arguments)

    def run_console_command(self, arguments: Any):
        """
        Executes a console command.
        Runs a shell command with a specified timeout and returns the output.

        Args:
            arguments (Any): A dictionary with 'command' and 'timeout' keys.

        Returns:
            str: Output from the executed command.
        """
        return self.shell_exec.execute_shell_command(arguments)

    def task_status(self, arguments: Any):
        """
        Reports the status of a task.
        Returns the current status of a task as provided in the arguments.

        Args:
            arguments (Any): A dictionary with a 'status' key indicating task status.

        Returns:
            str: The reported task status.
        """
        return self.status.report_task_status(arguments)

    def read_directory_structure(self, arguments: Any):
        """
        Reads the directory structure of the project.
        Retrieves a string representation of the project directory structure.

        Args:
            arguments (Any): A dictionary containing the key 'project' for the relative path to scan.

        Returns:
            str: The project directory structure.
        """
        scan_folder = os.path.join(self.project_abspath, arguments['project'])
        logger.info(f"Reading directory content {scan_folder}")
        return get_project_structure(scan_folder)

def process_tool_calls(messages, assistant_message: dict, project_abspath: str):
    """
    Processes tool calls issued by the assistant message.
    Executes functions specified in the assistant message's tool_calls field and appends the results
    to the messages list.

    Args:
        messages (list): The current list of conversation messages.
        assistant_message (dict): The assistant's message containing tool calls.
        project_abspath (str): The absolute path of the project directory.

    Returns:
        bool: A flag indicating whether to skip the user's next question.
    """
    if not assistant_message.tool_calls:
        return False

    skip_user_question = True
    functions = Functions(project_abspath)

    def message_append(id, name, content):
        messages.append({
            "tool_call_id": id,
            "role": "tool",
            "name": name,
            "content": content,
        })

    for tool in assistant_message.tool_calls:
        tool_name = tool['name']
        tool_args = tool['args']
        tool_id = tool['id']
        function = getattr(functions, tool_name, None)
        logger.info(f"Run function '{tool_name}'")
        if callable(function):
            content = function(tool_args)
            message_append(tool_id, tool_name, content)
            if tool_name == 'task_status' and tool_args['status'] == 'Completed':
                skip_user_question = False
                logger.info("Task completed")
        else:
            plugin_results = plugin_loader.execute_plugin_function(tool_name, tool_args)
            if not plugin_results:
                message_append(tool_id, tool_name, "Function does not return any results")
            else:
                for result in plugin_results:
                    message_append(tool_id, tool_name, result)

    return skip_user_question
