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
            if ch == "\n":
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
            "+",
            "-",
            "*",
            "/",
            "<",
            "=",
            ";",
            ",",
            "(",
            ")",
            "{",
            "}",
            "[",
            "]",
            "!",
            ">",
        }

    def _is_valid_id_char(self, char: str) -> bool:
        return char is not None and (char.isalnum() or char == "_")

    def _is_valid_id_start(self, char: str) -> bool:
        """Check if character can start an identifier (letter or underscore)."""
        return char is not None and (char.isalpha() or char == "_")

    def get_next_token(self) -> bool:
        """
        Advances through text to find the next valid token.
        Handles errors internally (Panic Mode) and returns True if a token was found,
        False if EOF reached.
        """
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

            # 5. Illegal Character (Catch-all)
            # If we are here, the character is not whitespace, digit, letter, or valid symbol start
            # Consume consecutive illegal characters together
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

        # Check for Malformed Number (followed by letters)
        # Example: 123d
        if self._peek() is not None and self._peek().isalpha():
            # Panic Mode for Number: consume until delimiter
            while self._peek() is not None and (
                self._peek().isalnum() or self._peek() == "_"
            ):
                lexeme += self._advance()
            self._add_error(
                LeximError(self.line_number, lexeme, LeximErrorType.MALFORMED_NUM)
            )
            return True  # We processed input, even if error

        # Validate Number Format (e.g., leading zeros)
        # '0' is valid, '012' is not.
        if len(lexeme) > 1 and lexeme.startswith("0"):
            # Technically confusing logic in prompt, usually 0 is OK, 05 is not.
            # We treat it as standard C convention: leading zero is octal or error?
            # Prompt says: "012 (leading zero unless the number is exactly 0)" -> Malformed
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
        next_char = self._peek()
        if (
            next_char is not None
            and next_char not in WHITESPACE
            and not self._is_symbol_start(next_char)
            and not self._is_valid_id_char(next_char)
        ):
            # Look ahead to see if there are valid ID chars after the illegal char(s)
            saved_cursor = self.cursor
            saved_line = self.line_number

            # Consume illegal chars temporarily
            illegal_chars = ""
            while (
                self._peek() is not None
                and self._peek() not in WHITESPACE
                and not self._is_symbol_start(self._peek())
                and not self._is_valid_id_char(self._peek())
            ):
                illegal_chars += self._advance()

            # Check if valid ID char follows
            has_id_after = self._is_valid_id_start(self._peek())

            # Restore cursor
            self.cursor = saved_cursor
            self.line_number = saved_line

            if has_id_after:
                # Case: invalid@char - emit ID, then consume illegal chars as separate error
                if lexeme in KEYWORDS:
                    self._add_token(TokenType.KEYWORD, lexeme)
                else:
                    self._add_token(TokenType.ID, lexeme)

                # Now consume and report the illegal chars
                illegal_chars = ""
                while (
                    self._peek() is not None
                    and self._peek() not in WHITESPACE
                    and not self._is_symbol_start(self._peek())
                    and not self._is_valid_id_char(self._peek())
                ):
                    illegal_chars += self._advance()
                self._add_error(
                    LeximError(
                        self.line_number, illegal_chars, LeximErrorType.INVALID_CHAR
                    )
                )
                return True
            else:
                # Case: voi$$ - consume ID + illegal chars together as error
                while (
                    self._peek() is not None
                    and self._peek() not in WHITESPACE
                    and not self._is_symbol_start(self._peek())
                    and not self._is_valid_id_char(self._peek())
                ):
                    lexeme += self._advance()
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

        # If we start with a symbol char but it isn't a valid symbol (like '!' strictly by itself if '!=' not supported or logic fails)
        # Note: C-minus usually does not have '!' as a unary operator, only '!='.
        # The prompt list of tokens didn't explicitly list '!', but the error example 'cd!' exists.
        # If '!' appears alone, it's illegal.
        self._add_error(LeximError(self.line_number, char, LeximErrorType.INVALID_CHAR))
        self._advance()
        return True

    def _handle_line_comment(self) -> None:
        # Consume //
        self._advance()
        self._advance()
        # Consume until newline or EOF
        while self._peek() is not None and self._peek() != "\n":
            _ = self._advance()
        # Note: \n will be handled by the main loop or next _advance call logic

    def _handle_block_comment(self) -> None:
        # Consume /*
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

            # Capture content for error reporting if EOF is hit (max 7 chars before ...)
            if len(comment_content) < 7:
                comment_content += char

            self._advance()

        # If loop finishes, EOF was reached without closing */
        self._add_error(
            LeximError(start_line, comment_content, LeximErrorType.UNCLOSED_COMMENT)
        )
