# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025 Pavel Shago <pavel@shago.dev>

# Immediate C lib loading, bc you dont need this thing
# in your system installed. Check README.md for more info
from sys import path
path.insert(0, "build")

import huffman

def main():
    str = input()

    encoded, tree = huffman.encode(str)
    print("Encoded bytes:", encoded)
   
    decoded = huffman.decode(encoded, tree)
    print("Decoded string:", decoded)

if __name__ == "__main__":
    main()
