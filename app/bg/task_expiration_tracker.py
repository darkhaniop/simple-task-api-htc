"""
The TaskExpirationTracker extension

Periodically checks and updates task states.
"""

import logging
import threading
import time
from typing import Optional

from ..common import db_ops


class TaskExpirationTracker(threading.Thread):
    """TaskExpirationTracker background thread extension"""

    stop_event: threading.Event
    logger: logging.Logger

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        super().__init__(daemon=False)
        self.stop_event = threading.Event()
        if logger is None:
            logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")
        self.logger = logger

    def init_app(self) -> None:
        """Initialize the app

        This method can be used to check if the database was initilized.
        """

    def stop(self) -> None:
        """Stop the TaskExpirationTracker thread"""
        self.stop_event.set()

    def count_tasks(self) -> int:
        """Count tasks in the DB"""

        return db_ops.get_task_count()

    def reset_expired_tasks(self) -> None:
        """Reset expired tasks"""

        db_ops.reset_expired_tasks()

    def run(self) -> None:
        self.logger.debug("thread starting")

        self.stop_event.clear()
        count_at = time.monotonic()
        while not self.stop_event.is_set():
            time.sleep(1)
            current_t = time.monotonic()
            if current_t > count_at:
                # self.count_tasks()
                self.reset_expired_tasks()
                count_at = time.monotonic() + 12

        self.logger.debug("thread exiting")
