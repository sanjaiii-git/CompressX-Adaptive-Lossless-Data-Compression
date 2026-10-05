"""Unit tests for Hybrid RLE + Huffman compression."""

import pytest
from compression.hybrid import HybridCompressor


def test_hybrid_empty():
    compressed, freq, pad, inter_size = HybridCompressor.compress(b"")
    assert compressed == b""
    assert HybridCompressor.decompress(compressed, freq, pad, inter_size) == b""


def test_hybrid_repetitive():
    data = b"AAAAAAABBBBBBBBCCCCCCCC" * 10
    compressed, freq, pad, inter_size = HybridCompressor.compress(data)
    assert len(compressed) < len(data)
    decompressed = HybridCompressor.decompress(compressed, freq, pad, inter_size)
    assert decompressed == data


def test_hybrid_text():
    data = b"System log entry: ERROR 404 Not Found at 127.0.0.1\n" * 20
    compressed, freq, pad, inter_size = HybridCompressor.compress(data)
    decompressed = HybridCompressor.decompress(compressed, freq, pad, inter_size)
    assert decompressed == data


def test_hybrid_binary():
    data = bytes([10] * 50 + [255] * 100 + [0] * 30 + [42] * 80)
    compressed, freq, pad, inter_size = HybridCompressor.compress(data)
    decompressed = HybridCompressor.decompress(compressed, freq, pad, inter_size)
    assert decompressed == data
