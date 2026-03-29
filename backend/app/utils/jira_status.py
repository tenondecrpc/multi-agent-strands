from enum import StrEnum


class JiraStatus(StrEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
