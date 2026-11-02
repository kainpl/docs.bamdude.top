---
title: AI assistants
description: Connect your own AI client to the optional read-only BamDude MCP server
---

# AI assistants

!!! warning "Development preview"
    This describes the MCP implementation under development after v0.7.2. It is not a claim that the published v0.7.2 has these controls. The base module, initial farm diagnostics, timelines, logs and energy inspection have passed independent acceptance; recovery explanations are awaiting review. The [support matrix](clients.md) separates package validation from a verified client connection.

BamDude supplies an optional **MCP server** at `/mcp`. Your assistant supplies the model and its account. The **client connector** handles the connection; the **skill** teaches the assistant how to use the available tools. Installing a skill does not connect a server or grant access.

The base module provides two operations: read capabilities and read the usage guide. It also provides the same guide as a resource and a short prompt. Diagnostics add **farm overview, printer inspection, local-service health, print timelines, opt-in application logs, persisted energy evidence and recovery explanations**. The assistant must read capabilities: permissions can hide tools, and period summaries are not available yet.

## First diagnostic reads

Ask “Which of my printers are waiting?” for a scoped, paginated overview, then “Inspect printer 5” for a narrower read. A key without permission to read all queue jobs receives printer status without job names or waiting details. Global system health is available only to unrestricted printer keys with the owner's system-read permission.

These tools read existing observations. They do not reconnect printers, capture photos, poll plugs, run active diagnostics or run the scheduler. The report separates current telemetry from persisted queue claims. A claim alone is not proof that a printer is busy or that the claim is stale; inspect it in BamDude before taking action. An unknown camera timestamp stays unknown, and plug schedules describe current rules rather than yesterday's execution history.

## Print timelines and logs

Ask “Show the timeline of archive 123” using its archive ID. The timeline includes only positively linked archive, queue, feed-journal and recovery records; identical filenames do not establish a connection. It labels slicer-derived end times as estimates. Current status is not a complete transition history, and missing retained events do not prove that a runout or replacement never happened. Spool identities and grams require the owner's inventory-read permission.

For a narrow application-log query, the key needs both an unrestricted printer scope and the separate log opt-in, plus the owner's settings-read permission. The server reads only its configured current log, at most 2 MiB per page, and removes known credentials and supported secret patterns before literal search. It omits oversized or incomplete entries. Unknown secrets in arbitrary prose can remain: enable log access only when that is acceptable for the chosen model provider. Log timestamps have no recorded offset and are converted from server local time. After `log_changed`, restart the query; after `busy`, allow one retry. A timed-out file reader can keep its slot occupied until the file operation really finishes.

MCP is disabled by default. A separate API key must opt in, have an active owner and satisfy that owner's existing permissions. Choose only the printers needed. Logs require an additional opt-in. The diagnostic preset grants no queue-write, printer-control, inventory-write, cloud-token or label-printing permissions.

The integration does not start prints, switch plugs, execute shell/SQL, fetch arbitrary URLs, repair the database or run a background AI agent. Repairs remain in BamDude's normal UI.

## Energy evidence

Ask for energy evidence for one printer and an explicit time interval, for example “Inspect printer 5's energy from October 24 to October 26, with Kyiv's UTC offsets.” The maximum range is 31 days. The owner's printer-read, all-archives-read, smart-plug-read and statistics-read rights are required; printer restrictions still apply.

Prints are selected by archive creation time. Returned print totals cover only that page, with measured, approximate, estimated and legacy figures separated; missing or unavailable energy stays unknown, while stored zero remains zero. Follow the cursor for more records. Repeated power-quality summaries describe the requested range and must not be added across pages.

Counter deltas describe sampled windows of the currently bound plug after its measurement-source cutoff. They are not exact requested-period consumption or the printer's historical total. Older source history is omitted after reassignment; archive-owned print figures remain available. Decreasing readings are evidence of a decrease, without guessing a reset. Counter growth beside missing print accounting is an observed coincidence, not proof that those prints consumed the delta: idle usage also contributes. The tool reads persisted meter suspicions and quality gaps without polling plugs, recalculating energy or changing accounting.

## Explain a print-state inconsistency

Ask the assistant to list print-state issues, then explain one printer, record kind and target ID. It uses the same recovery policy as System diagnostics and needs the owner's system-read, printer-read, all-queue-read and all-archive-read rights. It can explain a refusal without granting write permission. A dependency may prevent deletion while still allowing alignment; ambiguous runs and unresolved completion effects remain blockers.

The assistant cannot confirm that a print completed, sign a preview or perform a repair. An estimated end stays labelled as an estimate. Follow its link to the addressed record: BamDude rereads the current state under your browser account's permissions. Missing, changed or inaccessible records do not offer the old action. Request a fresh preview and confirm it manually in the normal dialog. A restart does not fix a durable queue claim.

## Choose the next step

- [Connect an assistant](setup.md): server address, key, installation and first check.
- [AI clients](clients.md): Codex, Claude Code, Claude Desktop and ChatGPT limitations.
- [Troubleshooting](troubleshooting.md): certificate, access and connection failures.

## What leaves the farm

BamDude returns permitted data to the client that requested it. That client may send it to its model provider. BamDude does not store the provider's API key or call the model itself. Diagnostic logs can contain personal or confidential text even after secret redaction. Cameras, videos and complete model files are outside v1.

The endpoint's limits apply per BamDude process: two simultaneous domain calls per key, eight per process, and sixty per minute per key. A second worker is not a shared global quota.
