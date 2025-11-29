from enum import Enum


class LeximErrorType(Enum):
    INVALID_CHAR = "Illegal character"
    MALFORMED_NUM = "Malformed number"
    UNCLOSED_COMMENT = "Open comment at EOF"
    STRAY_COMMENT = "Stray closing comment"
    INVALID_ID_START = "Invalid Identifier Start"


class LeximError:
    def __init__(self, line: int, lexeme: str, error_type: LeximErrorType):
        self.line = line
        self.lexeme = lexeme
        self.error_type = error_type
        self.message = error_type.value

    def __str__(self):
        return f"{self.line} ({self.lexeme}, {self.message})"
