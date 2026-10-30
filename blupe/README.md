# Spotter on Blupe

This separate application ports the **Spotter supervision approach** to physical
YAM arms. It preserves the upstream Spotter source and licenses, and pins
`andlyu/blupe-remote-yam` as a Git submodule for camera capture, session leases,
trajectory submission, measured execution feedback, IK and gateway checks.
It is an embodiment port, not a reproduction of the paper's benchmark results.

The **DreamZero YAM1** or **Dream-1 Robo-house** policy leads. A Qwen-compatible vision service
screens completed windows in parallel; suspicious windows go to a confirming
judge. The policy may lead supervision by at most two windows. Confirmed faults
pause the policy at a packet boundary, plan from the **current** scene, execute
YAM primitives, verify outcomes and return control. Supervisor failure stops
new commands rather than silently turning the run into policy-only execution.

Both modes use the same YAM transport. If a frozen-policy segment exceeds the
saved 10 Hz joint-step/velocity envelope, the adapter inserts intermediate
samples while retaining every target in order. It never clips arm-joint targets;
the gateway still validates the whole path and can reject unsafe motion.

Each station also offers the same **policy alone** as a baseline. This is
a selectable baseline, not a claim that uncontrolled live trials are comparable.
Harness VLA/RPent remains a future comparison, not a second implemented mode.

## Run

```sh
git submodule update --init --recursive
python3 -m venv .venv
.venv/bin/pip install -r blupe/requirements.txt
export PYTHONPATH="$PWD/blupe"
# Configure server-owned services using blupe/deploy/config.env.example.
.venv/bin/uvicorn spotter_yam.app:create_app --factory --host 127.0.0.1 --port 8820
```

Without model configuration the page still shows live robot cameras, and Run
returns a setup error before creating a queue entry. A configured host warms
the supervisor before queue admission. DreamZero also warms its checkpoint
before admission. Dream-1 visitor handles activate after lease grant,
overlapping native robot preparation; only one visitor owns its SDK worker.
Visitors never receive either model credential or the robot session capability.

Dream's SDK also prepares a local inverse-kinematics solver before its first
prediction. The default isolated worker uses a new private JAX cache per visitor,
which can repeat expensive compilation. The hosted Robo-house recipe therefore
sets a private, service-owned `JAX_COMPILATION_CACHE_DIR`. A measured fresh process
still took about88seconds to configure after a successful cold prime; disk caching
alone did not establish fast startup. The recipe also sets
`SPOTTER_DREAM_RESIDENT_DIR` to retain one fully prepared process. At service start,
the pinned pool prepares both checkpoint policies and both trajectory-kernel
structures in the background, without a robot lease or model prediction. The
page reports preparation status; launch stays unavailable until the pool is ready.

The pool lends an exclusive handle after lease grant. It drains in-flight replies
and resets SDK episodes before another visitor can use the process. Failed cleanup
destroys the process; bounded recovery keeps launch unavailable until preparation
succeeds. Credential changes invalidate readiness. Shutdown closes the pool after
visitor cleanup. The solver remains compiled, while camera history, model sessions
and action blending are reset. Solver objectives, limits and branch selection are
unchanged. Persistent directories must remain private and service-owned.

For a separate no-motion disk-cache diagnostic, use the same trusted SDK, cache
directory and `YAM_DREAM_BLOCKWISE_IK=1` environment as the service:

```sh
PYTHONPATH=blupe python3 -m spotter_yam.prepare_dream
```

This command compiles both pinned trajectory-kernel structures from synthetic
rest poses. It does not read robot observations, request model actions, lease a
robot or send motion. Repeat it in a fresh process to measure cache reuse before
an API-backed physical run. It preserves the SDK's solver configuration, limits
and runtime branch selection; caching does not establish task success.

The VLM URL is an administrator-controlled OpenAI-compatible base serving
chat completions. The self-hosted setting uses
Qwen3.8-27B-FP8 (served name `qwen38`). The YAM prompts replace Franka-specific
millimetre aperture assumptions with normalized grippers and visual evidence.
Frozen simulator lessons are not blindly applied to physical YAM geometry.

The pinned DreamZero checkpoint remains **YAM1 only**. Robo-house uses the hosted
`dreamlabs/dream-1-beta` API with its own saved controller geometry and calibration.
Dream-1 is a hosted policy; its model weights are not supplied by this repository.
The qualified self-hosted Qwen supervisor runs on RunPod serverless GPUs. The
AWS web backend sends images and measured state to the configured supervisor;
neither model runs on the YAM.

### Managed Qwen through OpenRouter

OpenRouter support is implemented; switching the live hosts requires a funded
server-owned key and live validation. `deploy/robohouse.env.example` contains
the complete target configuration:

```sh
SPOTTER_VLM_API_STYLE=openrouter
SPOTTER_VLM_ENDPOINT=https://openrouter.ai/api/v1
SPOTTER_VLM_MODEL=qwen/qwen3.8-27b
SPOTTER_VLM_KEY_FILE=/home/ubuntu/.config/openrouter/api-key
```

Install the key as an owner-readable credential file outside the repository.
The browser never receives it. OpenRouter requests use its normalized reasoning
setting with reasoning disabled, JSON output, and routing that requires support
for all requested parameters. Camera frames retain the same three-camera format.
The selected model is Qwen3.8-27B; provider quantization/revision can differ from
the pinned self-hosted FP8 deployment, so this is not an identical checkpoint run.

Before queue admission, the managed supervisor makes a small authenticated
completion request (up to32output tokens) to verify model access and credits.
The public model catalog alone cannot establish readiness. Authentication,
credit and API failures end preparation with a sanitized error; they do not
enter the self-hosted twenty-minute GPU-warmup retry loop. A readiness check
does not establish image understanding or physical task success: validate a
three-camera inference and a bounded real run before qualifying the migration.

For self-hosting, keep `SPOTTER_VLM_API_STYLE=vllm` (the default); its model
discovery/warmup behavior remains available. Both providers fail closed if
supervision fails during execution.

Dream-1 retains its live 5 Hz three-camera history during policy execution.
Before handback after a Spotter repair, the adapter resets the SDK episode and
discards prior camera history and action-smoothing anchors. It then requests a
new prediction from fresh measured inputs. Stop releases the exclusive visitor
handle; the resident pool drains and resets its episode before reuse.

## Validation and hosting

Hosted page: [Spotter on Blupe](https://spotter.54.209.185.15.sslip.io/).
Robo-house: [Spotter + Dream-1](https://robohouse.spotter.54.209.185.15.sslip.io/).
This dedicated virtual host uses the existing Blupe server, with its own backend
and repository. `spotter.blupe.io` can replace it when a DNS record is available.

```sh
PYTHONPATH=blupe python3 -m pytest blupe/tests -q
node --check blupe/static/site.js
```

`blupe/deploy/spotter.service` installs a separate loopback-only service on the
existing Blupe host. It does not modify or restart the main playground backend.
The separate `spotter-robohouse.service` uses port8821 and
`/etc/blupe-spotter-robohouse.env` (see `robohouse.env.example`).
Set `SPOTTER_OTHER_STATION_ORIGIN` on each instance to link the station picker.
Use a separate HTTPS virtual host and preserve Host/Origin and WebSocket headers.
Keep one worker: visitor sessions, credentials and supervisor state are in memory.
Do not put credentials in this repository or in browser settings.
Public hosting keeps the shared runner's private, ephemeral visitor recordings;
`SPOTTER_RECORDINGS` applies only to localhost station hosting.

The self-hosted inference configuration pins the Qwen model revision and official vLLM image.
That image uses its native `vllm serve` command and requires CUDA 13.0 or newer.
The RunPod model endpoints allow at most one worker each and scale to zero after five
idle minutes. Initial startup includes model loading; preparation precedes robot
queue admission.

Physical qualification must record an actual model-backed session, executed
waypoints, settled feedback and video. Passing unit tests, a live camera, a
successful inference or a served page alone does not establish task success.

Sources: [Spotter paper](https://arxiv.org/abs/2609.36808),
[upstream code](https://github.com/zqc3117/Spotter),
[Blupe API](https://blupe.io/docs/robot-api/),
[Harness VLA](https://arxiv.org/abs/2607.08448).
