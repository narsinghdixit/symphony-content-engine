"""pytest configuration: make the project root importable so tests can do
`from lib.textutils import ...` etc.

Without this, pytest discovers tests from the project root but doesn't add
the root to sys.path, so `import lib` fails. Adding `pyproject.toml` or
`pytest.ini` would also work; conftest.py is the smallest possible change.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
