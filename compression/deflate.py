"""DEFLATE compression and decompression implementation (RFC 1951).

Combines LZ77-style sliding window dictionary matching with Huffman coding.
Uses Python's standard library zlib engine configured for raw DEFLATE bitstreams.

Note:
- DEFLATE is the underlying compression algorithm defined in RFC 1951 (used in ZIP, GZIP, and PNG).
- This implementation produces raw DEFLATE byte streams without container wrapping.
"""

from typing import Optional
import zlib


class DeflateCompressor:
    """DEFLATE (LZ77 + Huffman) compressor using Python standard library zlib."""

    ENGINE = "Python Standard Library (zlib RFC 1951)"

    @classmethod
    def compress(cls, data: bytes, level: int = 9) -> bytes:
        """Compress arbitrary binary data using DEFLATE.

        Args:
            data: Input raw byte sequence.
            level: Compression level (1 = fastest, 6 = balanced, 9 = maximum).

        Returns:
            Raw DEFLATE compressed byte sequence.
        """
        if not data:
            return b""

        # wbits = -15 specifies raw DEFLATE stream without zlib header/trailer (RFC 1951)
        compressor = zlib.compressobj(level=level, method=zlib.DEFLATED, wbits=-15)
        compressed = compressor.compress(data) + compressor.flush()
        return compressed

    @classmethod
    def decompress(cls, data: bytes) -> bytes:
        """Decompress a raw DEFLATE byte sequence.

        Args:
            data: Compressed DEFLATE byte sequence.

        Returns:
            Exact reconstructed original byte sequence.
        """
        if not data:
            return b""

        # wbits = -15 matches the raw DEFLATE stream without zlib header/trailer
        decompressor = zlib.decompressobj(wbits=-15)
        decompressed = decompressor.decompress(data) + decompressor.flush()
        return decompressed
