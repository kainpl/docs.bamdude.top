---
title: AI troubleshooting
description: Resolve MCP setup failures without bypassing credentials or certificate verification
---

# AI troubleshooting

Use the status, error code and client log together. Do not paste an API key, authorization header, cookie or unredacted support bundle into chat. [Setup](setup.md) explains the normal path.

| Symptom | Check / next action |
|---|---|
| Server disabled / `/mcp` gives 404 | Enable MCP and save settings. Use exactly `/mcp`, without a trailing slash. `/mcp/` deliberately returns 404, without a redirect. |
| Server unavailable at startup | Install the current BamDude requirements through your normal update procedure, then restart. The new MCP dependency is needed; the rest of BamDude can start without it. |
| Held after restore / readers still stopping | Finish recovery and restart BamDude as directed. An enable toggle cannot bypass the restore hold. |
| `invalid_endpoint` | Use HTTPS outside loopback, with exact `/mcp`. In builds with the trusted-LAN HTTP option, a private HTTP address requires the explicit [server and connector opt-ins](setup.md#server-address). Remove user info, query strings and fragments. |
| `network_or_tls_error` | Check DNS/IP, port, reachability, certificate name and trust. A private LAN address cannot be reached by a cloud connector merely because its UI runs locally. |
| `redirect_forbidden` | Point directly at the final `/mcp`. Fix proxy HTTP-to-HTTPS or trailing-slash redirects; the connector never forwards credentials through a redirect. |
| `unauthorized` / 401 | Replace an expired, disabled or revoked key in client settings. Do not start OAuth discovery or put a key in the URL. |
| `forbidden` / 403 | Check key MCP/status flags, its active owner and permissions, exact allowed host and any supplied Origin. Do not broaden permissions blindly. |
| `incompatible_contract` | Update the client package and server to compatible versions. Do not change contract numbers by hand. |
| Package missing or incompatible | Use matching build/release assets. The server refuses wrong hashes, versions or canonical skill/guide content. Source installs need the AI package build step. |
| `response_too_large` | Ask for less data or a smaller page. The local connector returns a bounded error and keeps the connection usable. |
| `busy`, `rate_limited`, timeout | Reduce concurrency or wait. The connector does not retry indefinitely; the server's read limits remain in effect. |

## Self-signed certificate, especially an IP address

1. Obtain the correct PEM CA file from whoever manages your farm's HTTPS endpoint.
2. Select it in the local extension/plugin's **Trusted CA file** setting.
3. Use an address listed in the server certificate. A certificate for `farm.local` does not authenticate `192.0.2.10`; that IP must be explicitly present in subject alternative names if you use it.
4. After replacing a certificate/CA, update explicit trust and restart the MCP connection. A changed untrusted certificate must be refused.

**Never disable TLS verification**, including through `NODE_TLS_REJECT_UNAUTHORIZED=0`. The connector refuses that setting. Installing a provider/cloud remote connector is not the same as configuring trust in this local connector.

## The farm was offline when the client started

The local connector exits on a startup failure rather than retrying in the background. After the farm returns, restart the client or its MCP connection. A package can still be installed while its connection is failed.

## Server ready, but no client request observed

Run capabilities/guide in the selected client, select the same key in BamDude and click **Check connection**. Check the client's actual network route and credentials. REST `last_used` does not prove an MCP call. After a BamDude restart the marker is empty until another authorized MCP request.

The marker proves neither a successful diagnostic conclusion nor skill installation. Install the skill separately where required. If a tool is unavailable, explain the limitation rather than substituting arbitrary REST, SQL or device commands.

## Safe information for a report

Include the BamDude and client versions, OS, package format, whether the client is local or cloud, error code, server status, and the time of the attempt. Replace private hostnames/IPs if needed. Never include the key. A successful SDK test or manifest validation alone is not proof that your named client is supported.
