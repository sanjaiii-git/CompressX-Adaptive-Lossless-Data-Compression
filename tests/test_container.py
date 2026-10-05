"""Unit tests for binary container serialization and unpacking."""

import pytest
from storage.container import Container
from storage.metadata import Metadata


def test_container_pack_unpack_roundtrip():
    original_data = b"Hello, Adaptive Compression Container!"
    payload = b"FAKE_COMPRESSED_PAYLOAD_12345"
    meta = Metadata(file_name="test.txt", padding_bits=3, intermediate_size=120)

    container_bytes = Container.pack("HUFFMAN", payload, original_data, meta)
    pkg = Container.unpack(container_bytes)

    assert pkg.version == Container.VERSION
    assert pkg.algorithm_name == "HUFFMAN"
    assert pkg.original_size == len(original_data)
    assert pkg.payload == payload
    assert pkg.metadata.file_name == "test.txt"
    assert pkg.metadata.padding_bits == 3
    assert pkg.metadata.intermediate_size == 120


def test_container_corrupted_magic():
    bad_bytes = b"XXXX" + b"\x00" * 60
    with pytest.raises(ValueError, match="Invalid format"):
        Container.unpack(bad_bytes)


def test_container_truncated():
    with pytest.raises(ValueError, match="Corrupt file"):
        Container.unpack(b"AHDC\x01")
