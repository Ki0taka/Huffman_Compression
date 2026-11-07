# Huffman Compression — Step-by-Step Code Explanation

## Table of Contents

1. [Overview](#1-overview)
2. [Data Structure: The Tree Node](#2-data-structure-the-tree-node)
3. [Step 1 — Counting Character Occurrences](#3-step-1--counting-character-occurrences)
4. [Step 2 — Building the Huffman Tree](#4-step-2--building-the-huffman-tree)
5. [Step 3 — Generating the Coding Table](#5-step-3--generating-the-coding-table)
6. [Step 4 — Compression (Encoding)](#6-step-4--compression-encoding)
7. [Step 5 — Decompression (Decoding)](#7-step-5--decompression-decoding)
8. [Step 6 — Computing the Compression Ratio](#8-step-6--computing-the-compression-ratio)
9. [Display Functions](#9-display-functions)
10. [Sample Text Generator](#10-sample-text-generator)
11. [Orchestration and CLI Interface](#11-orchestration-and-cli-interface)
12. [Full Worked Example with Trace](#12-full-worked-example-with-trace)

---

## 1. Overview

The program implements the Huffman compression algorithm in Python. The core idea is:

- **Frequent** characters are assigned **short** binary codes.
- **Rare** characters are assigned **long** binary codes.
- This variable-length coding produces a more compact representation than fixed-length coding.

The file [`huffman.py`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py) is organized into 5 sections:

| Section | Lines | Purpose |
|---|---|---|
| `HuffmanNode` | 17–33 | Data structure for the tree |
| Core algorithms | 40–167 | Counting, tree construction, code generation, compression, decompression |
| Display functions | 174–249 | Formatted console tables |
| Sample generator | 256–274 | 30×80 text from `{a,b,c,d,e,f}` |
| CLI and interactive menu | 281–424 | Orchestration and user interface |

---

## 2. Data Structure: The Tree Node

```python
class HuffmanNode:
    def __init__(self, char, freq, left=None, right=None):
        self.char  = char   # The character (None for internal nodes)
        self.freq  = freq   # The weight (occurrence count)
        self.left  = left   # Left child (branch "1")
        self.right = right  # Right child (branch "0")
```

**Each node** in the tree contains:

- `char`: the character it represents (only for **leaf** nodes). Internal nodes have `char = None`.
- `freq`: the frequency (weight). For a leaf, this is the character's occurrence count. For an internal node, it is the **sum of the frequencies** of its two children.
- `left` / `right`: the two child subtrees.

The `is_leaf()` method returns `True` if the node has no children (it is a leaf).

The `__lt__` method allows comparing two nodes by frequency, which is required for sorting within the heap.

---

## 3. Step 1 — Counting Character Occurrences

> **Function**: [`count_occurrences(text)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L40-L45)

```python
def count_occurrences(text):
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq
```

**What happens:**

1. We iterate through the text **character by character**.
2. We use a dictionary `freq` where the key is the character and the value is how many times it appears.
3. `freq.get(char, 0)` returns the current count for the character (or 0 if it doesn't exist yet), then we increment it by 1.

**Example:** for the text `"aabbbccdddd"` we get:

```
{'a': 2, 'b': 3, 'c': 2, 'd': 4}
```

---

## 4. Step 2 — Building the Huffman Tree

> **Function**: [`build_huffman_tree(freq)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L48-L98)

This is the heart of the algorithm. It uses a **min-heap** via Python's `heapq` module.

### 4.1 — Heap Initialization

```python
counter = 0
heap = []
for char in sorted(freq):
    node = HuffmanNode(char=char, freq=freq[char])
    heapq.heappush(heap, (node.freq, counter, node))
    counter += 1
```

- We create a **leaf node** for each character.
- Each heap element is a triple `(frequency, counter, node)`.
- The `counter` serves as a **tie-breaker**: if two nodes have the same frequency, the one inserted first gets priority. This guarantees stable, reproducible behavior.

### 4.2 — Merge Loop

```python
while len(heap) > 1:
    freq1, _, left  = heapq.heappop(heap)   # Smallest
    freq2, _, right = heapq.heappop(heap)   # Second smallest

    merged_freq = freq1 + freq2
    parent = HuffmanNode(char=None, freq=merged_freq, left=left, right=right)
    heapq.heappush(heap, (merged_freq, counter, parent))
    counter += 1
```

**At each iteration:**

1. **Sort** — The heap automatically maintains ascending order.
2. **Select** — We extract the **two nodes with the lowest frequency** (`heappop` × 2).
3. **Merge** — We create a **parent node** where:
   - Left child = the lightest node.
   - Right child = the second lightest node.
   - Weight = sum of the two frequencies.
4. **Re-insert** — The parent node is pushed back into the heap.
5. **Repeat** — Until only one node remains: the **root** of the tree.

### 4.3 — Construction Trace

At each step, a `trace` list records:

| Field | Description |
|---|---|
| `step` | Step number |
| `sorted_list` | Current sorted state of the heap (for visualization) |
| `selected_left` | Left node selected (lowest frequency) |
| `selected_right` | Right node selected (second lowest) |
| `merged_node` | The newly created merged node |

**Visual example of the construction:**

```
Step 1:  [a:2, c:2, b:3, d:4]  →  merge a(2) + c(2) = *(4)
Step 2:  [b:3, d:4, *:4]       →  merge b(3) + d(4) = *(7)
Step 3:  [*:4, *:7]            →  merge *(4) + *(7) = *(11)
                                   → root of the tree
```

---

## 5. Step 3 — Generating the Coding Table

> **Function**: [`generate_codes(node, prefix, codes)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L101-L117)

```python
def generate_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}

    if node.is_leaf():
        codes[node.char] = prefix if prefix else "1"
        return codes

    if node.left is not None:
        generate_codes(node.left,  prefix + "1", codes)  # Left → 1
    if node.right is not None:
        generate_codes(node.right, prefix + "0", codes)  # Right → 0

    return codes
```

**What happens:**

1. We traverse the tree **recursively** starting from the root.
2. At each move:
   - Going **left** → append `"1"` to the prefix
   - Going **right** → append `"0"` to the prefix
3. When we reach a **leaf**, the accumulated prefix is the **Huffman code** for that character.
4. **Edge case**: if the text contains only one distinct character, the root is directly a leaf — it gets the code `"1"`.

> ⚠️ As specified in the project: **1 = left**, **0 = right**.

**Example result:**

```
'd' → "0"     (1 bit)
'b' → "10"    (2 bits)
'a' → "111"   (3 bits)
'c' → "110"   (3 bits)
```

The most frequent characters (`d` with 4 occurrences) get the shortest code.

---

## 6. Step 4 — Compression (Encoding)

> **Function**: [`huffman_compress(text)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L120-L138)

```python
def huffman_compress(text):
    freq = count_occurrences(text)          # Step 1
    root, trace = build_huffman_tree(freq)  # Step 2
    codes = generate_codes(root)            # Step 3
    compressed = "".join(codes[char] for char in text)  # Step 4
    return compressed, codes, root, freq, trace
```

**What happens:**

1. We chain the 3 previous steps together.
2. We produce the **compressed string** by replacing each character in the text with its Huffman code.
3. We return everything needed for display and decompression:
   - `compressed`: the compressed binary string
   - `codes`: the coding table (character → code)
   - `root`: the tree root (needed for decompression)
   - `freq`: the frequencies (for display)
   - `trace`: the construction steps (for display)

**Example:**

```
Text:       "aabbbccdddd"
Compressed: "11111110101011011000000"
```

---

## 7. Step 5 — Decompression (Decoding)

> **Function**: [`huffman_decompress(bitstring, root)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L141-L167)

```python
def huffman_decompress(bitstring, root):
    result = []
    node = root
    for bit in bitstring:
        if bit == "1":
            node = node.left     # go left
        elif bit == "0":
            node = node.right    # go right

        if node.is_leaf():
            result.append(node.char)  # character found
            node = root               # go back to root

    return "".join(result)
```

**What happens:**

1. We start at the **root** of the tree.
2. We read the binary string **bit by bit**:
   - `"1"` → go **left**
   - `"0"` → go **right**
3. When we reach a **leaf**:
   - We've found a character → add it to the result.
   - We **go back to the root** to decode the next character.
4. At the end, we verify we're back at the root (otherwise the bitstring is incomplete).

**Round-trip verification:**

```
Compressed:   "11111110101011011000000"
Decompressed: "aabbbccdddd"  ← identical to the original ✓
```

---

## 8. Step 6 — Computing the Compression Ratio

> **Function**: [`print_compression_summary(text, compressed, codes)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L218-L249)

Two baselines are computed for comparison:

### 8.1 — Fixed-Length Coding (Minimal Baseline)

$$\text{bits per character} = \lceil \log_2(n) \rceil$$

where $n$ is the number of distinct characters. For example, with 6 characters: $\lceil \log_2(6) \rceil = 3$ bits per character.

$$\text{Original size (fixed)} = \text{number of characters} \times \text{bits per character}$$

### 8.2 — ASCII Coding (8 bits)

$$\text{Original size (ASCII)} = \text{number of characters} \times 8$$

### 8.3 — Compression Ratio

$$\text{Ratio} = \frac{\text{compressed size}}{\text{original size}}$$

$$\text{Savings (\%)} = \left(1 - \text{ratio}\right) \times 100$$

### 8.4 — Weighted Average Code Length

$$\bar{l} = \frac{\sum_{c} \text{freq}(c) \times \text{len}(\text{code}(c))}{\text{total number of characters}}$$

This is the frequency-weighted average length of the Huffman codes. The lower this value, the better the compression.

---

## 9. Display Functions

The program uses aligned column tables (same style as `lzw.py`).

| Function | What it displays |
|---|---|
| [`print_occurrences(freq)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L174-L186) | Table: character, occurrences, percentage |
| [`print_tree_trace(trace)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L189-L203) | Table of each tree construction step |
| [`print_coding_table(codes)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L206-L215) | Table: character → Huffman code → length |
| [`print_compression_summary(...)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L218-L249) | Sizes and compression ratios |

Each function dynamically computes the **column widths** so the table is always properly aligned, regardless of the data size.

---

## 10. Sample Text Generator

> **Function**: [`generate_sample_text(rows, cols, alphabet, seed)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L259-L274)

```python
SAMPLE_ALPHABET = ("a", "b", "c", "d", "e", "f")

def generate_sample_text(rows=30, cols=80, alphabet=SAMPLE_ALPHABET, seed=42):
    rng = random.Random(seed)
    weights = [2 ** i for i in range(len(alphabet))]  # [1, 2, 4, 8, 16, 32]
    lines = []
    for _ in range(rows):
        line = "".join(rng.choices(alphabet, weights=weights, k=cols))
        lines.append(line)
    return "\n".join(lines)
```

**What happens:**

1. It uses the 6 characters `{a, b, c, d, e, f}` as required by the project specification.
2. The weights are `[1, 2, 4, 8, 16, 32]` → the characters have **very different** frequencies (e.g. `f` is ~32× more frequent than `a`). This produces an interesting Huffman tree with varied code lengths.
3. `seed=42` ensures **reproducible** results.
4. The text is 30 lines × 80 characters = **2400 characters** (+ 29 newlines).

---

## 11. Orchestration and CLI Interface

### 11.1 — Orchestration Functions

| Function | Purpose |
|---|---|
| [`_print_compression(text)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L281-L309) | Runs the full compression and displays all results |
| [`_print_decompression(compressed, root, original)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L312-L326) | Decompresses and verifies the round-trip |
| [`_run_mode(mode, text, filepath, use_sample)`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L329-L348) | Dispatches based on the chosen mode |

### 11.2 — Interactive Menu

> **Function**: [`_interactive_menu()`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L355-L386)

```
1) Compress text     2) Compress file     3) Sample (30×80)
4) Round trip text   5) Round trip file   0) Quit
```

The user picks an option, enters text or a file path, and the program displays all results.

### 11.3 — Command-Line Interface (CLI)

> **Function**: [`main()`](file:///home/kiotaka/Desktop/MIV/Multimedia/TP/Project_3/huffman.py#L389-L424)

```bash
# Compress text directly
python3 huffman.py compress "aabbbccdddd"

# Compress the 30×80 sample text
python3 huffman.py compress --sample

# Compress a file
python3 huffman.py compress --file my_file.txt

# Compress + decompress (round-trip verification)
python3 huffman.py roundtrip "aabbbccdddd"

# Interactive menu
python3 huffman.py
```

---

## 12. Full Worked Example with Trace

Here is a complete example for the text `"aabbbccddddeeeeeefffff"`:

### Occurrences

| Character | Occurrences | Percentage |
|---|---|---|
| `e` | 6 | 27.27% |
| `f` | 5 | 22.73% |
| `d` | 4 | 18.18% |
| `b` | 3 | 13.64% |
| `a` | 2 | 9.09% |
| `c` | 2 | 9.09% |

### Tree Construction

| Step | Action | Result |
|---|---|---|
| 1 | Merge `a`(2) + `c`(2) | Node `*`(4) |
| 2 | Merge `b`(3) + `d`(4) | Node `*`(7) |
| 3 | Merge `*`(4) + `f`(5) | Node `*`(9) |
| 4 | Merge `e`(6) + `*`(7) | Node `*`(13) |
| 5 | Merge `*`(9) + `*`(13) | Root `*`(22) |

### Coding Table

| Character | Code | Length |
|---|---|---|
| `f` | `10` | 2 bits |
| `e` | `01` | 2 bits |
| `a` | `111` | 3 bits |
| `c` | `110` | 3 bits |
| `b` | `001` | 3 bits |
| `d` | `000` | 3 bits |

### Result

```
Original text   : "aabbbccddddeeeeeefffff"  (22 characters)
Compressed      : "1111110010010011101100000000000000101010101011010101010"  (55 bits)
Fixed-length    : 66 bits (3 bits/char × 22 chars)
Savings         : 16.67% vs fixed-length coding, 68.75% vs ASCII
```
