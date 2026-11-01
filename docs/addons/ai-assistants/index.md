---
title: AI assistants
description: Connect your own AI client to the optional read-only BamDude MCP server
---

# AI assistants

!!! warning "Development preview"
    This describes the MCP implementation under development after v0.7.2. It is not a claim that the published v0.7.2 has these controls. The base module has passed independent acceptance; the first farm diagnostics slice is awaiting review. The [support matrix](clients.md) separates package validation from a verified client connection.

BamDude supplies an optional **MCP server** at `/mcp`. Your assistant supplies the model and its account. The **client connector** handles the connection; the **skill** teaches the assistant how to use the available tools. Installing a skill does not connect a server or grant access.

The base module provides two operations: read capabilities and read the usage guide. It also provides the same guide as a resource and a short prompt. The first diagnostics slice adds **farm overview, printer inspection and local-service health**. The assistant must read capabilities: permissions can hide tools, and print-history, filament, energy, log and recovery tools are not available in this slice.

## First diagnostic reads

Ask “Which of my printers are waiting?” for a scoped, paginated overview, then “Inspect printer 5” for a narrower read. A key without permission to read all queue jobs receives printer status without job names or waiting details. Global system health is available only to unrestricted printer keys with the owner's system-read permission.

These tools read existing observations. They do not reconnect printers, capture photos, poll plugs, scan logs or run the scheduler. The report separates current telemetry from persisted queue claims. A claim alone is not proof that a printer is busy or that the claim is stale; inspect it in BamDude before taking action. An unknown camera timestamp stays unknown, and plug schedules describe current rules rather than yesterday's execution history.

MCP is disabled by default. A separate API key must opt in, have an active owner and satisfy that owner's existing permissions. Choose only the printers needed. Logs require an additional opt-in. The diagnostic preset grants no queue-write, printer-control, inventory-write, cloud-token or label-printing permissions.

The integration does not start prints, switch plugs, execute shell/SQL, fetch arbitrary URLs, repair the database or run a background AI agent. Repairs remain in BamDude's normal UI.

## Choose the next step

- [Connect an assistant](setup.md): server address, key, installation and first check.
- [AI clients](clients.md): Codex, Claude Code, Claude Desktop and ChatGPT limitations.
- [Troubleshooting](troubleshooting.md): certificate, access and connection failures.

## What leaves the farm

BamDude returns permitted data to the client that requested it. That client may send it to its model provider. BamDude does not store the provider's API key or call the model itself. Diagnostic logs can contain personal or confidential text even after secret redaction. Cameras, videos and complete model files are outside v1.

The endpoint's limits apply per BamDude process: two simultaneous domain calls per key, eight per process, and sixty per minute per key. A second worker is not a shared global quota.
