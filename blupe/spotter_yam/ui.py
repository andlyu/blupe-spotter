"""Small, checked compatibility overlay for the pinned runner's model warmup UI."""
from . import RUNNER


def runner_script():
    script = (RUNNER / 'static/hosted.js').read_text()
    edits = {
        'player.play().catch(() => {});':
            'player.muted = true; player.play().catch(() => {});',
        '`${playbackSource(run, false).speed}× speed · idle pauses removed`':
            '`${playbackSource(run, false).speed}× speed · ${run.idle_removed_s === 0 ? "pauses retained" : "idle pauses removed"}${run.capture_fps ? " · " + run.capture_fps + " fps camera API recording" : ""}`',
        'Preparing replay… · View run': 'Video not published · View run details',
        "const entryModel = playgroundEntryModel(location.search, $('provider').options, session);":
            "const entryModel = session.spotter && !new URLSearchParams(location.search).has('model') ? null : playgroundEntryModel(location.search, $('provider').options, session);",
        "event.kind === 'model_response' && astraStreamNote(event)":
            "['model_response','model_progress'].includes(event.kind) && astraStreamNote(event)",
        "['molmoact2','dreamzero'].includes(payload.provider)":
            "['molmoact2','dreamzero','spotter'].includes(payload.provider)",
        "['groot','molmoact2','dreamzero'].includes(state.provider?.provider)":
            "['groot','molmoact2','dreamzero','spotter'].includes(state.provider?.provider)",
        "    const preparing = phase === 'preparing';":
            "    const preparing = phase === 'preparing';\n"
            "    const warmingModels = preparing && !state.session_id && state.provider?.provider === 'spotter';",
        "const waiting = queued || preparing && !aspire && !reviewing;":
            "const waiting = queued || preparing && !aspire && !reviewing && !warmingModels;",
        ": preparing ? (aspire ? '—' : 'Up next')":
            ": preparing ? (aspire || warmingModels ? '—' : 'Up next')",
        ": preparing ? 'Your run is preparing'":
            ": warmingModels ? 'Preparing Spotter' : preparing ? 'Your run is preparing'",
        "? 'The robot is getting ready. You can stop your run here.'":
            "? (warmingModels ? 'Preparing Spotter before joining the robot queue. The run timer has not started.' : 'The robot is getting ready. You can stop your run here.')",
        ": preparing ? 'The robot is getting ready for your run.'":
            ": warmingModels ? 'Spotter is preparing before the robot queue.' : preparing ? 'The robot is getting ready for your run.'",
    }
    for before, after in edits.items():
        expected = 2 if before.startswith("['groot'") else 1
        if script.count(before) != expected:
            raise RuntimeError('Pinned runner warmup UI changed; review the Spotter overlay')
        script = script.replace(before, after)
    return script.encode()
