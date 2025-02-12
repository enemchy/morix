"""
Module for performing file operations in the Morix project.

This module defines the FileOperations class which handles create, read, update, and delete operations on files
within the project directory.
"""

import logging
import os
from typing import Any
from ..helpers import read_file_content

logger = logging.getLogger(__name__)

class FileOperations:
    def __init__(self, project_abspath: str):
        """
        Initializes the FileOperations instance.
        Sets the base absolute path of the project for file operations.

        Args:
            project_abspath (str): The absolute path to the project directory.
        """
        self.project_abspath = project_abspath

    def manage_files_on_disk(self, arguments: Any):
        """
        Performs file operations (create, read, update, delete) based on provided arguments.
        Iterates over the provided file operations and executes them, returning a summary message.

        Args:
            arguments (Any): A dictionary containing a 'files' key with a list of file operation dictionaries.

        Returns:
            str: A summary of the file operations performed.
        """
        result = []
        operations = {
            'create': ('created', 'w'),
            'read': ('read', None),
            'update': ('updated', 'w'),
            'delete': ('deleted', None)
        }
        
        for file in arguments['files']:
            filename = file['filename']
            file_path = os.path.join(self.project_abspath, filename)
            content = file.get('content', '')
            operation = file['operation']

            if operation in operations:
                action, mode = operations[operation]

                if operation == 'create':
                    self._create_file(file_path, content)
                    action = 'directory created' if content == '' else action

                if operation == 'delete':
                    action = self._delete_file(file_path)

                if mode and content != '' and operation in ['create', 'update']:
                    self._write_to_file(file_path, content, mode)

                if operation == 'read':
                    content = self._read_file(file_path)
                    result.append(f"{filename}: {content}")
                else:
                    result.append(f"{filename}: {action}")

                logger.info(f"{filename}: {action}")
        return "\n".join(result)

    def _create_file(self, file_path, content):
        """
        Creates a new file or directory at the specified path.
        If content is empty, creates a directory; otherwise, ensures the directory exists for a file creation.

        Args:
            file_path (str): The target file or directory path.
            content (str): The content to write if creating a file.
        """
        if content == '':
            os.makedirs(file_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def _delete_file(self, file_path):
        """
        Deletes a file or directory at the specified path.
        Removes the file if it exists; if it's a directory, removes the directory.

        Args:
            file_path (str): The path to the file or directory to delete.

        Returns:
            str: 'deleted' if deletion was successful, or 'does not exist' if the file was not found.
        """
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)
            return 'deleted'
        return 'does not exist'

    def _write_to_file(self, file_path, content, mode):
        """
        Writes content to a file using the specified mode.
        Opens the file in the given mode and writes the provided content.

        Args:
            file_path (str): The path to the file.
            content (str): The content to write to the file.
            mode (str): The file open mode (e.g., 'w').
        """
        if not os.path.isdir(file_path):
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
        else:
            logger.error(f"{file_path} is a directory, cannot open it as a file.")

    def _read_file(self, file_path):
        """
        Reads and returns the content of a file.
        Reads the file at the specified path if it is not a directory.

        Args:
            file_path (str): The path to the file to read.

        Returns:
            str: The content of the file, or an empty string if the file is a directory.
        """
        if not os.path.isdir(file_path):
            return read_file_content(file_path)
        logger.error(f"{file_path} is a directory, cannot read it as a file.")
        return ""
