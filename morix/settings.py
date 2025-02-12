"""
Module for application configuration in the Morix project.

This module loads and processes configuration files, sets up paths, and provides utility functions
for configuration management.
"""

import os
import re
import shutil
import logging
import typer
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from .version import PROGRAM_NAME
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIG_LOCAL_DIR = '../configs'
CONFIG_HOME_DIR = '.config'
CONFIG_YAML = 'config.yml'
CONFIG_FUNCTIONS = 'functions/functions.yml'
CONFIG_IGNORE_FILE = '.gptignore'


class ScanConfig(BaseModel):
    ignore_pattern_files: List[str]
    text_extensions: List[str]


class ConsoleCommandsConfig(BaseModel):
    max_output_lines: int
    allow_run: bool
    wait_enter_before_run: bool


class LLMProviderConfig(BaseModel):
    name: str
    base_url: str
    token: str


class Config(BaseModel):
    path: str = Field(default_factory=lambda: str(get_config_folder()))
    llm: Dict[str, LLMProviderConfig]
    scan: ScanConfig
    console_commands: ConsoleCommandsConfig
    is_develop_mode: bool = Field(default_factory=lambda: str(is_development_mode()))
    plugins_path: str = Field(default_factory=lambda: str(get_config_folder() / "plugins"))
    functions: List[Any] = Field(default_factory=lambda: load_functions(get_config_folder()))
    role_system_content: Optional[str] = None


def get_config_folder() -> Path:
    """
    Returns the configuration folder path based on the development mode.
    Determines if the project is in development mode and returns the appropriate configuration directory.

    Returns:
        Path: The path to the configuration directory.
    """
    if is_development_mode():
        return Path(__file__).parent / CONFIG_LOCAL_DIR
    return Path.home() / CONFIG_HOME_DIR / PROGRAM_NAME


def load_yaml_file(file_path: Path) -> Any:
    """
    Loads a YAML file from the given path.
    Reads and parses a YAML file, returning its contents as a Python object.

    Args:
        file_path (Path): The path to the YAML file.

    Returns:
        Any: Parsed content of the YAML file.

    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: For errors during YAML parsing.
    """
    if not file_path.exists():
        logger.error(f"File not found at path: {file_path}")
        raise FileNotFoundError(f"File not found at path: {file_path}")
    try:
        return yaml.safe_load(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}", exc_info=True)
        raise


def load_functions(config_dir: Path) -> List[Any]:
    """
    Loads function definitions from YAML files.
    Reads function configuration from the main functions YAML and any additional plugin YAML files,
    and returns a combined list of function definitions.

    Args:
        config_dir (Path): The configuration directory path.

    Returns:
        List[Any]: A list of function definitions.
    """
    functions = []
    functions_files = [Path(__file__).parent / CONFIG_FUNCTIONS]
    plugins_folder = config_dir / 'plugins'
    if plugins_folder.exists():
        for file in plugins_folder.iterdir():
            if file.suffix == '.yml':
                functions_files.append(file)
    for function_file in functions_files:
        functions_data = load_yaml_file(function_file)
        if functions_data:
            functions.extend(functions_data)
    return functions


def load_config() -> Config:
    """
    Loads the configuration from the YAML file.
    Copies default configuration if necessary and loads configuration details from the config.yml file.

    Returns:
        Config: The application configuration object.

    Raises:
        FileNotFoundError: If the configuration file is not found.
    """
    copy_config_if_not_exist()
    config_dir = get_config_folder()
    config_path = config_dir / CONFIG_YAML
    if not config_path.exists():
        logger.error(f"File not found at path: {config_path}")
        raise FileNotFoundError(f"File not found at path: {config_path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        if 'llm' in data:
            data['llm'] = {key: LLMProviderConfig(**value) for key, value in data['llm'].items()}
        return Config(**data)
    except Exception as e:
        logger.error(f"Error loading {config_path}: {e}", exc_info=True)
        raise


def open_config_file() -> None:
    """
    Opens the configuration file in the system editor.
    If the configuration file exists, opens it using the default system command for editing.
    Otherwise, logs an error and exits.

    Raises:
        typer.Exit: To terminate the program after attempting to open the config file.
    """
    config_path = get_config_folder() / CONFIG_YAML
    if config_path.exists():
        if os.name == 'posix':
            os.system(f'open "{config_path}"')
        else:
            os.system(f'start "" "{config_path}"')
    else:
        logger.error("Configuration file not found.")
    raise typer.Exit()


def is_development_mode() -> bool:
    """
    Determines if the application is running in development mode.
    Checks the parent directory for setup.py to decide if the project is in development mode.

    Returns:
        bool: True if in development mode, False otherwise.
    """
    parent_dir = Path(__file__).parent.parent.resolve()
    dev_mode = (parent_dir / 'setup.py').is_file()
    if dev_mode:
        logger.debug("Running in development mode")
    return dev_mode


def copy_config_if_not_exist() -> None:
    """
    Copies default configuration files to the home directory if they do not exist.
    Checks if configuration files exist in the home config directory, and if not, copies them from the templates.
    """
    if is_development_mode():
        return

    home_config_dir = Path.home() / CONFIG_HOME_DIR / PROGRAM_NAME
    templates_dir = Path(__file__).parent / CONFIG_LOCAL_DIR

    for template_file in templates_dir.rglob('*'):
        if template_file.is_file():
            rel_path = template_file.relative_to(templates_dir)
            target_path = home_config_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if not target_path.exists():
                shutil.copy(template_file, target_path)
    logger.info(f"Configuration copied to {home_config_dir}")


def read_role_promt(role) -> str:
    """
    Reads the role prompt from a markdown file.
    Opens the markdown file corresponding to the given role and returns its content.

    Args:
        role: The role identifier (e.g., 'developer').

    Returns:
        str: The content of the role prompt file.
    """
    if role is None:
        return None
    promt_path = get_config_folder() / f'promts/role.{role}.md'
    with promt_path.open('r', encoding='utf-8') as file:
        return file.read()


def get_available_roles() -> List:
    """
    Retrieves a list of available roles based on prompt files.
    Scans the 'promts' directory for files that match the role pattern and returns a list of role names.

    Returns:
        List: A list of role names.
    """
    pattern = re.compile(r'^role\.(.+?)\.md$')
    roles = [None]
    promt_path = get_config_folder() / f'promts'
    for filename in os.listdir(promt_path):
        match = pattern.match(filename)
        if match:
            roles.append(match.group(1))
    return roles



config = load_config()
