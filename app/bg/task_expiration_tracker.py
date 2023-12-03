import threading
import time

from ..common import db_ops


class TaskExpirationTracker(threading.Thread):
    stop_event: threading.Event

    def __init__(self) -> None:
        super().__init__(daemon=False)
        self.stop_event = threading.Event()

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
        self.stop_event.clear()
        count_at = time.monotonic()
        while not self.stop_event.is_set():
            time.sleep(1)
            current_t = time.monotonic()
            if current_t > count_at:
                # self.count_tasks()
                self.reset_expired_tasks()
                count_at = time.monotonic() + 12
