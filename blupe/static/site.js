'use strict';
window.yamApplication = {
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
    document.title = `Spotter on Blupe · ${setup.station}`;
    const readiness = document.getElementById('spotterReadiness');
    function showReadiness(state) {
      const dream = state.dream_runtime;
      readiness.textContent = state.configured
        ? `${setup.base} + ${setup.supervisor} · ${dream ? 'Dream solver is ready; each run starts a clean model episode.' : 'Models prepare before execution.'} Select policy alone for a baseline.`
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
    document.getElementById('openCodexInstructions').hidden = true;
    for (const id of ['runAstra', 'runClaude', 'runGroot']) document.getElementById(id).hidden = true;
  }
};
