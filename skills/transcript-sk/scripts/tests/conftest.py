"""Test configuration -- add scripts/ to sys.path for direct imports."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the scripts directory to sys.path so `from transcript import ...` works
sys.path.insert(0, str(Path(__file__).parent.parent))
