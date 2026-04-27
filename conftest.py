import os
import sys

_venv_site = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../local/lib/python3.12/site-packages")
)
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)
