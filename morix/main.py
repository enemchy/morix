import argparse
import logging
import sys
import os
from .helpers import check_git_presence
from .conversation import conversation
from .settings import open_config_file, get_available_roles, read_role_promt, config
from .version import PROGRAM_NAME, PROGRAM_VERSION

# Add the root directory to PYTHONPATH if it's not there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description="Scanning the folder and sending to GPT")
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Path to working directory")
    parser.add_argument("-m", "--message", help="Message to send as initial user input")
    parser.add_argument("-r", "--role", help="Role for system prompt", choices=get_available_roles(), default="developer")
    parser.add_argument("--llm", help="Choose LLM to use", choices=(list(config.llm.keys()) if isinstance(config.llm, dict) else ['openai']), default="openai")
    parser.add_argument("-c", "--contents", action="store_true", help="Scan directory structure and files content")
    parser.add_argument("-s", "--structure-only", action="store_true", help="Scan directory structure")
    parser.add_argument("--config", action="store_true", help="Open configuration file")
    parser.add_argument("-e", "--wait-enter", action="store", help="Enable waiting for Enter key before executing console command")
    parser.add_argument("-vvv", "--verbose", action="store_true", help="Enable verbose/debug mode")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {PROGRAM_VERSION}")
    return parser.parse_args()


def handle_command(args: argparse.Namespace):
    """
    Handles the command based on parsed arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug(f"Using configs in: {config.path}")

    if args.config:
        open_config_file()
    else:
        if type(config.llm) == dict:
            config.llm = config.llm[args.llm]
            config.llm.token = os.getenv(config.llm.token)

        work_folder = args.path

        _text = ""
        full_scan, structure_only = False, False
        if args.structure_only:
            structure_only = True
            _text = "with scan structure only"
        elif args.contents:
            full_scan = True
            _text = "with full scan"

        logger.info(f"Starting work on the project at: {os.path.abspath(work_folder)} {_text}")

        if not os.path.isdir(work_folder):
            logger.error(f"Error: Path '{work_folder}' is not a directory.")
            raise SystemExit(1)

        if not check_git_presence(work_folder):
            logger.warning("No .git directory found in the working directory")

        if args.wait_enter:
            config.console_commands.wait_enter_before_run = args.wait_enter

        if not config.console_commands.wait_enter_before_run:
            logger.warning("Выполнение консольных скриптов не будет ожидать нажатия кнопки Enter")
        config.role_system_content = read_role_promt(args.role)
        conversation(work_folder, full_scan, structure_only, args.message)


def main() -> None:
    args = parse_args()
    handle_command(args)


if __name__ == '__main__':
    main()
