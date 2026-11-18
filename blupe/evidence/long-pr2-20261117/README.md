# PR #2 verification — November 17, 2026 (America/Los_Angeles)

**PR #2 is not ready for physical qualification.** Its native offline release
suite passes, but an added command-path regression demonstrates that newly
permitted raw Cartesian repairs bypass the scene-freshness guard. The PR remains
unmerged; this verification made no production source/configuration changes and
sent no robot commands.

- PR: [Spotter prompts handback](https://github.com/andlyu/blupe-spotter/pull/2).
- Exact PR revision: `fa7ee51a3b57ef765b893a452610b6ec959fdfeb`.
- Comparison main: `d6139533fcda4e465c41cf2ada68a0fc379c30a8`.
- Test environment: isolated source trees on the existing US website backend;
  existing `/home/ubuntu/blupe-spotter/.venv/bin/python` and installed vendor
  source. No robot-controller access. No model API credentials were loaded.
- Repository dependency gitlinks: remote-yam `e8158b7cfcbb90b2824dfc73e632b537bdfd942c`,
  upstream Spotter `e90090cbbd625d27f140b771cf72dfe0110b4a9d`. The installed vendor
  copy has no Git metadata: these are requested pins, not a claim that its entire
  working tree was proved identical to that commit. Actual tested Python-source
  hashes are retained in [the dependency manifest](tested-dependency-hashes.json).
  The canonical packet validator `session.py` SHA256 is
  `2e1735da0b528e57369a46c43e4ce831e798d7d3adba19b8f2c18684f07515e1`.

## Results

| Check | Revision | Result | Command wall time |
| --- | --- | --- | --- |
| Existing repository release preflight | Exact PR | 174 passed, 2 subtests passed | 78.211450 s; pytest 73.28 s |
| Added expired-depth command-path regression | Main | 4 passed | 9.430692 s; pytest 3.54 s |
| Same regression | Exact PR | 4 failed | 7.584796 s; pytest 4.59 s |
| Full preflight with new native regression file | Main plus review tests | 176 passed, 2 subtests passed | 62.781529 s; pytest 60.24 s |

Receipts: [PR native preflight](preflight.json),
[baseline regression](main-freshness-v2.json),
[PR regression](pr2-freshness-v2.json),
[review branch full preflight](review-branch-preflight.json).

The four cases cover left/right arms and `move_to`/horizontal `nudge`. They use
the real measured-state trajectory generator, canonical packet validation and
JSON serialization, with only outbound actuator transport intercepted. A valid
35 mm horizontal target is paired with a six-second-old scene snapshot and an
unavailable fresh capture. Main rejects the raw operation with zero transport
calls. The PR serializes one accepted-format actuator packet in each case and
never attempts a fresh capture. This proves a local validation regression; it
does not claim that any of those packets moved physical hardware.

## Finding: preserve the measured-target/fresh-scene boundary

In `grounding.py`, the PR removes the rejection of raw `move_to` and horizontal
`nudge`. Refresh/changed-scene checking still runs only for `move_to_point`.
Meanwhile, `repair_contract.py` now offers raw operations even when grounding is
present or all selected depths are missing. A model can therefore copy an old
surface coordinate into `move_to` and bypass the check that would refresh or
reject the corresponding named-point operation. IK and packet limits still
validate the trajectory, but they do not establish that an object remains at
that coordinate.

The PR changes the existing guard tests to expect raw operations to succeed,
which explains why its native suite is green. The separate regression restores
coverage of the actual measured-scene boundary without weakening existing
hardware, interpolation or invalid-input checks.

Recommendation: keep the prompt/handback improvements, retain measured-point
references for object-directed XY motion, and keep bounded clearance lifts for
missing depth. [The suggested two-file patch](suggested-measured-guard.patch)
restores main's schema/resolver restrictions while leaving the new prompts and
handback implementation intact. It is a review aid, **not a fully qualified
release candidate**. The patch uses zero context (`git apply --unidiff-zero`);
the PR's raw-operation tests and explanatory wording need
to be reconciled before applying it and rerunning the full gate.

## Read-only US-host depth check

Three public overhead RGB-D captures were attempted through the currently
installed API client on Robo-house `robot-ba8413962083809c`. No queue/session,
identity submission, model request or movement was involved. Image bytes stayed
in memory; only timing/metadata were retained.

Using the stricter moving-robot two-second age limit: one cold sample was
rejected at age 2.056745 s; two samples passed at ages 1.351271/1.336967 s.
Total capture calls took 2.350607/3.314976/3.994241 s. HTTP bundle waits, rather
than just byte transfer, dominated the latter two calls. This is three diagnostic
samples, not a reliability estimate or a measurement of Long's network. The
repair path's normal stopped-robot five-second threshold was not widened.
See [capture spans](depth-latency.json).

## Scope and remaining verification

The user supplied the request to test this PR under the adopted shared BluPe
harness. Confirmed runner identity remains Andrew, optional empty email and no
notifications; this task submitted no identity to a queue. Existing Dream-1 beta,
Qwen screening and GPT-6.1 sol repair configuration was not changed. The optional
Codex backend has two mocked subprocess tests here; no live Codex login/inference
or model substitution is claimed.

Physical PR execution, task success, live-model behavior, and a new same-run
replay remain unverified because the new command-path gate fails. Existing
production run/replay evidence remains historical evidence for its deployed
revision. No new physical timing, paper benchmark, or overall harness-complete
claim is made. The existing broader approach-label, model-provenance and detailed
wait-reporting gaps remain open. No email or GitHub message was sent to the author.

## Reproduction

With the source revision and dependencies selected explicitly, run the existing
release command:

```sh
PYTHON=/path/to/test-venv/bin/python bash blupe/deploy/preflight.sh
```

The review branch adds `blupe/tests/test_grounding_freshness.py` to the existing
preflight discovery. Copy that same file into an isolated checkout of the exact
PR and run it there to reproduce the four failures. Use the real pinned client
validator; do not replace it with an accepting mock.
