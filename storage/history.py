"""Compression job history manager for CompressX.

Provides lightweight, persistent local storage of compression operations in JSON format.
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


def load_history() -> List[Dict[str, Any]]:
    """Load history records from disk."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(records: List[Dict[str, Any]]) -> None:
    """Save history records to disk."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except Exception:
        pass


def add_history_entry(
    file_name: str,
    original_size: int,
    compressed_size: int,
    compression_ratio: float,
    space_saved_pct: float,
    algorithm: str,
    encoding_time_sec: float,
    decoding_time_sec: float,
    integrity_status: str,
    sha256_hash: str,
) -> Dict[str, Any]:
    """Add a new compression job record to persistent history."""
    records = load_history()
    
    entry = {
        "id": len(records) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": file_name,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": round(compression_ratio, 3),
        "space_saved_pct": round(space_saved_pct, 2),
        "algorithm": algorithm,
        "encoding_time_sec": round(encoding_time_sec, 5),
        "decoding_time_sec": round(decoding_time_sec, 5),
        "integrity_status": integrity_status,
        "sha256_hash": sha256_hash,
    }
    
    # Prepend newest entry to the top
    records.insert(0, entry)
    # Keep last 50 entries
    records = records[:50]
    save_history(records)
    return entry


def clear_history() -> None:
    """Clear all stored history records."""
    save_history([])
