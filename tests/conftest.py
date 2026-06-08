"""Shared pytest fixtures / path setup.

Adds the (space-containing) `prediction model` and `dashboard` directories to
sys.path so the modules under test import cleanly.
"""

import sys
from pathlib import Path

_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO / "prediction model"))
sys.path.insert(0, str(_REPO / "dashboard"))
