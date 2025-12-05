from consts import KEYWORDS, SYMBOLS, WHITESPACE
from error import LeximError, LeximErrorType
from tables import error_table, token_table
from tokens import Token, TokenType


class Scanner:
    def __init__(self, input_text):
        self.text = input_text
        self.cursor = 0
        self.length = len(input_text)
        self.line_number = 1

    def _peek(self, offset: int = 0) -> str:
        if self.cursor + offset < self.length:
            return self.text[self.cursor + offset]
        return " "

    def _advance(self) -> str:
        if self.cursor < self.length:
            ch = self.text[self.cursor]
            if ch == "\n" or ch == "\f":
                self.line_number += 1
            self.cursor += 1
            return ch
        return " "

    def _is_eof(self) -> bool:
        return self.cursor >= self.length

    def _add_token(self, token_type: TokenType, token_lexim: str) -> None:
        token_table.add_token(Token(self.line_number, token_type, token_lexim))

    def _add_error(self, error: LeximError) -> None:
        error_table.add_error(error)

    def _is_symbol_start(self, char: str) -> bool:
        return char in {
            ";",
            ":",
            ",",
            "[",
            "]",
            "(",
            ")",
            "{",
            "}",
            "+",
            "-",
            "*",
            "/",
            "=",
            "<",
        }

    def _is_valid_id_char(self, char: str) -> bool:
        return char is not None and (char.isalnum() or char == "_")

    def _is_valid_id_start(self, char: str) -> bool:
        return char is not None and (char.isalpha() or char == "_")

    def get_next_token(self) -> bool:
        while not self._is_eof():
            char = self._peek()
            if char is None:
                break

            # 1. Skip Whitespace
            if char in WHITESPACE:
                self._advance()
                continue

            # 2. Numbers
            if char.isdigit():
                return self._handle_number()

            # 3. IDs and Keywords
            if self._is_valid_id_start(char):
                return self._handle_id()

            # 4. Comments and Symbols
            # Need to check for comments first because they start with symbol characters
            if char == "/":
                next_char = self._peek(1)
                if next_char == "*":
                    self._handle_block_comment()
                    continue  # After comment, look for next token
                elif next_char == "/":
                    self._handle_line_comment()
                    continue
                else:
                    return self._handle_symbol()

            if char == "*":
                next_char = self._peek(1)
                if next_char == "/":
                    self._add_error(
                        LeximError(self.line_number, "*/", LeximErrorType.STRAY_COMMENT)
                    )
                    self._advance()  # *
                    self._advance()  # /
                    continue  # Panic mode: skip and continue

            if self._is_symbol_start(char):
                return self._handle_symbol()

            # 5. Illegal Character
            # Invalid character that can't begin any token
            # Panic Mode: consume consecutive illegal characters
            lexeme = ""
            while (
                self._peek() is not None
                and self._peek() not in WHITESPACE
                and not self._peek().isalnum()
                and self._peek() != "_"
                and not self._is_symbol_start(self._peek())
            ):
                lexeme += self._advance()
            if not lexeme:  # Safety: consume at least one char
                lexeme = self._advance()
            self._add_error(
                LeximError(self.line_number, lexeme, LeximErrorType.INVALID_CHAR)
            )
            # Loop continues to find next token

        return False  # EOF

    def _handle_number(self) -> bool:
        _ = self.cursor
        lexeme = ""

        # Consume digits
        while self._peek() is not None and self._peek().isdigit():
            lexeme += self._advance()

        next_char = self._peek()
        
        # Check if followed by invalid character (not whitespace, not symbol, not EOF)
        if (next_char is not None 
            and next_char not in WHITESPACE 
            and not self._is_symbol_start(next_char)):
            # Panic Mode for Number: consume until delimiter (whitespace or symbol)
            while (self._peek() is not None 
                   and self._peek() not in WHITESPACE 
                   and not self._is_symbol_start(self._peek())):
                lexeme += self._advance()
            self._add_error(
                LeximError(self.line_number, lexeme, LeximErrorType.MALFORMED_NUM)
            )
            return True  # We processed input, even if error

        # Validate Number Format
        if len(lexeme) > 1 and lexeme.startswith("0"):
            self._add_error(
                LeximError(self.line_number, lexeme, LeximErrorType.MALFORMED_NUM)
            )
            return True

        self._add_token(TokenType.NUMBER, lexeme)
        return True

    def _handle_id(self) -> bool:
        lexeme = ""

        # Consume valid ID characters
        while self._is_valid_id_char(self._peek()):
            lexeme += self._advance()

        # Check if immediately followed by illegal characters
        # PANIC MODE: Continue until whitespace or symbol
        next_char = self._peek()
        if (
            next_char is not None
            and next_char not in WHITESPACE
            and not self._is_symbol_start(next_char)
            and not self._is_valid_id_char(next_char)
        ):
            # Panic Mode: consume until delimiter (whitespace or symbol)
            while (
                self._peek() is not None
                and self._peek() not in WHITESPACE
                and not self._is_symbol_start(self._peek())
            ):
                lexeme += self._advance()
            
            # Report error with thrown-away characters
            self._add_error(
                LeximError(self.line_number, lexeme, LeximErrorType.INVALID_CHAR)
            )
            return True

        # Valid ID or Keyword
        if lexeme in KEYWORDS:
            self._add_token(TokenType.KEYWORD, lexeme)
        else:
            self._add_token(TokenType.ID, lexeme)
        return True

    def _handle_symbol(self) -> bool:
        char = self._peek()
        next_char = self._peek(1)

        # Check for double-char symbols first
        two_chars = char + (next_char if next_char else "")

        if two_chars == "==":
            self._advance()
            self._advance()
            self._add_token(TokenType.SYMBOL, "==")
            return True

        # Check for valid single char symbol
        if char in SYMBOLS:
            self._advance()
            self._add_token(TokenType.SYMBOL, char)
            return True

        # Invalid symbol character - should not reach here in normal flow
        # This is a safety fallback
        self._add_error(LeximError(self.line_number, char, LeximErrorType.INVALID_CHAR))
        self._advance()
        return True

    def _handle_line_comment(self) -> None:
        # Consume //
        self._advance()
        self._advance()
        while not self._is_eof() and self._peek() != "\n" and self._peek() != "\f":
            _ = self._advance()
        # Note: \n or \f will be handled by the main loop

    def _handle_block_comment(self) -> None:
        # Block comments
        # Format: /* ... */
        start_line = self.line_number
        self._advance()
        self._advance()

        comment_content = "/*"

        while not self._is_eof():
            char = self._peek()
            next_char = self._peek(1)

            if char == "*" and next_char == "/":
                self._advance()
                self._advance()
                return  # Comment closed successfully

            # Capture content for error reporting if EOF is hit
            # Capture more than 10 so tables.py can detect truncation is needed
            if len(comment_content) <= 10:
                comment_content += char

            self._advance()

        # Unclosed comment at EOF
        self._add_error(
            LeximError(start_line, comment_content, LeximErrorType.UNCLOSED_COMMENT)
        )
