# tests/conftest.py
# Lets tests import backend modules (main, config, models, api) the same way
# the app does when it runs from the backend/ folder.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = str(REPO_ROOT / "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
