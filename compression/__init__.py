"""Compression module providing lossless compression algorithms and the adaptive orchestrator."""

from .rle import RLECompressor
from .huffman import HuffmanCompressor
from .hybrid import HybridCompressor
from .lz77 import LZ77Compressor
from .deflate import DeflateCompressor
from .lzw import LZWCompressor
from .bwt import BWTCompressor
from .adaptive import AdaptiveCompressor

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
