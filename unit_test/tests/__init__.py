"""Test configuration for unit tests."""

import sys
from pathlib import Path

# Add unit_test/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))