"""Comprehensive lossless integrity verification tests across all algorithms and edge cases."""

import pytest
import os
from compression.rle import RLECompressor
from compression.huffman import HuffmanCompressor
from compression.hybrid import HybridCompressor
from compression.adaptive import AdaptiveCompressor


@pytest.mark.parametrize(
    "dataset_bytes",
    [
        b"",  # Empty
        b"X",  # Single byte
        b"ZZZZZZZZZZ",  # All identical
        b"A" * 1000 + b"B" * 500,  # Highly repetitive
        "Hello 🌍 World! Привет мир! 日本語 🚀".encode("utf-8"),  # Unicode UTF-8 multi-byte
        bytes(range(256)) * 3,  # Full binary alphabet with null bytes
        b"timestamp,ip,status,bytes\n" + b"2026-10-05,192.168.1.1,200,1024\n" * 50,  # Structured CSV/log
        bytes([(i * 101 + 17) % 256 for i in range(1500)]),  # Pseudorandom
    ],
)
def test_lossless_roundtrip_all_algorithms(dataset_bytes):
    # 1. Test RLE
    rle_comp = RLECompressor.compress(dataset_bytes)
    rle_decomp = RLECompressor.decompress(rle_comp)
    assert rle_decomp == dataset_bytes, "RLE failed lossless integrity"

    # 2. Test Huffman
    huff_comp, freqs, pad = HuffmanCompressor.compress(dataset_bytes)
    huff_decomp = HuffmanCompressor.decompress(
        huff_comp, freqs, pad, original_size=len(dataset_bytes)
    )
    assert huff_decomp == dataset_bytes, "Huffman failed lossless integrity"

    # 3. Test Hybrid
    hyb_comp, hyb_freqs, hyb_pad, inter_sz = HybridCompressor.compress(dataset_bytes)
    hyb_decomp = HybridCompressor.decompress(
        hyb_comp, hyb_freqs, hyb_pad, intermediate_size=inter_sz
    )
    assert hyb_decomp == dataset_bytes, "Hybrid failed lossless integrity"

    # 4. Test Adaptive Container roundtrip
    comp = AdaptiveCompressor()
    container_bytes, strat, pred, details = comp.compress_adaptive(
        dataset_bytes, file_name="sample.dat"
    )
    restored, passed, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
    assert passed is True, f"Adaptive container verification failed: {msg}"
    assert restored == dataset_bytes, "Adaptive decompressed bytes do not match original"
