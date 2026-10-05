"""Unit tests for Run-Length Encoding (RLE) implementation."""

import pytest
from compression.rle import RLECompressor


def test_rle_empty():
    assert RLECompressor.compress(b"") == b""
    assert RLECompressor.decompress(b"") == b""


def test_rle_single_byte():
    data = b"A"
    compressed = RLECompressor.compress(data)
    assert compressed == b"\x01A"
    assert RLECompressor.decompress(compressed) == data


def test_rle_repetitive():
    data = b"AAAAAAAABBBBBBBBBCCCCCCCC"
    compressed = RLECompressor.compress(data)
    assert len(compressed) < len(data)
    decompressed = RLECompressor.decompress(compressed)
    assert decompressed == data


def test_rle_run_longer_than_255():
    data = b"X" * 600
    compressed = RLECompressor.compress(data)
    # 600 = 255 + 255 + 90 -> 3 runs of 2 bytes each = 6 bytes
    assert len(compressed) == 6
    decompressed = RLECompressor.decompress(compressed)
    assert decompressed == data


def test_rle_distinct_bytes():
    data = b"ABCDEF"
    compressed = RLECompressor.compress(data)
    # Each distinct byte turns into 2 bytes (count, val) -> size doubles
    assert len(compressed) == 12
    decompressed = RLECompressor.decompress(compressed)
    assert decompressed == data


def test_rle_binary_bytes():
    # Test all bytes 0..255
    data = bytes(range(256)) * 4
    compressed = RLECompressor.compress(data)
    decompressed = RLECompressor.decompress(compressed)
    assert decompressed == data


def test_rle_invalid_data():
    with pytest.raises(ValueError):
        RLECompressor.decompress(b"\x05A\x03")  # Odd number of bytes


def test_rle_zero_count():
    with pytest.raises(ValueError):
        RLECompressor.decompress(b"\x00A")


def test_rle_text_readable():
    text = "AAAAAAABBBCC"
    encoded = RLECompressor.encode_text_readable(text)
    assert encoded == "A7B3C2"
    decoded = RLECompressor.decode_text_readable(encoded)
    assert decoded == text
