"""Repetition analysis module for evaluating Run-Length Encoding suitability.

Calculates run characteristics including:
- Total runs
- Average run length
- Maximum run length
- Repetition percentage (fraction of data that forms runs of length >= 2)
- Run-Length Suitability Score
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class RepetitionStats:
    """Repetition statistics data structure."""
    total_runs: int
    average_run_length: float
    max_run_length: int
    repetition_percentage: float
    is_rle_promising: bool


def analyze_repetition(data: Union[bytes, str]) -> RepetitionStats:
    """Analyze consecutive repetitive symbols in the input data.

    Args:
        data: Input bytes or string.

    Returns:
        RepetitionStats dataclass with calculated metrics.
    """
    if not data:
        return RepetitionStats(
            total_runs=0,
            average_run_length=0.0,
            max_run_length=0,
            repetition_percentage=0.0,
            is_rle_promising=False,
        )

    if isinstance(data, str):
        data = data.encode("utf-8")

    total_len = len(data)
    total_runs = 0
    max_run_len = 0
    symbols_in_runs_ge_2 = 0

    i = 0
    while i < total_len:
        current_byte = data[i]
        run_len = 1
        while i + run_len < total_len and data[i + run_len] == current_byte:
            run_len += 1

        total_runs += 1
        if run_len > max_run_len:
            max_run_len = run_len

        if run_len >= 2:
            symbols_in_runs_ge_2 += run_len

        i += run_len

    avg_run_len = round(total_len / total_runs, 3)
    repetition_pct = round((symbols_in_runs_ge_2 / total_len) * 100.0, 2)

    # RLE encodes each run as 2 bytes: (count, symbol).
    # Compressed size under RLE will be total_runs * 2 bytes.
    # RLE is mathematically profitable if 2 * total_runs < total_len
    # which is equivalent to avg_run_len > 2.0.
    is_rle_promising = avg_run_len > 2.0 or repetition_pct > 35.0

    return RepetitionStats(
        total_runs=total_runs,
        average_run_length=avg_run_len,
        max_run_length=max_run_len,
        repetition_percentage=repetition_pct,
        is_rle_promising=is_rle_promising,
    )
