# Amir Hossein Ravan Nakhjavani - 400104975
# Maedeh Heydari - 400104918

import logging

from scanner import Scanner
from parser import Parser
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
    parser = Parser(scanner)

    # Run parser (parser calls scanner as needed)
    parser.parse()

    # Export outputs for Phase 2
    parser.export_parse_tree("parse_tree.txt")
    parser.export_syntax_errors("syntax_errors.txt")
    
    # Also export scanner outputs (for Phase 1 compatibility if needed)
    token_table.export_to_file("tokens.txt")
    error_table.export_to_file("lexical_errors.txt")
    symbol_table.export_to_file("symbol_table.txt")


if __name__ == "__main__":
    main()
