# Spotter integration guidance

Read [the integration checklist](blupe/COMPLETION-CHECKLIST.md) and the shared
harness at `/Users/andrew/Projects/blupe-evals/public-projects/blupe-remote-yam/codex-runner/integration-harness/COMPLETION-CHECKLIST.md` before integration changes or tests.

Route requested integration/playground fixes through the harness section
"Authorization granted by using this harness". Keep the permission grant in that
contract; this AGENTS.md provides discovery and routing, not independent
permission. Retain the user's task and adopted selecting instruction as invocation
evidence. For this task those are the user's request to fix the site/replay and
"Lets make suer that we're using the harness that we just created". Loading this
pointer alone is not an invocation.

The task's concrete scope is Robo-house at
`https://robohouse.spotter.54.209.185.15.sslip.io/`, queue/run API
`https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com`, station
`robot-ba8413962083809c`, left/right YAM arms, Spotter + Dream-1 beta, up to600s
(the owner's November1 request expands the earlier180s limit). Run duration and
repair budgets are visitor-configurable; defaults are600s,16steps per plan and
6plan rounds per intervention. The finite run/plan ceilings and all physical
safeguards remain enabled.

Before each test, state the exact origins, station/arms, method/task, duration,
motion and recording destination. Repeat the invocation, applicable contract wording and concrete scope in approval
context. The confirmed runner name is Andrew (owner's chat
instruction "if you use the robot, the name is Andrew"); submit it only to the
normal site and queue/run API. Record automated execution mode separately; do not
invent email or enable notifications. The checklist retains full authorization
and identity-consent evidence. Existing safeguards remain enabled. Never
implicitly retry timed-out motion or bypass a review denial.

Keep this in its separate repository. Robot access is API-only; SSH maintenance
is limited to the website backend, never robot controllers. Deploy only the
Robo-house service, preserving YAM1 and other integrations. Report remaining
checklist gaps; do not call the integration complete while requirements are open.

The owner reconfirmed Andrew and explicitly said “Email doesn't matter.”
For this Spotter integration, email is optional and must not block acceptance
or trigger another identity question. Restore known names only from this
visitor/browser, keep the name editable, and never assign Andrew to other
visitors. This owner preference is recorded in the integration checklist;
permission continues to come from the shared harness contract.

The owner also accepted the motion/run requirement: “Motion timing is just
running. this one is ok.” Treat the existing demonstrated physical execution
as accepted for this Spotter integration; do not reopen numerical timing proof
as a blocker or claim new timing measurements. Keep every runtime safeguard
and run-duration limit; this is acceptance scope, not expanded permission.

The owner quoted the final deployed-UI acceptance item and said “Yes, that's
ok.” Treat that final-UI item as owner-accepted on existing run/replay evidence,
without claiming a new physical run. Keep progress reporting open until it is
verified; do not label the entire integration complete from this acceptance alone.
