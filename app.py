"""Root entrypoint proxy for Streamlit Cloud and standard deployments.

Forwards execution to app/app.py while ensuring proper sys.path resolution.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
root_str = str(ROOT_DIR)
if root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)

# Pre-bind local compression package to avoid Python 3.14 PEP 784 collision
local_comp_dir = ROOT_DIR / "compression"
if local_comp_dir.is_dir():
    init_path = local_comp_dir / "__init__.py"
    if init_path.exists():
        spec = importlib.util.spec_from_file_location(
            "compression", str(init_path), submodule_search_locations=[str(local_comp_dir)]
        )
        if spec and spec.loader:
            comp_mod = importlib.util.module_from_spec(spec)
            sys.modules["compression"] = comp_mod
            try:
                spec.loader.exec_module(comp_mod)
            except Exception:
                pass

    for sub in ["rle", "huffman", "hybrid", "lz77", "deflate", "lzw", "bwt", "adaptive"]:
        sub_path = local_comp_dir / f"{sub}.py"
        if sub_path.exists():
            s_spec = importlib.util.spec_from_file_location(f"compression.{sub}", str(sub_path))
            if s_spec and s_spec.loader:
                s_mod = importlib.util.module_from_spec(s_spec)
                sys.modules[f"compression.{sub}"] = s_mod
                try:
                    s_spec.loader.exec_module(s_mod)
                    if "compression" in sys.modules:
                        setattr(sys.modules["compression"], sub, s_mod)
                except Exception:
                    pass

# Run main application in app/app.py
import runpy

app_path = ROOT_DIR / "app" / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
