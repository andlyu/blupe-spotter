# Spotter changes: goal-based judging, hand-back on give-up, raw repair motion

Changes on branch `spotter-prompts-handback` (seamoke), on top of `d613953`.
Robot safeguards, run-duration limits and gateway validation are unchanged.

## Prompts (`spotter_yam/vlm.py`)

Screen, judge, repair and verify share two blocks:

- `ROBOT`: what the measurements can and cannot say. The gripper value is an
  opening, not a grasp signal; only a lift shows that something is held. A
  completed packet is not a completed task. Side cameras give height and
  contact, never coordinates.
- `GOAL`: judge the scene against the goal state, not against arm activity.
  Lists concrete failures (empty close-and-lift, wrong object, drop, release
  off target, repeated failed attempts) and non-failures (first approach,
  transport, holding over the target).

Per role:

- **Screen** flags concrete evidence of failure only; slow progress passes.
- **Judge** intervenes only when it can name the problem, a short supported
  repair fixes it, and enough time remains; it then acts at the first window
  that shows the problem.
- **Repair** decides which arm is in trouble. A small misalignment is
  re-staged and handed back to the policy. A wrong object, a release off
  target, or a grasp the policy already missed after a hand-back is finished
  by Spotter itself (approach, close, grasp_check lift, carry, release,
  withdraw). `previous_repairs` must not be repeated unchanged.
- **Verify** distinguishes `clearance` lifts (target need not move) from
  `grasp_check` lifts (target must rise with the hand).

## Hand back instead of stopping (`spotter_yam/policy.py`)

If a repair uses up its plan rounds, or two planning attempts in a row give no
valid plan, Spotter returns control to the policy and keeps watching
(`_hand_back`). The attempt is recorded in `previous_repairs` as
`gave_up_handback`, so the next intervention plans something different.
Before this change the run ended.

## Raw motion beside measured points (`spotter_yam/grounding.py`, `repair_contract.py`)

`move_to_point` is no longer mandatory when grounding points exist. The
schema always offers `move_to` and `nudge`; `move_to_point` is added when
points were measured. Malformed point references are still rejected, and IK
and the gateway still check every target.

## Optional `codex` api_style (`spotter_yam/vlm.py`)

`SPOTTER_VLM_API_STYLE=codex` or `SPOTTER_REPAIR_API_STYLE=codex` runs that
role through a local `codex exec` (read-only sandbox, images attached,
`--output-schema` for the strict repair schema). The endpoint names the
binary. By default it uses the host's ChatGPT login; with
`SPOTTER_CODEX_USE_CONFIG=1` it uses the provider in `$CODEX_HOME/config.toml`
instead. Codex calls take 15–30 s, so its readiness timeout is at least
150 s. Existing `vllm` and `openrouter` settings are unaffected.

## Tests

Updated `test_grounding.py`, `test_repair_recovery.py`, `test_roles.py` and
`test_spotter.py` for the behaviour above; added `test_codex_supervisor.py`.

## Running far from the robot

These changes were tested from China, where one control step takes about
25 s (camera frame 2–3 s, Dream chunk ~15 s), the hosted Dream session
expires on most chunks, and the ~1 MB RGB-D bundle cannot arrive within the
5 s freshness limit, so repairs stop with `NoDepthImage`. Those are network
effects, not part of this change. The Spotter host should run next to the
robot API (us-east).
