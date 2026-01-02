from __future__ import annotations

import sys
from pathlib import Path


# Ensure the local checkout is importable when running pytest without installing
# the package (common during migration work).
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
