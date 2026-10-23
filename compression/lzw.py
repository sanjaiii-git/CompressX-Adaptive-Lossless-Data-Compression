"""LZW (Lempel–Ziv–Welch) dictionary lossless compression implementation.

Implements byte-oriented LZW with:
- Initial 256 single-byte vocabulary dictionary (codes 0 to 255)
- Dynamic phrase dictionary with bounded maximum size (default 4096 entries)
- 16-bit big-endian integer code packing (>H)
- Robust KwKwK edge-case handling during inverse decoding
- Exact lossless reconstruction on arbitrary binary byte streams
"""

import struct
from typing import List


class LZWCompressor:
    """Lempel-Ziv-Welch (LZW) dictionary compressor."""

    MAX_DICT_SIZE = 4096

    @classmethod
    def compress(cls, data: bytes) -> bytes:
        """Compress arbitrary binary data using LZW.

        Args:
            data: Input raw byte sequence.

        Returns:
            Compressed byte sequence containing 16-bit packed codes.
        """
        if not data:
            return b""

        # Initialize dictionary with all 256 single-byte sequences
        # Key: bytes, Value: code (int)
        dictionary = {bytes([i]): i for i in range(256)}
        next_code = 256

        current = bytearray()
        codes = []

        for byte in data:
            current.append(byte)
            cur_bytes = bytes(current)
            if cur_bytes in dictionary:
                pass
            else:
                # Output code for prefix (all except last byte)
                prefix = cur_bytes[:-1]
                codes.append(dictionary[prefix])

                # Add new sequence to dictionary if under maximum limit
                if next_code < cls.MAX_DICT_SIZE:
                    dictionary[cur_bytes] = next_code
                    next_code += 1

                # Reset current to the new byte
                current = bytearray([byte])

        if current:
            codes.append(dictionary[bytes(current)])

        # Pack codes as 16-bit big-endian unsigned integers
        output = bytearray()
        for code in codes:
            output.extend(struct.pack(">H", code))

        return bytes(output)

    @classmethod
    def decompress(cls, data: bytes) -> bytes:
        """Decompress an LZW-compressed byte sequence.

        Args:
            data: Compressed byte sequence containing 16-bit packed codes.

        Returns:
            Exact reconstructed original byte sequence.
        """
        if not data:
            return b""

        # Unpack 16-bit codes
        if len(data) % 2 != 0:
            raise ValueError(f"Corrupted LZW payload: length {len(data)} is not a multiple of 2")

        num_codes = len(data) // 2
        codes = [struct.unpack_from(">H", data, i * 2)[0] for i in range(num_codes)]

        if not codes:
            return b""

        # Initialize dictionary with all 256 single-byte sequences
        dictionary = {i: bytes([i]) for i in range(256)}
        next_code = 256

        output = bytearray()

        # First code
        first_code = codes[0]
        if first_code not in dictionary:
            raise ValueError(f"Invalid initial LZW code: {first_code}")

        current_entry = dictionary[first_code]
        output.extend(current_entry)

        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == next_code:
                # Special KwKwK edge case: code not yet in dictionary
                entry = current_entry + bytes([current_entry[0]])
            else:
                raise ValueError(f"Corrupted LZW code: {code} not in dictionary (max {next_code})")

            output.extend(entry)

            # Add previous entry + first byte of new entry to dictionary
            if next_code < cls.MAX_DICT_SIZE:
                dictionary[next_code] = current_entry + bytes([entry[0]])
                next_code += 1

            current_entry = entry

        return bytes(output)
