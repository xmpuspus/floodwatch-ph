"""Shared pytest fixtures and path setup.

Adds the repo root to sys.path so tests can `import floodwatch_ph` without
requiring an editable install, mirroring the structure used by SolarMap.PH.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
