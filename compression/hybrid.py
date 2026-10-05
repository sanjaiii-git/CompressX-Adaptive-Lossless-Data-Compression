"""Hybrid RLE + Huffman lossless compression implementation.

Combines Run-Length Encoding and Huffman Coding in a sequential two-stage pipeline:
1. Stage 1 (RLE): Collapses consecutive repeating symbols into (count, value) runs.
2. Stage 2 (Huffman): Takes the intermediate run stream and applies variable-length
   prefix coding based on the resulting symbol distribution.

Decompression performs the exact inverse operations in reverse order:
1. Stage 1: Huffman decoding to restore intermediate RLE stream.
2. Stage 2: RLE decoding to restore original byte sequence.
"""

from typing import Dict, Optional, Tuple
from .rle import RLECompressor
from .huffman import HuffmanCompressor


class HybridCompressor:
    """Two-stage Hybrid compressor: RLE followed by Huffman coding."""

    @classmethod
    def compress(cls, data: bytes) -> Tuple[bytes, Dict[int, int], int, int]:
        """Compress byte sequence using RLE followed by Huffman coding.

        Args:
            data: Raw input bytes.

        Returns:
            Tuple of:
            - compressed_bytes: Packed Huffman bitstream
            - frequencies: Frequency table of intermediate RLE bytes
            - padding_bits: Bit padding added to the final byte (0-7)
            - intermediate_size: Length in bytes of the intermediate RLE representation
        """
        if not data:
            return b"", {}, 0, 0

        # Stage 1: Run-Length Encoding
        rle_intermediate = RLECompressor.compress(data)

        # Stage 2: Huffman Coding on intermediate stream
        huffman_payload, frequencies, padding_bits = HuffmanCompressor.compress(rle_intermediate)

        return huffman_payload, frequencies, padding_bits, len(rle_intermediate)

    @classmethod
    def decompress(
        cls,
        compressed_data: bytes,
        frequencies: Dict[int, int],
        padding_bits: int,
        intermediate_size: Optional[int] = None,
    ) -> bytes:
        """Decompress Hybrid bitstream back to original bytes.

        Args:
            compressed_data: Packed Huffman bitstream.
            frequencies: Frequency table of intermediate RLE stream.
            padding_bits: Number of padding bits in the final byte.
            intermediate_size: Expected byte length of the intermediate RLE stream.

        Returns:
            Decompressed original bytes.
        """
        if not compressed_data:
            return b""

        # Stage 1: Invert Huffman
        rle_intermediate = HuffmanCompressor.decompress(
            compressed_data, frequencies, padding_bits, original_size=intermediate_size
        )

        # Stage 2: Invert RLE
        original_data = RLECompressor.decompress(rle_intermediate)

        return original_data
