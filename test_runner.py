#!/usr/bin/env python3
"""Test runner for scanner tests."""

import sys
from pathlib import Path

from consts import KEYWORDS
from scanner import Scanner
from tables import error_table, symbol_table, token_table


def run_test(test_dir):
    """Run a single test case."""
    input_file = test_dir / "input.txt"
    expected_tokens = test_dir / "tokens.txt"
    expected_errors = test_dir / "lexical_errors.txt"
    expected_symbols = test_dir / "symbol_table.txt"

    # Read input
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Run scanner
    scanner = Scanner(content)
    while scanner.get_next_token():
        pass

    # Generate output strings
    actual_tokens = []
    for lineno in sorted(token_table.tokens.keys()):
        line_tokens = " ".join(token_table.tokens[lineno])
        actual_tokens.append(f"{lineno}.\t{line_tokens} ")

    actual_errors = []
    if not error_table.errors:
        actual_errors.append("No lexical errors found.")
    else:
        actual_errors = error_table.errors

    actual_symbols = []
    index = 1
    # Keywords (already sorted)
    keywords = [s for s in symbol_table.symbols if s in KEYWORDS]
    # IDs (need to sort)
    ids = sorted([s for s in symbol_table.symbols if s not in KEYWORDS])
    for symbol in keywords + ids:
        actual_symbols.append(f"{index}.\t{symbol}")
        index += 1

    # Read expected outputs
    with open(expected_tokens, "r", encoding="utf-8") as f:
        expected_tokens_lines = [line.rstrip("\n") for line in f.readlines()]

    with open(expected_errors, "r", encoding="utf-8") as f:
        expected_errors_lines = [line.rstrip("\n") for line in f.readlines()]

    with open(expected_symbols, "r", encoding="utf-8") as f:
        expected_symbols_lines = [line.rstrip("\n") for line in f.readlines()]

    # Compare
    tokens_match = actual_tokens == expected_tokens_lines
    errors_match = actual_errors == expected_errors_lines
    symbols_match = actual_symbols == expected_symbols_lines

    return (
        tokens_match,
        errors_match,
        symbols_match,
        actual_tokens,
        actual_errors,
        actual_symbols,
        expected_tokens_lines,
        expected_errors_lines,
        expected_symbols_lines,
    )


def main():
    test_base = Path(__file__).parent / "test" / "phase1-tests"

    all_passed = True

    for i in range(1, 11):
        test_name = f"T{i:02d}"
        test_dir = test_base / test_name

        if not test_dir.exists():
            print(f"❌ {test_name}: Test directory not found")
            all_passed = False
            continue

        (
            tokens_match,
            errors_match,
            symbols_match,
            actual_tokens,
            actual_errors,
            actual_symbols,
            expected_tokens_lines,
            expected_errors_lines,
            expected_symbols_lines,
        ) = run_test(test_dir)

        if tokens_match and errors_match and symbols_match:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
            all_passed = False

            if not tokens_match:
                print("  Tokens mismatch:")
                print(f"    Expected ({len(expected_tokens_lines)} lines):")
                for line in expected_tokens_lines[:5]:
                    print(f"      {line}")
                if len(expected_tokens_lines) > 5:
                    print(f"      ... ({len(expected_tokens_lines) - 5} more lines)")
                print(f"    Actual ({len(actual_tokens)} lines):")
                for line in actual_tokens[:5]:
                    print(f"      {line}")
                if len(actual_tokens) > 5:
                    print(f"      ... ({len(actual_tokens) - 5} more lines)")

            if not errors_match:
                print("  Errors mismatch:")
                print("    Expected:")
                for line in expected_errors_lines:
                    print(f"      {line}")
                print("    Actual:")
                for line in actual_errors:
                    print(f"      {line}")

            if not symbols_match:
                print("  Symbol table mismatch:")
                print("    Expected:")
                for line in expected_symbols_lines[:10]:
                    print(f"      {line}")
                if len(expected_symbols_lines) > 10:
                    print(f"      ... ({len(expected_symbols_lines) - 10} more lines)")
                print("    Actual:")
                for line in actual_symbols[:10]:
                    print(f"      {line}")
                if len(actual_symbols) > 10:
                    print(f"      ... ({len(actual_symbols) - 10} more lines)")

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
