"""Root entrypoint proxy for Streamlit Cloud and standard deployments.

Forwards execution to app/app.py while ensuring proper sys.path resolution.
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
root_str = str(ROOT_DIR)
if root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)

# Run main application in app/app.py
import runpy

app_path = ROOT_DIR / "app" / "app.py"
runpy.run_path(str(app_path), run_name="__main__")
