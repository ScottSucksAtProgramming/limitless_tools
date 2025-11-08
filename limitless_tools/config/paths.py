from __future__ import annotations

import os
from pathlib import Path


def default_data_dir() -> str:
    """Return the default data directory path for lifelogs."""
    return str(Path(os.path.expanduser("~")) / "limitless_tools" / "data" / "lifelogs")

