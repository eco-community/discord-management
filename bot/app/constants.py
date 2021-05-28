from enum import Enum


class EngagementScoreChoices(int, Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class TaskTypesChoices(str, Enum):
    KICK = "KICK"  # Kick members
    BAN = "BAN"  # Ban members
    ASSIGN_ROLE = "ASSIGN_ROLE"  # Assign role to members
    REMOVE_ROLE = "REMOVE_ROLE"  # Remove role from members


class TaskStatusChoices(str, Enum):
    IN_QUEUE = "IN_QUEUE"  # Task in queue
    STARTED = "STARTED"  # Task started
    FINISHED = "FINISHED"  # Task finished
    FAILED = "FAILED"  # Task failed


SETTINGS_SINGLETON_ID = 1
EVERYONE_ROLE = "@everyone"
