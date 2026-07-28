import os
import sys
import importlib.util

try:
    # Prefer the root-level package when available.
    from app import app as application
except Exception:
    repo_root = os.path.dirname(os.path.abspath(__file__))
    inner_app_path = os.path.join(repo_root, "sabr-central", "sabr-central", "app.py")

    if not os.path.exists(inner_app_path):
        raise RuntimeError(f"Could not find inner app at {inner_app_path}")

    spec = importlib.util.spec_from_file_location("inner_app", inner_app_path)
    inner_app = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(inner_app_path))
    spec.loader.exec_module(inner_app)  # type: ignore

    application = getattr(inner_app, "app")

app = application
