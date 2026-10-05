"""Run-Length Encoding (RLE) lossless compression implementation.

RLE is a simple form of data compression in which consecutive data elements
(runs) are stored as a single data value and count. This is most effective on
data that contains many repeated values (e.g., simple graphics, repetitive logs).
"""

from typing import Tuple


class RLECompressor:
    """Byte-level Run-Length Encoding compressor and decompressor."""

    MAX_RUN_LENGTH = 255  # Stored in a single unsigned byte (uint8)

    @classmethod
    def compress(cls, data: bytes) -> bytes:
        """Compress a byte sequence using Run-Length Encoding.

        Format: Each run is stored as [count: 1 byte (1-255), byte_value: 1 byte].
        If a run exceeds 255 bytes, it is split into chunks of at most 255.

        Args:
            data: Raw input bytes.

        Returns:
            Compressed bytes.
        """
        if not data:
            return b""

        output = bytearray()
        data_len = len(data)
        i = 0

        while i < data_len:
            current_byte = data[i]
            run_length = 1

            # Count consecutive identical bytes up to MAX_RUN_LENGTH
            while (
                i + run_length < data_len
                and data[i + run_length] == current_byte
                and run_length < cls.MAX_RUN_LENGTH
            ):
                run_length += 1

            # Append count and byte value
            output.append(run_length)
            output.append(current_byte)

            i += run_length

        return bytes(output)

    @classmethod
    def decompress(cls, compressed_data: bytes) -> bytes:
        """Decompress RLE encoded byte sequence.

        Args:
            compressed_data: RLE compressed bytes (pairs of [count, value]).

        Returns:
            Decompressed raw bytes.

        Raises:
            ValueError: If compressed_data format is invalid (odd number of bytes).
        """
        if not compressed_data:
            return b""

        if len(compressed_data) % 2 != 0:
            raise ValueError("Corrupt RLE data: compressed length must be an even number of bytes.")

        output = bytearray()
        for i in range(0, len(compressed_data), 2):
            count = compressed_data[i]
            val = compressed_data[i + 1]
            if count == 0:
                raise ValueError("Corrupt RLE data: run length cannot be 0.")
            output.extend(bytes([val]) * count)

        return bytes(output)

    @classmethod
    def encode_text_readable(cls, text: str) -> str:
        """Human-readable RLE representation for demonstration (e.g. 'AAAAAAABBBCC' -> 'A7B3C2').

        Args:
            text: Input string.

        Returns:
            Formatted RLE string.
        """
        if not text:
            return ""

        result = []
        i = 0
        n = len(text)
        while i < n:
            char = text[i]
            count = 1
            while i + count < n and text[i + count] == char:
                count += 1
            result.append(f"{char}{count}")
            i += count
        return "".join(result)

    @classmethod
    def decode_text_readable(cls, encoded_text: str) -> str:
        """Decode a human-readable RLE string (e.g. 'A7B3C2' -> 'AAAAAAABBBCC').

        Args:
            encoded_text: Formatted RLE string.

        Returns:
            Original decoded string.
        """
        import re
        if not encoded_text:
            return ""

        pattern = re.compile(r"([a-zA-Z0-9_ \t\n\r])(\d+)")
        matches = pattern.findall(encoded_text)
        result = []
        for char, count in matches:
            result.append(char * int(count))
        return "".join(result)
