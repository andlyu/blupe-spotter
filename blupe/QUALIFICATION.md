# Physical qualification — 30 October 2026

The hosted Spotter application ran on **physical YAM1** with the pinned frozen
DreamZero checkpoint and the hosted open-source Qwen3.8-27B-FP8 supervisor.
The model and camera connections, feedback loop, intervention primitives,
handback and visual verification were exercised. **Task success was not established.**

| Trial | UTC interval | Completed packets | Confirmed settled waypoints | Outcome |
| --- | --- | --- | --- | --- |
| 1, `ep_bfc81ebb65c34c24` | 17:15:10–17:16:06 | 4 | 56 | A Spotter repair completed, then a later policy packet was rejected before motion by the gateway joint-step guard. |
| 2, `ep_0759ffeb8c944a1b` | 17:21:04–17:22:44 | 9 | 128 | Screen, judge, repair, handback and verification executed. Verification correctly continued reporting an ungrasped duck; the run stopped after its three-plan repair budget. |

Both trials requested “Put the duck into the cardboard bin.” The duck was not
placed in the bin. These trials establish an operational embodiment integration,
not reliable task completion, a success rate, or a paper benchmark reproduction.

The first rejected policy path had a maximum adjacent joint step of **14.4465°**
against the saved **9°** limit. The common policy transport now inserts linear
intermediate samples: that exact regression path becomes 12 rather than 8
waypoints with maximum step **7.2232°**. Every policy target and its order remain
unchanged; joint values are not clipped. The entire retimed path still goes
through the existing gateway's joint, velocity, table and swept-collision checks.
The rejected path is retained as a regression fixture.

Deployed-runtime validation: **56 tests and 6 transport subtests passed in 5.24s**.
The supervisor also completed a separate read-only inference on three fresh
camera images in **2.156s**. Cold-start preparation measured Qwen ready at
361.6s and both endpoints ready at 583.4s from the readiness probe's start;
allocation/cache state can change these times.

The page displays actual Spotter phase notes and preserves explicit error and
unverified outcomes. YAM1 calibration matched the pinned workspace before
queue admission. This port uses current images and normalized gripper state,
without simulator reset or privileged success labels. Model credentials and
robot session capabilities remain on the backend.

Full sanitized trial journals and inference/retiming receipts are retained in
the operator's task outputs; they are not bundled into the public web assets.
Robot-recording publication is asynchronous and is separate from the local
model journal. The hosted page offers its normal replay link when a recording
is available.

## Robo-house with Dream-1

The separate Robo-house page ran **hosted Dream-1 beta + Qwen Spotter** on robot
`robot-ba8413962083809c`, using its original encoder coordinates and corrected
repair geometry. Trial `run_cc136d422fe240ec985b83d7cc6d8cb6` requested
“Pick up the small red cube and place it on the dark round tray.”

From **19:00:11–19:03:04 UTC**, it completed **5 packets / 128 settled waypoints**:
four Dream-1 chunks and one Spotter Cartesian repair. Screen, confirming judge,
repair, handback and verification all executed. Qwen identified the policy
approaching the large red block instead of the small red cube. After repair,
the SDK reset completed in **0.20s**, and a fresh Dream-1 prediction executed.
This exercised the stateful-policy handoff on physical hardware.

**The task did not succeed.** The small red cube remained unplaced. Verification
reported that the arm was still over the wrong object. Further repair plans
did not produce a verified correction, and the run stopped at the configured
three-plan budget. The native automatic queue subsequently parked both arms
and verified torque off. This is an operational integration, not evidence that
Dream-1 outperforms DreamZero or a measured success rate.

Before the trial, live joint limits and arm-calibration offsets matched the
saved Robo-house profile. Its saved Cartesian repair envelope is a conservative
subset of the live controller's wider crossover envelope; the integration did
not widen its limits. The gateway checked every dispatched packet.

The combined integration, Dream-policy and controller-workspace suites passed
**121 tests in 23.20s**. Initial Dream SDK configuration took **81.50s** after
lease grant; measured inference calls took **0.70–4.47s**. Qwen also required
several minutes of prequeue model reload. These startup costs are separate
from action execution and depend on cache/allocation state.

The sanitized Robo-house journal and SDK stage timings are retained in the
operator's task outputs. Public replay publication was not used as evidence.
