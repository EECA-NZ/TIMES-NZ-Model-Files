"""PUBLISH-owned application paths."""

from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
PUBLISH_ROOT = _THIS_DIR.parent.parent.parent

ASSETS = PUBLISH_ROOT / "assets"
