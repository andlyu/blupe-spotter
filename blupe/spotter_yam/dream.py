"""Spotter handoff for the pinned Dream-1 adapter's causal action history."""
from remote_yam.dream_policy import DreamAdapter


class SpotterDreamAdapter(DreamAdapter):
    def supervisor_intervention(self):
        # The upstream adapter resets between predictions before collecting new
        # inputs. Use that path to discard smoothing anchors and camera history
        # from before the repair, including any prediction Spotter superseded.
        with self._changed:
            self._commanded = self._pending_commanded = None
            self._workspace_reset_pending = True
            self._workspace_feedback = (
                'Spotter intervened and repaired the scene. The previous action '
                'plan was discarded. Continue from fresh measured state and images.')
