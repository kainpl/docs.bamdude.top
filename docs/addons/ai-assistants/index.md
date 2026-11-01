---
title: AI assistants
description: Connect your own AI client to the optional read-only BamDude MCP server
---

# AI assistants

!!! warning "Development preview"
    This describes the MCP implementation under development after v0.7.2. It is not a claim that the published v0.7.2 has these controls. Client installation acceptance is still pending. The [support matrix](clients.md) separates package validation from a verified client connection.

BamDude supplies an optional **MCP server** at `/mcp`. Your assistant supplies the model and its account. The **client connector** handles the connection; the **skill** teaches the assistant how to use the available tools. Installing a skill does not connect a server or grant access.

The base module provides two operations: read capabilities and read the usage guide. It also provides the same guide as a resource and a short prompt. **Farm, print-history, filament and energy diagnostic tools are not available in this base module.** The assistant must read capabilities before claiming those features exist.

MCP is disabled by default. A separate API key must opt in, have an active owner and satisfy that owner's existing permissions. Choose only the printers needed. Logs require an additional opt-in. The diagnostic preset grants no queue, printer-control, inventory-write, cloud-token or label-printing permissions.

The integration does not start prints, switch plugs, execute shell/SQL, fetch arbitrary URLs, repair the database or run a background AI agent. Repairs remain in BamDude's normal UI.

## Choose the next step

- [Connect an assistant](setup.md): server address, key, installation and first check.
- [AI clients](clients.md): Codex, Claude Code, Claude Desktop and ChatGPT limitations.
- [Troubleshooting](troubleshooting.md): certificate, access and connection failures.

## What leaves the farm

BamDude returns permitted data to the client that requested it. That client may send it to its model provider. BamDude does not store the provider's API key or call the model itself. Diagnostic logs can contain personal or confidential text even after secret redaction. Cameras, videos and complete model files are outside v1.

The endpoint's limits apply per BamDude process: two simultaneous domain calls per key, eight per process, and sixty per minute per key. A second worker is not a shared global quota.
