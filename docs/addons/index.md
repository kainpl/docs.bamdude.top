---
title: Add-ons
description: Companion apps that extend BamDude beyond what a container can reach
---

# Add-ons

BamDude is a self-hosted server. Add-ons connect it to applications and hardware on your computer. BamDude Bridge handles slicer files and USB labels; AI assistant packages connect your chosen assistant to the server's optional read-only MCP endpoint.

<div class="grid cards" markdown>

-   :material-bridge:{ .lg .middle } **BamDude Bridge**

    ---

    A Windows tray app that accepts sliced plates straight from Bambu Studio's *Send to…* button and drives USB Niimbot label printers from BamDude's label queue.

    [:octicons-arrow-right-24: Documentation](bridge.md)

-   :material-brain:{ .lg .middle } **Obico ML**

    ---

    A standalone container for AI print-failure detection. Install and update just the ML API, without the full Obico stack.

    [:octicons-arrow-right-24: Installation and updates](obico-ml.md)

</div>

## AI assistants — development preview

The MCP server runs inside BamDude. The client package and skill are installed in your assistant, not on a printer. Start with the [AI assistant guide](ai-assistants/index.md); installation and client support are checked separately.
