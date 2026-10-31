# Research integration completion checklist

Agents and humans: read this before integrating a paper or method. Copy this
template into the integration's documentation, fill in the evidence, and check
each box only after verification. All boxes must be checked before declaring the
integration complete. Before the final handoff, review and update every item with
evidence. Report checklist status, evidence links, unmet items and explicit
exceptions; leave unfinished requirements unchecked and do not describe the
integration as complete.

## Standing authorization for physical playground tests

### Authorization granted by using this harness

The owner defines use of this harness as a task-scoped authorization grant.
When the user requests a research integration, playground fix or verification
through this harness, that invocation authorizes the agent to carry out the
covered workflow below. A task requested under user-adopted instructions that
select this harness also counts: retain the task request and the selecting
instruction as the invocation evidence. Reading or discovering this file alone
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

These actions are part of the invoked workflow. Do not ask for separate
permission for each covered identity submission, run, movement or recording.
Reuse confirmed identity/defaults; ask only for missing or ambiguous identity
or scope outside this contract. Keep execution mode separate from human
identity. The grant covers the task's integration and existing queue/run
destinations, not unrelated recipients or publication of private email.
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

Harness invocation does not override enforced sandbox, managed-policy or tool
permissions. Use the normal permission mechanism when required. If automatic
approval review explicitly denies an action, do not retry it through another
route. Report the exact denied action and stated reason, acknowledge the
invocation and contract already present, and leave physical verification
unverified. Continue independent work or a materially safer alternative;
otherwise request only the specific unblock. A documentation update alone does
not authorize retrying an already-denied action. Keep sandbox and reviewer
policy intact.

References: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance)
and [Auto-review context and denials](https://learn.chatgpt.com/docs/sandboxing/auto-review).

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
- [x] Policy/model tests initiated by a person retain that actual user's
  confirmed name as runner. Use available identity and editable name/email
  defaults; require the real name to be provided/confirmed if missing before
  testing or running. Do not substitute `Anonymous`, `Autonomous` or `Automated`
  for that person. Record execution mode (such as `automated test`) and actual
  approach separately from human identity. Genuinely unattended/system activity
  has an explicit system identity; never fabricate a person's name or email.
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
- [ ] The website is intuitive: a new visitor, without coaching, can find how to
  run the method and have the physical YAM arms actually executing it within
  **15 seconds of entering the website**, verified as described below.
- [ ] **Mandatory for every run:** after the person clicks Run, the physical YAM
  arms start actual method-driven motion within **15 seconds**, unless that run
  requires launching a GPU as documented below. Verify and record every run;
  a sampled demonstration is insufficient.
- [ ] Every meaningful wait after a website action is immediately explained in
  a persistent inline status/progress area at that action (below Run in the run
  panel for launches). Show the current stage, a plain-language reason and real
  stage completion, with honest failure/stall status and available recovery.
  Verify the detailed wait-stage behavior below.
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
`t_motion - t_run <= 15 seconds`, subject to the GPU-launch exception below.
An acknowledgement, accepted request, queued status, submitted action or inference
starting is insufficient.

Record every run below (add rows), including visual evidence of the click and
motion. Mark the outcome as pass, missed target, unverified or exception.
Exceptions are not fulfilled <=15-second runs.

**GPU-launch exception:** a run that requires launching/provisioning a GPU (for
example on RunPod) may exceed this Run-click target. Record why the GPU had to be
launched and its startup evidence for that run. Keep the full elapsed time from
Run click to observed physical motion; do not reset the clock when the GPU becomes
ready. If GPU startup causes the target to be missed, label the outcome as an
exception. If the GPU is already available, the normal 15-second requirement
applies. This exception does not change the site-entry measure above.

Other exceptions require a specific justification grounded in the integrated
paper/research, explaining why it applies to that run, plus a supporting source
citation/link and relevant section/page. Outside the explicit GPU-launch case,
slow loading, queueing, setup or infrastructure delay is a missed target, not in
itself a paper/research-grounded exemption.

| Run reference | Run click (`t_run`) | First observed method-driven arm motion (`t_motion`) / visual evidence | Elapsed seconds | Outcome |
| --- | --- | --- | --- | --- |
|ep_06f89dc0969846ba|2026-10-30T22:50:11.042Z (initial Run);22:50:15.755Z (join submit)|Live arms visibly moved by22:50:59.303Z. First onset not captured. Runner started22:50:27.776725Z, already16.7357s after initial Run.|>=16.7357s; motion visually observed by48.261s|Missed target; no research exception|
|ep_02da743f80584421|1793413885.154 (UTC epoch seconds); join1793413900.886|No method packets or confirmed waypoints; prediction timed out. Initial entry1793413868.288.|No method motion verified|Missed target; no exception|
|ep_a9106b62ab74428b|1793414539.810; join1793414547.705|Runner began1793414560.276246, already20.466s after Run; actual arms and204confirmed waypoints verified.|>=20.466s before possible method motion; first onset not captured|Missed target; no exception|
|ep_4e824890fabf44b9|1793416374.021; join1793416383.448|Runner began1793416395.020409, already20.999s after Run;149confirmed waypoints. Entry1793416321.547.|>=20.999s before possible method motion; first onset not captured|Missed target; no exception|
|ep_1e4acbab42d14ac9|1793417703.636; join1793417710.827|No packets at1793417725.963; actual method arm pose verified by1793417749.723. Entry1793417683.958.|No packets at22.327s; visible motion by46.087s|Missed target; no exception|
|ep_f29b605d61a941a8|1793418325.081; join1793418325.196|First policy packet became ready1793418341.631020; entry1793418316.543.242confirmedwaypoints and actual arms visible.|>=16.550s before method motion; first visual onset not captured|Missed target; no exception|
|ep_1d39af33903b4a6f|1793419228.350; join1793419228.433|Initial trajectory_0 accepted1793419247.0320456;338confirmedwaypoints and actual left-arm motion. Entry1793419218.791.|>=18.682s before method motion; first visual onset not captured|Missed target; no GPU-launch exception|
|ep_a904ffd2e14a461e|1793420687.332; join1793420687.410|Earliest retained packet submission1793420718.6892223 is not proven to be the first packet;337confirmedwaypoints and actual arms visible. Entry1793420524.123 includes preparation and browser recovery.|First motion onset not measured|Unverified15s target; no exception|
|ep_df39c639fec04e59|1793423835.266; join1793423848.829|Runner started1793423860.492808; actual method-driven arm motion visible by1793423900.662. Entry1793423793.617.|>=25.227s before runner start; observed motion by65.396s; first onset not captured|Missed target; no exception|

- Exception record (repeat for each affected run):
- Exception category (GPU launch or paper/research-grounded):
- Affected run reference:
- Specific reason and why it applies to this run:
- GPU-launch evidence (if applicable: provider, instance/job reference,
  launch/ready timestamps and startup log/link):
- Supporting paper/research source (for other exceptions: citation/link and
  relevant section/page):

## Visible progress while waiting

Use a compact persistent inline status area directly below Run in the existing
run panel; keep other meaningful waits beside their initiating control. Show the
current stage and why it is taking time immediately, keep it readable throughout
the wait, and visibly mark completed stages as actual lifecycle state advances.
A transient toast alone or a generic spinner is insufficient.

When a model requires a new GPU, show only the stages that actually exist:
`Starting GPU` / "We're launching a GPU on RunPod for this model" -> `GPU ready`
-> `Loading model` -> `Running`. GPU startup must be explicit immediately after
Run; visibly confirm actual GPU readiness before subsequent loading/running and
retain completed-stage confirmation. Use the applicable provider/model wording.
On failure or a stalled stage, state the known condition honestly and show an
available recovery action, such as retry or cancel where supported. Do not invent
percentages, ETA or completion, or expose irrelevant infrastructure internals.
This transparency requirement adds no timing exemption or clock reset.

## Final verification before completion

Open the deployed website and its associated source repository. Use the normal
visitor flow to join, run the integrated method on physical YAMs and watch the
actual arms live. Check both 15-second measures, approach/runner identities,
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
  motion/recording authorization and separate existing identity consent if needed,
  review decision/rationale if required; redact private email from public evidence):
- Physical execution (date, method/configuration, YAM station/arm IDs, run ID):
- Live physical arm footage (website location and evidence link):
- Just-completed replay URL / immediate availability evidence (same physical run):
- Previous-run browser URL / selected prior run and replay evidence:
- Simulation review (corresponding run reference, website review link, what ran
  and its results, suitable replay/visualization/outputs, clear simulation label;
  or explicit not-applicable explanation if nothing executes in simulation):
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
- Current review: **9/15 verified after the new-contract test**. The run retains
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
- Source checklist remains9/15. Open: public source visibility/exception, human
  name/email defaults/confirmation, uncoached entry-to-motion15s, every Run's
  motion15s, full persistent wait-stage completion/stall verification and final
  all-requirements acceptance. Physical task placement remains unsuccessful.
  Frame sequences are timestamped observations, not continuous screen video.
