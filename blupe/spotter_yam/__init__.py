"""Physical YAM port of Spotter, using the pinned Blupe controller."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'blupe/vendor/remote-yam/codex-runner'
sys.path[:0] = [str(ROOT), str(RUNNER), str(RUNNER / 'src')]
