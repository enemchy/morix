"""
Module for reporting task statuses in the Morix project.

This module defines the TaskStatusReporter class which provides a method to report the status of tasks.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class TaskStatusReporter:
    def report_task_status(self, arguments: Any):
        """
        Reports and returns the status of a given task.
        Reads the 'status' from the provided arguments and returns it after logging.

        Args:
            arguments (Any): A dictionary containing the task status under the key 'status'.

        Returns:
            str: The task status.
        """
        status = arguments['status']
        if status != 'Completed':
            logger.info(f"Task status {status}")
        return status
