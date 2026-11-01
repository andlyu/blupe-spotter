'use strict';
window.yamApplication = {
  runPayload() {
    if (document.getElementById('provider').value !== 'spotter') return {};
    // Other station processes can still serve the older pinned page during
    // this Robo-house-only deployment of the shared static assets.
    if (!document.getElementById('spotterRepairSteps') || !document.getElementById('spotterRepairRounds')) return {};
    const limits = {};
    for (const [id, key, maximum, label] of [
      ['spotterRepairSteps', 'max_plan_steps', 32, 'steps per repair plan'],
      ['spotterRepairRounds', 'max_plan_rounds', 12, 'plan rounds per intervention']
    ]) {
      const value = Number(document.getElementById(id).value);
      if (!Number.isInteger(value) || value < 1 || value > maximum) {
        throw new Error(`Choose 1–${maximum} ${label}.`);
      }
      limits[key] = value;
    }
    return {spotter: limits};
  },
  async sessionReady(session) {
    const picker = document.getElementById('provider');
    const setup = session.spotter;
    document.getElementById('robotSelector').addEventListener('change', event => {
      const station = setup.stations.find(item => item.id === event.target.value);
      if (station && station.id !== session.robot_id) {
        // These stations have separate backends. Override the shared fleet
        // picker's same-origin query routing before its bubble listener runs.
        event.stopImmediatePropagation();
        window.location.assign(station.url);
      }
    }, {capture: true});
    picker.replaceChildren(...Array.from(picker.options).filter(option => ['spotter', setup.base_provider].includes(option.value)));
    picker.value = 'spotter';
    picker.dispatchEvent(new Event('change'));
    const repairSettings = document.getElementById('spotterRepairSettings');
    const runDuration = document.getElementById('runDuration');
    if (repairSettings && runDuration?.closest) runDuration.closest('.runDurationControl')?.after(repairSettings);
    function updateRepairSettings() {
      if (!repairSettings) return;
      repairSettings.hidden = picker.value !== 'spotter';
      for (const id of ['spotterRepairSteps', 'spotterRepairRounds']) {
        const input = document.getElementById(id);
        if (input) input.disabled = repairSettings.hidden || runDuration?.disabled === true;
      }
    }
    picker.addEventListener('change', updateRepairSettings);
    if (repairSettings && runDuration) new MutationObserver(updateRepairSettings).observe(runDuration, {attributes: true, attributeFilter: ['disabled']});
    updateRepairSettings();
    document.title = `Spotter on Blupe · ${setup.station}`;
    const progress = document.getElementById('message');
    const status = document.getElementById('status');
    function showSpotterProgress() {
      if (setup.base_provider !== 'dream' || picker.value !== 'spotter' || !progress || !status) return;
      const text = progress.textContent;
      const starting = 'Starting Spotter and joining the robot queue…';
      if (text !== starting && !/^(Preparing the model GPU|Preparing before the robot queue · warming |In the robot queue · warming )/.test(text)) return;
      const next = status.textContent.trim().toLowerCase() === 'running' ? '' : starting;
      if (progress.textContent !== next) progress.textContent = next;
    }
    if (setup.base_provider === 'dream' && progress && status) {
      const observer = new MutationObserver(showSpotterProgress);
      observer.observe(progress, {childList: true, subtree: true});
      observer.observe(status, {childList: true, subtree: true});
      showSpotterProgress();
    }
    const readiness = document.getElementById('spotterReadiness');
    function showReadiness(state) {
      const dream = state.dream_runtime;
      readiness.textContent = state.configured
        ? `${setup.base} + ${setup.supervisor}${setup.intervention ? ' screen / ' + setup.intervention + ' repair' : ''} · ${dream ? 'Dream solver is ready; each run starts a clean model episode.' : 'Models prepare before execution.'} Select policy alone for a baseline.`
        : dream?.preparing
          ? 'Preparing the Dream solver. Cameras are live; Run becomes available when preparation finishes.'
          : 'Model services are unavailable. Cameras remain live; Run is unavailable until preparation succeeds.';
    }
    showReadiness(setup);
    if (setup.dream_runtime) {
      setInterval(async () => {
        try {
          const response = await fetch('/spotter/readiness', {cache: 'no-store'});
          if (!response.ok) throw new Error('Readiness unavailable');
          showReadiness(await response.json());
        } catch {
          readiness.textContent = 'Model readiness is unavailable. Reconnecting…';
        }
      }, 3000);
    }
    // The owner can inspect their existing private status even when they have
    // not enabled the separate public-conversation publisher.
    if (setup.base_provider === 'dream' && progress) {
      const runnerName = document.getElementById('runnerName');
      const rememberName = () => {
        try {
          const name = runnerName.value.trim();
          if (name) localStorage.setItem('spotter.runnerName', name);
          else localStorage.removeItem('spotter.runnerName');
        } catch { /* Storage can be unavailable in a private browser. */ }
      };
      try {
        if (!runnerName.value.trim()) runnerName.value = localStorage.getItem('spotter.runnerName') || '';
      } catch { /* An owned run can still provide the confirmed name below. */ }
      runnerName.addEventListener('input', rememberName);
      let identityRestored = false;
      const activity = document.createElement('div');
      activity.id = 'spotterOwnActivity';
      activity.hidden = true;
      activity.setAttribute('role', 'status');
      activity.setAttribute('aria-live', 'polite');
      activity.style.marginTop = '.5rem';
      const title = document.createElement('strong');
      const note = document.createElement('p');
      note.style.margin = '.25rem 0 0';
      activity.replaceChildren(title, note);
      progress.after(activity);
      let first = true, watching = false, fetching = false;
      async function refreshOwnActivity() {
        const stopping = /stop run/i.test(document.getElementById('quickRun')?.textContent || '');
        if (fetching || (!first && !watching && !stopping)) return;
        first = false;
        fetching = true;
        try {
          const response = await fetch('/api/status', {cache: 'no-store'});
          if (!response.ok) throw new Error('Activity unavailable');
          const state = await response.json();
          if (!identityRestored) {
            identityRestored = true;
            if (!runnerName.value.trim() && typeof state.runner_name === 'string' && state.runner_name.trim()) {
              runnerName.value = state.runner_name.trim();
              rememberName();
            }
          }
          const events = state.interactions?.events || [];
          const latest = [...events].reverse().find(event =>
            event.kind === 'model_progress' && event.details?.spotter_phase);
          watching = ['preparing', 'queued', 'running'].includes(state.status);
          const ownSpotterRun = state.provider?.provider === 'spotter' || state.run_configuration?.provider === 'spotter';
          activity.hidden = !ownSpotterRun || !state.attempt_id || !latest;
          if (activity.hidden) return;
          const ending = {completed: 'Finished', failed: 'Failed', stopped: 'Stopped',
            safety_aborted: 'Stopped', timed_out: 'Stopped', cancelled: 'Stopped'}[state.status] || 'Ended';
          title.textContent = watching ? 'Spotter activity' : 'Last Spotter run · ' + ending;
          const used = state.run_configuration?.spotter;
          const limits = used ? ` · Repair limits: ${used.max_plan_steps} steps/plan, ${used.max_plan_rounds} rounds/intervention` : '';
          note.textContent = String(latest.message || '').slice(0, 2000) + limits;
        } catch {
          if (!activity.hidden) title.textContent = 'Spotter activity unavailable · Reconnecting…';
        } finally {
          fetching = false;
        }
      }
      await refreshOwnActivity();
      setInterval(refreshOwnActivity, 2000);
    }
    document.getElementById('openCodexInstructions').hidden = true;
    for (const id of ['runAstra', 'runClaude', 'runGroot']) document.getElementById(id).hidden = true;
  }
};
