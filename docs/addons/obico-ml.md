---
title: Standalone Obico ML server
description: Install and update only the Obico machine-learning container for BamDude, without the Obico web application, workers or Redis.
---

# Standalone Obico ML server

BamDude needs only Obico's **`ml_api`** container for [AI failure detection](../features/obico.md). This guide installs that container in its own Docker Compose project. It does not install Obico's web application, background workers, Redis, a database or a cloud account.

The installer builds the ML image from the official [Obico server `release` branch](https://github.com/TheSpaghettiDetective/obico-server/tree/release/ml_api). You can run it on the BamDude host or a separate machine on your trusted LAN.

## Requirements

- A Linux host with Bash and a local Docker Engine. This recipe targets the standard CPU image; GPU and ARM-specific builds are outside this guide.
- [Docker Engine and the Compose plugin](https://docs.docker.com/engine/install/), with support for `docker compose up --wait`. Your account must be able to run `docker info`.
- Git, curl, OpenSSL, `flock` (usually in `util-linux`) and `realpath` (usually in `coreutils`). On Debian/Ubuntu, after installing Docker:

    ```bash
    sudo apt-get update
    sudo apt-get install -y git curl openssl util-linux coreutils
    ```

- Internet access for GitHub, the container registry and model downloads. Allow several GB of disk space for source, images and build cache; the model alone is hundreds of MB. Memory and CPU needs depend on the model and polling load.
- Network access **in both directions**: BamDude → ML API, and the ML container → BamDude's External URL to retrieve camera frames.

## Download the script

[Download obico-ml.sh](../assets/downloads/obico-ml.sh){ .md-button download="obico-ml.sh" }

Or download it on the Linux host:

```bash
curl -fL --proto '=https' --tlsv1.2 \
  https://docs.bamdude.top/assets/downloads/obico-ml.sh -o obico-ml.sh
less obico-ml.sh
bash obico-ml.sh --help
```

Download and inspect the file before running it. The script does not install Docker or change the host firewall. It creates a new directory, a separate Compose project and a random API token. No addresses or credentials from the BamDude maintainers' server are included.

## Install

Choose an unused directory and a free host port. Replace **`10.0.0.20`** below with a LAN IPv4 address assigned to the **ML host**:

```bash
bash obico-ml.sh install "$HOME/obico-ml" 10.0.0.20 3333
```

For BamDude running directly on the same host, you can use the defaults:

```bash
bash obico-ml.sh install
```

The default address is `127.0.0.1`, port `3333`, directory `$HOME/obico-ml`. Loopback is **not reachable from a separate BamDude container**; use the host's LAN address for that setup too. Run later commands as the same user and pass the same directory if you chose another location.

The first build downloads the base image, dependencies and model weights, so it can take several minutes. On success, the script prints the ML URL and source revision. The service restarts automatically with Docker.

!!! warning "Trusted LAN only"
    Keep the published port on your trusted network; do not forward it to the Internet. The API uses HTTP, so the bearer token is not encrypted in transit. Binding a LAN address is not a firewall rule. Docker's published ports can bypass ordinary UFW rules; use [Docker-aware firewall rules](https://docs.docker.com/engine/network/packet-filtering-firewalls/) when access must be restricted.

The installation contains:

| File | Purpose |
|---|---|
| `obico-ml.sh` | Local copy of the installer/updater |
| `compose.yaml` | One service: `ml_api` |
| `.env` | Bind address, port, project name and secret token; readable only by the installing user by default |
| `source/` | Official Obico source checkout |

Do not reuse a full Obico installation directory. This script neither migrates nor stops an existing Obico stack; choose a different directory and port if both must coexist. It never runs `down`, removes volumes or prunes Docker resources.

## Connect BamDude

1. Display the generated token locally:

    ```bash
    bash "$HOME/obico-ml/obico-ml.sh" token
    ```

2. Open **Settings → AI failure detection** in BamDude. Set **Obico ML API URL** to `http://10.0.0.20:3333` and paste the token into **ML API token**. Use the base URL, without `/p/`, `/hc/` or `/api/v1/octo/`.
3. Set **Settings → Network → External URL** to the address of **BamDude**, reachable from the ML container. For example, `http://10.0.0.10:8000` if BamDude is served on that address and port. `localhost` inside the ML container means the container itself.
4. Enable detection, choose the printers and use **Check**. Start with **Notify only** while assessing the camera view and sensitivity.
5. During an active print, verify that the analysed-frame count increases. This confirms the camera → BamDude → ML path, beyond a successful health check.

Do not share `.env` or the output of `token`. `/hc/` is public even when inference requires authentication, so a healthy endpoint alone does not prove the token is correct. The installer checks readiness, rejection without a token and acceptance of the configured token; it does not send a real camera frame.

## Update only ML

```bash
bash "$HOME/obico-ml/obico-ml.sh" check
bash "$HOME/obico-ml/obico-ml.sh" update
```

`check` validates the local configuration and source checkout; it does not fetch, build, restart or test live inference.

`update` fetches the official `release` branch, fast-forwards the clean checkout, builds **only `ml_api`** while the current container keeps serving, then replaces that container and waits for readiness. The token, bind address and port stay unchanged. There is a brief interruption during replacement. The script takes a directory lock to prevent concurrent runs.

If the build fails, the running container is left intact. If replacement or the subsequent checks fail, the command exits with an error; **there is no automatic rollback**. Inspect the logs, fix the cause and rerun `update`. The source checkout may already have advanced even when the running container still uses the old image.

The updater does not replace itself. To adopt a newer version of the helper, download and inspect it separately; keep your existing `.env` and review any migration instructions on this page before replacing the local script.

## Status and troubleshooting

```bash
bash "$HOME/obico-ml/obico-ml.sh" status
bash "$HOME/obico-ml/obico-ml.sh" logs
curl --noproxy '*' -fsS http://10.0.0.20:3333/hc/
```

The last command should print `ok`. A response body of `error`, even with HTTP 200, means the model is not ready.

| Symptom | What to check |
|---|---|
| Port already in use / cannot bind address | The selected IP must belong to this host and the port must be free. Change `ML_BIND` or `ML_PORT` in `.env`, then run `update`. |
| Build/download failure | Registry/GitHub/model-host connectivity, free disk space and the Docker build output. |
| Healthy ML but BamDude reports 401 | Paste the value from `token` into BamDude's ML API token field. |
| Healthy ML but no detections | Check an active print, selected printers, camera availability and the External URL reachable **from the ML container**. A login gateway in front of BamDude must allow the cached-frame callback. |
| Source checkout has local changes / non-fast-forward merge | Inspect `source/`; the updater deliberately does not discard local edits or reset Git history. |
| Install failed before cloning finished | Inspect the partial directory. Retry in a new empty directory; do not delete an existing installation blindly. After cloning has completed, `update` can retry a failed build or startup. |
| API responds but there are no saved frames | Saved detection history is a BamDude feature, not storage in the ML container. Check the recording setting and which events the installed BamDude version records; the live frame counter does not mean every frame was saved. |

## Sources and scope

This helper is maintained with BamDude's documentation. Obico's implementation remains upstream: [ML Dockerfile](https://github.com/TheSpaghettiDetective/obico-server/blob/release/ml_api/Dockerfile), [service definition](https://github.com/TheSpaghettiDetective/obico-server/blob/release/docker-compose.yml), [API](https://github.com/TheSpaghettiDetective/obico-server/blob/release/ml_api/server.py) and [authentication](https://github.com/TheSpaghettiDetective/obico-server/blob/release/ml_api/auth.py). Installation and updates follow `release`, rather than a fixed model revision. Review upstream changes before updating a production farm.
