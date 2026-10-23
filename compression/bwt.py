"""Burrows–Wheeler Transform (BWT) with Move-to-Front (MTF) and RLE compression.

Implements a reversible three-stage transform pipeline:
1. Stage 1 (BWT): Block-based Burrows–Wheeler Transform permutes symbols to group
   identical contexts together.
2. Stage 2 (MTF): Move-To-Front coding converts grouped characters into a stream
   dominated by low integer values (especially zero).
3. Stage 3 (RLE): Run-length encodes the MTF zero-runs for compact storage.

Decompression performs the exact inverse stages in reverse:
1. Inverse RLE restores the MTF stream.
2. Inverse MTF restores the BWT permuted block.
3. Inverse BWT (LF-mapping) restores the exact original byte sequence.
"""

import struct
from typing import List, Tuple


class BWTCompressor:
    """Block-based Burrows-Wheeler Transform compressor with MTF and RLE."""

    BLOCK_SIZE = 16384  # 16 KB block size for optimal throughput and bounded memory

    @classmethod
    def _bwt_block(cls, data: bytes) -> Tuple[bytes, int]:
        """Perform BWT on a single block of bytes."""
        if not data:
            return b"", 0
        n = len(data)
        rotations = sorted(range(n), key=lambda i: data[i:] + data[:i])
        orig_idx = rotations.index(0)
        bwt_bytes = bytes(data[(i + n - 1) % n] for i in rotations)
        return bwt_bytes, orig_idx

    @classmethod
    def _ibwt_block(cls, bwt_bytes: bytes, orig_idx: int) -> bytes:
        """Perform inverse BWT on a single block using LF-mapping."""
        if not bwt_bytes:
            return b""
        n = len(bwt_bytes)
        counts = [0] * 256
        for b in bwt_bytes:
            counts[b] += 1

        first = [0] * 256
        total = 0
        for i in range(256):
            first[i] = total
            total += counts[i]

        T = [0] * n
        rank = [0] * 256
        for i, b in enumerate(bwt_bytes):
            T[first[b] + rank[b]] = i
            rank[b] += 1

        res = bytearray(n)
        idx = orig_idx
        for i in range(n):
            idx = T[idx]
            res[i] = bwt_bytes[idx]
        return bytes(res)

    @classmethod
    def _mtf_encode(cls, data: bytes) -> bytes:
        """Move-To-Front encode a byte sequence."""
        alphabet = bytearray(range(256))
        res = bytearray(len(data))
        for i, b in enumerate(data):
            idx = alphabet.index(b)
            res[i] = idx
            alphabet.pop(idx)
            alphabet.insert(0, b)
        return bytes(res)

    @classmethod
    def _mtf_decode(cls, data: bytes) -> bytes:
        """Inverse Move-To-Front decode a byte sequence."""
        alphabet = bytearray(range(256))
        res = bytearray(len(data))
        for i, idx in enumerate(data):
            b = alphabet[idx]
            res[i] = b
            alphabet.pop(idx)
            alphabet.insert(0, b)
        return bytes(res)

    @classmethod
    def _rle_zeros(cls, data: bytes) -> bytes:
        """Compress zero-runs in MTF data using escape-byte run-length encoding."""
        # 0x00 is escaped: [0x00, count] where count is 1..255
        out = bytearray()
        i = 0
        n = len(data)
        while i < n:
            b = data[i]
            if b == 0:
                run_len = 0
                while i < n and data[i] == 0 and run_len < 255:
                    run_len += 1
                    i += 1
                out.append(0)
                out.append(run_len)
            else:
                out.append(b)
                i += 1
        return bytes(out)

    @classmethod
    def _irle_zeros(cls, data: bytes) -> bytes:
        """Decompress zero-runs in MTF data."""
        out = bytearray()
        i = 0
        n = len(data)
        while i < n:
            b = data[i]
            if b == 0:
                if i + 1 >= n:
                    break
                run_len = data[i + 1]
                out.extend(b"\x00" * run_len)
                i += 2
            else:
                out.append(b)
                i += 1
        return bytes(out)

    @classmethod
    def compress(cls, data: bytes) -> bytes:
        """Compress arbitrary binary data using block-based BWT + MTF + RLE.

        Args:
            data: Input raw byte sequence.

        Returns:
            Compressed byte stream with block headers.
        """
        if not data:
            return b""

        output = bytearray()
        # Number of blocks
        num_blocks = (len(data) + cls.BLOCK_SIZE - 1) // cls.BLOCK_SIZE
        output.extend(struct.pack(">I", num_blocks))

        for block_idx in range(num_blocks):
            start = block_idx * cls.BLOCK_SIZE
            end = min(start + cls.BLOCK_SIZE, len(data))
            block = data[start:end]

            # Stage 1: BWT
            bwt_bytes, orig_idx = cls._bwt_block(block)

            # Stage 2: MTF
            mtf_bytes = cls._mtf_encode(bwt_bytes)

            # Stage 3: Zero-run RLE
            compressed_block = cls._rle_zeros(mtf_bytes)

            # Block header: orig_idx (uint32) + original block len (uint32) + compressed len (uint32)
            output.extend(struct.pack(">III", orig_idx, len(block), len(compressed_block)))
            output.extend(compressed_block)

        return bytes(output)

    @classmethod
    def decompress(cls, data: bytes) -> bytes:
        """Decompress a BWT-compressed byte stream.

        Args:
            data: Compressed byte stream.

        Returns:
            Exact reconstructed original byte sequence.
        """
        if not data:
            return b""

        if len(data) < 4:
            raise ValueError("Corrupted BWT data: missing block count header")

        num_blocks = struct.unpack(">I", data[:4])[0]
        offset = 4
        result = bytearray()

        for _ in range(num_blocks):
            if offset + 12 > len(data):
                raise ValueError("Corrupted BWT data: truncated block header")

            orig_idx, orig_len, comp_len = struct.unpack(">III", data[offset : offset + 12])
            offset += 12

            if offset + comp_len > len(data):
                raise ValueError("Corrupted BWT data: truncated block payload")

            comp_block = data[offset : offset + comp_len]
            offset += comp_len

            # Inverse Stage 3: IRLE
            mtf_bytes = cls._irle_zeros(comp_block)

            # Inverse Stage 2: IMTF
            bwt_bytes = cls._mtf_decode(mtf_bytes)

            # Inverse Stage 1: IBWT
            block = cls._ibwt_block(bwt_bytes, orig_idx)

            if len(block) != orig_len:
                raise ValueError(
                    f"BWT reconstruction length mismatch: expected {orig_len}, got {len(block)}"
                )

            result.extend(block)

        return bytes(result)
