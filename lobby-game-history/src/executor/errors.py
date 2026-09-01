from enum import Enum


class Errors(Enum):
    OK = 0
    TIMEOUT_EXCEEDED = 1
    PREVIOUS_REQUEST_FAILED = 2
