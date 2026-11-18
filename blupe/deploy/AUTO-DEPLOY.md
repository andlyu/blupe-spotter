# Automatic Robo-house deployment

Merging into `andlyu/blupe-spotter:main` runs **Test and deploy Spotter** in
GitHub Actions. A server-side timer detects new main commits over public HTTPS
within about two minutes; the workflow waits for its result over public HTTPS.
Only the current main commit is eligible; the server fetches its exact source
and both submodule commits from public GitHub, then runs the complete existing
offline preflight. Failure leaves the current website unchanged. PR branches
and forks receive no deployment credential or deployment execution.

After preflight, the public run endpoint pauses new launches while existing
preparation, queue, execution, parking and cleanup finish. Live cameras, Stop,
history and replay remain available. Two consecutive idle observations are
required. A busy/unknown state never authorizes a restart. Drain has a finite
15-minute budget; a timeout leaves the current release running.

The release symlink switches only after draining. The deployed application
reports its startup-loaded source revision, solver readiness, active run count
and in-flight launch count at `/spotter/health`; no runner name, email, session
capability or model credential appears there. Deployment succeeds only when
both localhost and the public site report that exact revision ready. Startup
has a ten-minute bound. A failed startup restores the previous release and
checks its readiness. Failed rollback keeps new-run admission paused. Interrupted
updates are recovered against `last-good` when the next deployment acquires
the process lock. GitHub concurrency does not cancel a deployment in progress.

Robo-house has its own source releases and service override. YAM1 continues
using its existing source, environment and process. Robot controllers are
never accessed; deployment does not create a robot lease, run or motion.

## Operator locations

- Workflow: `.github/workflows/deploy-robohouse.yml`; automatic on main pushes,
  with a manual **Run workflow** option on main.
- Installed deployment code: `/usr/local/libexec/spotter-deploy/`.
- Pull service/timer: `blupe-spotter-deploy.service` / `blupe-spotter-deploy.timer`.
- Nonsecret host configuration: `/etc/blupe-spotter-deploy.json`.
- Releases/current/last-good: `/home/ubuntu/spotter-auto-deploy/`.
- Public maintenance metadata: `/var/lib/blupe-spotter-deploy/maintenance.json`.
- Service: `blupe-spotter-robohouse.service`, port8821.
- No deployment credential in GitHub Actions. Owner SSH and model/session
  credentials stay outside the workflow.

The deployment requires no GitHub Actions secret, inbound SSH access or new
firewall rule. The server independently checks main again
after draining, so a queued older commit cannot overwrite a newer release.
Host-key checking is pinned; it is never disabled. Runtime requirement changes
use a separate cached virtual environment, leaving the current environment intact.
The interpreter/test-package bootstrap versions are recorded in host configuration;
every release records exact dependency pins, file hashes and preflight output.

Infrastructure entry-point/Caddy/systemd changes require an explicit update of
the installed infrastructure files; ordinary application, prompt, test and
asset changes deploy directly. To roll back manually, first pause admission,
wait for idle, point `current` at a known healthy release, restart only the
Robo-house service and verify its public health/replay before reopening launches.
An explicitly failing source is not retried every timer tick. After correcting
source, merge a new main commit; for an infrastructure-only retry, an operator can
run `/usr/bin/python3 /usr/local/libexec/spotter-deploy/poll_main.py --retry` as ubuntu.
Do not restart an active robot run or automatically retry a timed-out movement.

## Retained regression gate

The release includes the four demonstrated raw-XY expired-depth regressions.
Long's raw move support remains available beside measured points. When planning
outlives the existing five-second scene window, all selected surfaces must be
remeasured and unchanged before raw XY moves pass. Missing points reject raw XY
while retaining bounded clearance lifts. No workspace, IK, interpolation,
finite-number or canonical packet-validator limit was widened.

The full offline gate also exercises admission races, queued/busy/unknown state,
drain timeout, superseded commits, wrong revision, public-site mismatch, rollback,
failed rollback, rejected archive traversal/links, and zero activation after
preflight failure. These are deployment/command checks, not a new physical task
success or a complete research-harness acceptance claim. Earlier physical
success remains evidence for its original source revision.

References: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[GitHub repository secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets),
[Caddy request matchers](https://caddyserver.com/docs/caddyfile/matchers#file).

The initial SSH-triggered workflow could not reach port22 from GitHub hosted
runners. It failed before source activation. The final pull deployment avoids
that network dependency and does not open SSH/firewall access.
