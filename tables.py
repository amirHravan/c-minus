import logging

from consts import KEYWORDS
from error import LeximError, LeximErrorType
from tokens import Token, TokenType

logger = logging.getLogger(__name__)


class SymbolTable:
    def __init__(self) -> None:
        self.symbols = []
        for keyword in KEYWORDS:
            self.symbols.append(keyword)

    def add_symbol(self, symbol: str) -> None:
        if symbol not in self.symbols:
            self.symbols.append(symbol)

    def __contains__(self, symbol: str) -> bool:
        return symbol in self.symbols

    def __str__(self) -> str:
        return "\n".join(self.symbols)

    def get_symbols(self) -> list[str]:
        return self.symbols

    def export_to_file(self, filename: str) -> bool:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                index = 1
                keywords = sorted([s for s in self.symbols if s in KEYWORDS])
                ids = sorted([s for s in self.symbols if s not in KEYWORDS], key=str.lower)
                for symbol in keywords + ids:
                    f.write(f"{index}.\t{symbol}\n")
                    index += 1
            return True
        except Exception as e:
            logger.error(f"Error exporting symbol table to file: {e}")
            return False


class TokenTable:
    def __init__(self) -> None:
        self.tokens = {}

    def add_token(self, token: Token) -> None:
        if token.line_number not in self.tokens:
            self.tokens[token.line_number] = []
        self.tokens[token.line_number].append(
            f"({token.token_type.value}, {token.token_string})"
        )

        # Add to symbol table if ID
        if token.token_type == TokenType.ID:
            if token.token_string not in symbol_table:
                symbol_table.add_symbol(token.token_string)

    def export_to_file(self, filename: str) -> bool:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                for lineno in sorted(self.tokens.keys()):
                    line_tokens = " ".join(self.tokens.get(lineno, []))
                    f.write(f"{lineno}.\t{line_tokens} \n")
            return True
        except Exception as e:
            logger.error(f"Error exporting token table to file: {e}")
            return False


class ErrorTable:
    def __init__(self) -> None:
        self.errors = []

    def add_error(self, error: LeximError) -> None:
        # Truncate unclosed comment error specifically
        # T07 test expects 9 characters before "..."
        if error.error_type == LeximErrorType.UNCLOSED_COMMENT:
            if len(error.lexeme) > 9:
                lexeme = error.lexeme[:9] + "..."
            else:
                lexeme = error.lexeme
        else:
            lexeme = error.lexeme
        self.errors.append(f"{error.line}.\t({lexeme}, {error.message})")

    def is_empty(self) -> bool:
        return len(self.errors) == 0

    def get_errors(self) -> list[str]:
        return self.errors

    def export_to_file(self, filename: str) -> bool:
        try:
            # 2. Write lexical_errors.txt
            with open(filename, "w", encoding="utf-8") as f:
                if error_table.is_empty():
                    f.write("No lexical errors found.\n")
                else:
                    for error in self.errors:
                        f.write(f"{error}\n")
            return True
        except Exception as e:
            logger.error(f"Error exporting error table to file: {e}")
            return False


symbol_table = SymbolTable()
token_table = TokenTable()
error_table = ErrorTable()
