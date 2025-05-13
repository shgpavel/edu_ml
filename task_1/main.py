# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025 Pavel Shago <pavel@shago.dev>

# Immediate C lib loading, bc you dont need this thing
# in your system installed. Check README.md for more info
from sys import path
path.insert(0, "build")

import huffman

print(huffman.encode("some bullshit"))
print(huffman.decode(abobajan))
