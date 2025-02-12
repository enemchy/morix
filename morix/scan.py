"""
Module for scanning project directories in the Morix project.

This module provides functions to retrieve ignore patterns, determine whether files should be ignored,
read file contents, and generate a scan or project structure overview.
"""

import os
import fnmatch
import logging
from pathlib import Path
from typing import List
from .settings import config, CONFIG_LOCAL_DIR, CONFIG_IGNORE_FILE
from .helpers import read_file_content

logger = logging.getLogger(__name__)

def get_ignore_patterns_paths(scan_folder: str) -> List[str]:
    """
    Returns the paths to files containing ignore patterns.
    Given a scan folder, returns a list of file paths that contain patterns for ignoring files during scanning.

    Args:
        scan_folder (str): The folder to search for ignore pattern files.

    Returns:
        List[str]: A list of file paths with ignore patterns.
    """
    ignore_pattern_files = config.scan.ignore_pattern_files
    ignore_files_paths = []

    for file in ignore_pattern_files:
        expanded_path = os.path.expanduser(file)
        root_path = os.path.join(scan_folder, file)

        if os.path.exists(root_path):
            ignore_files_paths.append(root_path)
        elif os.path.exists(expanded_path):
            ignore_files_paths.append(expanded_path)

    if config.is_develop_mode:
        dev_ignore_path = os.path.join(os.path.dirname(__file__), CONFIG_LOCAL_DIR, CONFIG_IGNORE_FILE)
        ignore_files_paths.append(dev_ignore_path)

    return ignore_files_paths


def read_ignore_file(ignore_files_paths: List[str]) -> List[str]:
    """
    Reads ignore pattern files to extract patterns.
    Opens each file in the list of ignore pattern file paths and reads the newline-separated patterns.

    Args:
        ignore_files_paths (List[str]): List of file paths containing ignore patterns.

    Returns:
        List[str]: A list of ignore patterns.
    """
    ignore_patterns = []
    for path in ignore_files_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                    ignore_patterns.extend(file.read().splitlines())
            except IOError as e:
                logger.error(f"Failed to read file {path}: {e}", exc_info=True)
        else:
            logger.error(f"File {path} does not exist")

    return ignore_patterns


def should_ignore(path: str, patterns: List[str]) -> bool:
    """
    Determines if a file should be ignored based on provided patterns.
    Checks if the given file path matches any of the ignore patterns using fnmatch.

    Args:
        path (str): The file or folder path to check.
        patterns (List[str]): A list of ignore patterns.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    from pathlib import Path
    path_obj = Path(path)
    check_obj = path_obj.parent.name or path_obj.name

    for pattern in patterns:
        if fnmatch.fnmatch(check_obj, pattern) or fnmatch.fnmatch(path_obj.name, pattern):
            return True

        if path_obj.is_relative_to(Path.cwd()):
            if any(fnmatch.fnmatch(check_obj, f"{pattern}*") for pattern in patterns):
                return True

    return False


def is_text_file(file_path: str) -> bool:
    """
    Checks if a file is a text file based on extension and content.
    Determines if the file is text by checking its extension and content for null bytes.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file is considered text, False otherwise.
    """
    _, ext = os.path.splitext(file_path)
    if ext in config.scan.text_extensions:
        return True

    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
            if b'\0' in chunk:
                return False
            try:
                chunk.decode('utf-8', errors='ignore')
                return True
            except (UnicodeDecodeError, IOError) as e:
                logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
                return False
    except IOError as e:
        logger.error(f"File cannot be opened: {file_path}: {e}", exc_info=True)
        return False


def get_text_files(root: str, ignore_patterns: List[str]) -> List[str]:
    """
    Retrieves all text files from the root directory that are not ignored.
    Walks through the directory tree starting from root and returns a list of relative paths for files
    that are text files and do not match any ignore patterns.

    Args:
        root (str): The root directory to scan.
        ignore_patterns (List[str]): A list of ignore patterns.

    Returns:
        List[str]: A list of relative file paths of text files.
    """
    text_files = []
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            new_dirnames = [d for d in dirnames if not should_ignore(os.path.relpath(os.path.join(dirpath, d), root), ignore_patterns)]
            for dirname in list(dirnames):
                if dirname not in new_dirnames:
                    dirnames.remove(dirname)
            for filename in filenames:
                relpath = os.path.relpath(os.path.join(dirpath, filename), root)
                full_path = os.path.join(root, relpath)
                if not should_ignore(relpath, ignore_patterns) and is_text_file(full_path):
                    text_files.append(relpath)
    except Exception as e:
        logger.error(f"Error during scanning: {e}", exc_info=True)
    return text_files


def scan(scan_folder: str) -> str:
    """
    Scans a folder and concatenates the content of all text files.
    Uses ignore patterns to filter files and returns a formatted string with file names and their contents.

    Args:
        scan_folder (str): The folder to scan for text files.

    Returns:
        str: A concatenated string of file names and their contents.
    """
    ignore_files_paths = get_ignore_patterns_paths(scan_folder)
    logger.debug(f"Files to search for ignore patterns: {ignore_files_paths}")
    ignore_patterns = read_ignore_file(ignore_files_paths)
    logger.debug(f"Ignore patterns: {ignore_patterns}")

    text_files = get_text_files(scan_folder, ignore_patterns)
    logger.debug(f"Files to scan: {text_files}")

    scan_result = "\n".join(
        f"{file}\n```\n{read_file_content(os.path.join(scan_folder, file))}\n```"
        for file in text_files
    )

    return scan_result


def get_project_structure(scan_folder: str) -> str:
    """
    Generates a string representation of the project structure.
    Walks through the directory tree of the given folder and returns a newline separated list
    of file paths that are not ignored.

    Args:
        scan_folder (str): The folder to scan for project structure.

    Returns:
        str: A string listing the project structure.
    """
    ignore_files_paths = get_ignore_patterns_paths(scan_folder)
    logger.debug(f"Files to search for ignore patterns: {ignore_files_paths}")
    ignore_patterns = read_ignore_file(ignore_files_paths)
    logger.debug(f"Ignore patterns: {ignore_patterns}")

    project_structure = []

    try:
        for dirpath, dirnames, filenames in os.walk(scan_folder):
            new_dirnames = [d for d in dirnames if not should_ignore(os.path.relpath(os.path.join(dirpath, d), scan_folder), ignore_patterns)]
            for dirname in list(dirnames):
                if dirname not in new_dirnames:
                    dirnames.remove(dirname)
            for filename in filenames:
                relpath = os.path.relpath(os.path.join(dirpath, filename), scan_folder)
                if not should_ignore(relpath, ignore_patterns):
                    project_structure.append(relpath)
    except Exception as e:
        logger.error(f"Error scanning structure: {e}", exc_info=True)

    return "\n".join(project_structure)
