"""Compression module providing lossless compression algorithms and the adaptive orchestrator."""

try:
    from .rle import RLECompressor
    from .huffman import HuffmanCompressor
    from .hybrid import HybridCompressor
    from .lz77 import LZ77Compressor
    from .deflate import DeflateCompressor
    from .lzw import LZWCompressor
    from .bwt import BWTCompressor
    from .adaptive import AdaptiveCompressor
except (ImportError, ValueError):
    from compression.rle import RLECompressor
    from compression.huffman import HuffmanCompressor
    from compression.hybrid import HybridCompressor
    from compression.lz77 import LZ77Compressor
    from compression.deflate import DeflateCompressor
    from compression.lzw import LZWCompressor
    from compression.bwt import BWTCompressor
    from compression.adaptive import AdaptiveCompressor

__all__ = [
    "RLECompressor",
    "HuffmanCompressor",
    "HybridCompressor",
    "LZ77Compressor",
    "DeflateCompressor",
    "LZWCompressor",
    "BWTCompressor",
    "AdaptiveCompressor",
]

