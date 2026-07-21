"""
Regression test: application import smoke test.

Verifies that ``src.backend.main`` imports cleanly using the fully-qualified
package path — the same path used when the application is launched with:

    python -m uvicorn src.backend.main:app

This test runs after conftest.py inserts the repo root onto sys.path
(matching what uvicorn does).  It imports via the full ``src.backend.*``
path, so it would fail if any intra-backend module still uses a bare name
(e.g. ``from services.budget_estimator import ...``), even though such bare
names would be masked as importable by the old conftest.py behaviour that
inserted ``src/backend`` directly.

This is the regression guard for:
    ModuleNotFoundError: No module named 'services'
which occurs at runtime but was invisible to the test suite.
"""

import importlib


def test_src_backend_main_imports_cleanly():
    """
    src.backend.main must be importable via its fully qualified package path.
    Verifies that the FastAPI app object and create_app factory are exposed.
    """
    mod = importlib.import_module("src.backend.main")
    assert hasattr(mod, "app"), (
        "src.backend.main must expose 'app' (the FastAPI application instance)"
    )
    assert hasattr(mod, "create_app"), (
        "src.backend.main must expose 'create_app' (the application factory)"
    )


def test_src_backend_routers_import_cleanly():
    """
    All routers must be importable via their fully qualified package paths.
    This catches bare-name imports in any router that conftest.py would mask.
    """
    for module_path in (
        "src.backend.routers.health",
        "src.backend.routers.scripts",
        "src.backend.routers.budget",
        "src.backend.routers.generate",
        "src.backend.routers.animatic",
    ):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "router"), (
            f"{module_path} must expose a 'router' object"
        )


def test_src_backend_services_import_cleanly():
    """
    Core services must be importable via their fully qualified package paths.
    """
    for module_path in (
        "src.backend.services.script_parser",
        "src.backend.services.script_store",
        "src.backend.services.budget_estimator",
    ):
        importlib.import_module(module_path)  # raises on any import failure
