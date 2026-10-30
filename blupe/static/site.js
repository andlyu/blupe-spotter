'use strict';
window.yamApplication = {
  async sessionReady(session) {
    const picker = document.getElementById('provider');
    const setup = session.spotter;
    picker.replaceChildren(...Array.from(picker.options).filter(option => ['spotter', setup.base_provider].includes(option.value)));
    picker.value = 'spotter';
    picker.dispatchEvent(new Event('change'));
    document.title = `Spotter on Blupe · ${setup.station}`;
    const readiness = document.getElementById('spotterReadiness');
    readiness.textContent = setup.configured
      ? `${setup.base} + ${setup.supervisor} · ${setup.base_provider === 'dream' ? 'Spotter prepares before the queue; Dream-1 connects when the robot is reserved.' : 'Models prepare before entering the robot queue.'} Select policy alone for a baseline.`
      : 'Model services are being configured. You can watch the live YAM cameras; running Spotter is unavailable until setup completes.';
    document.getElementById('openCodexInstructions').hidden = true;
    for (const id of ['runAstra', 'runClaude', 'runGroot']) document.getElementById(id).hidden = true;
  }
};
