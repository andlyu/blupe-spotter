"""Run the actual browser adapter with an owned status feed and sharing off."""
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize('scenario', ['running', 'ended', 'yam1', 'cached_name', 'new_visitor'])
def test_owned_progress_is_visible_without_publishing_or_changing_yam1(scenario):
    root = Path(__file__).resolve().parents[1]
    subprocess.run(['node', str(root / 'tests/progress-ui.cjs'), scenario,
                    str(root / 'static/site.js')], check=True, capture_output=True, text=True)


@pytest.mark.parametrize('station', ['YAM1', 'Robo-house'])
def test_initial_picker_matches_the_station_backend(station):
    from spotter_yam import RUNNER
    root = Path(__file__).resolve().parents[1]
    subprocess.run(['node', str(root / 'tests/station-routing.cjs'),
                    'Spotter on Blupe · ' + station, str(root / 'static/site.js'),
                    str(RUNNER / 'static/hosted.js')],
                   check=True, capture_output=True, text=True)
