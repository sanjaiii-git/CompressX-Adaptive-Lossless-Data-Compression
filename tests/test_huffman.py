"""Unit tests for Huffman Coding implementation."""

import pytest
from compression.huffman import HuffmanCompressor


def test_huffman_empty():
    compressed, freq, pad = HuffmanCompressor.compress(b"")
    assert compressed == b""
    assert freq == {}
    assert pad == 0
    assert HuffmanCompressor.decompress(compressed, freq, pad) == b""


def test_huffman_single_byte():
    data = b"A"
    compressed, freq, pad = HuffmanCompressor.compress(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data


def test_huffman_single_distinct_symbol_repeated():
    data = b"AAAAAAA"
    compressed, freq, pad = HuffmanCompressor.compress(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data


def test_huffman_two_symbols():
    data = b"ABABABBA"
    compressed, freq, pad = HuffmanCompressor.compress(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data


def test_huffman_skewed_frequencies():
    # 'A' occurs 100 times, 'B' 10 times, 'C' 2 times
    data = b"A" * 100 + b"B" * 10 + b"C" * 2
    compressed, freq, pad = HuffmanCompressor.compress(data)
    assert len(compressed) < len(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data


def test_huffman_all_bytes():
    # All 256 byte values
    data = bytes(range(256)) * 2
    compressed, freq, pad = HuffmanCompressor.compress(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data


def test_huffman_text():
    data = b"The quick brown fox jumps over the lazy dog."
    compressed, freq, pad = HuffmanCompressor.compress(data)
    decompressed = HuffmanCompressor.decompress(compressed, freq, pad, original_size=len(data))
    assert decompressed == data
