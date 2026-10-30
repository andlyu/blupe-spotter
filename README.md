# Spotter on Blupe

[**Open the hosted demo**](https://spotter.54.209.185.15.sslip.io/)
[**Robo-house · Spotter + Dream-1**](https://robohouse.spotter.54.209.185.15.sslip.io/)

Spotter supervision on physical **YAM1 and Robo-house** arms, in a separate application and
repository. **DreamZero** leads on YAM1; the hosted **Dream-1 beta** leads on
Robo-house. An open-source **Qwen3.8-27B-FP8**
supervisor screens execution, confirms failures, plans a repair, verifies it and
hands control back. The same policy alone is available as a baseline.

This is a YAM embodiment port of the approach, not a reproduction of the paper's
benchmark results. Harness VLA/RPent is future comparison scope.

## Run locally

```sh
git submodule update --init --recursive
python3 -m venv .venv
.venv/bin/pip install -r blupe/requirements.txt
# Configure server-held model endpoints and credential files first.
PYTHONPATH=blupe .venv/bin/uvicorn spotter_yam.app:create_app --factory --host 127.0.0.1 --port 8820
```

See [setup, method and hosting](blupe/README.md),
[physical qualification](blupe/QUALIFICATION.md), and
[UI design notes](blupe/DESIGN-NOTES.md).

Pinned dependencies: [upstream Spotter](https://github.com/zqc3117/Spotter) and
[Blupe Remote YAM](https://github.com/andlyu/blupe-remote-yam) are Git submodules.
[Blupe robot API](https://blupe.io/docs/robot-api/) ·
[Spotter paper](https://arxiv.org/abs/2609.36808).
