from enum import Enum


class TokenType(Enum):
    NUMBER = "NUM"
    ID = "ID"
    KEYWORD = "KEYWORD"
    SYMBOL = "SYMBOL"
    EOF = "EOF"


class Token:
    def __init__(self, line_number: int, token_type: TokenType, token_string: str):
        self.line_number = line_number
        self.token_type = token_type
        self.token_string = token_string

    def __str__(self):
        return f"({self.token_type}, {self.token_string})"
