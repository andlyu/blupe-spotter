# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Completion requirements

- [x] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [ ] The website and its source repository are public, unless an explicit
  public-visibility exception for either is recorded below.
- [x] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
- [ ] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [x] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [x] Automated test runs retain the actual approach name and explicitly label
  their runner as `Automated` or an equivalent clearly automated identity.
  They require no interactive human signup. Do not invent a person's email
  address for automated runs.
- [x] A person can use the website to run the integrated paper's method on
  physical YAM robots/arms. Record a verified physical execution of that method.
- [x] The actual physical arms are visible live on the website while the method
  runs, so a visitor can see that it is executing on real hardware.
- [x] Immediately after a run finishes, the person can replay that just-completed
  physical YAM execution through the website, with retained footage showing the
  actual arms executing the integrated method.
- [x] The person can browse/select previous runs on the website and replay their
  retained physical arm footage, associated with the executed method and run.
  Mock animations do not satisfy either replay requirement.
- [ ] The website is intuitive: a new visitor, without coaching, can find how to
  run the method and have the physical YAM arms actually executing it within
  **15 seconds of entering the website**, verified as described below.
- [ ] **Mandatory for every run:** after the person clicks Run, the physical YAM
  arms start actual method-driven motion within **15 seconds**, verified and
  recorded per run as described below. A sampled demonstration is insufficient.
- [ ] Before marking the integration complete or reporting it done, open the
  deployed website and perform a final end-to-end physical YAM run through its
  normal user interface. Verify every completion requirement against that
  deployment and record evidence; unmet or unverified requirements block
  completion.

## Verify the 15-second path

Time a visitor's full path. Start at initial navigation to the website (`t0`);
stop at the first observed physical arm motion executing the integrated method
(`t1`). Require `t1 - t0 <= 15 seconds`. Include page loading, finding the controls,
login/setup, queue/readiness waits and inference in the elapsed time; do not
restart the clock at Run. Queued, submitted, accepted or a UI "running" status
alone does not pass, nor does backend latency alone.

Include join-time name/email entry or confirmation in this same measurement.

Record the visitor's starting state and test conditions. Keep a timed screen
recording showing site entry, the visitor's actions and the live arms beginning
the method, linked to the matching physical run. If the elapsed time exceeds
15 seconds or physical motion is unverified, leave the box unchecked.

## Verify every Run click

This is an additional per-run measure; keep the site-entry test above. For every
run, start at the Run click (`t_run`) and stop at the first observed actual
method-driven physical arm motion (`t_motion`). Require
`t_motion - t_run <= 15 seconds`. An acknowledgement, accepted request, queued
status, submitted action or inference starting is insufficient.

Record every run below (add rows), including visual evidence of the click and
motion. Mark the outcome as pass, missed target, unverified or exception.
Exceptions are not fulfilled <=15-second runs. Each exception requires a specific
justification grounded in the integrated paper/research, explaining why it
applies to that run, plus a supporting source citation/link and relevant
section/page. Slow loading, queueing, setup or infrastructure delay is a missed
target, not in itself a paper/research-grounded exemption.

| Run reference | Run click (`t_run`) | First observed method-driven arm motion (`t_motion`) / visual evidence | Elapsed seconds | Outcome |
| --- | --- | --- | --- | --- |
|ep_06f89dc0969846ba|2026-10-30T22:50:11.042Z (initial Run);22:50:15.755Z (join submit)|Live arms visibly moved by22:50:59.303Z. First onset not captured. Runner started22:50:27.776725Z, already16.7357s after initial Run.|>=16.7357s; motion visually observed by48.261s|Missed target; no research exception|

- Exception record (repeat for each affected run):
- Affected run reference:
- Specific paper/research-grounded reason and why it applies to this run:
- Supporting paper/research source (citation/link and relevant section/page):

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
visitor flow to join, run the integrated method on physical YAMs and watch the
actual arms live. Check both 15-second measures, approach/runner identities,
replay of the just-completed run and selection/replay of previous runs. Review
every checklist item against current evidence, including public visibility and
automated runner identity. Record the tested deployment, run and evidence below.
Leave unmet or unverified items unchecked and report gaps and explicit exceptions
before any completion claim.

## Integration and evidence

- Paper / method (link and version):
- Final verification (reviewer/date, tested website URL and deployed revision,
  physical run reference):
- Final checklist review (evidence for every item, replay links/timings, unmet
  items and explicit exceptions):
- Actual approach name / website label evidence:
- Human join evidence (name/email collection or confirmation, prefilled defaults
  and edits to both fields):
- Run context evidence (run ID, approach and runner identity; website attribution):
- Automated test evidence (run ID, approach, explicit automated runner label and
  non-interactive execution):
- Website URL:
- Website source repository URL / deployed revision:
- Public-visibility exceptions (write "none", or the affected website/repository,
  explicit exception, reason and approval reference):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / immediate availability evidence (same physical run):
- Previous-run browser URL / selected prior run and replay evidence:
- 15-second test (tester/date, browser/session/network and robot readiness):
- Visitor's starting state and entry-to-motion steps:
- `t0` / `t1` / total elapsed seconds:
- Timed screen recording / matching physical run evidence:
- Remaining gaps:

## Spotter acceptance record — partial, not integration complete

- Contract copied from the newly created shared BLUPE Remote Bots harness:
  `codex-runner/integration-harness/COMPLETION-CHECKLIST.md`. Template SHA256:
  `36895c5add8d81f02bd8cd42a2b213e52cd85292d76661cddd180cc0d61b9421`.
- Reviewed2026-10-30 on the deployed Robo-house website. Runtime revision:
  `2aea99236b8584024b67c39e94a9027dde6b4996`. Source tests:49passed,2subtests.
- Website:https://robohouse.spotter.54.209.185.15.sslip.io/
- Associated source:https://github.com/andlyu/blupe-spotter
- Station:robot-ba8413962083809c. Actual method:Spotter supervising
  dreamlabs/dream-1-beta with OpenRouter qwen/qwen3.8-27b.
- Final deployed-site test:normal website Run flow, one-minute task“Put the
  orange block into the cup”, runner“Andrew · Automated verification”. No
  interactive human signup or invented email. Session:sess_7b31774b390b487c;
  episode:ep_06f89dc0969846ba. Actual arms were visible and moved. Four execution
  packets,88confirmed waypoints,11.2757s execution. Run ended at the configured
  time limit; cube placement was not verified successful.
- Just-completed replay:
  https://robohouse.spotter.54.209.185.15.sslip.io/?run=ep_06f89dc0969846ba&robot_id=robot-ba8413962083809c
  Runner ended1793400688.4416277; immutable MP4 ready1793400689.3770597:
  **0.935432seconds after end**. Website automatically opened and played this
  same episode.53.5s H.264,960x576,107encoded frames,2fps asynchronous camera
  API recording with timestamped JPEG provenance. It is sampled footage, not
  a continuous native10Hz recording. No idle cuts are applied.
- Replay verification:watched to53.5s; fresh URL open auto-played muted and
  advanced to24.993807s/readyState4; native scrubber sought26.75s/readyState4.
  Actual recorded arms are visible in all three camera views.
- Previous-run browser:both ep_2e08e138f81f4ac0 andep_00ed44db3c87402f were
  selected, played and sought on the website. The user's3:29pm
  episodeep_be009411059045e2 was separately recovered from all1118original
  samples and all three native camera views. It became locally ready at
  23:00:50.4133263UTC. Website playback advanced0.20213s→5s/readyState4,
  and native seeking returned2.5s/readyState4. This is its own original footage;
  the new test recording is not a replacement. Its native preview is accelerated
  9.16× with idle pauses removed, as labeled on the page.
- Evidence retained in this chat workspace'soutputs/spotter/:
  live-replay-browser-proof.json,live-replay-physical-proof.json,
  live-acceptance-first.jpg,live-acceptance-motion.jpg,
  live-replay-playing.jpg,live-replay-fresh-open.jpg,
  replay-be-recovered.jpg,replay-be-browser-proof.json. Physical proof includes
  source-camera timestamps,MP4 SHA256 andffprobe, plus byte-range seek206.
- **8/13 requirements verified. Remaining gaps:**source repository is private
  with no public-visibility exception established; fresh human join does not
  confirm prefilled known name/email defaults; entry-to-motion<=15seconds is
  unverified/missed during restart preparation; this test also missed the
  per-Run15-second target. Readiness/queue/network delay is not a research
  exemption. Every-run visual timing is not yet enforced or comprehensively
  recorded. Final all-requirements acceptance remains unchecked.
- No claim that the entire research integration is complete.
