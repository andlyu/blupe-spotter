"""Run the actual browser adapter with an owned status feed and sharing off."""
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize('scenario', ['running', 'ended', 'yam1'])
def test_owned_progress_is_visible_without_publishing_or_changing_yam1(scenario):
    root = Path(__file__).resolve().parents[1]
    subprocess.run(['node', str(root / 'tests/progress-ui.cjs'), scenario,
                    str(root / 'static/site.js')], check=True, capture_output=True, text=True)
