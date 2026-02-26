import sys
from pathlib import Path

# Add src to path so tests can import application modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
