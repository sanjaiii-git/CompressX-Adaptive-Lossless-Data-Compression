"""Regression test suite for CompressX Adaptive Algorithm Selection on repetitive and varied data.

Validates:
- Case A: b"a" * 17 (Short sequence, Raw Bypass on container expansion)
- Case B: b"a" * 10000 (Long repetition, Hybrid/RLE outperforming DEFLATE)
- Case B2: Alternating runs where pure RLE produces the smallest container
- Case C: b"abcabcabcabc" * 1000 (Pattern repetition, dictionary wins, RLE avoided)
- Case D: Natural-language text
- Case E: Server logs
- Case F: Random binary data (Raw Bypass selected due to expansion)
- Correctness of RLE with runs > 255 bytes and arbitrary binary data
- Multi-objective consistency (max_compression, balanced, fast)
- Lossless restoration and cryptographic SHA-256 integrity on all inputs
"""

import hashlib
import os
import pytest
from compression.adaptive import AdaptiveCompressor
from compression.rle import RLECompressor
from storage.container import Container


@pytest.fixture
def compressor():
    return AdaptiveCompressor()


class TestRepetitiveSelection:
    """Test suite targeting algorithm selection on repetitive and diverse data."""

    def test_case_a_short_repeated_bytes(self, compressor):
        """Case A: b'a' * 17

        A 17-byte input cannot compress once 50-byte header and metadata overhead
        are included. Verify that Raw Bypass (NONE) is selected to prevent expansion,
        and verify exact SHA-256 integrity.
        """
        data = b"a" * 17
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_a.txt", objective="max_compression"
        )

        assert selected_strat == "NONE", f"Expected Raw Bypass (NONE) for 17-byte input, got {selected_strat}"
        assert details["container_size"] > len(data)
        assert "storage expansion" in details["selection_rationale"].lower() or "raw bypass" in details["selection_rationale"].lower()

        # Lossless restoration check
        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_b_long_repeated_bytes(self, compressor):
        """Case B: b'a' * 10000

        With 10,000 identical bytes, RLE and Hybrid produce tiny payloads.
        Verify that:
        1. DEFLATE does NOT beat Hybrid/RLE in maximum compression.
        2. The candidate producing the smallest valid container is selected.
        3. Lossless restoration produces exact original bytes.
        """
        data = b"a" * 10000
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_b.txt", objective="max_compression"
        )

        # In max_compression, Hybrid or RLE should win over DEFLATE
        assert selected_strat in ("HYBRID", "RLE"), f"Expected HYBRID or RLE for 10000 'a's, got {selected_strat}"
        assert selected_strat != "DEFLATE", "DEFLATE should not win under max_compression when HYBRID/RLE is smaller"

        # Verify comparison matrix recorded sizes
        matrix = {r["Algorithm"]: r for r in details["comparison_matrix"]}
        assert "RLE" in matrix
        assert "HYBRID" in matrix
        assert "DEFLATE" in matrix

        winner_size = matrix[selected_strat]["Final Stored Size (B)"]
        deflate_size = matrix["DEFLATE"]["Final Stored Size (B)"]
        assert winner_size <= deflate_size, f"Selected {selected_strat} ({winner_size}B) should be <= DEFLATE ({deflate_size}B)"

        # Lossless restoration
        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_b2_pure_rle_winner(self, compressor):
        """Case B2: Alternating long runs where pure RLE produces the smallest container.

        Hybrid incurs Huffman tree metadata overhead that makes it larger than pure RLE.
        Verify that RLE is strictly selected.
        """
        data = b"A" * 300 + b"B" * 300 + b"C" * 300 + b"D" * 300 + b"E" * 300
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_b2.bin", objective="max_compression"
        )

        assert selected_strat == "RLE", f"Expected pure RLE to win, got {selected_strat}"
        matrix = {r["Algorithm"]: r for r in details["comparison_matrix"]}
        rle_size = matrix["RLE"]["Final Stored Size (B)"]
        hybrid_size = matrix["HYBRID"]["Final Stored Size (B)"]
        deflate_size = matrix["DEFLATE"]["Final Stored Size (B)"]

        assert rle_size < hybrid_size
        assert rle_size < deflate_size

        # Lossless restoration
        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_c_pattern_repeated_bytes(self, compressor):
        """Case C: b'abcabcabcabc' * 1000

        This input has a 3-byte repeating phrase.
        - RLE on alternating abc has run-lengths of 1 and would double the payload.
        - Dictionary/sliding-window compression (DEFLATE / LZ77) should excel.
        - Verify RLE does not cause bloat and DEFLATE or another dictionary algorithm is selected.
        """
        data = b"abcabcabcabc" * 1000
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_c.txt", objective="max_compression"
        )

        assert selected_strat in ("DEFLATE", "LZ77", "LZW"), f"Expected dictionary compressor, got {selected_strat}"
        matrix = {r["Algorithm"]: r for r in details["comparison_matrix"]}
        assert matrix["RLE"]["Space Saved (%)"] < 0, "RLE should expand on non-run data"

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_d_natural_language_text(self, compressor):
        """Case D: Natural-language text

        Evaluates candidate algorithms on realistic English text.
        """
        data = (
            b"CompressX is an intelligent adaptive lossless data compression system. "
            b"It profiles the entropy, byte distribution, run lengths, and skew of input data. "
            b"Based on empirical measurements, it selects the optimal compression strategy.\n"
        ) * 30

        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_d.txt", objective="max_compression"
        )

        assert selected_strat != "NONE"
        assert details["space_saving_pct"] > 50.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_e_server_logs(self, compressor):
        """Case E: Server access logs with high timestamp redundancy."""
        data = (
            b'192.168.1.105 - - [23/Oct/2026:14:02:19 +0000] "GET /api/v2/telemetry HTTP/1.1" 200 4812 "-" "Mozilla/5.0"\n'
            b'192.168.1.106 - - [23/Oct/2026:14:02:20 +0000] "POST /api/v2/telemetry HTTP/1.1" 201 1024 "-" "Mozilla/5.0"\n'
        ) * 40

        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_e.log", objective="balanced"
        )

        assert selected_strat in ("DEFLATE", "LZ77", "LZW", "BWT")
        assert details["space_saving_pct"] > 60.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_f_random_binary_data(self, compressor):
        """Case F: High-entropy pseudo-random binary data.

        Shannon entropy is near 8.0 bits/symbol. All compressors should fail to compress,
        and Raw Bypass (NONE) must be selected.
        """
        data = os.urandom(2500)
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="case_f.bin", objective="max_compression"
        )

        assert selected_strat == "NONE", f"Expected Raw Bypass (NONE) for random bytes, got {selected_strat}"
        assert "storage expansion" in details["selection_rationale"].lower() or "raw bypass" in details["selection_rationale"].lower()

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True
        assert decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_1_100k_repeated_a(self, compressor):
        """1. 100,000 repeated 'a' bytes."""
        data = b"a" * 100000
        container_bytes, selected_strat, pred, details = compressor.compress_adaptive(
            data, file_name="100k_a.bin", objective="max_compression"
        )
        assert selected_strat in ("DEFLATE", "HYBRID", "RLE")
        assert details["space_saving_pct"] > 95.0

        # Verify next-best algorithm and delta diagnostics
        assert "next_best_algorithm" in details
        assert details["size_delta_bytes"] >= 0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True and decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_2_100k_space_bytes(self, compressor):
        """2. 100,000 space bytes (whitespace runs)."""
        data = b" " * 100000
        profile, pred = compressor.analyze(data)
        assert profile["has_whitespace_runs"] is True
        assert profile["whitespace_run_bytes"] == 100000

        container_bytes, selected_strat, _, details = compressor.compress_adaptive(
            data, file_name="100k_spaces.txt", objective="max_compression"
        )
        assert selected_strat in ("DEFLATE", "HYBRID", "RLE")
        assert details["space_saving_pct"] > 95.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True and decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_3_repeated_newline_bytes(self, compressor):
        """3. Repeated newline bytes (whitespace runs)."""
        data = b"\n" * 10000
        profile, pred = compressor.analyze(data)
        assert profile["has_whitespace_runs"] is True
        assert profile["whitespace_run_bytes"] == 10000

        container_bytes, selected_strat, _, details = compressor.compress_adaptive(
            data, file_name="newlines.txt", objective="max_compression"
        )
        assert selected_strat in ("HYBRID", "RLE", "DEFLATE")
        assert details["space_saving_pct"] > 95.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True and decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_4_alternating_abab(self, compressor):
        """4. Alternating 'abababababab' (pattern repetition, no runs >= 2)."""
        data = b"ab" * 10000
        profile, pred = compressor.analyze(data)
        # Run length is 1, so no repeated runs
        assert profile["average_run_length"] == 1.0

        container_bytes, selected_strat, _, details = compressor.compress_adaptive(
            data, file_name="abab.txt", objective="max_compression"
        )
        # RLE must not win because it expands abab
        assert selected_strat != "RLE"
        assert selected_strat in ("DEFLATE", "LZ77", "LZW", "BWT")
        assert details["space_saving_pct"] > 95.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True and decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_5_repeated_words_and_paragraphs(self, compressor):
        """5. Repeated words and ordinary paragraphs."""
        paragraph = (
            b"CompressX is an intelligent lossless data compression engine. "
            b"It performs empirical content analysis across Shannon entropy, run-length distributions, "
            b"and frequency skew to select optimal compression strategies without heuristic bias.\n"
        )
        data = paragraph * 100
        container_bytes, selected_strat, _, details = compressor.compress_adaptive(
            data, file_name="article.txt", objective="max_compression"
        )
        assert selected_strat in ("DEFLATE", "LZ77", "LZW", "BWT")
        assert details["space_saving_pct"] > 80.0

        decomp, ok, msg, info = AdaptiveCompressor.decompress_container(container_bytes)
        assert ok is True and decomp == data
        assert hashlib.sha256(decomp).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_case_6_mixed_whitespace_and_text(self, compressor):
        """6. Mixed whitespace and text: 'aaaa\\n\\n\\n\\nbbbb' and separated spaces 'a a a a'."""
        # Subcase 6a: runs of letters separated by runs of newlines
        data_a = b"aaaa\n\n\n\nbbbb" * 200
        profile_a, _ = compressor.analyze(data_a)
        assert profile_a["has_whitespace_runs"] is True
        assert profile_a["average_run_length"] == 4.0

        c_a, strat_a, _, d_a = compressor.compress_adaptive(data_a, objective="max_compression")
        decomp_a, ok_a, _, _ = AdaptiveCompressor.decompress_container(c_a)
        assert ok_a and decomp_a == data_a

        # Subcase 6b: isolated spaces 'a a a a' where spaces do NOT form runs
        data_b = b"a a a a a a a a " * 200
        profile_b, _ = compressor.analyze(data_b)
        assert profile_b["has_whitespace_runs"] is False
        assert profile_b["average_run_length"] == 1.0

        c_b, strat_b, _, d_b = compressor.compress_adaptive(data_b, objective="max_compression")
        decomp_b, ok_b, _, _ = AdaptiveCompressor.decompress_container(c_b)
        assert ok_b and decomp_b == data_b

    def test_case_7_random_binary_data(self, compressor):
        """7. Random binary data (entropy ~ 8.0 bits/symbol)."""
        data = os.urandom(3000)
        c, strat, _, d = compressor.compress_adaptive(data, objective="max_compression")
        assert strat == "NONE", f"Expected Raw Bypass (NONE) for random bytes, got {strat}"
        decomp, ok, _, _ = AdaptiveCompressor.decompress_container(c)
        assert ok and decomp == data

    def test_case_8_empty_and_single_byte_files(self, compressor):
        """8. Empty and single-byte files."""
        # 8a: Empty file (0 bytes)
        c_0, s_0, _, d_0 = compressor.compress_adaptive(b"", objective="max_compression")
        assert s_0 == "NONE"
        decomp_0, ok_0, _, _ = AdaptiveCompressor.decompress_container(c_0)
        assert ok_0 and decomp_0 == b""

        # 8b: Single-byte file (1 byte)
        c_1, s_1, _, d_1 = compressor.compress_adaptive(b"Z", objective="max_compression")
        assert s_1 == "NONE"
        decomp_1, ok_1, _, _ = AdaptiveCompressor.decompress_container(c_1)
        assert ok_1 and decomp_1 == b"Z"


class TestRLECorrectness:
    """Detailed verification of RLE chunking, arbitrary binary data, and edge cases."""

    def test_rle_empty(self):
        assert RLECompressor.compress(b"") == b""
        assert RLECompressor.decompress(b"") == b""

    def test_rle_single_byte(self):
        encoded = RLECompressor.compress(b"\x42")
        assert encoded == bytes([1, 0x42])
        assert RLECompressor.decompress(encoded) == b"\x42"

    def test_rle_run_longer_than_255(self):
        """Verify runs exceeding 255 bytes are chunked into valid uint8 chunks."""
        # 600 bytes = 255 + 255 + 90
        data = b"\x7f" * 600
        encoded = RLECompressor.compress(data)
        assert len(encoded) == 6  # 3 pairs
        assert encoded == bytes([255, 0x7f, 255, 0x7f, 90, 0x7f])

        restored = RLECompressor.decompress(encoded)
        assert restored == data

    def test_rle_arbitrary_binary_including_zero(self):
        """Verify arbitrary binary data containing 0x00 and 0xFF compresses and restores losslessly."""
        data = bytes([0x00] * 300 + [0xFF] * 150 + [0x01, 0x02, 0x03] + [0x00] * 50)
        encoded = RLECompressor.compress(data)
        restored = RLECompressor.decompress(encoded)
        assert restored == data

    def test_rle_all_256_byte_values(self):
        """Verify that every possible byte value (0..255) in repeated pairs compresses losslessly."""
        data = bytearray()
        for b in range(256):
            data.extend(bytes([b] * (b % 10 + 1)))
        data_bytes = bytes(data)

        encoded = RLECompressor.compress(data_bytes)
        restored = RLECompressor.decompress(encoded)
        assert restored == data_bytes


class TestMultiObjectiveBehavior:
    """Verify objective modes: max_compression, balanced, fast."""

    def test_objectives_on_repetitive_data(self, compressor):
        data = b"a" * 10000

        # Max compression: strictly smallest stored container
        c_max, s_max, _, d_max = compressor.compress_adaptive(data, objective="max_compression")
        assert s_max in ("HYBRID", "RLE")

        # Fast: fastest encoding time among compressing candidates
        c_fast, s_fast, _, d_fast = compressor.compress_adaptive(data, objective="fast")
        # DEFLATE is C-accelerated and takes <0.0002s, so it should win fast mode
        assert s_fast == "DEFLATE"
        assert d_fast["encoding_time"] <= d_max["encoding_time"]

        # Balanced: weighs size 85% and speed 15%
        c_bal, s_bal, _, d_bal = compressor.compress_adaptive(data, objective="balanced")
        assert s_bal in ("HYBRID", "RLE")
