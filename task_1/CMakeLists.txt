# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025 Pavel Shago <pavel@shago.dev>

cmake_minimum_required(VERSION 3.30)
project(huffman LANGUAGES C)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

add_library(huffman MODULE pyhuffman.c huffman.c)

target_include_directories(huffman PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(huffman PRIVATE ${Python3_LIBRARIES})

#set_target_properties(huffman PROPERTIES
#    PREFIX ""
#    OUTPUT_NAME "huffman"
#    SUFFIX ".cpython-313-x86_64-linux-gnu.so"
#)

set_target_properties(pyhuffman PROPERTIES
  PREFIX ""
  SUFFIX "${Python3_EXTENSION_SUFFIX}"
)
