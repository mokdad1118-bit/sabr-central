import os
import sys

# Ensure the inner application package is importable when Render runs
project_dir = os.path.dirname(__file__)
inner = os.path.join(project_dir, "sabr-central", "sabr-central")
if inner not in sys.path:
    sys.path.insert(0, inner)

# Import the Flask app object from the inner package and expose it
from app import app  # noqa: E402

# WSGI servers sometimes expect `application`; keep both names available
application = app
