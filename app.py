import os
import sys
import importlib.util

# Load the inner application module directly from its file to avoid
# import-name collisions with this top-level module called 'app'.
project_dir = os.path.dirname(__file__)
inner_app_path = os.path.join(project_dir, "sabr-central", "sabr-central", "app.py")

if not os.path.exists(inner_app_path):
    raise RuntimeError(f"Inner app not found at {inner_app_path}")

spec = importlib.util.spec_from_file_location("inner_app", inner_app_path)
inner_app = importlib.util.module_from_spec(spec)
sys.modules["inner_app"] = inner_app
# Ensure the inner app directory is on sys.path so local imports resolve
inner_dir = os.path.dirname(inner_app_path)
if inner_dir not in sys.path:
    sys.path.insert(0, inner_dir)

spec.loader.exec_module(inner_app)  # type: ignore

# Expose the Flask app object under both `app` and `application` names
app = getattr(inner_app, "app")
application = app
