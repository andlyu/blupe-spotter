# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Product Purpose

Showcase the Spotter supervision approach through a hosted page that can run
physical Blupe YAM arms. The user explicitly requested a separate repository
and a working physical demonstration, then selected Robo-house with Dream-1
as an additional base policy.

## Operating Context

Visitors choose a station and policy, describe a task, join the native robot
queue, watch the overhead and wrist cameras, follow decisions, and stop the run.
Each station offers Spotter supervision and the matching policy alone.
The application is hosted separately from the main Blupe playground.

## Capabilities and Constraints

- YAM1 uses its pinned DreamZero checkpoint; Robo-house uses hosted Dream-1 beta.
- Qwen3.8-27B-FP8 runs through vLLM on RunPod serverless GPUs as the supervisor.
  The AWS backend sends camera images and measured state; models do not run on the arms.
- Spotter screens in parallel, confirms failures, repairs from current state,
  verifies the outcome, and hands control back. A failed supervisor stops commands.
- Native leases, measured feedback and gateway motion guards remain authoritative.
  Station geometry and calibration must agree with the selected robot.
- The project ports the approach to YAM hardware. It does not reproduce paper
  benchmarks. Harness VLA/RPent comparison remains future scope.
- Credentials remain on the backend. Dream-1 model weights are not supplied here.

## Evidence on Hand

The upstream Spotter source and Blupe controller are pinned submodules.
`blupe/QUALIFICATION.md` records measured trials and their limits. A page, camera
feed, successful model response or passing test alone does not establish physical
execution or task success. Robo-house performance comparisons remain unproven.

## Product Principles

- Keep the integration in its own repository.
- Use current measured observations and station-specific geometry.
- Preserve the native controller's queue, Stop and motion checks.
- Distinguish demonstrated execution from model-reported and measured task success.
