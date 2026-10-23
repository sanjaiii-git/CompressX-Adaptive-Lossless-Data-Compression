"""Unit tests for newly added compression algorithms and multi-objective adaptive selection.

Tests:
- LZ77 compression and lossless decompression
- DEFLATE (RFC 1951) standard compression and lossless decompression
- LZW dictionary compression and KwKwK edge-case decompression
- BWT + MTF + Zero-run RLE block compression and exact restoration
- Container storage serialization and validation for all 8 algorithms
- Multi-objective adaptive optimization ('max_compression', 'balanced', 'fast')
"""

import pytest
import os
from compression.lz77 import LZ77Compressor
from compression.deflate import DeflateCompressor
from compression.lzw import LZWCompressor
from compression.bwt import BWTCompressor
from storage.container import Container, Metadata
from compression.adaptive import AdaptiveCompressor


TEST_SAMPLES = [
    b"",  # Empty
    b"A",  # Single byte
    b"A" * 1000,  # Highly repetitive
    b"ABABABABABABABABABABABABABAB" * 50,  # Periodic pattern
    b"The quick brown fox jumps over the lazy dog. 1234567890! " * 25,  # Natural language
    bytes(range(256)) * 4,  # Full binary spectrum 0-255
    b"TOBEORNOTTOBEORTOBEORNOT",  # Classic LZW test phrase (KwKwK pattern)
    bytes([(i * 47 + 11) % 256 for i in range(1500)]),  # Pseudorandom bytes
]


class TestLZ77:
    @pytest.mark.parametrize("data", TEST_SAMPLES)
    def test_lz77_lossless_roundtrip(self, data):
        compressed = LZ77Compressor.compress(data)
        restored = LZ77Compressor.decompress(compressed)
        assert restored == data

    def test_lz77_empty(self):
        assert LZ77Compressor.compress(b"") == b""
        assert LZ77Compressor.decompress(b"") == b""

    def test_lz77_compression_gain(self):
        repetitive = b"CompressX-Adaptive-Lossless-" * 40
        compressed = LZ77Compressor.compress(repetitive)
        assert len(compressed) < len(repetitive)


class TestDeflate:
    @pytest.mark.parametrize("data", TEST_SAMPLES)
    def test_deflate_lossless_roundtrip(self, data):
        compressed = DeflateCompressor.compress(data)
        restored = DeflateCompressor.decompress(compressed)
        assert restored == data

    def test_deflate_levels(self):
        data = b"Testing deflate compression levels..." * 30
        c1 = DeflateCompressor.compress(data, level=1)
        c9 = DeflateCompressor.compress(data, level=9)
        assert DeflateCompressor.decompress(c1) == data
        assert DeflateCompressor.decompress(c9) == data
        assert len(c9) <= len(c1)


class TestLZW:
    @pytest.mark.parametrize("data", TEST_SAMPLES)
    def test_lzw_lossless_roundtrip(self, data):
        compressed = LZWCompressor.compress(data)
        restored = LZWCompressor.decompress(compressed)
        assert restored == data

    def test_lzw_kwkwk_edge_case(self):
        # KwKwK pattern where decoder encounters unknown symbol code
        data = b"ABABABA" * 100
        compressed = LZWCompressor.compress(data)
        restored = LZWCompressor.decompress(compressed)
        assert restored == data

    def test_lzw_empty(self):
        assert LZWCompressor.compress(b"") == b""
        assert LZWCompressor.decompress(b"") == b""


class TestBWT:
    @pytest.mark.parametrize("data", TEST_SAMPLES)
    def test_bwt_lossless_roundtrip(self, data):
        compressed = BWTCompressor.compress(data)
        restored = BWTCompressor.decompress(compressed)
        assert restored == data

    def test_bwt_empty(self):
        assert BWTCompressor.compress(b"") == b""
        assert BWTCompressor.decompress(b"") == b""

    def test_bwt_single_byte(self):
        data = b"Z"
        assert BWTCompressor.decompress(BWTCompressor.compress(data)) == data


class TestContainerAndMultiObjective:
    @pytest.mark.parametrize("algo", ["RLE", "HUFFMAN", "HYBRID", "LZ77", "DEFLATE", "LZW", "BWT", "NONE"])
    def test_container_all_algorithms(self, algo):
        data = b"Sample dataset for container packing and unpacking tests." * 10
        meta = Metadata(file_name="test.dat", extra_attributes={"algo": algo})

        if algo == "NONE":
            payload = data
        elif algo == "LZ77":
            payload = LZ77Compressor.compress(data)
        elif algo == "DEFLATE":
            payload = DeflateCompressor.compress(data)
        elif algo == "LZW":
            payload = LZWCompressor.compress(data)
        elif algo == "BWT":
            payload = BWTCompressor.compress(data)
        else:
            payload = data  # dummy payload for container check

        container = Container.pack(algo, payload, data, meta)
        pkg = Container.unpack(container)

        assert pkg.original_size == len(data)
        assert pkg.metadata.file_name == "test.dat"
        assert pkg.algorithm_name == algo

    def test_adaptive_objectives(self):
        # Test file with mixed characteristics
        data = b"Adaptive data compression optimization benchmark test payload! " * 50
        compressor = AdaptiveCompressor()

        # Maximum compression objective
        pkg_max, strat_max, _, details_max = compressor.compress_adaptive(
            data, file_name="benchmark.txt", objective="max_compression"
        )
        decomp_max, pass_max, _, _ = AdaptiveCompressor.decompress_container(pkg_max)
        assert pass_max is True
        assert decomp_max == data
        assert len(details_max["comparison_matrix"]) >= 7

        # Fast objective
        pkg_fast, strat_fast, _, details_fast = compressor.compress_adaptive(
            data, file_name="benchmark.txt", objective="fast"
        )
        decomp_fast, pass_fast, _, _ = AdaptiveCompressor.decompress_container(pkg_fast)
        assert pass_fast is True
        assert decomp_fast == data

        # Balanced objective
        pkg_bal, strat_bal, _, details_bal = compressor.compress_adaptive(
            data, file_name="benchmark.txt", objective="balanced"
        )
        decomp_bal, pass_bal, _, _ = AdaptiveCompressor.decompress_container(pkg_bal)
        assert pass_bal is True
        assert decomp_bal == data
