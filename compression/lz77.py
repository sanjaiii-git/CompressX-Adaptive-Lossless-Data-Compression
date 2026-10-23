"""LZ77 sliding-window dictionary lossless compression implementation.

Implements byte-oriented LZ77 with:
- Configurable sliding window size (default 4096 bytes = 12-bit offset)
- Lookahead buffer (length 3 to 18 bytes = 4-bit length)
- Hash-indexed match searching for high-throughput encoding
- Flag-byte bitstream packing: 8 items per flag byte
  - Literal: 1 byte
  - Match: 2 bytes (12 bits offset, 4 bits length)
- Exact lossless inverse reconstruction for arbitrary binary data
"""

import struct
from typing import Tuple


class LZ77Compressor:
    """Sliding-window dictionary compressor (LZ77)."""

    WINDOW_SIZE = 4096
    MIN_MATCH = 3
    MAX_MATCH = 18

    @classmethod
    def compress(cls, data: bytes) -> bytes:
        """Compress arbitrary binary data using LZ77.

        Args:
            data: Input raw byte sequence.

        Returns:
            Compressed byte sequence with flag-byte framing.
        """
        if not data:
            return b""

        n = len(data)
        pos = 0
        output = bytearray()

        # Hash table mapping 3-byte prefixes to their latest position in the window
        # Key: 3-byte prefix (int), Value: list of recent positions
        pos_hash = {}

        tokens = []  # list of (is_match, offset, length, literal_byte)

        while pos < n:
            best_offset = 0
            best_len = 0

            # Only search for matches if we have at least MIN_MATCH bytes remaining
            if pos + cls.MIN_MATCH <= n:
                prefix = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
                window_start = max(0, pos - cls.WINDOW_SIZE)

                if prefix in pos_hash:
                    # Check recent candidates in window
                    candidates = pos_hash[prefix]
                    # Filter out candidates outside current window
                    valid_candidates = [c for c in candidates if c >= window_start]
                    pos_hash[prefix] = valid_candidates

                    max_possible = min(cls.MAX_MATCH, n - pos)
                    for cand in reversed(valid_candidates):
                        match_len = 0
                        while (
                            match_len < max_possible
                            and data[cand + match_len] == data[pos + match_len]
                        ):
                            match_len += 1

                        if match_len > best_len:
                            best_len = match_len
                            best_offset = pos - cand
                            if best_len == cls.MAX_MATCH:
                                break

            if best_len >= cls.MIN_MATCH:
                tokens.append((True, best_offset, best_len, 0))
                # Update hash table for consumed positions
                for i in range(best_len):
                    if pos + i + cls.MIN_MATCH <= n:
                        p = (data[pos + i] << 16) | (data[pos + i + 1] << 8) | data[pos + i + 2]
                        if p not in pos_hash:
                            pos_hash[p] = []
                        pos_hash[p].append(pos + i)
                pos += best_len
            else:
                lit = data[pos]
                tokens.append((False, 0, 0, lit))
                if pos + cls.MIN_MATCH <= n:
                    p = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2]
                    if p not in pos_hash:
                        pos_hash[p] = []
                    pos_hash[p].append(pos)
                pos += 1

        # Pack tokens into bytes with flag bytes (1 flag byte per 8 items)
        for i in range(0, len(tokens), 8):
            chunk = tokens[i : i + 8]
            flag = 0
            payload = bytearray()
            for bit_idx, (is_match, offset, length, lit) in enumerate(chunk):
                if is_match:
                    flag |= 1 << bit_idx
                    # Pack 12-bit offset (0..4095) and 4-bit length (0..15 for len 3..18)
                    # offset_val = offset - 1 (0..4095)
                    # len_val = length - 3 (0..15)
                    code = ((offset - 1) & 0x0FFF) | (((length - cls.MIN_MATCH) & 0x0F) << 12)
                    payload.extend(struct.pack(">H", code))
                else:
                    payload.append(lit)

            output.append(flag)
            output.extend(payload)

        return bytes(output)

    @classmethod
    def decompress(cls, data: bytes) -> bytes:
        """Decompress an LZ77-compressed byte sequence.

        Args:
            data: Compressed byte sequence.

        Returns:
            Exact reconstructed original byte sequence.
        """
        if not data:
            return b""

        output = bytearray()
        idx = 0
        n = len(data)

        while idx < n:
            flag = data[idx]
            idx += 1

            for bit_idx in range(8):
                if idx >= n:
                    break
                is_match = bool(flag & (1 << bit_idx))

                if is_match:
                    if idx + 2 > n:
                        break
                    code = struct.unpack(">H", data[idx : idx + 2])[0]
                    idx += 2
                    offset = (code & 0x0FFF) + 1
                    length = ((code >> 12) & 0x0F) + cls.MIN_MATCH

                    start = len(output) - offset
                    for _ in range(length):
                        output.append(output[start])
                        start += 1
                else:
                    output.append(data[idx])
                    idx += 1

        return bytes(output)
