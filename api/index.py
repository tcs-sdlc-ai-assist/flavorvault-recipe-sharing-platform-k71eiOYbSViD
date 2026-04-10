import sys
from pathlib import Path

# Ensure project root is on sys.path so all top-level modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

handler = app