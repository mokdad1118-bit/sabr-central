import os
import sys
import importlib.util

# This package exposes the Flask app as `app` so commands like
# `gunicorn app:app` or `from app import app` work regardless of
# Render's working directory.
base_dir = os.path.dirname(os.path.dirname(__file__))
inner_app_path = os.path.join(base_dir, "sabr-central", "sabr-central", "app.py")

if not os.path.exists(inner_app_path):
    raise RuntimeError(f"Inner app not found at {inner_app_path}")

spec = importlib.util.spec_from_file_location("inner_app", inner_app_path)
inner_app = importlib.util.module_from_spec(spec)

# Ensure inner app directory is on sys.path for its local imports
inner_dir = os.path.dirname(inner_app_path)
if inner_dir not in sys.path:
    sys.path.insert(0, inner_dir)

sys.modules["inner_app"] = inner_app
spec.loader.exec_module(inner_app)  # type: ignore

# Expose the Flask application object
app = getattr(inner_app, "app")
application = app
