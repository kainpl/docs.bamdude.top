---
title: AI clients
description: Package formats, connection steps and honest client verification status
---

# AI clients

This matrix was checked on **1 November 2026**. It describes a development build, not features already released in v0.7.2. A validated manifest or SDK test does not prove installation in the named client. No public marketplace approval is claimed.

| Client / route | Package | What is verified | Remaining boundary |
|---|---|---|---|
| Codex CLI app-server 0.166.0, Windows | Portable skill plugin plus separately configured direct MCP | Installed/removed through the package's bundled local catalog in an isolated profile; installed skill discovered; real BamDude capabilities, guide and refusal after revoke; no model turn | Desktop and other OSes unverified |
| Claude Code 2.1.314, Windows | Claude plugin ZIP, local Node 22.19+ | Installed/removed through the package's bundled local catalog in an isolated profile; skill loaded; user configuration accepted; bundled connector connected and advertised both tools | Model-mediated calls, Desktop and other OSes unverified |
| Claude Desktop 4.4212.0, Windows | MCPB connector plus separate skill ZIP | Real MCPB install/remove; built-in Node enabled; configuration with empty CA; separate skill installed and used; one model request called capabilities and guide through an isolated loopback server | Desktop updates, LAN TLS, refusal after revoke through Desktop and macOS unverified |
| ChatGPT web / cloud | None supported in v1 | No key-only network path verified | Private LAN reachability, client auth/account availability |

## Codex

The ZIP includes a local catalog, not a published marketplace. Extract it to a permanent folder such as `C:\BamDude-AI`; keep that folder for updates. The same path is used below as `<extracted-folder>`.

1. Download and extract the portable plugin ZIP, then run these commands with your actual folder path. They install the skill; they do not configure credentials or a server:

    ```powershell
    codex plugin marketplace add "<extracted-folder>"
    codex plugin add bamdude-ai@bamdude-ai-local
    ```
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

1. Extract the Claude plugin ZIP to a permanent folder and register its bundled local catalog, then install:

    ```powershell
    claude plugin marketplace add "<extracted-folder>"
    claude plugin install bamdude-ai@bamdude-ai-local
    ```

    For a temporary test, `claude --plugin-dir <extracted-folder>` loads it for that session.
2. Enter **BamDude MCP address**, **BamDude MCP key** and, when needed, **Trusted CA file** in the plugin's user configuration. The key field is marked sensitive; the client manages its storage.
3. This plugin uses the local Node connector. Node 22.19+ must be available on that computer.
4. Start a fresh client connection and request capabilities and guide. The plugin includes the canonical skill.

This package has no public marketplace; do not use a made-up GitHub install command. Its local catalog is already in the ZIP. See [Claude's plugin reference](https://code.claude.com/docs/en/plugins-reference).

The setup panel's **Manual connection** HTTP example connects directly, bypassing the local connector: its CA-file setting, redirect/OAuth protections and connector limits do not apply; for a self-signed server, configure trust in Claude Code itself and never disable TLS verification.

## Claude Desktop

1. Download the `.mcpb` package from the setup panel.
2. Open **Settings → Extensions → Advanced settings → Install extension**, select the package, review it and confirm **Install**. The tested host had **Use built-in Node.js for MCP** enabled; its built-in Node met the package's minimum.
3. Enter the farm address and key in **Configure**, save, then enable the extension. Leave the optional **Trusted CA file** empty for a normally trusted certificate. For a self-signed certificate, select its CA file. **Settings → Developer → BamDude AI** should show **Running**; this alone does not prove a tool call.
4. Download the **skill ZIP** separately. Use **Skills → Add → Upload skill**, select the ZIP and confirm **Upload**. The skill appears as `bamdude-diagnostics`; its **Contents** includes `SKILL.md` and the references. Installing MCPB alone does not install the skill. Uploading the skill stores its instructions in your Claude account.
5. Start a fresh chat with the skill (or use **Try in chat**) and request capabilities and guide. Approve the named read-only tool calls when prompted. Check the selected key's MCP marker in BamDude.

The Windows check used an isolated test database, an ephemeral key and a loopback server, not a live farm. The connector was removed after the key was revoked; the installed skill and test chat were kept. Updating an existing Desktop extension and connecting over LAN TLS were not tested.

Desktop's cloud **remote connector** is a different route: its requests may come from the provider's infrastructure, not your computer. See [local MCP servers on Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

## ChatGPT web and public tunnels

The v1 matrix has no verified ChatGPT cloud installation path. Do not expose the entire farm to make a connectivity test turn green. If a future supported setup needs a public proxy/tunnel, it must expose **only `/mcp`**; `/api/v1` and the web UI must remain inaccessible through it. Add only that exact external host to the MCP allowlist, and understand that the chosen provider receives permitted data. OAuth/relay infrastructure is outside v1.
