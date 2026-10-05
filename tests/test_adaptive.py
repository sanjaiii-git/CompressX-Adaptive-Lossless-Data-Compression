"""Unit tests for the Adaptive Compressor and prediction engine."""

import os
import pytest
from compression.adaptive import AdaptiveCompressor


def test_adaptive_prediction_repetitive():
    data = b"A" * 500 + b"B" * 500 + b"C" * 300
    compressor = AdaptiveCompressor()
    profile, prediction = compressor.analyze(data)

    assert prediction.repetition_level == "HIGH"
    assert prediction.recommended_strategy in ("RLE", "HYBRID")


def test_adaptive_prediction_skewed_text():
    # Natural English text has high frequency skew (lots of 'e', ' ', 't') and low repetition
    data = (
        b"Adaptive data compression is an advanced topic in computer science and information theory. "
        b"We analyze the empirical character frequency distribution and calculate the Shannon entropy. "
    ) * 15
    compressor = AdaptiveCompressor()
    profile, prediction = compressor.analyze(data)

    assert prediction.repetition_level == "LOW"
    assert prediction.recommended_strategy == "HUFFMAN"


def test_adaptive_prediction_random_incompressible():
    # High entropy pseudorandom data
    # Pre-generate 1000 bytes with broad distribution
    data = bytes([(i * 37 + 13) % 256 for i in range(2000)])
    compressor = AdaptiveCompressor()
    profile, prediction = compressor.analyze(data)

    assert prediction.entropy_level == "HIGH"
    assert prediction.repetition_level == "LOW"
    assert prediction.recommended_strategy in ("NONE", "HUFFMAN")


def test_adaptive_compression_and_decompression_roundtrip():
    data = b"Line 1: System started OK\nLine 2: Processing event 100\n" * 30
    compressor = AdaptiveCompressor()

    # Mode: prediction
    container_bytes, strategy, prediction, details = compressor.compress_adaptive(
        data, file_name="events.log", selection_mode="prediction"
    )
    assert len(container_bytes) > 0

    decompressed, passed, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
    assert passed is True
    assert decompressed == data
    assert "PASSED" in msg

    # Mode: evaluate_all
    container_bytes2, strategy2, prediction2, details2 = compressor.compress_adaptive(
        data, file_name="events.log", selection_mode="evaluate_all"
    )
    decompressed2, passed2, msg2, info2 = AdaptiveCompressor.decompress_container(container_bytes2)
    assert passed2 is True
    assert decompressed2 == data
