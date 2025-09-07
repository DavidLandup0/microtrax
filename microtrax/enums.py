from enum import Enum


class ExperimentStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"

    def __str__(self):
        return self.value
