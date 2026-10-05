"""Metadata representation for the Adaptive Hybrid Data Compression container format."""

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, Optional


@dataclass
class Metadata:
    """Algorithm-specific and file-level metadata stored inside the container."""
    file_name: str = ""
    file_extension: str = ""
    padding_bits: int = 0
    intermediate_size: int = 0
    frequencies: Dict[str, int] = field(default_factory=dict)  # str(byte_int) -> count
    extra_attributes: Dict[str, Any] = field(default_factory=dict)

    def to_json_bytes(self) -> bytes:
        """Serialize metadata object to UTF-8 encoded JSON bytes."""
        data = asdict(self)
        return json.dumps(data, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_json_bytes(cls, raw_bytes: bytes) -> "Metadata":
        """Deserialize metadata object from UTF-8 JSON bytes."""
        if not raw_bytes:
            return cls()
        data = json.loads(raw_bytes.decode("utf-8"))
        return cls(
            file_name=data.get("file_name", ""),
            file_extension=data.get("file_extension", ""),
            padding_bits=data.get("padding_bits", 0),
            intermediate_size=data.get("intermediate_size", 0),
            frequencies={str(k): int(v) for k, v in data.get("frequencies", {}).items()},
            extra_attributes=data.get("extra_attributes", {}),
        )

    def get_int_frequencies(self) -> Dict[int, int]:
        """Convert string keys in frequency map back to integer byte values (0-255)."""
        return {int(k): v for k, v in self.frequencies.items()}
