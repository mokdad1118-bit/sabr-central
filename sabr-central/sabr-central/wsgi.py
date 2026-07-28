import sys

project_home = '/home/hadekaliil/sabr-central/sabr-central'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application