# Spotter on Blupe

This separate application ports the **Spotter supervision approach** to physical
YAM1 arms. It preserves the upstream Spotter source and licenses, and pins
`andlyu/blupe-remote-yam` as a Git submodule for camera capture, session leases,
trajectory submission, measured execution feedback, IK and gateway checks.
It is an embodiment port, not a reproduction of the paper's benchmark results.

The frozen **DreamZero YAM1** policy leads. A Qwen-compatible vision service
screens completed windows in parallel; suspicious windows go to a confirming
judge. The policy may lead supervision by at most two windows. Confirmed faults
pause the policy at a packet boundary, plan from the **current** scene, execute
YAM primitives, verify outcomes and return control. Supervisor failure stops
new commands rather than silently turning the run into policy-only execution.

The page also offers the same **DreamZero policy alone** as a baseline. This is
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
the supervisor and the exact pinned DreamZero checkpoint before queue admission.
Visitors never receive either model credential or the robot session capability.

The VLM URL is an administrator-controlled OpenAI-compatible `/v1` base serving
chat completions and model discovery. The paper's open-source setting uses
Qwen3.8-27B-FP8 (served name `qwen38`). The YAM prompts replace Franka-specific
millimetre aperture assumptions with normalized grippers and visual evidence.
Frozen simulator lessons are not blindly applied to physical YAM geometry.

The pinned DreamZero checkpoint is for **YAM1 only**. Robo-house requires a
compatible policy checkpoint and its own verified geometry; the app rejects
that identity rather than relabelling a YAM1 checkpoint.

## Validation and hosting

```sh
PYTHONPATH=blupe python3 -m pytest blupe/tests -q
node --check blupe/static/site.js
```

`blupe/deploy/spotter.service` installs a separate loopback-only service on the
existing Blupe host. It does not modify or restart the main playground backend.
Use a separate HTTPS virtual host and preserve Host/Origin and WebSocket headers.
Keep one worker: visitor sessions, credentials and supervisor state are in memory.
Do not put credentials in this repository or in browser settings.

Physical qualification must record an actual model-backed session, executed
waypoints, settled feedback and video. Passing unit tests, a live camera, a
successful inference or a served page alone does not establish task success.

Sources: [Spotter paper](https://arxiv.org/abs/2609.36808),
[upstream code](https://github.com/zqc3117/Spotter),
[Blupe API](https://blupe.io/docs/robot-api/),
[Harness VLA](https://arxiv.org/abs/2607.08448).
