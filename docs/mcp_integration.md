# MCP Server Integration

This project leverages the **Model Context Protocol (MCP)** to allow AI agents (like Antigravity/Windsurf/Cursor) to directly interact with the 3D printer and the edge device.

> [!NOTE]
> **MCP is completely optional.**
>
> * **Core Functionality**: The spaghetti detection and printer pausing (`scripts/deploy.py` and `src/inference_loop.py`) work entirely without MCP or AI agents. They use standard SSH and HTTP requests.
> * **MCP Role**: MCP is strictly a "convenience layer" that allows you to chat with your printer or ask an AI to debug issues for you.

## Available Servers

### 1. Moonraker API (`moonraker-api`)

* **Source**: `@mcp-market/3d-printer-server`
* **Purpose**: Allows the AI to query printer status, temperatures, and control the print job (pause/cancel/resume) via the Moonraker API.
* **Authentication**: Requires IP and Port (and optionally API Key if configured on Moonraker).

### 2. Voron SSH Gateway (`voron-ssh-gateway`)

* **Source**: Custom Python module (`mcp_ssh_gateway`)
* **Purpose**: Provides safe, scoped SSH execution on the Raspberry Pi.
* **Capabilities**:
  * Restarting systemd services (`sudo systemctl restart klipper-cortex`).
  * Reading log files (`journalctl`).
  * Verifying file deployment.

## Setup for Developers

To enable these tools for your AI agent, you need to configure your client's MCP settings.

1. **Copy the Example Config**:
    Use `mcp_config.example.json` as a reference.

2. **Install Dependencies**:
    * **Node.js** (for `moonraker-api`).
    * **Python 3** (for `voron-ssh-gateway`).
    * *Note: `mcp_ssh_gateway` must be installed in your python environment.*

3. **Configure Environment Variables**:
    Fill in your specific IP address, SSH user, and keys in the configuration.

    ```json
    "env": {
      "PRINTER_IP": "192.168.1.100",
      "SSH_KEY_FILE": "/absolute/path/to/key"
    }
    ```

4. **Enable the Servers**:
    Ensure `"disabled": false` is set in your configuration.

## Usage

Once configured:

* **Status Checks**: You can ask the AI "Is the printer currently printing?" or "What is the bed temperature?".
* **Debugging**: You can ask "Check the logs on the Pi to see why the service failed."
* **Safety**: The AI can double-check printer state before issuing deployment commands.
