"""General statistical profiling module for input data streams.

Calculates:
- Total size in bytes
- Number of unique symbols (alphabet cardinality)
- Most frequent and least frequent symbols
- Frequency distribution skewness (Gini coefficient)
"""

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union


@dataclass
class DataStats:
    """Comprehensive statistical profile of input data."""
    size_bytes: int
    unique_symbols: int
    most_frequent: List[Tuple[int, str, int, float]]  # (byte_val, repr, count, pct)
    least_frequent: List[Tuple[int, str, int, float]]
    entropy: float
    gini_coefficient: float
    is_skewed: bool


def _safe_char_repr(byte_val: int) -> str:
    """Return printable representation of a byte."""
    if 32 <= byte_val <= 126:
        return chr(byte_val)
    if byte_val == 10:
        return "\\n"
    if byte_val == 13:
        return "\\r"
    if byte_val == 9:
        return "\\t"
    return f"0x{byte_val:02X}"


def calculate_gini(frequencies: List[int]) -> float:
    """Calculate Gini coefficient of symbol frequencies (0.0 = uniform, 1.0 = maximal skew)."""
    if not frequencies:
        return 0.0

    sorted_freqs = sorted(frequencies)
    n = len(sorted_freqs)
    total_sum = sum(sorted_freqs)

    if total_sum == 0:
        return 0.0

    cumulative_sum = 0
    gini_sum = 0
    for i, f in enumerate(sorted_freqs, 1):
        cumulative_sum += f
        gini_sum += (2 * i - n - 1) * f

    return round(gini_sum / (n * total_sum), 4)


def calculate_statistics(data: Union[bytes, str], entropy_val: float) -> DataStats:
    """Generate statistical summary of the input data."""
    if isinstance(data, str):
        data = data.encode("utf-8")

    total_len = len(data)
    if total_len == 0:
        return DataStats(
            size_bytes=0,
            unique_symbols=0,
            most_frequent=[],
            least_frequent=[],
            entropy=0.0,
            gini_coefficient=0.0,
            is_skewed=False,
        )

    counts = Counter(data)
    unique_symbols = len(counts)

    sorted_by_freq = counts.most_common()

    most_frequent = [
        (b, _safe_char_repr(b), count, round((count / total_len) * 100, 2))
        for b, count in sorted_by_freq[:5]
    ]

    least_frequent = [
        (b, _safe_char_repr(b), count, round((count / total_len) * 100, 2))
        for b, count in sorted_by_freq[-5:]
    ]

    gini = calculate_gini(list(counts.values()))
    # Gini > 0.4 or entropy < 6.5 indicates significant frequency skew favorable for Huffman
    is_skewed = gini > 0.35 or (entropy_val < 6.5 and unique_symbols > 1)

    return DataStats(
        size_bytes=total_len,
        unique_symbols=unique_symbols,
        most_frequent=most_frequent,
        least_frequent=least_frequent,
        entropy=entropy_val,
        gini_coefficient=gini,
        is_skewed=is_skewed,
    )
