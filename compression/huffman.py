"""Huffman Coding lossless compression implementation.

Implements classical variable-length prefix coding based on symbol frequencies.
Frequently occurring symbols are assigned shorter bit codes, while less frequent
symbols are assigned longer bit codes.
"""

from collections import Counter
import heapq
from typing import Dict, Optional, Tuple


class HuffmanNode:
    """Node in the Huffman prefix tree."""

    def __init__(
        self,
        freq: int,
        symbol: Optional[int] = None,
        left: Optional["HuffmanNode"] = None,
        right: Optional["HuffmanNode"] = None,
    ):
        self.freq = freq
        self.symbol = symbol  # Byte integer value (0-255) if leaf, else None
        self.left = left
        self.right = right

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def __lt__(self, other: "HuffmanNode") -> bool:
        # Fallback comparison by frequency; heapq uses sequence counter to break ties
        return self.freq < other.freq


class HuffmanCompressor:
    """Byte-level Huffman compressor and decompressor."""

    @classmethod
    def _build_tree(cls, frequencies: Dict[int, int]) -> Optional[HuffmanNode]:
        """Build Huffman tree deterministically from symbol frequencies using a min-heap."""
        if not frequencies:
            return None

        # If only one symbol exists, create a single-leaf tree
        if len(frequencies) == 1:
            symbol, freq = next(iter(frequencies.items()))
            return HuffmanNode(freq=freq, symbol=symbol)

        # Min-heap elements: (frequency, counter, node)
        # Using counter ensures stable, deterministic tie-breaking without comparing nodes
        heap = []
        counter = 0

        # Sort symbols for reproducible initial heap ordering
        for symbol in sorted(frequencies.keys()):
            freq = frequencies[symbol]
            node = HuffmanNode(freq=freq, symbol=symbol)
            heapq.heappush(heap, (freq, counter, node))
            counter += 1

        while len(heap) > 1:
            freq1, _, left = heapq.heappop(heap)
            freq2, _, right = heapq.heappop(heap)

            merged = HuffmanNode(freq=freq1 + freq2, left=left, right=right)
            heapq.heappush(heap, (merged.freq, counter, merged))
            counter += 1

        return heap[0][2]

    @classmethod
    def _generate_codes(
        cls, root: Optional[HuffmanNode], current_code: str = "", code_map: Optional[Dict[int, str]] = None
    ) -> Dict[int, str]:
        """Traverse tree to generate prefix bit codes for each leaf symbol."""
        if code_map is None:
            code_map = {}

        if root is None:
            return code_map

        # Special case: single-node tree
        if root.is_leaf:
            code_map[root.symbol] = current_code if current_code else "0"
            return code_map

        if root.left:
            cls._generate_codes(root.left, current_code + "0", code_map)
        if root.right:
            cls._generate_codes(root.right, current_code + "1", code_map)

        return code_map

    @classmethod
    def compress(cls, data: bytes) -> Tuple[bytes, Dict[int, int], int]:
        """Compress byte sequence using Huffman coding.

        Args:
            data: Raw input bytes.

        Returns:
            Tuple of:
            - compressed_bytes: Packed bitstream
            - frequencies: Frequency table mapping byte (0-255) -> count
            - padding_bits: Number of padding bits added to the last byte (0-7)
        """
        if not data:
            return b"", {}, 0

        frequencies = dict(Counter(data))
        root = cls._build_tree(frequencies)
        code_map = cls._generate_codes(root)

        # Build bitstream
        bit_chunks = [code_map[b] for b in data]
        bitstream = "".join(bit_chunks)

        total_bits = len(bitstream)
        padding_bits = (8 - (total_bits % 8)) % 8
        if padding_bits > 0:
            bitstream += "0" * padding_bits

        # Pack bitstream into bytearray
        packed_bytes = bytearray()
        for i in range(0, len(bitstream), 8):
            byte_str = bitstream[i : i + 8]
            packed_bytes.append(int(byte_str, 2))

        return bytes(packed_bytes), frequencies, padding_bits

    @classmethod
    def decompress(
        cls, compressed_data: bytes, frequencies: Dict[int, int], padding_bits: int, original_size: Optional[int] = None
    ) -> bytes:
        """Decompress Huffman packed bytes back to original bytes.

        Args:
            compressed_data: Packed bitstream bytes.
            frequencies: Frequency table used during compression.
            padding_bits: Number of padding bits in the final byte.
            original_size: Expected original byte length (for strict verification if provided).

        Returns:
            Decompressed raw bytes.
        """
        if not compressed_data:
            return b""

        root = cls._build_tree(frequencies)
        if root is None:
            return b""

        # Convert bytes back to bit string
        bit_parts = [f"{b:08b}" for b in compressed_data]
        bitstream = "".join(bit_parts)

        # Remove padding bits
        if padding_bits > 0:
            bitstream = bitstream[:-padding_bits]

        # Single distinct symbol edge case
        if root.is_leaf:
            symbol = root.symbol
            # Each '0' represents one occurrence of the symbol
            count = len(bitstream)
            if original_size is not None:
                count = original_size
            return bytes([symbol]) * count

        # Traverse tree for general case
        decoded = bytearray()
        curr = root
        for bit in bitstream:
            curr = curr.left if bit == "0" else curr.right
            if curr.is_leaf:
                decoded.append(curr.symbol)
                curr = root
                if original_size is not None and len(decoded) == original_size:
                    break

        return bytes(decoded)
