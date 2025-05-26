# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025 Pavel Shago <pavel@shago.dev>

# Immediate C lib loading, bc you dont need this thing
# in your system installed. Check README.md for more info
from sys import path

path.insert(0, "build")

import huffman
import gzip
import pandas as pd

from collections import Counter
from math import log2
from io import BytesIO


def print_bitstream(encoded: bytes, bit_lenght: int):
    bits = []
    for i in range(bit_lenght):
        byte_index = i // 8
        bit_index = 7 - (i % 8)
        bit = (encoded[byte_index] >> bit_index) & 1
        bits.append(str(bit))
    print("".join(bits))
    print(f"encoded size: {bit_lenght}")


def get_entropy(freqs: dict, total: int) -> float:
    return -sum((f / total) * log2(f / total) for f in freqs.values())


def compress_gzip(text: str) -> bytes:
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb") as f:
        f.write(text.encode("utf-8"))
    return out.getvalue()


def main():
    some_str = input()

    # encoded, table, bit_lenght = huffman.encode(some_str)
    # print_bitstream(encoded, bit_lenght)

    # decoded = huffman.decode(encoded, table, bit_lenght)
    # print("Decoded string:", decoded)

    # print(decoded == some_str)

    encoded, table, bit_length = huffman.encode(some_str)
    decoded = huffman.decode(encoded, table, bit_length)
    assert decoded == some_str, "Mismatch!"

    # print("\nBitstream:")
    # print_bitstream(encoded, bit_length)

    original_bits = len(some_str) * 8
    huffman_bits = bit_length
    gzip_bytes = compress_gzip(some_str)
    gzip_bits = len(gzip_bytes) * 8

    freqs = Counter(some_str)
    total = sum(freqs.values())
    entropy = get_entropy(freqs, total)

    avg_len = huffman_bits / len(some_str)
    efficiency = entropy / avg_len if avg_len else 0

    df = pd.DataFrame(
        [
            ["Original", original_bits, "N/A", "N/A"],
            ["Huffman", huffman_bits, round(avg_len, 3), round(efficiency * 100, 2)],
            ["Gzip", gzip_bits, "N/A", "N/A"],
        ],
        columns=["Method", "Size (bits)", "Avg Code Length", "Efficiency (%)"],
    )

    print("\nCompression Comparison:\n")
    print(df.to_markdown(index=False))

    ratio_huffman = (
        round(original_bits / huffman_bits, 2) if huffman_bits else float("inf")
    )
    ratio_gzip = round(original_bits / gzip_bits, 2) if gzip_bits else float("inf")
    print(f"\nCompression Ratio (Original → Huffman): {ratio_huffman}")
    print(f"Compression Ratio (Original → Gzip):    {ratio_gzip}")
    print(f"Entropy: {round(entropy, 3)} bits/symbol")


if __name__ == "__main__":
    main()
