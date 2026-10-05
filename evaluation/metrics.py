"""Evaluation metrics and integrity verification utilities."""

from dataclasses import dataclass
import hashlib
import time
import tracemalloc
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class CompressionMetrics:
    """Comprehensive performance metrics for a compression method."""
    algorithm: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    space_saving_pct: float
    encoding_time_sec: float
    decoding_time_sec: float
    peak_memory_kb: float
    integrity_verified: bool
    sha256_match: bool


def verify_integrity(original: bytes, decompressed: bytes) -> Tuple[bool, str, str]:
    """Verify that original and decompressed bytes are identical in length and SHA-256 digest."""
    h_orig = hashlib.sha256(original).hexdigest()
    h_decomp = hashlib.sha256(decompressed).hexdigest()
    is_identical = (h_orig == h_decomp) and (original == decompressed)
    return is_identical, h_orig, h_decomp


def calculate_metrics(
    algorithm_name: str,
    original_data: bytes,
    compress_fn: Callable[[bytes], Any],
    decompress_fn: Callable[[Any], bytes],
) -> Tuple[CompressionMetrics, bytes]:
    """Execute compression and decompression with high-resolution timing, memory tracking, and verification.

    Args:
        algorithm_name: Name of algorithm.
        original_data: Input uncompressed bytes.
        compress_fn: Function mapping bytes -> compressed object/bytes.
        decompress_fn: Function mapping compressed object/bytes -> decompressed bytes.

    Returns:
        Tuple of (CompressionMetrics, decompressed_bytes).
    """
    orig_size = len(original_data)

    # Start memory tracing and timing for compression
    tracemalloc.start()
    t0 = time.perf_counter()
    compressed_output = compress_fn(original_data)
    t_enc = time.perf_counter() - t0
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Determine compressed byte size
    if isinstance(compressed_output, bytes):
        comp_size = len(compressed_output)
    elif isinstance(compressed_output, tuple) and isinstance(compressed_output[0], bytes):
        comp_size = len(compressed_output[0])
    else:
        comp_size = len(bytes(compressed_output))

    # Measure decompression
    t0 = time.perf_counter()
    decompressed_data = decompress_fn(compressed_output)
    t_dec = time.perf_counter() - t0

    # Verification
    is_valid, h1, h2 = verify_integrity(original_data, decompressed_data)

    ratio = round(orig_size / comp_size, 3) if comp_size > 0 else 0.0
    space_saving = round(((orig_size - comp_size) / max(orig_size, 1)) * 100.0, 2)
    peak_mem_kb = round(peak_mem / 1024.0, 2)

    metrics = CompressionMetrics(
        algorithm=algorithm_name,
        original_size=orig_size,
        compressed_size=comp_size,
        compression_ratio=ratio,
        space_saving_pct=space_saving,
        encoding_time_sec=round(t_enc, 5),
        decoding_time_sec=round(t_dec, 5),
        peak_memory_kb=peak_mem_kb,
        integrity_verified=is_valid,
        sha256_match=(h1 == h2),
    )

    return metrics, decompressed_data
