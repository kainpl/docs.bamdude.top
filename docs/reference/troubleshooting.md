---
title: Troubleshooting
description: Common issues and solutions
---

# Troubleshooting

Solutions for common issues with BamDude.

## Printer states appear slowly when opening the page

Printer cards can display live WebSocket states while the REST status request is
still pending. REST supplies additional archive and plate information and remains
the fallback when WebSocket access is unavailable. Simultaneous status reads are
combined into a bounded batch; returning to a tab refreshes only active data
that is stale, failed, or changed while the tab was hidden. A quick switch away
and back does not reread a fresh farm.
A stalled WebSocket viewer is disconnected so it cannot hold up other viewers.

The queue badge reads compact counts, not every queued job. Queue and Printers
views share active queue reads across their cards; closed Issues sections show
counts and load paged details only when opened. While a tab is hidden, these
farm reads pause. A failed count is shown as unavailable, never as a complete
zero. WebSocket disconnection does not turn off the independent REST fallback.
The per-card status fallback of a whole page is merged into one batched request
per interval, and a printer whose live state arrived recently is skipped until
its own interval is due. After a network drop the browser reconnects with growing,
slightly randomised delays of up to 30 seconds instead of every few seconds.

For a support report, note the time you opened the page and attach backend logs
covering that time. The following entries help narrow down the delay:

- `WebSocket bootstrap timing`: authentication/accept and initial queue preparation,
  including waits for that viewer's writer to make room in the queue.
- `WebSocket bootstrap applied`: the browser has committed every printer state
  received before the bootstrap marker to its query cache. Match the `id` with
  the previous entry. `client_connect_ms` runs from token-request start to that
  cache commit; `token_ms`, `socket_open_ms`, `first_status_ms` (opening to the
  first status, if any), and `marker_to_cache_ms` separate the stages. Missing
  stages from an older client appear as `None`. `server_elapsed` includes the
  return trip for the acknowledgement. None measures the first painted card.
- `Slow WebSocket send`, `WebSocket send timed out`, or `WebSocket outbox overflow`:
  a browser connection cannot keep up with outgoing data.

Missing acknowledgement alone does not prove a server fault: an older browser
bundle, a disconnected tab or a network interruption can also explain it. These
timings do not include loading the application's JavaScript or the printer list.
Under a steady stream of archive, library or inventory events, affected cache
entries are marked stale within five seconds of the first event while browser
timers are running (a suspended tab may resume later). Active reads
are then started at a limited pace; an inactive view refreshes when opened.

---

## :material-printer-3d: Printer Connection Issues

### Printer Won't Connect

**Symptoms:** Printer shows as disconnected, red indicator.

**Solutions:**

1. **Verify Developer Mode is enabled**
   - Settings > Network > LAN Only Mode (ON)
   - Then enable Developer Mode
   - Toggle off/on to get a fresh access code

2. **Check IP address**
   - Verify IP in printer network settings
   - Use static IP or DHCP reservation

3. **Verify access code**
   - Access code changes when Developer Mode is toggled
   - Copy the code exactly (case-sensitive)

4. **Check network connectivity**
   ```bash
   ping YOUR_PRINTER_IP
   ```

5. **Verify ports are accessible**
   - MQTT: Port 8883
   - FTPS: Port 990

6. **Check firewall rules**

---

### Connection Drops Frequently

1. **Check WiFi signal strength** on the printer card
2. **Network congestion** -- Try a dedicated network/VLAN
3. **Router issues** -- Restart, check firmware, disable "smart" features
4. **Check BamDude logs:**
   ```bash
   tail -f logs/bamdude.log
   ```

!!! info "A dropped printer now recovers itself"
    BamDude checks every minute for a printer that **was** working, has been silent
    for five minutes, and **whose port still answers** — and rebuilds the connection
    itself rather than waiting for the network library to get around to it. One
    report had a printer offline from 02:19 to 11:24 with the page open the whole
    time; the old check only ever looked at connections that were still up but had
    gone quiet, so a fully dropped one fell outside it.

    A printer that is simply **switched off** is left alone, so powering the farm
    down overnight causes no churn and no log noise. A printer whose connection
    keeps dying is retried at a growing distance rather than every minute, and the
    log names how long it was gone.

### The printer looks connected and idle, but ignores every command

**Symptom.** Prints, temperature changes and filament loads are all silently dropped. Uploads appear to succeed, the printer echoes the job back, and then nothing happens — over and over. Status queries still answer, so the printer shows as connected and idle.

**Cause.** Some firmware (**P1 series, 01.08.03 and later**) can end up rejecting control commands it cannot verify. The printer reports it the whole time, as HMS **`0500-0500-0001-0007`** — *MQTT command verification failed*.

**Fix — on the printer:**

1. On the printer's screen, enable **Developer Mode** (LAN Mode / Developer options, depending on firmware).
2. **Restart the printer.**

BamDude now recognises the code, shows it with the same four-group form the printer's own screen displays, and carries that remedy. (Bambu's own advice for this code is to update Bambu Studio or Handy, which is no help for a print sent from BamDude.)

!!! note "What else changed with it"
    - Queueing a print onto such a printer **stops on the first attempt and names
      the cause**, instead of spending four and a half minutes and three uploads
      before failing with an unrelated message about SD cards.
    - The Developer Mode check in the support bundle and printer diagnostics has a
      third answer, **undetermined**, rather than treating any reply that was not an
      outright refusal as a pass.
    - A healthy printer is no longer told to go check its serial number in the
      moment right after it reconnects.

---

## :material-camera: Camera Issues

### Stream Won't Start

1. Is the printer powered on?
2. Is camera enabled in printer settings?
3. Is ffmpeg installed? (included in Docker image)
4. Is Developer Mode enabled?
5. Docker users: try `network_mode: host`

### Stream Freezes

- Check WiFi signal strength
- Try lowering FPS
- Use snapshot mode instead

---

## :material-archive: Archiving Issues

### Prints Not Being Archived

1. **SD card inserted?** Required for file downloads
2. **Developer Mode enabled?** Required for FTP access
3. **Auto-archive enabled?** Check per-printer setting
4. **Calibration prints** are automatically skipped

---

## :material-clock-outline: Queue Issues

### Prints Not Starting

1. **Printer connected?** Must show green indicator
2. **Plate cleared?** Check if "Clear Plate & Start Next" button is showing
3. **Scheduled time?** Check if print has a future schedule
4. **Queue Only mode?** Check for purple "Staged" badge

### A queued print is deferred again and again {#dispatch-stalled}

**Symptom.** The printer is connected and idle, its queue is not paused, a job is waiting — and nothing starts. Each pass tries the job and gives it back. **System Health** lists *A print start keeps being deferred*; older logs show the same line over and over, `Dispatch … deferred before publish: dispatch_claim_changed`, without saying which printer or job.

**What it means.** A healthy *connection* is not a healthy *status*. One cause is established: a print ended while the link was down, the reconnect check closed it in the archive and the queue, and its run stayed in BamDude's memory, so every new start on that printer is refused before it is sent. Older log lines that name no printer or job show only that starts were deferred repeatedly; they do not establish the cause.

**What to do.**

1. Open **System → Print state diagnostics**. A stalled start is shown with its job, how many times it was deferred and for how long, and a link to the row that holds the printer.
2. If that row offers **Release the finished context**, preview it and confirm. Only that finished run leaves memory; the archive and accounting stay; nothing is sent to the printer; the queue is paused. If the row explains why there is no button (a swap still owed, a start or completion still running, a printer whose state is not fresh, …), deal with that first or wait and **Check again**.
3. Check the printer and the plate — the release is not a plate confirmation — then **Resume queue**. The waiting job starts the ordinary way.
4. If heating was left requested by a refused start, the row says so; the pause does not turn heaters off.

If the result reads *not recorded*, look at the printer's recovery history before doing anything else. Restarting BamDude also empties its memory, and with it the evidence: download the support bundle **before** restarting. Details: [System Info → Print-state diagnostics and recovery](../features/system-info.md#print-state-diagnostics-and-recovery).

### Second printer waits a few seconds before starting

Not a bug — but the diagnostic changed. Since `c485db1`, BamDude's dispatch runs **in parallel across printers**; only the brief DB-insert phase is wrapped in a startup-lock. The two printers really do receive their jobs simultaneously, and the dispatch toast shows two FTP progress bars side-by-side. The earlier "one job at a time across the whole farm" gate that landed in mid-0.4.1 was scrapped once the startup-lock was in. See [Per-Printer Queues → Dispatch behaviour](../features/print-queue.md#dispatch-behaviour) for the full description.

---

## :material-cursor-pointer: Skip-Objects Button Issues

### Skip-objects button is greyed out for OrcaSlicer files

OrcaSlicer ships with both `Label objects` and `Exclude objects` **off** in the print profile, so its 3MFs land in BamDude without the metadata the firmware needs to address individual objects. Bambu Studio enables both by default, so files sliced there work out of the box.

**Fix per file:**

1. **Print Settings > Others > "Label objects"** -- emits the per-object IDs (`M624`/`M625`) the firmware needs.
2. **Print Settings > Others > "Exclude objects"** -- turns on the slicer-side metadata BamDude reads.
3. Both must be ticked **before slicing**. Re-sending an old 3MF without these flags doesn't help -- re-slice with both on, re-upload, and the button lights up.

The flags are stored in the source 3MF's `Metadata/project_settings.config`; BamDude extracts them on upload (and backfills existing files via migration `m022`).

### Skip-objects button "dies" 5 minutes into a print (old behaviour)

Fixed in 0.4.1, no action needed. Earlier versions periodically swapped the printer's MQTT client for a fresh instance every ~5 minutes, which wiped the in-memory `printable_objects` state. The button is now repopulated whenever the duplicate-guard branch of `on_print_start` re-fires, so it stays alive for the whole print. Restart-resilient as well -- printer-started fallback prints get the same treatment via `archive_download_retry`.

---

## :material-arrow-up-bold-circle: Upgrade-Time Hangs

### "Server takes minutes to come up" on first boot after 0.4.1

Migrations `m022` and `m023` both open every existing 3MF on disk to backfill metadata. `m022` extracts the `gcode_label_objects` / `exclude_object` flags; `m023` extracts the full per-plate breakdown that powers the per-plate gallery in File Manager. Roughly 50-200 ms per file each, and they run sequentially — an install with thousands of archives can spend several minutes inside the migration step before the API responds. Watch for `m022 library_files: progress`, `m022 print_archives: progress`, then the matching `m023` lines — if they're advancing in batches of 100, the migrations are healthy and just need to finish.

Both are one-shot — subsequent boots skip them via the `_migrations` table.

### Browser console floods with 401s after a long-idle tab

Fixed in `dd1d9eb`, no action needed on 0.4.1+. Earlier versions waited for a 401 to fire `/auth/refresh` reactively; when a backgrounded tab returned with five React-Query keys all firing simultaneously, the network panel briefly logged 20–40 401s before the first refresh response unblocked them. The client now decodes the JWT `exp` claim, schedules a one-shot refresh ~60 s before expiry, and a near-expiry pre-flight check awaits the same coalesced refresh promise. Result: the access token is fresh by the time the visibility-sync invalidates queries, and no 401 leaves the browser. The reactive path stays as a fallback for binary / streaming endpoints.

---

## :material-docker: Docker Issues

### Container Won't Start

```bash
docker compose logs bamdude
```

### Can't Connect to Printer

```bash
docker compose exec bamdude ping YOUR_PRINTER_IP
```

Try `network_mode: host` on Linux.

### macOS / Windows Docker

Docker Desktop runs containers in a VM. Use port mapping instead of host mode, and add printers manually by IP.

---

## :material-send: Telegram Bot Issues

### Bot Not Responding

1. Check that the Telegram provider is enabled in Settings > Notifications
2. Verify the bot token is correct
3. Check BamDude logs for polling errors
4. Ensure your chat is authorized

### Commands Not Working

1. Check that your chat has the required permissions
2. Verify the chat's group assignment in the web UI
3. Try `/start` to re-register the chat

---

## :material-database: Database Issues

### Resetting the Database

!!! danger "Data Loss"
    This deletes all your print history and settings!

```bash
docker compose down
# Remove the database file from the data volume
docker compose up -d
```

---

## :material-tag-text-outline: Trace IDs in logs

Every HTTP request through BamDude gets a unique trace ID. The same ID is:

- **Echoed in the response** as the `X-Trace-Id` header (so a curl / browser DevTools / log dump can grab it).
- **Attached to every log line** that ran during that request — `bamdude.log`, plus child loggers (`bambu_mqtt`, `print_scheduler`, `background_dispatch`, `archive_download_retry`, …).
- **Survived across async hops** — if a request kicks off a fire-and-forget task (e.g. archive 3MF retry-download), that task's logs still carry the originating request's trace ID.

When reporting an issue, the easiest way to give us the right slice of the log:

1. Reproduce the problem in your browser. **DevTools → Network → click the failing request → Response Headers → copy `X-Trace-Id`**.
2. Find that ID in `bamdude.log`:
   ```bash
   grep <trace-id> logs/bamdude.log
   ```
3. Paste the matched lines into the GitHub issue. That cluster correlates HTTP entry → service work → MQTT / scheduler side effects all in one go, instead of "guess what was happening at 14:32:17 across N components".

The format is short (8 hex chars, `[trace=abc12345]` in log lines) so log lines stay readable. Trace IDs aren't stable across restarts — they're per-request, not session.

---

## :material-speedometer: Finding what is slow

A farm that "feels slow" has two very different possible causes, and telling them apart is the whole game: either a **database statement** is slow, or the server is **busy elsewhere** and the database is idle. BamDude can measure both. Neither is on by default — leave them off unless you are investigating.

**Settings → General**:

| Setting | What it does |
|---|---|
| **Slow query log** | Writes one warning for every database statement slower than this many milliseconds. `0` turns it off. |
| **Slow request log** | Writes one warning for every API request slower than this many milliseconds, with its database share. `0` turns it off. |

Both take effect the moment you save — no restart — and both work on SQLite and PostgreSQL alike. Reasonable starting points on a busy farm: `500` for queries, `3000` for requests. Turn them back to `0` when you are done.

### Reading the request line

```
slow request 1830ms GET /api/v1/inventory/spools (db 41 queries, 1620ms) [a1b2c3d4]
```

That trailing `[a1b2c3d4]` is the trace ID from the section above, so you can pull the whole request's log cluster with one `grep`. The part in brackets before it is what makes the line worth reading:

- **Most of the time in the database, over many statements** (`db 41 queries, 1620ms`) — the endpoint is asking too often. Usually one query per row where one query for all rows would do.
- **Most of the time in the database, in one or two statements** — a missing index, or a query over more rows than it needs. The slow query log names the statement.
- **Almost no time in the database** (`db 3 queries, 12ms` out of 1830 ms) — the database is fine and the server was busy with something else: a big file walk, image work, or simply too much happening at once.

### Without turning anything on

Every response already carries a standard `Server-Timing` header:

```
Server-Timing: db;dur=1620.4, total;dur=1830.2
```

Your browser renders it in **DevTools → Network → the request → Timing**, so the same split is one click away for anything you can reproduce in the UI.

!!! info "What the log does and does not contain"
    The slow query log records the **text** of a statement, shortened and with any credentials in it masked. It never records the values bound to it — those are your file names, spool names and printer serials, and `bamdude.log` is a file people attach to public issues. Request lines record the method and path only, never the query string.

---

## :material-stethoscope: Self-service diagnostics

BamDude can triage most setup problems for you. On the **System** page, the **Connection Diagnostic** section probes each printer (ports, LAN developer mode, Docker network mode, subnet, credentials) and the **System Health** section scans recent logs against the known-issue catalog below. The in-app bug reporter runs both when you open it, so a fixable problem is surfaced before you file a report. The "How to fix" links on each finding point at the matching section here.

### Wrong access code

The printer rejected the file-transfer login. The access code is wrong, or it changed after Developer Mode was toggled. Re-copy the access code from the printer screen (LAN settings) and update it in the printer's settings in BamDude. Note that the serial number is case-sensitive — BamDude now uppercases it for you on save.

### FTPS port 990 blocked

BamDude could not reach the printer's file-transfer port (FTPS 990). The port is blocked, or the printer is off or on another subnet. Make sure nothing (firewall, Docker bridge networking) blocks port 990 between BamDude and the printer, and that both are on the same network.

### FTPS cleartext answer

The printer answered its secure file-transfer port (990) in plain text instead of starting TLS — the log shows `[SSL: WRONG_VERSION_NUMBER]`. This is not a firewall or a firmware version problem: a plain-text reply on that port is exactly what produces this error, while a TLS version mismatch produces a different one. It is how the printer's file server turns a connection away, most often because another program — a slicer's device page, another integration — is using it at that moment; the printer accepts about one file connection at a time.

Close other programs that browse or send files to this printer and try again. If it keeps happening with nothing else connected, restart the printer. Right after the error BamDude asks the printer once what it said and logs it (`Printer … answered port 990 in cleartext with: …`) — include that line when you report the problem.

The **Connection Diagnostic** sees this state too: it completes a TLS handshake on port 990 (no login, so it works before a printer is added), and an open port that turns the handshake away is reported as a warning of its own rather than a green port. While it lasts, BamDude does not walk the card's directories for a missing 3MF — the connection those listings need is the one that was just refused; the archive's recovery triggers come back for the file.

### FTPS TLS failure

The TLS handshake with the printer's file-transfer server failed after the printer had started speaking TLS. Check that nothing between BamDude and the printer intercepts port 990 (a proxy or a security appliance) and try again; the sample line names the exact TLS error — include it in a report.

### MQTT connection unstable

The control connection (MQTT 8883) repeatedly disconnects and reconnects — usually a weak network path or a partially blocked port. Check the Wi-Fi signal at the printer, prefer a wired connection, and make sure port 8883 is reliably reachable.

### Camera RTSPS port 322

The live camera could not be reached on port RTSPS 322. The port is blocked, or the camera / LAN liveview is off on the printer. Enable the camera and LAN liveview on the printer and make sure port 322 is not blocked. This does not affect printing.

### Store sent files on external storage

BamDude read the printer's own report of the **Store sent files on external storage** setting (install step 4) and found it turned off. Without it, the printer never keeps the sliced `.gcode.3mf`, so every archived print is missing its thumbnail and slicer metadata. Turn the setting on in the slicer so each job is stored on the printer. Note that on some older firmware/slicer combinations this is a slicer-only preference the printer never reports back — the diagnostic can't see that variant, but the Archives page shows a banner when prints arrive without thumbnails.

On some models this check is **skipped** rather than failed: the P1P, P1S, A2L and X1E have an SD card slot but no reachable way to turn the option on — they never report support for it, so Bambu Studio / OrcaSlicer don't draw the toggle, and the P1-series has no screen to set it from. Because there is nothing to fix, the diagnostic explains that instead of showing a permanent failure. If a firmware update starts exposing the option, the check re-enables itself automatically.

### Printer is publishing status

The MQTT broker accepted the connection, but no status reports arrived from the printer. The broker accepts a connection even when the serial number is wrong or mis-cased — the printer's report topic is case-sensitive — so control looks connected while the slicer side shows empty AMS, no filaments, and no K-profiles. The diagnostic waits up to 10 seconds for the printer's first status report, showing a live elapsed-seconds counter so the wait doesn't look hung. If it fails, re-check the serial number for typos and case (BamDude now uppercases it on save) and confirm the printer is powered on and reachable.

### Database is locked

The SQLite database is hitting "database is locked" errors under load — common when running several printers at once. Switch BamDude to an external PostgreSQL database (see the PostgreSQL guide).

---

## :material-bug: Getting Help

### Camera and 3MF analysis workers

**Worker unavailable?** Open **System** and read that
worker's reason separately from preview health. The camera worker starts with
the application (a failed first attempt and cleanup may add up to about 40
seconds before HTTP is ready), then retries process failures with bounded
backoff. An unreapable child requires operator investigation; BamDude does not
start a second owner or switch to in-process camera capture. The analysis
worker shares the same bundled local broker as preview but has its own service
and parser child. A failed analysis service retries with bounded backoff; a
failed broker needs an application restart after its cause is resolved. A
previously completed calculation for a live print remains cached.
Normal camera shutdown waits for the worker to release its cameras before
closing the guardian. An unresponsive worker is forcibly reaped and retried;
the log distinguishes `graceful`, `forced` and `cleanup_failed` outcomes.
Neither failure stops unrelated printing or queues; a mandatory camera check
can hold its job until cameras recover. Check the application log,
local disk permissions and free space before restarting the service.

### Uploads and folder scans fail together

Check **System → Library file worker**, **3MF analysis worker** and **Local preview service**. They share the bundled broker, so several unavailable panels can have one startup cause. Read the first startup error, free space and access to the runtime directory. A missing `broker/logs/nats.log` does not rule out broker failure: startup can fail before a log is created.

After 0.7.0, the bundled broker manager restores private permissions (`0700` on POSIX) on its own service directories before startup, including directories previously created with `0755`. It does not repair a wrong owner or a read-only mount. Update to a version containing the fix and restart normally; do not recursively change permissions on the entire data directory or remove ownership records to force startup.

### Local preview service {#local-preview-service}

Open **System → Local preview service** to see whether it is available,
starting, restarting or unavailable. The panel gives the reason, error type
and runtime directory when unavailable, with a link to this guide. A worker
restart/backoff is distinct from an unresolved broker or process ownership;
the latter needs manual verification, not a blind restart loop. The same
reason, directory and recovery guidance are logged at WARNING level. No
credentials or protocol payloads are included in this status.

`Preview unavailable` means model-preview generation is unavailable; it does
not stop the API, printer connections or printing. Existing thumbnails remain
readable. Check free disk space, installation dependencies and write access to
`DATA_DIR/.cache/preview-service`, then restart BamDude normally.

Service shutdown must let the application stop its children first, with every
database backend. Current installers set systemd `KillMode=mixed` and
`TimeoutStopSec=90`, NSSM `AppStopMethodConsole=90000`, and launchd
`ExitTimeOut=90`. An existing manually managed service does **not** acquire
these settings from a code-only update: apply them before the next stop
(for systemd, use a service drop-in and `systemctl daemon-reload`). Windows
installer upgrades apply the timeout before stopping the old service. Docker's
default command replaces its shell with the application; preserve that `exec`
if overriding the command, and retain the Compose shutdown grace period.

After an abrupt stop (power loss, OOM or forced kill), the next BamDude start
automatically recovers a current-format broker runtime **only when its inherited
OS lifetime lock proves that no old broker retains ownership**. A closed port
or a missing PID is not sufficient. Persistent broker data is preserved; only
BamDude's disposable preview buckets are reset. This requires a local filesystem,
not a network-shared runtime directory.

A live broker, a legacy/damaged marker, a copied runtime directory or an
unverifiable lock still requires the manual checks below. WARNING logs include
the refusal reason and marker path. Old preview and analysis staging with
payloads or unknown entries is retained and logged: broker recovery does not
prove that an old worker has finished using it. A known empty service skeleton
is retained too, but only counted at INFO level; it needs no immediate action.
After a confirmed crash of the **current** service, BamDude cleans only that
service's abandoned attempts before relaunch. If an owned cleanup fails, look
for `staging_cleanup_failed` with its path and error in the server log; the
System page does not show per-file cleanup failures. A persistent disk or
permission error may require fixing the cause and restarting. Once BamDude and
all its workers are stopped, old temporary staging may be removed manually
after verifying ownership. Existing library/archive thumbnails and archive
source files are never removed by this cleanup.

If the log reports `RecoveryRequired` or an unresolved managed runtime, do not
delete `managed-runtime.json` or kill a process based only on the PID in it.
Stop BamDude and verify that its preview service, renderer and bundled NATS
process have stopped (check executable and command line, not just a reused PID).
If ownership is uncertain, retain the directory and request support. Once all
owners are confirmed stopped, move **only** `DATA_DIR/.cache/preview-service`
aside as a recovery copy and restart. This cache contains temporary artifacts,
not library files; never remove the library/archive or other service stores.
Keep the recovery copy until the new service works. Retry missing thumbnails
explicitly; interrupted preview attempts are not replayed after restart.

### Part thumbnail worker {#part-thumbnail-worker}

!!! info "After 0.7.0"
    The part thumbnail worker is in the current development branch after 0.7.0. It is not in the `0.7.0` release image.

Open **System → Part thumbnail worker**. It renders the [part pictures](../features/projects.md#part-pictures) with a pinned Node.js runtime, through the same bundled broker as the preview service. The panel shows its state, the reason as a sentence with its code, the pinned Node.js version, the queue and the last attempt.

**While it is down, nothing else stops.** Products, orders and stock keep working; parts show **being prepared** or the picture they already had; queued plates wait, and attempts that could not start are not counted as failures. When the worker is back, the queue carries on by itself.

| Reason | What to do |
|---|---|
| `runtime_provisioning` | Nothing to do: a native install that started without its pinned Node.js is installing it in the background, once per start, and part thumbnails start by themselves when it is in place. The log says `Render runtime provisioning … started (startup)` and then how it ended. If it ends in `runtime_missing`, see the next row. |
| `runtime_missing` | The pinned Node.js is not installed. A native install tries this by itself at every start, and the log says how the last try ended: `Render runtime provisioning … failed after …` with the reason, `… timed out after …` with the last thing it said, `… did not start after …` with the error's type, or `… no official Node.js build …`. **Docker:** pull the current image — it carries Node.js. **Native:** run `install/update.sh`, or from the installation directory with its venv, as the service user, `python -m backend.app.services.render_runtime provision --runtime <install>/runtime`; while another provisioning of the same installation runs, the command waits for it, with no time limit of its own. **Windows:** run the installer again; it replaces the runtime whole. |
| `runtime_failed` | Node.js is installed but does not start: an antivirus blocking `node`, an install directory mounted `noexec`, or a binary for another architecture. The log says `Part render runtime_failed: Node … does not start`. The worker probes it again by itself and logs `Part render runtime recovered: Node … starts again` when it works. |
| `bundle_mismatch` | The render bundle does not match this version — an update that did not finish. Update or reinstall again. |
| `no_runtime` | Nothing to repair: there is no official Node.js build for this machine (armv6 — Pi 1 / Zero, an armel or musl 32-bit system, RISC-V; 32-bit Raspberry Pi OS is supported). Parts get only the fallback picture a 3MF carries — the plate's top view and object masks; a raw `.gcode` gets none. |
| `staging_full` | Results of earlier renders under `DATA_DIR/.cache/part-render-service/staging` have not been cleaned up, and new renders wait until they are. Look for `Part render main staging is over its budget` and `staging retained` in the log, then check free disk space and write access. |
| `ownership_uncertain` | BamDude could not prove that an earlier render process is gone, so it takes no new renders. Restart BamDude normally. Do **not** kill processes by a PID from a file. If it repeats after a clean restart, keep the directory and ask for support. |
| `starting`, `not_started`, `startup_failed`, `broker_disconnected`, `worker_restarting`, `circuit_open` | The worker or its broker is starting or recovering, and it retries by itself. After several failures in a row it pauses before the next try. A start that failed before the worker could retry stays at `starting` or `not_started`: look for `Part render service unavailable at startup` in the log and restart BamDude. If it never becomes available, read the first `Part render worker …` error in the log; it often has the same cause as the other panels on the shared broker (see [Uploads and folder scans fail together](#uploads-and-folder-scans-fail-together)). |
| `stopped` | BamDude is shutting down, or a backup was restored — restart BamDude to resume rendering. |

The parent log records each attempt as `Part render attempt=<id> … started` and `Part render attempt=<id> outcome=<outcome> … elapsed_ms=…`, and the worker as `Part render worker ready pid=… node=…`. BamDude removes the staging of earlier runs once it has proven them over. It keeps and logs (`staging retained`) whatever it cannot prove, and that is never removed by hand while BamDude runs.

Rendered pictures are kept in `DATA_DIR/part-renders`. It is a cache: it is deliberately left out of backups, and after a restore the pictures are rendered again.

### STEP thumbnails {#step-thumbnails}

!!! info "After 0.7.0"
    STEP thumbnails are in the current development branch after 0.7.0. They are not in the `0.7.0` release image.

A STEP thumbnail that ends with **the STEP component is not available on this server** (`cad_unavailable`) means the Open CASCADE component that makes [STEP thumbnails](../features/file-manager.md#step-thumbnails) is missing. The file is kept in the library; it just gets no picture.

- **Docker on 32-bit ARM:** the image has no build of the component for this architecture. There is nothing to repair; everything else keeps working.
- **A native install that declined it** — at the installer's question, or with `--yes` on a fresh install: from the install directory run `sudo install/step-preview.sh enable` (without `sudo` on macOS). BamDude may keep running; the next STEP thumbnail uses the component. On Arch Linux and openSUSE install libGL, libX11 and expat yourself first; the script installs the system libraries only on Debian/Ubuntu and Fedora/RHEL.

`sudo install/step-preview.sh status` checks that the component really renders and says what to do if not — the System page's **STEP preview component** line shows *Installed*, never *works*. Both commands exit `0` when done (or when the component works), `1` on a failure, with its reason, and `3` when the component is not available for this machine or its Python.

| Reason | What to do |
|---|---|
| `smoke_failed:system_library:<soname>` | A system library is missing: install the package `status` names, then run `enable`. |
| `permission` | Something under `runtime/` is not writable by the install's owner (often left by an earlier `sudo` run): `sudo chown -R <owner> <install>/runtime`, then `enable`. |
| `lock_timeout` | Another install of the component held its lock for 15 minutes: let it finish, then run `enable` again. |
| `helper_unproven` | An update from Settings could not prove an earlier run of the helper ended: restart BamDude, then update again or run `enable`. |
| `pip_timeout`, `pip_failed` | The download did not complete: check the network, then run `enable`. |

Every other sentence a STEP thumbnail can end with — the model too large or too slow to convert, a job out of time, a backup in the way — is explained under [File Manager → STEP thumbnails](../features/file-manager.md#step-thumbnails); the previous thumbnail stays in every one of those cases. *The preview service is not available right now* is the [local preview service](#local-preview-service), not the STEP component.

### Reporting an issue

When reporting issues, include:

- BamDude version
- Printer model and firmware version
- Operating system
- Steps to reproduce
- Error messages from logs
- Docker compose configuration (if applicable)

File issues at [github.com/kainpl/bamdude/issues](https://github.com/kainpl/bamdude/issues).

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
