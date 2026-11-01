---
title: AI clients
description: Package formats, connection steps and honest client verification status
---

# AI clients

This matrix was checked on **1 November 2026**. It describes a development build, not features already released in v0.7.2. A validated manifest or SDK test does not prove installation in the named client. No public marketplace approval is claimed.

| Client / route | Package | What is verified | Remaining boundary |
|---|---|---|---|
| Codex CLI app-server 0.166.0, Windows | Direct MCP plus workspace skill; portable plugin separately | Real BamDude connection: capabilities, guide, discovered skill, refusal after revoke; no model turn | Plugin installation and other OSes unverified |
| Claude Code 2.1.314, Windows | Claude plugin ZIP, local Node 22.19+ | Strict manifest validation; bundled connector socket tests | Installation and client execution pending |
| Claude Desktop, Windows/macOS | MCPB connector plus separate skill ZIP | Manifest schema; bundled connector independently tested | Desktop installation and bundled Node compatibility unverified |
| ChatGPT web / cloud | None supported in v1 | No key-only network path verified | Private LAN reachability, client auth/account availability |

## Codex

1. Download the portable plugin ZIP and extract it. Install the skill/plugin through the client's local plugin flow. The package contains guidance; it does not install credentials or silently configure a server.
2. In BamDude's **Manual connection** section, copy the PowerShell command for the saved address. It contains an environment-variable name, not your key.
3. Supply `BAMDUDE_MCP_KEY` to the Codex process through your normal private environment configuration. Do not put it in chat or commit it to a project. This is an environment secret, not a claim of OS-vault storage.
4. Alternatively, add the following configuration using your own address:

    ```toml
    [mcp_servers.bamdude]
    url = "https://farm.example/mcp"
    bearer_token_env_var = "BAMDUDE_MCP_KEY"
    ```

5. Restart the MCP connection/client, then ask for capabilities and guide. Do not run an OAuth login for this key-only endpoint. For a self-signed certificate, use explicit trust in a suitable connector or your managed certificate setup; never disable certificate verification.

The ChatGPT desktop app's local Codex MCP settings are a different route from ChatGPT web/cloud. Availability in one does not establish availability in the other. See [official MCP setup](https://learn.chatgpt.com/docs/extend/mcp).

## Claude Code

1. Extract the Claude plugin ZIP and install that directory through Claude Code's plugin flow. For a temporary test, `claude --plugin-dir <extracted-directory>` loads it for that session.
2. Enter **BamDude MCP address**, **BamDude MCP key** and, when needed, **Trusted CA file** in the plugin's user configuration. The key field is marked sensitive; the client manages its storage.
3. This plugin uses the local Node connector. Node 22.19+ must be available on that computer.
4. Start a fresh client connection and request capabilities and guide. The plugin includes the canonical skill.

This package has no registered marketplace; do not use a made-up repository install command. See [Claude's plugin reference](https://code.claude.com/docs/en/plugins-reference).

The setup panel's **Manual connection** HTTP example connects directly, bypassing the local connector: its CA-file setting, redirect/OAuth protections and connector limits do not apply; for a self-signed server, configure trust in Claude Code itself and never disable TLS verification.

## Claude Desktop

1. Download the `.mcpb` package from the setup panel.
2. In Desktop's local **Extensions** installation UI, select that package and review its local connector permission request.
3. Enter the farm address and key in the extension's configuration. For a self-signed certificate, select its CA file. The package requires the host's bundled Node to meet its declared minimum; this still needs Desktop acceptance.
4. Download the **skill ZIP** separately and install it through the client's Skills UI. Installing MCPB alone does not install the skill.
5. Restart the connection and request capabilities and guide. Check the selected key's MCP marker in BamDude.

Desktop's cloud **remote connector** is a different route: its requests may come from the provider's infrastructure, not your computer. See [local MCP servers on Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

## ChatGPT web and public tunnels

The v1 matrix has no verified ChatGPT cloud installation path. Do not expose the entire farm to make a connectivity test turn green. If a future supported setup needs a public proxy/tunnel, it must expose **only `/mcp`**; `/api/v1` and the web UI must remain inaccessible through it. Add only that exact external host to the MCP allowlist, and understand that the chosen provider receives permitted data. OAuth/relay infrastructure is outside v1.
