"""Python runtime environment customizer for CompressX.

Resolves Python 3.14+ PEP 784 collision:
Python 3.14 introduced a standard library package named 'compression' (PEP 784).
This file executes automatically during Python startup to ensure our local 'compression'
package is bound into sys.modules ahead of the Python 3.14 standard library.
"""

import sys
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
local_compression_dir = ROOT_DIR / "compression"

if local_compression_dir.is_dir():
    init_file = local_compression_dir / "__init__.py"
    if init_file.exists():
        spec = importlib.util.spec_from_file_location(
            "compression",
            str(init_file),
            submodule_search_locations=[str(local_compression_dir)],
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["compression"] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception:
                pass

        # Pre-bind submodules into sys.modules
        for sub in ["rle", "huffman", "hybrid", "lz77", "deflate", "lzw", "bwt", "adaptive"]:
            sub_file = local_compression_dir / f"{sub}.py"
            if sub_file.exists():
                sub_spec = importlib.util.spec_from_file_location(f"compression.{sub}", str(sub_file))
                if sub_spec and sub_spec.loader:
                    sub_mod = importlib.util.module_from_spec(sub_spec)
                    sys.modules[f"compression.{sub}"] = sub_mod
                    try:
                        sub_spec.loader.exec_module(sub_mod)
                        if "compression" in sys.modules:
                            setattr(sys.modules["compression"], sub, sub_mod)
                    except Exception:
                        pass
