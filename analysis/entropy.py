"""Shannon Entropy calculation module for data compressibility analysis.

Information theory defines Shannon Entropy H(X) as:
    H(X) = - Σ [p(x) * log2(p(x))]  for all x in alphabet

For 8-bit byte streams:
- Theoretical maximum entropy is 8.0 bits/symbol (uniformly distributed random data).
- Theoretical minimum entropy is 0.0 bits/symbol (stream of identical symbols).
- Lower entropy indicates higher statistical redundancy, implying greater potential
  for lossless compression (e.g. via Huffman coding).
"""

from collections import Counter
import math
from typing import Dict, Union


def calculate_entropy(data: Union[bytes, str]) -> float:
    """Calculate Shannon Entropy in bits per symbol.

    Args:
        data: Input bytes or text string.

    Returns:
        Entropy value in bits/symbol (0.0 to 8.0 for byte data).
    """
    if not data:
        return 0.0

    if isinstance(data, str):
        data = data.encode("utf-8")

    total_len = len(data)
    counts = Counter(data)
    entropy = 0.0

    for count in counts.values():
        p = count / total_len
        entropy -= p * math.log2(p)

    return round(entropy, 4)


def shannon_entropy(data: Union[bytes, str]) -> float:
    """Alias for calculate_entropy."""
    return calculate_entropy(data)


def theoretical_compression_limit(entropy: float, original_size_bytes: int) -> int:
    """Calculate theoretical minimum size in bytes according to Shannon's source coding theorem.

    According to Shannon, average code length L >= H(X).
    Minimum bits = H(X) * N
    Minimum bytes = ceil((H(X) * N) / 8)

    Args:
        entropy: Calculated Shannon entropy in bits/symbol.
        original_size_bytes: Size of original data in bytes.

    Returns:
        Theoretical lower bound on compressed size in bytes.
    """
    if original_size_bytes <= 0 or entropy <= 0:
        return 0
    min_bits = entropy * original_size_bytes
    return math.ceil(min_bits / 8.0)
