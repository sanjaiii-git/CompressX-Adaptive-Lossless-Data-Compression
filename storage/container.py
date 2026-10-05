"""Binary container format serializer and deserializer for .ahdc files.

Container Specification:
+-------------------------------------------------------------+
| Magic Number (4 bytes)       : 'AHDC'                      |
| Format Version (1 byte)      : uint8 (current = 1)          |
| Algorithm ID (1 byte)        : uint8 (0:NONE, 1:RLE,        |
|                                       2:HUFFMAN, 3:HYBRID)  |
| Original File Size (8 bytes) : uint64 (Big-Endian)          |
| SHA-256 Digest (32 bytes)    : Raw binary hash              |
| Metadata Length (4 bytes)    : uint32 (Big-Endian)          |
| Metadata Payload             : JSON-encoded bytes           |
| Payload Length (8 bytes)     : uint64 (Big-Endian)          |
| Compressed Payload           : Algorithm-encoded bitstream  |
+-------------------------------------------------------------+
"""

from dataclasses import dataclass
import hashlib
import struct
from typing import Optional, Tuple
from .metadata import Metadata


# Algorithm Constants
ALG_NONE = 0
ALG_RLE = 1
ALG_HUFFMAN = 2
ALG_HYBRID = 3

ALG_MAP = {
    "NONE": ALG_NONE,
    "RLE": ALG_RLE,
    "HUFFMAN": ALG_HUFFMAN,
    "HYBRID": ALG_HYBRID,
}

REV_ALG_MAP = {v: k for k, v in ALG_MAP.items()}


@dataclass
class CompressedPackage:
    """Represents the parsed content of an .ahdc container."""
    version: int
    algorithm_name: str
    original_size: int
    original_sha256: str
    metadata: Metadata
    payload: bytes


class Container:
    """Manages encoding and decoding of the binary container archive."""

    MAGIC = b"AHDC"
    VERSION = 1
    # Header format:
    # 4s (magic) + B (version) + B (alg) + Q (orig_size) + 32s (sha256) + I (meta_len)
    HEADER_STRUCT = struct.Struct(">4sBBQ32sI")

    @classmethod
    def pack(
        cls,
        algorithm: str,
        payload: bytes,
        original_data: bytes,
        metadata: Optional[Metadata] = None,
    ) -> bytes:
        """Pack compressed payload, metadata, and verification hash into a binary container.

        Args:
            algorithm: Algorithm identifier ('RLE', 'HUFFMAN', 'HYBRID', 'NONE').
            payload: Compressed payload bytes.
            original_data: Original uncompressed bytes (used to compute SHA-256 digest and size).
            metadata: Metadata object containing decompression parameters.

        Returns:
            Packaged binary container bytes.
        """
        alg_id = ALG_MAP.get(algorithm.upper(), ALG_NONE)
        original_size = len(original_data)
        sha256_digest = hashlib.sha256(original_data).digest()

        meta = metadata or Metadata()
        meta_bytes = meta.to_json_bytes()
        meta_len = len(meta_bytes)

        payload_len = len(payload)

        # Build header
        header = cls.HEADER_STRUCT.pack(
            cls.MAGIC,
            cls.VERSION,
            alg_id,
            original_size,
            sha256_digest,
            meta_len,
        )

        # Pack payload length (uint64)
        payload_len_bytes = struct.pack(">Q", payload_len)

        return header + meta_bytes + payload_len_bytes + payload

    @classmethod
    def unpack(cls, container_bytes: bytes) -> CompressedPackage:
        """Unpack binary container into metadata, payload, and integrity attributes.

        Args:
            container_bytes: Raw bytes read from an .ahdc file.

        Returns:
            CompressedPackage with unpacked components.

        Raises:
            ValueError: If container format is corrupt or unsupported.
        """
        header_size = cls.HEADER_STRUCT.size
        if len(container_bytes) < header_size + 8:
            raise ValueError("Corrupt file: File is smaller than minimum container header.")

        magic, version, alg_id, original_size, sha256_bytes, meta_len = cls.HEADER_STRUCT.unpack(
            container_bytes[:header_size]
        )

        if magic != cls.MAGIC:
            raise ValueError(f"Invalid format: Magic number '{magic.decode('ascii', errors='ignore')}' does not match 'AHDC'.")

        if version != cls.VERSION:
            raise ValueError(f"Unsupported container version: {version}. Expected version: {cls.VERSION}.")

        # Read metadata
        meta_start = header_size
        meta_end = meta_start + meta_len
        if len(container_bytes) < meta_end + 8:
            raise ValueError("Corrupt file: Incomplete metadata block.")

        meta_raw = container_bytes[meta_start:meta_end]
        metadata = Metadata.from_json_bytes(meta_raw)

        # Read payload length
        payload_len = struct.unpack(">Q", container_bytes[meta_end : meta_end + 8])[0]
        payload_start = meta_end + 8
        payload = container_bytes[payload_start : payload_start + payload_len]

        if len(payload) != payload_len:
            raise ValueError(
                f"Corrupt payload: Expected {payload_len} bytes but found {len(payload)} bytes."
            )

        alg_name = REV_ALG_MAP.get(alg_id, "UNKNOWN")
        original_sha256_hex = sha256_bytes.hex()

        return CompressedPackage(
            version=version,
            algorithm_name=alg_name,
            original_size=original_size,
            original_sha256=original_sha256_hex,
            metadata=metadata,
            payload=payload,
        )
