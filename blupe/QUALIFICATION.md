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
