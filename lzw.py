"""Compress and decompress LZW streams over the alphabet {a, b, c}."""

from __future__ import annotations

import argparse
import sys
from typing import Any

INITIAL_ALPHABET = ("a", "b", "c")


def validate_input(text: str) -> None:
    """Raise ValueError unless text is non-empty and uses only a, b, and c."""
    if not text:
        raise ValueError("Input must not be empty.")
    invalid = sorted(set(text) - set(INITIAL_ALPHABET))
    if invalid:
        raise ValueError(
            "Input may contain only the characters a, b, and c; "
            f"invalid character(s): {', '.join(repr(char) for char in invalid)}."
        )


def lzw_compress(text: str) -> tuple[list[int], dict[str, int], list[dict[str, Any]]]:
    """Return LZW codes, the final substring-to-code dictionary, and step trace."""
    validate_input(text)
    dictionary = {char: index for index, char in enumerate(INITIAL_ALPHABET)}
    codes: list[int] = []
    trace_steps: list[dict[str, Any]] = []
    next_code = len(dictionary)
    w = text[0]
    for step_number, k in enumerate(text[1:], start=1):
        candidate = w + k
        found = candidate in dictionary
        if found:
            trace_steps.append({"step": step_number, "current_w": w, "read_char": k,
                                "in_dictionary": "yes", "output_code": "-", "new_entry": "-"})
            w = candidate
        else:
            emitted = dictionary[w]
            dictionary[candidate] = next_code
            trace_steps.append({"step": step_number, "current_w": w, "read_char": k,
                                "in_dictionary": "no", "output_code": emitted,
                                "new_entry": f"{candidate} = {next_code}"})
            codes.append(emitted)
            next_code += 1
            w = k
    codes.append(dictionary[w])
    trace_steps.append({"step": len(text), "current_w": w, "read_char": "END",
                        "in_dictionary": "-", "output_code": dictionary[w], "new_entry": "-"})
    return codes, dictionary, trace_steps


def parse_codes(text: str) -> list[int]:
    """Parse a comma-, whitespace-, or bracket-separated code list and optional label."""
    stripped = text.strip()
    if ":" in stripped:
        stripped = stripped.split(":", 1)[1].strip()
    stripped = stripped.strip().strip("[](){}").strip()
    if not stripped:
        raise ValueError("No codes provided.")
    tokens = stripped.replace(",", " ").split()
    if not tokens:
        raise ValueError("No codes provided.")
    codes: list[int] = []
    for token in tokens:
        if not token.isascii() or not token.isdigit():
            raise ValueError(f"Invalid code: {token!r}. Codes must be non-negative integers.")
        codes.append(int(token))
    return codes


def lzw_decompress(codes: list[int]) -> tuple[str, dict[int, str], list[dict[str, Any]]]:
    """Decode LZW codes, returning text, rebuilt code dictionary, and trace rows."""
    if not isinstance(codes, list) or not codes:
        raise ValueError("The code list must not be empty.")
    if any(type(code) is not int or code < 0 for code in codes):
        raise ValueError("Codes must be non-negative integers.")
    dictionary = {index: char for index, char in enumerate(INITIAL_ALPHABET)}
    if codes[0] not in dictionary:
        raise ValueError(f"The first code must be 0, 1, or 2 (received {codes[0]}).")
    first = dictionary[codes[0]]
    output = [first]
    previous = first
    trace: list[dict[str, Any]] = [{
        "step": 1, "code_read": codes[0], "case": "first code", "entry": first,
        "output_so_far": first, "new_entry": "-",
    }]
    next_code = len(dictionary)
    for step, code in enumerate(codes[1:], start=2):
        if code in dictionary:
            entry = dictionary[code]
            case = "in dictionary"
        elif code == next_code:
            entry = previous + previous[0]
            case = "special case (code = next index)"
        else:
            raise ValueError(f"Invalid code {code}: the next available index is {next_code}.")
        output.append(entry)
        new_entry = previous + entry[0]
        dictionary[next_code] = new_entry
        trace.append({"step": step, "code_read": code, "case": case, "entry": entry,
                      "output_so_far": "".join(output), "new_entry": f"{new_entry} = {next_code}"})
        next_code += 1
        previous = entry
    return "".join(output), dictionary, trace


def print_trace(trace_steps: list[dict[str, Any]]) -> None:
    """Print the compression trace in aligned plain-text columns."""
    columns = [("Step", "step"), ("Current w", "current_w"), ("Read char k", "read_char"),
               ("w+k in dict?", "in_dictionary"), ("Output code", "output_code"),
               ("New dict entry", "new_entry")]
    widths = [max(len(title), *(len(str(row[key])) for row in trace_steps)) for title, key in columns]
    print(" | ".join(title.ljust(width) for (title, _), width in zip(columns, widths)))
    print("-+-".join("-" * width for width in widths))
    for row in trace_steps:
        print(" | ".join(str(row[key]).ljust(width) for (_, key), width in zip(columns, widths)))


def print_decompression_trace(trace_steps: list[dict[str, Any]]) -> None:
    """Print the decompression trace in aligned plain-text columns."""
    columns = [("Step", "step"), ("Code read", "code_read"), ("Case", "case"),
               ("Entry", "entry"), ("Output so far", "output_so_far"),
               ("New dictionary entry", "new_entry")]
    widths = [max(len(title), *(len(str(row[key])) for row in trace_steps)) for title, key in columns]
    print(" | ".join(title.ljust(width) for title, width in zip((item[0] for item in columns), widths)))
    print("-+-".join("-" * width for width in widths))
    for row in trace_steps:
        print(" | ".join(str(row[key]).ljust(width) for (_, key), width in zip(columns, widths)))


def print_dictionary(dictionary: dict[str, int] | dict[int, str]) -> None:
    """Print either dictionary orientation sorted by code, identifying entry type."""
    if dictionary and all(isinstance(key, int) for key in dictionary):
        entries = [(value, key) for key, value in dictionary.items()]
    else:
        entries = [(key, value) for key, value in dictionary.items()]
    entries.sort(key=lambda item: item[1])
    labels = ["initial" if index < len(INITIAL_ALPHABET) else "added" for _, index in entries]
    w_idx = max(len("Index"), *(len(str(index)) for _, index in entries))
    w_sub = max(len("Substring"), *(len(substring) for substring, _ in entries))
    w_type = max(len("Kind"), *(len(label) for label in labels))
    print(f"{'Index'.ljust(w_idx)} | {'Substring'.ljust(w_sub)} | {'Kind'.ljust(w_type)}")
    print(f"{'-' * w_idx}-+-{'-' * w_sub}-+-{'-' * w_type}")
    for (substring, index), label in zip(entries, labels):
        print(f"{str(index).rjust(w_idx)} | {substring.ljust(w_sub)} | {label}")


def substitute_codes(codes: list[int], dictionary: dict[str, int]) -> list[str]:
    """Return the substring represented by each code in the final dictionary."""
    inverse = {code: substring for substring, code in dictionary.items()}
    try:
        return [inverse[code] for code in codes]
    except KeyError as error:
        raise ValueError(f"Unknown dictionary code: {error.args[0]}") from error


def _print_compression(text: str) -> tuple[list[int], dict[str, int]]:
    """Run and print compression details, returning codes and its dictionary."""
    codes, dictionary, trace = lzw_compress(text)
    print(f"Input: {text}")
    print("\nCompression trace:")
    print_trace(trace)
    print("\nCodes:", codes)
    print("\nFinal dictionary:")
    print_dictionary(dictionary)
    pieces = substitute_codes(codes, dictionary)
    reconstructed = "".join(pieces)
    status = "Verification OK" if reconstructed == text else "Verification FAILED"
    print(f"\nSubstitution: {' | '.join(pieces)}  ->  {reconstructed}  ({status})")
    ratio = len(codes) / len(text)
    print(f"Compression summary: original length = {len(text)}, number of codes = {len(codes)}, ratio = {ratio:.3f}")
    decoded, _, _ = lzw_decompress(codes)
    print("Round-trip OK" if decoded == text else "Round-trip FAILED")
    return codes, dictionary


def _print_decompression(codes: list[int]) -> None:
    """Run and print decompression trace, dictionary, verification, and summary."""
    text, dictionary, trace = lzw_decompress(codes)
    print("Decompression trace:")
    print_decompression_trace(trace)
    print(f"\nDecompressed text: {text}")
    print("\nFinal dictionary:")
    print_dictionary(dictionary)
    recodes, rec_dictionary, _ = lzw_compress(text)
    inverse_dictionary = {code: substring for substring, code in rec_dictionary.items()}
    canonical = recodes == codes and inverse_dictionary == dictionary
    print("Verification OK" if canonical else "Verification: non-canonical codes")
    ratio = len(codes) / len(text)
    print(f"Summary: number of codes = {len(codes)}, output length = {len(text)}, ratio = {ratio:.3f}")


def _run_mode(mode: str, value: str) -> None:
    """Run a requested CLI or menu mode, parsing or validating once."""
    if mode == "compress":
        _print_compression(value.strip())
    elif mode == "decompress":
        _print_decompression(parse_codes(value))
    else:
        text = value.strip()
        codes, _ = _print_compression(text)
        _print_decompression(codes)
        decoded, _, _ = lzw_decompress(codes)
        print(f"\nFinal comparison: {'OK' if decoded == text else 'ÉCHEC'}")


def _interactive_menu() -> None:
    """Show the interactive menu until the user chooses to quit."""
    while True:
        print("\n1) Compression   2) Decompression   3) Round trip   0) Quit")
        choice = input("Your choice: ").strip()
        if choice == "0":
            return
        modes = {"1": "compress", "2": "decompress", "3": "roundtrip"}
        if choice not in modes:
            print("Invalid choice.")
            continue
        mode = modes[choice]
        prompt = "Enter a string over {a, b, c}: " if mode != "decompress" else "Enter the codes: "
        value = input(prompt)
        try:
            _run_mode(mode, value)
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)


def main() -> None:
    """Dispatch CLI subcommands or launch the interactive menu."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="LZW compression and decompression over {a, b, c}.")
    subparsers = parser.add_subparsers(dest="mode")
    for mode in ("compress", "decompress", "roundtrip"):
        subparser = subparsers.add_parser(mode)
        subparser.add_argument("value", nargs="?", help="text or list of codes")
    args = parser.parse_args()
    if args.mode is None:
        _interactive_menu()
        return
    prompt = "Enter a string over {a, b, c}: " if args.mode != "decompress" else "Enter the codes: "
    value = args.value if args.value is not None else input(prompt)
    try:
        _run_mode(args.mode, value)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
