"""
pytest configuration for the script parser test suite.

Inserts src/backend onto sys.path so backend modules are importable
without installing the package.
"""

import os
import sys

# Make `src/backend` importable as a root package path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))
# Make `tests/` itself importable so test modules can do `from helpers import ...`
sys.path.insert(0, os.path.dirname(__file__))
