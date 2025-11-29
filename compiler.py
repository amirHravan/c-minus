import logging

from scanner import Scanner
from tables import error_table, symbol_table, token_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error("Error: input.txt not found.")
        return

    scanner = Scanner(content)

    # Run Scanner until EOF
    while scanner.get_next_token():
        pass

    token_table.export_to_file("tokens.txt")
    error_table.export_to_file("lexical_errors.txt")
    symbol_table.export_to_file("symbol_table.txt")


if __name__ == "__main__":
    main()
