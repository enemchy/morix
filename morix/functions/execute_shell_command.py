"""
Module for executing shell commands in the Morix project.

This module defines the ShellExecutor class which runs shell commands with a timeout and captures their output.
"""

import subprocess
import logging
import os
import threading
import signal
from typing import Any

from morix.helpers import console_print
from ..settings import config

logger = logging.getLogger(__name__)

class ShellExecutor:
    def __init__(self, project_abspath: str):
        """
        Initializes the ShellExecutor with the project directory.
        Sets the base directory for executing shell commands.

        Args:
            project_abspath (str): The absolute path to the project directory.
        """
        self.project_abspath = project_abspath

    def execute_shell_command(self, arguments: Any):
        """
        Executes a shell command with a specified timeout.
        Runs the provided shell command in a subprocess, waits for output up to the timeout,
        and returns the captured output or error message if it times out or is interrupted.

        Args:
            arguments (Any): A dictionary containing 'command' (str) and 'timeout' (int).

        Returns:
            str: The output from the shell command, or an error message if execution fails.
        """
        command = arguments['command']
        timeout = arguments['timeout']

        if not config.console_commands.allow_run:
            content = "Execution of shell commands is not allowed based on the config settings."
            logger.warning(content)
            return content

        console_print(f"[red][bold]Exec:[/bold][/red] {command}", f"timeout {timeout}s")

        if config.console_commands.wait_enter_before_run:
            input("Press Enter to run...")

        def _read_output(process, output_list):
            try:
                for line in process.stdout:
                    print(line, end='')
                    output_list.append(line)
            except Exception as e:
                logger.error(f"Error reading process output: {e}")

        output = []
        err_content = None

        try:
            with subprocess.Popen(
                ['sh', '-c', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.project_abspath,
                preexec_fn=os.setsid
            ) as process:

                thread = threading.Thread(target=_read_output, args=(process, output))
                thread.daemon = True
                thread.start()

                try:
                    thread.join(timeout)
                except KeyboardInterrupt:
                    logger.info("Interrupt received, terminating process.")
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    thread.join()
                    raise
                finally:
                    if thread.is_alive():
                        process.kill()
                        thread.join()

        except subprocess.TimeoutExpired:
            err_content = "The command was interrupted due to timeout expiration."
            logger.error(err_content)
        except KeyboardInterrupt:
            err_content = "Process was interrupted by user."
            logger.error(err_content)
        finally:
            output = ''.join(output)
            logger.info(f"Command return code: {process.returncode}")
            max_lines = config.console_commands.max_output_lines
            stdout_lines = output.splitlines()[-max_lines:]
            content = "\n".join(stdout_lines)

            if err_content:
                return f"{content}\n{err_content}" if content else err_content
            return content or f"No shell command execution result received, exit code: {process.returncode}"
