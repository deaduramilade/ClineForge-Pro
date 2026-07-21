"""
pytest configuration for the CineForge AI Pro test suite.

Inserts the repository root onto sys.path so that both:
  - src.backend.* (the production import path used by uvicorn)
  - helpers (test utilities in the tests/ directory)
are importable without installing any package.

The repo-root sys.path entry mirrors exactly what happens when uvicorn is
launched as:
    python -m uvicorn src.backend.main:app
from the repository root, ensuring that tests exercise the same import
resolution as the production application.
"""

import os
import sys

# Repository root — parent of src/ and tests/.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)

# tests/ directory — allows `from helpers import ...` in test modules.
sys.path.insert(0, os.path.dirname(__file__))
