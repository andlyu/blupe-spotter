'use strict';
window.yamApplication = {
  async sessionReady(session) {
    const picker = document.getElementById('provider');
    picker.replaceChildren(...Array.from(picker.options).filter(option => ['spotter', 'dreamzero'].includes(option.value)));
    picker.value = 'spotter';
    picker.dispatchEvent(new Event('change'));
    document.title = 'Spotter on Blupe · Physical YAM demo';
    document.getElementById('runnerName').value ||= 'Andrew';
    const readiness = document.getElementById('spotterReadiness');
    readiness.textContent = session.spotter.configured
      ? `DreamZero + ${session.spotter.supervisor} · Models prepare before entering the robot queue. Select policy alone for a baseline.`
      : 'Model services are being configured. You can watch the live YAM cameras; running Spotter is unavailable until setup completes.';
    document.getElementById('openCodexInstructions').hidden = true;
    for (const id of ['runAstra', 'runClaude', 'runGroot']) document.getElementById(id).hidden = true;
  }
};
