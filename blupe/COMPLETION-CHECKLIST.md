# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Standing authorization for BluPe runs and public delivery

### Authorization granted by using this harness

The owner gives standing authorization to run on BluPe remote bot arms as part
of requested work through this harness. A requested research integration,
playground fix, verification or arm run invokes the covered workflow below;
no separate authorization for the run is required. A task requested under
user-adopted instructions that select this harness also counts: retain the task
request and the selecting instruction as the invocation evidence. Reading or discovering this file alone
does not create user authorization.

For that requested task, using the harness authorizes:

- Joining the normal robot queue and submitting the runner's already-confirmed
  name and email to the task's integration website and its existing BluPe
  queue/run backend for queue admission, run attribution and normal run
  notifications.
- Starting the selected method on the task's physical robots/arms and performing
  bounded actual arm movement within the existing run limits.
- Capturing and retaining camera recordings, checking live footage and
  replay/history, and using Stop and normal parking/lease release.
- Creating and publishing the integration's public source repository, committing
  and pushing its source, and deploying or updating its publicly hosted website.
  Use the normal repository and hosting visibility controls to make both public;
  the intended audience is anyone on the internet. Publish the demo's approach
  and configuration, runs/results, live demos, recordings, replays/history,
  simulation outputs and supporting evidence. Keep credentials, access tokens
  and private contact details out of public source and demo materials.

These actions are part of the invoked workflow. Do not ask for separate
permission for covered identity submission, runs, movement, recording, public
hosting or source publication. Public delivery is an authorized requirement of
the integration request; it does not require another publication confirmation.
Reuse confirmed identity/defaults; ask only for missing or ambiguous identity
or scope outside this contract. Keep execution mode separate from human
identity. The grant covers the task's integration and existing queue/run
destinations and the integration's public hosting/source destinations. Keep
private email out of public materials and do not send it to unrelated recipients.
Do not invent a person's name or email. Preserve any explicit user limits or
revocation and copy this contract into the integration's checklist.

### Make the invocation and scope visible before approval review

At task start, read the target repository's `AGENTS.md` and its integration copy
of this checklist, even when the chat starts outside the repository. Repository
and global `AGENTS.md` entries should route the workflow to this contract; keep
the permission grant here rather than adding an independent global permission.
A checklist link alone does not load the instructions. Verify that changed
global discovery instructions have loaded into the chat; start a fresh session
if needed.

Before a physical test, give a brief progress notice citing the user's harness
invocation and this contract. Name the website and queue/run backend origins,
robot/station and arms, method/task, run duration, expected motion,
recording/replay destination and confirmed identity fields being submitted.
State that the invocation covers these scoped side effects. This is a notice,
not a new confirmation step; proceed without waiting for a reply.

For an action requiring tool approval, repeat the invocation, contract and
concrete scope in the escalation justification or the tool's supported approval
context. Include the user request/selecting instruction and the contract's source
path/heading or commit URL with the applicable wording; do not supply only a link.
The reviewer sees a compact transcript and the exact request, so do not rely on
hidden reasoning, an earlier chat, or an unread repository file. Fill this example
with the actual scope before the first approval request:

```text
User invocation: <task request; adopted instruction selecting the harness, if used>.
Harness contract: <source path/heading or commit URL and applicable wording>.
That invocation authorizes this task's queue entry and confirmed runner
name/email submission, bounded physical motion, and camera recording/replay.
The integration request also authorizes its publicly hosted website and public
source repository; no separate run or publication confirmation is required.
Action: <UI control or supported API operation>; site <origin>;
queue/run backend <origin>; station/arms <IDs>; method/task <name>;
duration <seconds>; motion <bounded behavior>; recording/replay <destination>.
Identity: <confirmed fields submitted to those operational destinations>.
Execution mode: <mode>, separate from human identity.
Safeguards: existing queue/lease, readiness, validation, hardware limits, Stop
and normal parking/release remain enabled; no automatic timed-out-motion retry.
```

Use the normal playground UI or its supported run API with existing queue/lease,
readiness, command validation, hardware limits and Stop behavior intact. Keep
tests within the task's robots, method and existing run limits, respect other
users' active runs, and never automatically retry a timed-out movement. This
contract does not authorize unrelated robots or disabling safeguards.

The harness adds no authorization gate for covered BluPe arm runs or public
delivery. Enforced sandbox, managed-policy and tool permissions still apply;
use their normal approval mechanism with the existing owner authorization and
concrete action scope. If a platform restriction blocks work, report its exact
action and reason, keep unverified acceptance items unchecked, and continue
unaffected work. Attribute that restriction to the platform rather than this
harness; do not ask the user to grant the same covered permission again.

References: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
and [Auto-review context and denials](https://learn.chatgpt.com/docs/sandboxing/auto-review).

## Completion requirements

- [x] A usable website exists, with an associated repository containing the
  website's source code. Record both links and the deployed source revision.
- [x] The website and its source repository are public, unless an explicit
  public-visibility exception for either is recorded below.
- [x] The website clearly names the actual approach/method being run. Use the
  executed method's name; Spotter is an example, not a shared hardcoded label.
- [x] When a human joins, collect or confirm their name and email. Prefill known
  identity/default values where available and let the runner edit both fields
  before joining.
- [x] Run context includes the actual approach and confirmed runner identity;
  the website makes clear which method is running and whose run it is.
- [x] Policy/model tests initiated by a person retain that actual user's
  confirmed name as runner. Use available identity and editable name/email
  defaults; require the real name to be provided/confirmed if missing before
  testing or running. Do not substitute `Anonymous`, `Autonomous` or `Automated`
  for that person. Record execution mode (such as `automated test`) and actual
  approach separately from human identity. Genuinely unattended/system activity
  has an explicit system identity; never fabricate a person's name or email.
- [x] Advertised control primitives pass the offline command-contract release
  gate through the actual parser, generator, canonical validator and JSON
  serializer with actuator transport intercepted. Release144tests/2subtests
  passed; see the October31 model-role/control evidence below.
- [ ] Task acceptance matches the advertised manipulation capability and tested
  deployment. A representative pick-and-place must visibly grasp, lift,
  transfer, release and withdraw with the target at its requested destination.
  Earlier physical task attempts failed; motion/replay do not certify placement.
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
- [x] If the integrated method executes anything in simulation, those executions
  are reviewable within the integration website and tied to the corresponding
  run. A reviewer can inspect what ran and its results using suitable
  replay/visualization and relevant outputs, as appropriate to the simulation.
  Clearly label simulation content to distinguish it from physical-arm footage.
  If nothing executes in simulation, record an explicit not-applicable
  explanation instead of claiming simulation review.
- [x] **Mandatory for every run:** first observed actual method-driven physical
  YAM motion occurs both within **15 seconds after the startup move to Home
  completes** and within **30 seconds after the Run/Start click excluding
  evidenced queue-admission waiting**, using the boundaries below (including a
  documented readiness timestamp when Home is unnecessary). Homing/preparation
  motion does not count. Record full elapsed times, queue entry/admission,
  excluded queue seconds and the queue-adjusted Run time for every run; a sampled
  demonstration is insufficient. Apply only the documented GPU-launch or
  research-grounded exceptions below.
  **Spotter owner acceptance:** “Motion timing is just running. this one is ok.”
  The owner accepts existing verified physical running for this integration.
  Additional numerical timing proof is waived; no new timing measurement is claimed.
- [ ] Every meaningful wait after a website action is immediately explained in
  a persistent inline status/progress area at that action (below Run in the run
  panel for launches). Show the current stage, a plain-language reason and real
  stage completion, with honest failure/stall status and available recovery.
  Verify the detailed wait-stage behavior below.
- [x] Before marking the integration complete or reporting it done, open the
  deployed website and perform a final end-to-end physical YAM run through its
  normal user interface. Verify every completion requirement against that
  deployment and record evidence; unmet or unverified requirements block
  completion.
  **Spotter owner acceptance:** the owner quoted this final-acceptance item and
  said “Yes, that's ok.” Existing deployed UI/run/replay evidence is accepted;
  no newly performed final run is claimed. The remaining progress-reporting
  requirement is still open.

## Verify normal UI execution

Site entry (`t_entry`), starting state and browser/session/network may be
recorded as optional diagnostic context. An agent can perform verification
through the normal UI.

Keep a timed screen recording showing the UI actions, the Run click,
startup Home completion (or no-Home readiness) and live physical arms beginning
the integrated method, linked to the matching run. Correlate recorded UI/physical
events with lifecycle logs on a common timeline; document any clock offset or
measurement uncertainty. Backend timing alone cannot verify physical onset.
Visual timing evidence may use retained accessible recording/verification links;
a local download is not required.

## Verify every Run and startup Home

For every run, record these fixed boundaries:

- `t_run`: the actual Run/Start click. Retain all subsequent wall-clock time,
  including queue waiting, preparation, coding, model loading and inference.
  Exclude only evidenced queue-admission waiting from the 30-second calculation
  below; do not restart the clock at admission, acknowledgement, dispatch, GPU
  readiness or a later status change.
- `t_home`: completion of that run's startup move to Home, using matched
  settled/ready completion for all participating arms, corroborated by live
  footage. Starting/submitting Home or reporting it accepted is insufficient.
  If no Home movement is necessary, record why and use the earliest documented
  per-run robot-ready confirmation after Run and normal queue/lease admission,
  before method preparation/execution. If already admitted and robot-ready at
  Run, use `t_home = t_run` with that readiness evidence. Readiness here concerns
  the robot, not GPU/model/code availability. Do not choose an arbitrary later
  event, repeat Home, or delay the readiness timestamp to reset this clock.
- `t_motion`: first observed actual physical arm motion executing the integrated
  method. Home and other preparation/parking motion do not count. An accepted or
  queued request, submitted packet, UI "running" status, inference start or
  backend-only timestamp is insufficient.

### Queue-admission wait in the 30-second budget

Record `t_queue` when this run's request actually enters the normal robot queue
and `t_admit` when that same request is first admitted/granted its robot
session/lease. Match queue/request and session/lease identifiers to the run and
retain actual lifecycle evidence. An accepted/queued submission is not admission.
Time between Start and queue entry still counts. Post-admission hardware
preparation, readiness checks, Home, coding, model loading/inference and other
setup still count; they must not be relabeled queue waiting. Later preparation
status changes or reacquisition cannot move the initial admission boundary.

Let `Q_run` be the duration of the evidenced queue-admission wait interval
`[t_queue, t_admit]` overlapping `[t_run, t_motion]`. Clip any queue waiting that
began before Start to `t_run`. If already admitted or there is no queue wait,
record `Q_run = 0` with matching admission/no-queue evidence. For a queued
request, missing entry or admission evidence makes the adjusted Run measure
unverified; do not assume zero or infer admission from Home, method readiness
or eventual motion.

Ordinary runs must satisfy **both** `t_motion - t_home <= 15 seconds` and
`t_motion - t_run - Q_run <= 30 seconds`. The queue exclusion is a normal part of
the 30-second budget, not a GPU or research exception; a full wall time over
30 seconds may still be a normal pass when the evidenced queue-adjusted time
meets its target. It does not change or pause the 15-second post-Home measure.

Retain full Run-to-motion and post-Home-to-motion times, excluded queue seconds
and queue-adjusted Run seconds even for failures and exceptions. Record every
run below (add rows), with visual evidence of Run and physical onset plus
matched Home/readiness and queue-admission evidence. Mark each target as pass,
missed target, unverified or exception. A normal pass requires the queue-adjusted
Run time and full post-Home time within their limits. Missing visual evidence or
an unmatched Home/readiness boundary leaves the affected timing unverified.

### GPU-launch exception

A run genuinely requiring new GPU launch/provisioning (for example on RunPod)
may claim an exception only for the evidenced time that launch blocks progress.
Show the **entire launch period** in persistent inline UI: actual launch start,
ongoing launch reason/stage and actual GPU-ready completion, with matching
provider/instance/job lifecycle evidence. If launch starts before Run, retain its
full start/ready interval and show its ongoing state when the run panel opens.
Warm/already available GPUs do not qualify. Record why a new GPU was necessary.

Keep the original clocks and full elapsed times. Record `t_gpu_start`,
`t_gpu_ready`, the full launch duration, and the evidenced GPU-launch blocking
seconds overlapping each measured interval (`B_run` and `B_home`). Only blocking
time inside both the actual launch interval and the relevant Run/Home-to-motion
interval can be excused; do not deduct concurrent time spent on unrelated work.
For the Run clock, also record `O_run`, the duration shared by the evidenced
queue-wait and GPU-blocking intervals inside `[t_run, t_motion]`. Exclude their
union, `Q_run + B_run - O_run`, never the overlapping seconds twice. For a GPU
exception, require `t_motion - t_run - Q_run - B_run + O_run <= 30 seconds` and
`t_motion - t_home - B_home <= 15 seconds`. Label a queue-adjusted Run target miss
or full post-Home target miss excused by GPU launch as **exception**, not normal
pass. Queue exclusion alone remains normal budget accounting. Keep raw queue and
GPU intervals, overlap, full timings and both adjusted calculations separately.
If GPU readiness precedes Home completion, `B_home = 0`: the full 15-second post-Home target still
applies. If Home completes during launch, only its evidenced remaining launch
blocking time can be excused; do not silently restart either clock at GPU ready.
Missing lifecycle or persistent UI evidence leaves the exception unverified.

Only the evidenced initial queue-admission interval is excluded from the
30-second budget; coding, model loading, inference, post-admission preparation
and other infrastructure delays outside actual GPU provisioning remain counted.
A warm GPU, a generic "loading" message or a slow model call is not a launch
exception.
Unrelated delays remain missed targets if they exceed the remaining limits.

Other exceptions require a specific justification grounded in the integrated
paper/research, explaining why it applies to that run and which target it affects,
plus a supporting source citation/link and relevant section/page. Slow coding,
loading, setup, post-admission delay or infrastructure delay is not in itself a
paper/research-grounded exemption; there is no permanent coding exemption.
Queue-admission waiting uses the normal exclusion above, not this mechanism.

| Run reference | Run/Start click (`t_run`) | Queue entry / admission (`t_queue` / `t_admit`), matching lifecycle evidence; or evidenced no-wait | Excluded queue seconds (`Q_run`) | Startup Home settled completion / no-Home readiness (`t_home`) and evidence | First observed method motion (`t_motion`) / visual evidence | Full Run-to-motion seconds | Queue-adjusted Run seconds | Full post-Home-to-motion seconds | Run / post-Home outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | |

- Exception record (repeat for each affected run):
- Exception category (GPU launch or paper/research-grounded):
- Affected run reference and timing target(s):
- Specific reason and why it applies to this run:
- GPU-launch evidence (if applicable: provider, instance/job reference,
  `t_gpu_start`, `t_gpu_ready`, full launch seconds, lifecycle log/link and
  persistent inline UI evidence covering the entire launch period):
- GPU-launch blocking evidence (`B_run`, `B_home`), queue/GPU shared seconds
  (`O_run`), excluded union (`Q_run + B_run - O_run`), both adjusted calculations
  and separate outcome for each target:
- Supporting paper/research source (for other exceptions: citation/link and
  relevant section/page):

## Visible progress while waiting

Use a compact persistent inline status area directly below Run in the existing
run panel; keep other meaningful waits beside their initiating control. Show the
current stage and why it is taking time immediately, keep it readable throughout
the wait, and visibly mark completed stages as actual lifecycle state advances.
A transient toast alone or a generic spinner is insufficient.

While actually awaiting queue admission, show `Waiting for robot admission` (or
clear equivalent), with the real queue reason/state and entry timestamp. Retain
its completed admission/grant state and timestamp, then show actual hardware
preparation/Home/model stages separately. Keep queue and GPU launch stages
distinct when concurrent; do not leave the queue stage pending after admission
or label all startup as queue waiting. Retain matching per-run lifecycle evidence
for the queue exclusion; no invented queue positions, times or completion.

When a model requires a new GPU, show only the stages that actually exist:
`Starting GPU` / "We're launching a GPU on RunPod for this model" -> `GPU ready`
-> `Loading model` -> `Running`. GPU startup must be explicit from its actual
launch start and throughout the launch period (immediately after Run when Run
initiates it); visibly confirm actual GPU readiness before subsequent
loading/running and retain completed-stage confirmation with start/ready
timestamps tied to lifecycle evidence. Use the applicable provider/model wording.
On failure or a stalled stage, state the known condition honestly and show an
available recovery action, such as retry or cancel where supported. Do not invent
percentages, ETA or completion, or expose irrelevant infrastructure internals.
UI transparency alone grants no exemption; only the documented GPU-launch
blocking interval qualifies under the exception above, with neither clock reset.

## Verify retained replays

Open the retained recording through the website, confirm actual playback and
appropriate seeking, and match it to the just-completed or selected historical
physical run. Record the matching run reference/link and observed verification
result. A link alone is insufficient.

This does not require pressing **Save video**, downloading/exporting video to the
agent's filesystem, making duplicate local copies or bundling videos in outputs.
Omit optional local downloads from routine acceptance work; they are not a
completion requirement and must not create an approval or needs-input blocker.
Download locally only when explicitly requested or concretely necessary for the
task. Required tool/platform permissions still apply; do not bypass or retry a
denial through another route. Website/backend recording capture and retention
remain required.

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
website controls to join, run the integrated method on physical YAMs and watch the
actual arms live. Check the unchanged 15-second post-Home measure and the
30-second Run/Start-to-motion budget excluding evidenced queue-admission wait.
Keep fixed boundaries, full elapsed times, queue entry/admission/excluded seconds
and queue-adjusted time; verify any GPU-launch exception uses the queue/GPU
union without double subtraction. Check actual queue-to-admitted-to-preparation
inline stages; site entry is optional context. Check approach/runner identities,
replay of the just-completed run and selection/replay of previous runs. Review
every checklist item against current evidence, including public visibility and
actual user attribution in policy/model tests, with execution mode separate.
Verify wait status appears immediately, keeps a readable reason, and visibly
confirms real stage completion (GPU ready before subsequent loading/running).
Check failure/stall status and available recovery evidence too. Record the
tested deployment, run and evidence below.
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
- User-initiated test evidence (run ID, confirmed human runner, actual approach,
  separate execution mode; editable defaults and missing-name confirmation):
- Unattended/system activity evidence (explicit system identity, execution mode
  and actual approach; no fabricated person):
- Wait-status evidence (action/run reference, immediate inline visibility,
  ongoing stage/reason and real completion transitions):
- GPU-startup UI evidence (startup shown after Run, actual readiness confirmed
  before loading/running, completed stages and matching lifecycle evidence):
- Failure/stall status and available recovery evidence:
- Website URL:
- Website source repository URL / deployed revision:
- Public-visibility exceptions (write "none", or the affected website/repository,
  explicit exception, reason and approval reference):
- Physical-test authorization/scope (source path/heading or commit URL, website
  and queue/run backend origins, station/arms, confirmed runner identity fields,
  method/task, duration, expected motion and recording/replay destination):
- Approval-context evidence (surfaced notice and escalation wording, applicable
  user invocation/selecting instruction and harness contract version/scope,
  review decision/rationale if required; redact private email from public evidence):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / matching run reference / immediate availability
  and observed playback/seeking result:
- Previous-run browser URL / selected prior run reference / replay link and
  observed playback/seeking result:
- Simulation review (corresponding run reference, website review link, what ran
  and its results, suitable replay/visualization/outputs, clear simulation label;
  or explicit not-applicable explanation if nothing executes in simulation):
- Per-run timing verification (tester/date, browser/session/network and robot
  readiness; evidence for every run in the timing table above):
- Optional diagnostic context (site entry `t_entry`, starting state and
  browser/session/network):
- `t_run` / `t_home` / `t_motion`, full Run-to-motion and post-Home-to-motion
  seconds, queue-adjusted Run seconds and separate target outcomes:
- Queue evidence (`t_queue` / `t_admit`, matched run/request/session/lease IDs,
  lifecycle links and persistent inline stages), excluded `Q_run` seconds; or
  evidenced already-admitted/no-wait with zero exclusion:
- Matched settled Home completion evidence for participating arms, or no-Home
  reason and earliest robot-ready timestamp/evidence (already ready: Run time):
- GPU launch start/ready/full interval and inline UI/lifecycle evidence, `B_run`
  / `B_home`, queue/GPU overlap `O_run`, excluded union, adjusted calculations and
  exception outcome if applicable (otherwise "none"):
- Timed screen recording / matching physical run evidence and clock correlation:
- Remaining gaps:

## Current Spotter review — October30,2026

**13/14 requirements fulfilled:11 verified and2 owner-accepted.**
The shared harness removed the former uncoached-visitor gate; normal agent UI
verification is permitted. Only requirement13(complete wait-stage evidence)
remains open. Motion and final-UI acceptance are accepted by the owner. This review supersedes historical counts/rules preserved below.
Shared template SHA256: `fa38871c059bc8e95cf7415ef9841ea5c92650b7d94d397d931bfb21ffd2391b`.

### Confirmed identity and public-source evidence

The user explicitly requested making andlyu/blupe-spotter public. The existing
repository is now public; anonymous GitHub API GET returned200/private=false at
2026-10-31T05:55:46.722791UTC. The website also returns publicHTTP200.

The owner reconfirmed Andrew and said **“Email doesn't matter.”** For this
integration, that explicit instruction overrides email collection: email remains
optional, is not an acceptance blocker, and must never be invented. Human name
and execution mode stay separate. This is a preference/acceptance override;
permission remains in the copied shared contract.

The deployed normal identity form initially showed Andrew automatically from
this visitor's owned run. The name was editable; the current user page also
contains confirmed Andrew. Email is empty and required=false; notifications are
unchecked. No final Run was submitted during the form verification.

The new client remembers names in this browser or restores this visitor's owned
run identity. It does not hardcode Andrew for strangers, and status refreshes
preserve edits. Five Node/DOM cases pass. Browser reload verification then hit
a separate initialization stall; reload persistence is unit-verified but not
claimed browser-verified. This remains within open startup/wait/final checks.
The backend and all observed public script assets returned200 and parsed; the
pre-existing loaded page's controls remain usable. No controller access, service
restart, robot queue or motion was used for these changes.

### Evidence for retained fulfilled requirements

- 1: website https://robohouse.spotter.54.209.185.15.sslip.io/; public source
  https://github.com/andlyu/blupe-spotter. Runtime2f20e42; name-default client
  implementation17151fe. Deployment RELEASE.json retains exact source hashes.
- 2: anonymous public repository proof linked below; public website HTTP200.
- 3,5,6: actual Spotter+Dream-1beta+Qwen3-VL235B approach, confirmed Andrew
  attribution, execution mode automated test separately retained in evidence.
- 4: confirmed editable name/default behavior above; email optional by explicit
  owner override. No fabricated identity or private email publication.
- 7,8: ep_df39c639fec04e59 normal-UI physical run on Robo-house
  robot-ba8413962083809c:22accepted packets/501confirmed waypoints; live arms
  visible. Successful object placement is not an additional harness requirement.
- 9,10: own175.5s physical replay ready1.475218s after end, played fully and
  sought87.75s withreadyState4/no error. Historical physical runs selected and
  replayed through the site. No optional video download is needed.
- 11: explicitly not applicable; no simulated policy episodes. MuJoCo is used
  only for numerical physical FK/IK.

### Owner-accepted motion requirement

The owner explicitly accepted requirement12: “Motion timing is just running.
this one is ok.” Existing normal-UI physical execution includes
ep_df39c639fec04e59 with501confirmed waypoints and retained actual-arm footage.
For this Spotter integration, this demonstrated running satisfies the owner's
acceptance criterion; no additional15s/30s timing exercise is required. This
records an owner override, not a newly measured timing pass, GPU exception or
research exemption. Historical timings remain intact. Queue/lease, hardware
validation,180s agent-run bounds, Stop/parking and no timed-out-motion retry
remain unchanged. The shared harness contract is not modified globally.

### Owner-accepted final UI acceptance

The owner quoted the final deployed-UI acceptance item and said “Yes, that's
ok.” Record requirement14 as accepted on the existing deployed normal-UI
physical execution and retained replay evidence. No new final physical run or
complete all-requirements re-verification is claimed. Progress-reporting
requirement13 remains open, so this is not an overall integration-complete claim.

### Remaining requirements

- 13: verify persistent real queue/admitted/Home/model transitions, completed
  stages/timestamps, failure/stall status and recovery. Latest progress notes
  alone are insufficient; the observed fresh-page stall remains open.

Identity DOM/syntax checks pass. Full suite:101passed/2subtests plus one unchanged
load-dependent1.2s replay-fixture failure(17.26s; one bounded retry16.95s). No
assertion or timeout was relaxed; unit-test count is not a harness gate.

Evidence: [public repo](evidence/repository-public-proof.json),
[form proof](evidence/identity-default-browser-proof.json),
[form screenshot](evidence/identity-default-browser.jpg).

## Historical evidence under earlier harness versions

Old timing labels, counts and requirements below describe their original
verification versions; the copied current template and review above govern now.

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
- **Historical review used the former13-item contract. Remaining gaps then:**source repository is private
  with no public-visibility exception established; fresh human join does not
  confirm prefilled known name/email defaults; entry-to-motion<=15seconds is
  unverified/missed during restart preparation; this test also missed the
  per-Run15-second target. Readiness/queue/network delay is not a research
  exemption. Every-run visual timing is not yet enforced or comprehensively
  recorded. Final all-requirements acceptance remains unchecked.
- No claim that the entire research integration is complete.

## Capacity, feedback and measured-repair follow-up — October 30, 2026

This section follows the earlier acceptance record; it does not supersede its
unmet requirements or establish integration completion.

- Deployed runtime `7060327` adds bounded retry handling for explicit retryable
  Dream `DA-2000` capacity refusals, forwards failed-move feedback to the owning
  actor, prepares only Dream-1 beta, and uses a bounded startup overlay plus a
  persistent Robo-house CPU allocation. Vendor and SDK pins, robot safety limits,
  and the other station's backend are unchanged.
- Supervisor context includes completed/failed packet intent separately from
  measured results. A requested hold while carrying is not a missed release.
- Robo-house repairs now select points only in a paired overhead RGB-D image,
  convert explicit normalized coordinates to native pixels, and use the shared
  `ApiDepth` implementation for each named arm base. Slow planning requires fresh
  depth and unchanged selected surfaces before dispatch. Calibration is still
  experimental; these checks are not an independent physical calibration claim.
- Candidate suite: **82 tests and 2 subtests passed in 7.50s**. This includes
  capacity/cancellation, failed-move recovery, camera isolation, named-arm
  measurement, expired depth, changed RGB/depth/calibration, and replay tests.
- `ep_a9106b62ab74428b`: 12packets/204confirmed waypoints,142.954976s;
  repair budget exhausted and placement failed. Its134.5s replay auto-played to
  114.922064s, then sought67.25s with readyState4 and no media error.
- `ep_4e824890fabf44b9`: 11packets/149confirmed waypoints,84.241031s;
  repair budget exhausted, orange block remained beside plate/cup. Its81s
  recording auto-played to the end and sought40.5s with readyState4.
- `ep_1e4acbab42d14ac9`: 4packets/94confirmed waypoints,50.728137s;
  a controller final-position mismatch was delivered to the base provider and
  execution continued. It later stopped before a grounded repair because depth
  expired during planning. This exposed the handoff fixed in `7060327`.
  Its own49s recording automatically opened and played to the end,readyState4.
- Normal website UI, runner `Andrew · Automated verification`, three-minute caps
  for the latter trials, no invented email and no email notifications. The robot
  was released after each attempt. All robot observations/actions used the API;
  maintenance was limited to the separate website backend.
- Evidence: `outputs/spotter/dream-capacity-second-final-status.json`,
  `dream-capacity-second-replay-proof.json`, `dream-capacity-second-replay-seek.json`,
  `dream-capacity-final-progress.json`, `dream-capacity-final-replay-seek.json`,
  `dream-grounded-run-status.json`, `dream-grounded-run-replay.json`, timestamped
  frame directories, and `dream-measured-points-diagnostic.json` in the chat workspace.
  Frame sequences are timestamped observations, not a continuous screen recording.
- Measured-repair trial on `7060327`, episode `ep_f29b605d61a941a8`:
  10packets/242confirmed waypoints,127.499408s. Geometry and integration
  checks passed, but placement failed at the three-plan repair limit. The planner
  repeatedly released a wrong marker and handed back without re-staging. Its
  own124s recording automatically played to the end,readyState4.
- Runtime `8848cbd` adds an explicit failed-handback progress guard and structured
  repair history. It permits at most two invalid-plan corrections without motion
  and retains the three-round physical limit.85tests/2subtests passed in7.88s.
  This is a port-specific recovery guard related to upstream's optional
  Spotter-H rule, which upstream does not enable by default.
- Physical trial on `8848cbd`, episode `ep_1d39af33903b4a6f`: explicit left-arm
  rectangular-block instruction,15packets/338confirmed waypoints,130.000497s.
  The base grasped the block but dropped it to the left of the plate. Spotter
  detected the failed placement and executed a measured recovery approach,
  close and lift. Original camera frames before/after that lift confirm an empty
  grasp; replanning was appropriate. The next proposal used unsupported raw
  horizontal motion and was rejected before motion, ending the run. The same
  episode's125s recording automatically played to the end,readyState4, no error.
- Candidate follow-up (93tests/2subtests passed in8.97s) corrects invalid proposals within the existing bounded
  budget, makes checkpoint verification explicit and stops on physical movement
  timeouts without automatic retry. Final deployment/test pending.
- **Historical13-item contract status was8/13.** Public source visibility, human identity defaults,
  both15-second requirements, and final all-requirements acceptance remain open.
  Physical orange-block placement has not passed. No research exception claimed.

## Current harness invocation, authorization and contract review

Invocation evidence: the user requested "It didn't work. Please get it to work"
and "Please make sure that the replay actually works before stopping", then
explicitly selected this workflow: "Lets make sure that we're using the harness
that we just created". The owner's replacement AGENTS.md also routes these
playground fixes through the shared harness. This task request plus the adopted
selecting instruction invokes the contract; reading its pointer alone does not.

The copied shared section "Authorization granted by using this harness" is the
permission grant: for this invoked task it authorizes normal queue entry with
already-confirmed identity at the existing site/backend, bounded physical arm
motion, retained camera recording/replay, Stop and normal parking/lease release.
This evidence summary adds no independent permission. Keep queue, readiness,
validation and hardware limits active; never automatically retry timed-out motion.
Current shared-template SHA256: `475957ebcfb814bd0793b1ac28b05dec6f5c36943c2294fb8e18a9d08214eb44`.

- Site/backend: https://robohouse.spotter.54.209.185.15.sslip.io/
- Queue/run/camera API: https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com
- Station: robot-ba8413962083809c (Robo-house), left/right YAM arms only.
- Method: Spotter + requested dreamlabs/dream-1-beta, managed OpenRouter Qwen3-VL235B-A22B-Instruct (earlier trials used Qwen3.8-27B).
- Test bounds: at most180seconds per newly initiated test; normal limited
  pick/place or repair motion, Stop, parking and lease release.
- Recording/replay: retained camera API frames and episode metadata on the AWS
  Spotter backend under its private replay cache, replayed through the same site;
  normal public run attribution/history and the platform's standard archive path
  remain enabled. No separate email notification or recipient is added.
- Identity consent: the owner said "if you use the robot, the name is Andrew" in
  this chat. The confirmed name `Andrew` is submitted only to this normal site
  and its queue/run API, where runner attribution is public as already requested.
  Execution mode is recorded separately as `automated test`; no email is provided
  or invented. Historical runs used `Andrew · Automated verification` under the
  earlier contract; preserve their original records rather than rewriting them.
- New test notices and any tool approval context must repeat the task/harness
  invocation, applicable contract wording, concrete scope and confirmed identity.
  An explicit review denial must be reported and cannot be bypassed or retried
  merely because documentation changed. No new approval is being requested here.
- Simulation: not applicable. There are no simulated policy episodes, replayed
  simulation trials, resets or privileged simulation success signals. MuJoCo is
  used only as a numerical FK/IK model for physical trajectories, not as a policy
  rollout environment. Offline camera/plan checks are labeled diagnostics.
- Historical review: **9/15 verified after the new-contract test**. The run retains
  confirmed name Andrew; execution mode is separately recorded as automated test
  in the task evidence. Human identity defaults/confirmation, public source
  visibility, both15-second paths, detailed persistent wait-stage verification
  and final all-requirements acceptance remain open.
  Simulation item is checked as explicitly not applicable. Physical task placement
  remains unverified successful. No GPU-launch exception claimed for warm runs.

## Lift-intent and vision verification follow-up — October 30, 2026

- Runtime18ff10c was physically tested in ep_a904ffd2e14a461e as Andrew;
  execution mode was automated test, separately recorded. No email or
  notifications.14accepted packets/337confirmed waypoints,180.986755s;
  normal180s limit parked the robot and disabled torque. Placement failed.
- That same episode has its own176s sampled physical recording,
  SHA25686fbe1376e06b8796904c1fa8b12af9ff7006b53372fa6a1a1013f71a0f7b276.
  Locally ready1793420880.7887242 versus runner end1793420879.4756432:
  1.313081s after end. Website history selection auto-played0.0462→5.5888s,
  played to176s, and native seeking reached88.1585s and14.08s with
  readyState4/no media error. Playback screenshot and JSON are retained in
  outputs/spotter/dream-validation-run-replay*.
- The new VERIFY rule incorrectly treated an empty-hand clearance lift as a
  grasp test. Typed lift intents now separate clearance from grasp_check and
  survive schema validation into the measured-feedback checkpoint.
- Recorded-case diagnostics preserved all rejected prompt/history/model variants.
  An initial held-object fixture was excluded because its image occurred
  mid-packet while the supplied measured receipt was older; raw results remain.
  The corrected control uses settled feedback at1793419282.4974554 and
  original images near1793419283.1, before the next packet at1793419285.557553.
- Qwen3-VL235B-A22B-Instruct passed the three narrow held/missed/clearance
  controls with two latest measured windows. This is an open-weight model
  change on the same managed OpenRouter service, not a paper reproduction,
  benchmark or reliability claim. Other tested candidates failed at least one
  control and were not selected.
- Commit2f20e422a191cfdadd02c7cf0dc0170bf95dd995 adds typed lift intent,
  supported API parameters and the Robo-house model configuration. Four new
  regressions failed before implementation.97tests/2subtests passed in10.40s.
  The initial full-suite run exposed an unchanged replay fixture's1.2s
  wall-clock dependence: base1/20failures, candidate0/20; a forced1.3s
  first-frame delay reproduces it. One bounded full-suite rerun passed;
  no assertion/timeout was relaxed. Physical verification of2f20e42 is recorded below.
- All15requirements reviewed above; six remain open. No integration-complete
  claim and no GPU-launch exception. No timed-out movement was retried.

### Current deployed physical and owner-progress evidence

- Runtime2f20e42, episodeep_df39c639fec04e59, confirmed runner Andrew,
  execution mode automated test separately recorded; normal UI,180s cap.
 22accepted packets/501confirmed waypoints,180.697956s. Normal duration
  limit parked the station and disabled torque. No pool_full, missing failed-move
  hook or malformed-plan termination. The task was not completed.
- The vision supervisor screened the policy but did not intervene during this
  attempt, despite the task remaining unfinished. This run does not validate
  physical repair or reliable placement with the new model. The three recorded
  lift-control checks are narrow diagnostics only. No automatic motion retry.
- Same-run replay175.5s/351frames, source API camera samples at2fps, pauses
  retained. Ready1793424042.665982 versus runner end1793424041.1907642:
 1.475218s after end. SHA256aba765026c275c4a423c181c3794a96f5088ce8864ed6af9666a96507ed295a1.
  Native browser auto-played to166.2253s and then175.5s,readyState4.
  Native midpoint seek87.75s completed withreadyState4/no media error.
- Replay link:
  https://robohouse.spotter.54.209.185.15.sslip.io/?run=ep_df39c639fec04e59&robot_id=robot-ba8413962083809c
- Progress investigation: the deployed pinned helper already accepts progress
  events. An initial hypothesis based on a different checkout was rejected. The
  public decision feed was empty because conversation sharing is disabled.
  The owner display now reads their existing private GET /api/status and shows
  Spotter activity below Run. No public sharing is enabled. Two regressions
  failed before the fix;100tests/2subtests passed in12.55s after matching the actual terminal status shape, including
  no-publication/read-only assertions and the unchanged YAM1 branch.
- Historical source checklist was9/15. Open: public source visibility/exception, human
  name/email defaults/confirmation, uncoached entry-to-motion15s, every Run's
  motion15s, full persistent wait-stage completion/stall verification and final
  all-requirements acceptance. Physical task placement remains unsuccessful.
  Frame sequences are timestamped observations, not continuous screen video.

### Startup latency follow-up — October 31, 2026

- Owner request: “Lets get as close to15 as possible.” Existing owner acceptance
  remains; this optimization does not reopen waived acceptance gates.
- Runtime4d58800 reuses a successful authenticated Qwen readiness check for at
  most60s, bound to endpoint/model/API style/key. Page polling refreshes it before
  expiry; changed credentials, stale results and failed refreshes require a new
  successful check. No images, visitor identity or policy state are cached.
- Robo-house CPUQuota150% permits camera/replay work and resident IK to overlap;
  CPUWeight500 and other integrations are unchanged. Normal systemd restart
  took65.528s; cold configure18.134s and full preparation119.482s, without a lease.
- Full candidate suite:104tests and2subtests passed in13.08s. Two new readiness
  reuse/invalidation/single-flight regressions failed before implementation.
- Final physical timing trial: ep_0aedb22cd43b4592, Andrew, automated test mode,
  no email/notifications,60s cap. Initial Run1793431341.097, final submission
  click1341.430; first trajectory submission1357.514639 (16.418s after initial
  Run), gateway acceptance1357.708440. Sampled live UI captures show actual
  method-driven arm movement by18.183s after initial Run. Capture cadence0.5s;
  host/local clock diagnostic midpoint offset0.653s with0.637s half-RTT bound.
  Submission/acceptance are not counted as physical onset.
- Joined journal1342.236 and matched jetson_leased1352.094 identify this
  session's observed admission interval. These journal boundaries are diagnostic
  proxies, not a claim of exact server queue-entry timestamps. Settled Home
  feedback was reconciled at1352.746. No strict every-run numeric harness pass
  is claimed from these sampled captures; previous owner acceptance remains.
- Eight accepted packets/192confirmed waypoints,60.125s; normal time limit
  parked/released the robot. Placement was not completed. Final status: disabled,
  empty queue. No hardware checks or model/action cadence were removed.
- Same-run58.5s replay played to its end withreadyState4/no error; native
  midpoint seeking reached29.25s withreadyState4/no error:
  https://robohouse.spotter.54.209.185.15.sslip.io/?run=ep_0aedb22cd43b4592&robot_id=robot-ba8413962083809c
- Baseline first-submission latency28.415s after its final Run, CPU-only trial
 21.032s, final16.085s (16.418s including the initial identity-form Run click).
  Different load/network/scene conditions prevent attributing all improvement
  to CPU quota alone. Evidence: outputs/spotter/start-latency in the chat workspace.
- Status remains13/14fulfilled (11verified,2owner accepted). Detailed persistent
  wait-stage reporting remains required/open at the owner's lower priority.

### Long's model guidance and control-contract gate — October31,2026

- User supplied Long's clarification: the paper uses Qwen3.8, not Qwen3-VL;
  establish the intervention path with GPT-6.1 sol and a worked image/text example.
  Robo-house candidate uses qwen/qwen3.8-27b for screening and
  openai/gpt-6.1-sol for judge/locate/repair/verify through the existing OpenRouter
  endpoint/key. YAM1 configuration and its running process are unchanged.
- Authenticated text-only checks returned the exact requested models;0.0001692USD
  combined reported cost. A recorded-scene three-call diagnostic cost0.0200797USD.
  The single-frame screen/judge returned pass, which is not a detector benchmark.
  Sol's repair used CURRENT BLOCK from the current schema, passed point resolution
  and validate_plan, and sent no action. All outputs/usage are retained in
  outputs/spotter/long-guidance and the backend's spotter-long-guidance-01a18b9e.
- Repair output is constrained to supported steps and exact currently measured
  point names. Existing bounds, calibration/fresh-depth checks, IK, hardware
  protection, cancellation, hand-back rules and physical repair budgets remain.
  The real-image one-shot shows a proposed restaging correction from failed
  ep_f29b605d61a941a8; it is explicitly not successful/executed task footage.
- Current shared CONTROL-CONTRACT.md is adopted independently of the historical
 14-item checklist. Its two additional requirements above bring the inventory
  to16. Physical task acceptance and detailed wait reporting remain open; previous
  owner identity/email, timing and final-UI acceptance preferences are preserved.
- Required deployment gate: PYTHON=/home/ubuntu/blupe-spotter/.venv/bin/python
  bash blupe/deploy/preflight.sh.144tests/2subtests passed in15.48s. A regression
  failed on the pinned generator because uninstructed joints drifted3.55e-15deg;
  the repair wrapper now holds them exactly and preserves validated gripper
  endpoints. Strict[0,1], finite checks and joint/workspace bounds are unchanged.
- Command matrix: both arms' gripper0/1/partial/near-boundary targets from
 0.9992793312193716; multi-waypoint nudge/lift/move/rotate, grounded point binding,
  base-Dream joint chunks, first/interior/final samples, contiguous IDs,10Hz
  pacing and endpoint FK within the unchanged SDK2mm/orientation tolerance.
  Invalid requests/starts, malformed plans, negative interpolation-residual
  reproduction and exhausted budgets assert zero actuator submissions.
  Fresh/changed depth/calibration and cancelled handoff regressions are included.
  The numeric residual case is a minimal reproduction of the shared contract's
  documented defect, not a claim that this integration physically sent it.
- Canonical client: remote-yam e8158b7cfcbb90b2824dfc73e632b537bdfd942c;
  src/remote_yam/session.py SHA256
 2e1735da0b528e57369a46c43e4ce831e798d7d3adba19b8f2c18684f07515e1.
  No vendor or solver-tolerance change. Physical verification follows below;
  no physical task pass or integration-complete claim is made.

### Deployed two-stage physical verification

- Runtime/frontend5d7c743c6e8ba0c8e0ebbf5ee960d3b3b447498a;55owned files
  matched the release manifest. The exact committed-source preflight passed
 144tests/2subtests in15.08s before deployment. Normal Robo-house restart72.364s,
  configure17.695s and full solver preparation140.319s. YAM1/main service PIDs and
  lifetimes stayed unchanged; model preparation held no robot lease.
- Normal website UI, episodeep_f156d0ea4f494d2a, Andrew, separate automated-test
  mode, no email or notifications,180s cap. Active run config confirmed
  screening_model=qwen/qwen3.8-27b and intervention_model=openai/gpt-6.1-sol.
- Qwen flagged failed grasps; sol confirmed a failed pickup/placement and planned
  a measured left-arm restaging move. That repair was accepted and executed,
  followed by policy handback. The later post-handback visual check reported
  verified restaging; it did not establish grasp or task success. On a later
  intervention sol found no valid orange-block depth point and returned control
  without inventing a target. No repair-format rejection was observed.
-12accepted packets/285confirmed waypoints,180.489s, normal run-duration stop,
  parking/release, disabled station and empty queue. Orange block placement
  failed. Missed grasps and unavailable target depth remain; calibration remains
  experimental. This verifies repair-format/execution behavior, not reliable
  manipulation or the paper's benchmark results.
- Initial Run1793469622.971, confirmation9623.297; joined journal9624.427,
  jetson_leased9634.594, reconciled Home feedback9635.225. First trajectory
  submitted9641.874 (18.903s after initial Run), accepted9642.080. Submission is
  not physical onset;0.5s sampled UI frames retain live motion. No new strict
  every-run numerical pass is claimed; the owner's timing acceptance persists.
- Same-run176s/352frames at2fps from retained actual camera API samples;
  SHA2563751ff1294a8cc175967d85b03813b8b4a7125bdc2be5cba2128e038a3a3b879.
  Ready1793469815.610789 versus runner end9814.999035:0.611754s after end.
  Browser playback observed105.3353→176s/ended, native midpoint seek88s,
  readyState4/no media error. Replay:
  https://robohouse.spotter.54.209.185.15.sslip.io/?run=ep_f156d0ea4f494d2a&robot_id=robot-ba8413962083809c
- Evidence: outputs/spotter/long-guidance in the chat workspace: source/provider
  checks, original-frame hashes, required preflight, timed UI samples, early/mid/
  terminal status, intervention events, replay metadata and playback/seek proof.
- Current inventory14/16fulfilled:12verified and2owner-accepted. Open: physical
  task acceptance and detailed persistent wait reporting (retained at lower
  priority). The integration is not complete.


## BluPe shared history — November 1, 2026

Invocation: “When we reun spotter, these runs should also show up in blupe”,
followed by “right, but dont' we have access to spotter's runs throguh blupe?”
The user-adopted harness selects the requested playground-fix workflow. Its
“Authorization granted by using this harness” contract authorizes the task's
public source and website updates. This change uses retained public runs; it
submits no runner identity and starts no physical run or model inference.

- [x] Existing Spotter receipts are visible in BluPe's normal history and
  table/cloud catalogs: public GET checks at 2026-11-01T12:07:22Z returned
  21 runs with model `spotter/dreamlabs/dream-1-beta` and preserved runner names.
- [x] Retained episode `ep_f156d0ea4f494d2a` is readable through BluPe with
  Andrew attribution and the recorded stopped/time-limit result. Its 176s
  replay served HTTP206 for bytes1024–2047 of7,957,115 on the BluPe origin.
- [x] Future receipts are read from the existing integration database on every
  history request. Offline regression adds a receipt after the first catalog
  read and verifies immediate inclusion, processing state and no duplication.
- [x] Source reads are SQLite read-only and scoped to Robo-house. Only public
  run metadata, recorded model, name and result are projected; email and private
  provider configuration are excluded. Replay hash/range checks are covered.
- [x] Public shared source merged and website deployed. Both Spotter services
  retained their original PIDs; no Spotter model configuration changed. Main
  website restart3.784s after all four configured queues were observed empty.

Public website: https://playground.blupe.io/
Shared source: https://github.com/andlyu/blupe-remote-bots/pull/256
Shared merge: `c0bc07c0d501b6d8340c07e3311c9d86cc7e2cf7` (change3067782).
Implementation: `codex-runner/docs/integration-run-history.md` in that repository.
The deployed overlay preserves other website changes; its source hashes and
HTTP receipts are retained in `outputs/spotter-blupe-history-01a196bd` in the
shared working checkout and `/home/ubuntu/spotter-blupe-tests-01a196bd` on the
website host. Original data stores and recordings are not copied or migrated.

Validation:75relevant Python tests+10subtests;343JavaScript tests; full isolated
server suite1385passed/100skipped/181subtests and one display-dependent failure.
That remaining viewer test passed separately with `MUJOCO_GL=egl` (5.57s).
The baseline reproduces the unrelated local environment failures. No new
physical execution, placement-success or numerical motion-timing claim.

Broader integration acceptance remains14of16existing requirements fulfilled,
including earlier owner acceptances; physical manipulation/task acceptance and
detailed persistent wait reporting remain unchecked. The five checks above
verify this history fix, not completion of the entire research integration.

Browser verification of the deployed normal UI: select Table, filter to Spotter,
open “Put red block into cup” (`ep_259657d9252c4482`). Playback advanced3.966599s,
then sought52.250828s of104.5s with readyState4 and no media error. Source remained
the exact BluPe-origin immutable replay URL. The11.419s browser command closed
its own tab; no robot run or assessment vote. Screenshot and command log are
retained with the receipts above. Earlier checkbox-wait timeout was a test-flow
ordering issue (the filter was still closed); corrected flow passed.


## Configurable repair recovery — November1,2026 (candidate)

Invocation: owner requested visitor-editable run duration and repair limits,
600s/16steps/6rounds defaults, missing-depth clearance followed by fresh
measurements, and complete supported corrections after repeated failed handbacks.
The user-adopted shared harness's Authorization granted by using this harness
covers the integration's public source/site update and bounded normal-queue
verification. This expands the earlier180s task scope to600s on Robo-house,
robot-ba8413962083809c, left/right YAM arms, existing site and queue/run API.
Confirmed runner Andrew; no email or notifications; automated execution mode
separate. Physical motion/recording is pending candidate release checks.

- Default600s (editable60–600),16steps/plan (1–32),6plan rounds/intervention
  (1–12); existing8intervention ceiling unchanged. Selected values are validated
  before admission, applied per adapter/visitor and retained with model roles in
  run configuration. Old station pages remain compatible with shared assets.
- Clearance lifts are verified from settled feedback, then fresh paired RGB-D
  is captured and points reselected before further repair or handback. Remaining
  targets from the old view are discarded. No new depth source, guessed XYZ,
  relaxed calibration/bounds or automatic timeout retry is introduced.
- Explicit final policy steps still hand back. Segments without policy retain
  Spotter ownership for another bounded observation/plan round. A grasp-check lift
  must visibly lift the intended object before transport. Prior intervention
  history is retained; the prompt and annotated image example support full
  approach/grasp/lift/transfer/release/withdrawal where evidence permits it.
  The example remains a proposed, unexecuted correction from a failed scene.
- Red reproduction on9e6022c:5failed/1passed in0.99s (command1.787s), including
  premature handback after clearance, lost intervention history and eight-step
  rejection. First candidate preflight167passed/2subtests in16.54s
  (command17.461s); final committed-source gate follows before deployment.
- Current shared harness also adds explicit researcher model-choice/provenance
  evidence. The owner's prior adopted choices remain Dream-1 beta policy,
  qwen/qwen3.8-27b screening and openai/gpt-6.1-sol intervention via OpenRouter;
  no model substitution is made here. Requested IDs are retained as provider IDs,
  not claimed immutable weight revisions. Full new model-provenance/Model-field
  acceptance is not re-certified by these repair changes.
- Existing physical task acceptance and detailed persistent wait reporting stay
  open. No fresh physical task success, new numerical motion-timing pass or
  whole-integration completion is claimed at this candidate stage.
