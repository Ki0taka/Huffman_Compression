"""Compress and decompress text using Huffman coding."""

from __future__ import annotations

import argparse
import heapq
import math
import random
import sys
from typing import Any


# Huffman tree node

class HuffmanNode:
    """A node in the Huffman tree."""

    def __init__(self, char: str | None, freq: int,
                 left: HuffmanNode | None = None,
                 right: HuffmanNode | None = None) -> None:
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def __lt__(self, other: HuffmanNode) -> bool:
        # Tie-breaking is handled by the insertion counter in the heap tuple.
        return self.freq < other.freq


# Core algorithms
def count_occurrences(text: str) -> dict[str, int]:
    """Return a frequency dictionary for each character in *text*."""
    freq: dict[str, int] = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq


def build_huffman_tree(freq: dict[str, int]) -> tuple[HuffmanNode, list[dict[str, Any]]]:
    """Build the Huffman tree from a frequency table.

    Returns the root node and a trace of every merge step so the
    construction can be displayed step by step.
    """
    if not freq:
        raise ValueError("Frequency table is empty.")

    # Initialise the min-heap: (frequency, insertion_counter, node)
    counter = 0
    heap: list[tuple[int, int, HuffmanNode]] = []
    for char in sorted(freq):
        node = HuffmanNode(char=char, freq=freq[char])
        heapq.heappush(heap, (node.freq, counter, node))
        counter += 1

    trace: list[dict[str, Any]] = []
    step = 0

    while len(heap) > 1:
        step += 1

        # Current sorted state (for display)
        sorted_nodes = ", ".join(
            f"({item[2].char if item[2].char else '*'}: {item[2].freq})"
            for item in sorted(heap)
        )

        # Pop the two smallest
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)

        merged_freq = freq1 + freq2
        parent = HuffmanNode(char=None, freq=merged_freq, left=left, right=right)
        heapq.heappush(heap, (merged_freq, counter, parent))
        counter += 1

        left_label = left.char if left.char else f"*({left.freq})"
        right_label = right.char if right.char else f"*({right.freq})"

        trace.append({
            "step": step,
            "sorted_list": sorted_nodes,
            "selected_left": f"{left_label} ({freq1})",
            "selected_right": f"{right_label} ({freq2})",
            "merged_node": f"*({merged_freq})",
        })

    _, _, root = heap[0]
    return root, trace


def generate_codes(node: HuffmanNode, prefix: str = "",
                   codes: dict[str, str] | None = None) -> dict[str, str]:
    """Recursively assign codes: 1 for left, 0 for right."""
    if codes is None:
        codes = {}

    if node.is_leaf():
        # Edge case: a single unique character gets code "1".
        codes[node.char] = prefix if prefix else "1"
        return codes

    if node.left is not None:
        generate_codes(node.left, prefix + "1", codes)
    if node.right is not None:
        generate_codes(node.right, prefix + "0", codes)

    return codes


def huffman_compress(text: str) -> tuple[str, dict[str, str], HuffmanNode,
                                         dict[str, int], list[dict[str, Any]]]:
    """Compress *text* with Huffman coding.

    Returns:
        compressed  – the binary string
        codes       – character-to-code mapping
        root        – the Huffman tree root (needed for decompression)
        freq        – character frequencies
        trace       – tree-building trace steps
    """
    if not text:
        raise ValueError("Input must not be empty.")

    freq = count_occurrences(text)
    root, trace = build_huffman_tree(freq)
    codes = generate_codes(root)
    compressed = "".join(codes[char] for char in text)
    return compressed, codes, root, freq, trace


def huffman_decompress(bitstring: str, root: HuffmanNode) -> str:
    """Decode *bitstring* by walking the Huffman tree."""
    if not bitstring:
        raise ValueError("Bitstring must not be empty.")

    # Special case: only one unique character
    if root.is_leaf():
        return root.char * len(bitstring)

    result: list[str] = []
    node = root
    for bit in bitstring:
        if bit == "1":
            node = node.left
        elif bit == "0":
            node = node.right
        else:
            raise ValueError(f"Invalid bit: {bit!r}. Bitstring must contain only '0' and '1'.")

        if node.is_leaf():
            result.append(node.char)
            node = root

    if node is not root:
        raise ValueError("Bitstring is incomplete: ends in the middle of a code.")

    return "".join(result)


# Display helpers for CLI and menu
def print_occurrences(freq: dict[str, int]) -> None:
    """Print a table of character frequencies."""
    items = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    total = sum(f for _, f in items)
    w_char = max(len("Character"), *(len(repr(char)) for char, _ in items))
    w_occ = max(len("Occurrences"), *(len(str(f)) for _, f in items))
    w_pct = len("Percentage")
    print(f"{'Character'.ljust(w_char)} | {'Occurrences'.ljust(w_occ)} | {'Percentage'.ljust(w_pct)}")
    print(f"{'-' * w_char}-+-{'-' * w_occ}-+-{'-' * w_pct}")
    for char, f in items:
        pct = f"{f / total * 100:.2f}%"
        print(f"{repr(char).ljust(w_char)} | {str(f).rjust(w_occ)} | {pct.rjust(w_pct)}")
    print(f"{'Total'.ljust(w_char)} | {str(total).rjust(w_occ)} |")


def print_tree_trace(trace: list[dict[str, Any]]) -> None:
    """Print the tree-construction trace in aligned columns."""
    columns = [
        ("Step", "step"),
        ("Sorted list", "sorted_list"),
        ("Selected left", "selected_left"),
        ("Selected right", "selected_right"),
        ("Merged node", "merged_node"),
    ]
    widths = [max(len(title), *(len(str(row[key])) for row in trace))
              for title, key in columns]
    print(" | ".join(title.ljust(w) for (title, _), w in zip(columns, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in trace:
        print(" | ".join(str(row[key]).ljust(w) for (_, key), w in zip(columns, widths)))


def print_coding_table(codes: dict[str, str]) -> None:
    """Print character → Huffman code → code length."""
    items = sorted(codes.items(), key=lambda item: len(item[1]))
    w_char = max(len("Character"), *(len(repr(c)) for c, _ in items))
    w_code = max(len("Huffman code"), *(len(code) for _, code in items))
    w_len = len("Length")
    print(f"{'Character'.ljust(w_char)} | {'Huffman code'.ljust(w_code)} | {'Length'.ljust(w_len)}")
    print(f"{'-' * w_char}-+-{'-' * w_code}-+-{'-' * w_len}")
    for char, code in items:
        print(f"{repr(char).ljust(w_char)} | {code.ljust(w_code)} | {str(len(code)).rjust(w_len)}")


def print_compression_summary(text: str, compressed: str, codes: dict[str, str]) -> None:
    """Print original size, compressed size, and compression ratio."""
    n_chars = len(text)
    n_unique = len(codes)

    # Fixed-length code size (without Huffman): ceil(log2(n_unique)) bits per char
    if n_unique > 1:
        bits_fixed = math.ceil(math.log2(n_unique))
    else:
        bits_fixed = 1
    original_bits_fixed = n_chars * bits_fixed

    # ASCII baseline: 8 bits per character
    original_bits_ascii = n_chars * 8

    compressed_bits = len(compressed)

    # Weighted average code length
    freq = count_occurrences(text)
    avg_length = sum(freq[c] * len(codes[c]) for c in codes) / n_chars

    print(f"\nOriginal text length           : {n_chars} characters")
    print(f"Number of distinct characters  : {n_unique}")
    print(f"Fixed-length code              : {bits_fixed} bits/char")
    print(f"Original size (fixed-length)   : {original_bits_fixed} bits")
    print(f"Original size (ASCII, 8-bit)   : {original_bits_ascii} bits")
    print(f"Compressed size (Huffman)      : {compressed_bits} bits")
    print(f"Average code length            : {avg_length:.4f} bits/char")
    print(f"Compression ratio (vs fixed)   : {compressed_bits / original_bits_fixed:.4f}  "
          f"({(1 - compressed_bits / original_bits_fixed) * 100:.2f}% saved)")
    print(f"Compression ratio (vs ASCII)   : {compressed_bits / original_bits_ascii:.4f}  "
          f"({(1 - compressed_bits / original_bits_ascii) * 100:.2f}% saved)")


# Sample text generator
SAMPLE_ALPHABET = ("a", "b", "c", "d", "e", "f")


def generate_sample_text(rows: int = 30, cols: int = 80,
                         alphabet: tuple[str, ...] = SAMPLE_ALPHABET,
                         seed: int | None = 42) -> str:
    """Generate a sample text of *rows* × *cols* characters.

    Characters are drawn with non-uniform probabilities so Huffman coding
    produces interesting (non-trivial) code lengths.
    """
    rng = random.Random(seed)
    # Give each character a different weight so frequencies are varied.
    weights = [2 ** i for i in range(len(alphabet))]
    lines: list[str] = []
    for _ in range(rows):
        line = "".join(rng.choices(alphabet, weights=weights, k=cols))
        lines.append(line)
    return "\n".join(lines)


# High-level orchestration functions for CLI and menu

def _print_compression(text: str) -> tuple[str, dict[str, str], HuffmanNode]:
    """Run and display full compression details; return compressed data."""
    compressed, codes, root, freq, trace = huffman_compress(text)

    # Show a short preview if the text is very long
    if len(text) > 200:
        preview = text[:100] + " ... " + text[-50:]
    else:
        preview = text
    print(f"Input ({len(text)} characters): {preview}")

    print("\n--- Character occurrences ---")
    print_occurrences(freq)

    print("\n--- Huffman tree construction ---")
    print_tree_trace(trace)

    print("\n--- Coding table ---")
    print_coding_table(codes)

    print("\n--- Compressed bitstring ---")
    if len(compressed) > 200:
        print(compressed[:200] + f"... ({len(compressed)} bits total)")
    else:
        print(compressed)

    print_compression_summary(text, compressed, codes)

    return compressed, codes, root


def _print_decompression(compressed: str, root: HuffmanNode,
                         original: str | None = None) -> str:
    """Decompress and display the result."""
    text = huffman_decompress(compressed, root)

    if len(text) > 200:
        preview = text[:100] + " ... " + text[-50:]
    else:
        preview = text
    print(f"\nDecompressed text ({len(text)} characters): {preview}")

    if original is not None:
        match = text == original
        print(f"Round-trip verification: {'OK' if match else 'FAILED'}")
    return text


def _run_mode(mode: str, text: str | None = None, filepath: str | None = None,
              use_sample: bool = False) -> None:
    """Execute a CLI or menu mode."""
    if use_sample:
        text = generate_sample_text()
        print("(Using generated sample text: 30 lines × 80 chars from {a,b,c,d,e,f})\n")
    elif filepath is not None:
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
    elif text is None or text == "":
        raise ValueError("No input provided.")

    if mode == "compress":
        _print_compression(text)
    elif mode == "roundtrip":
        compressed, codes, root = _print_compression(text)
        print("\n" + "=" * 60)
        print("DECOMPRESSION")
        print("=" * 60)
        _print_decompression(compressed, root, original=text)


# CLI & interactive menu
def _interactive_menu() -> None:
    """Show the interactive menu until the user quits."""
    while True:
        print("\n1) Compress text     2) Compress file     3) Sample (30×80)")
        print("4) Round trip text   5) Round trip file   0) Quit")
        choice = input("Your choice: ").strip()
        if choice == "0":
            return

        actions = {
            "1": ("compress", "input"),
            "2": ("compress", "file"),
            "3": ("roundtrip", "sample"),
            "4": ("roundtrip", "input"),
            "5": ("roundtrip", "file"),
        }
        if choice not in actions:
            print("Invalid choice.")
            continue

        mode, source = actions[choice]
        try:
            if source == "sample":
                _run_mode(mode, use_sample=True)
            elif source == "file":
                path = input("File path: ").strip()
                _run_mode(mode, filepath=path)
            else:
                value = input("Enter text: ")
                _run_mode(mode, text=value)
        except (ValueError, FileNotFoundError, OSError) as error:
            print(f"Error: {error}", file=sys.stderr)


def main() -> None:
    """Dispatch CLI subcommands or launch the interactive menu."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Huffman compression and decompression.")
    subparsers = parser.add_subparsers(dest="mode")

    for mode in ("compress", "roundtrip"):
        sub = subparsers.add_parser(mode)
        sub.add_argument("value", nargs="?", help="text to compress")
        sub.add_argument("--file", dest="filepath", help="path to a text file")
        sub.add_argument("--sample", action="store_true",
                         help="use generated 30×80 sample text")

    args = parser.parse_args()

    if args.mode is None:
        _interactive_menu()
        return

    try:
        _run_mode(
            args.mode,
            text=args.value,
            filepath=args.filepath if hasattr(args, "filepath") else None,
            use_sample=args.sample if hasattr(args, "sample") else False,
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
