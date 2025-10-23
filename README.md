# Dynamic Network Priority Manager

## Overview

This tool provides a service for Ubuntu and other `systemd`-based Linux systems to automatically manage network priority between an ethernet and a Wi-Fi connection.

It is designed to solve the common problem where a wired ethernet connection is preferred, but may be unreliable. The service continuously monitors the ethernet connection's internet access. If connectivity is lost, it verifies the Wi-Fi connection has internet access and then automatically shifts network traffic to it. When ethernet connectivity is restored, the service seamlessly switches back.

## Features

- **Automatic Failover:** Automatically prioritizes Wi-Fi when the ethernet connection fails, after verifying Wi-Fi is online.
- **Automatic Recovery:** Automatically prioritizes ethernet again once it becomes stable.
- **Intelligent Failback:** If both ethernet and Wi-Fi are offline, no changes are made, and checks become more frequent to ensure rapid recovery.
- **Heuristic-based Detection:** No configuration needed. The script automatically finds one active ethernet and one active Wi-Fi interface.
- **Relative & Non-Persistent:** Changes to network routing are temporary (reset on reboot) and are calculated relative to your existing metric configuration to avoid conflicts with other network interfaces.
- **Simple Management:** A set of simple shell scripts are provided to install, start, monitor, and uninstall the service.

## How It Works

The core Python script (`network-monitor.py`) runs as a `systemd` service in the background.

1.  **Detection:** On startup, the script looks for exactly one active ethernet and one active Wi-Fi device. If it doesn't find them, it will wait 5 minutes and try again.
2.  **Monitoring:** It checks the primary (ethernet) connection by pinging a reliable external server (`8.8.8.8` or `1.1.1.1`).
3.  **Priority Switching:** It uses the `ip route replace` command to change the `metric` of the default routes. The script reads the existing metrics of the two interfaces and ensures the preferred interface receives the lower of the two values, preventing conflicts with other system routes.
4.  **Failover Logic:**
    - If ethernet is online, it is given the higher priority (lower metric).
    - If ethernet is offline, the script then checks if Wi-Fi is online.
    - If Wi-Fi is online, it is given the higher priority.
    - If both connections are offline, no changes are made, and the script re-checks everything in 1 minute.

## Files in this Repository

- `network-monitor.py`: The core Python script containing all the logic.
- `network-monitor.service`: The `systemd` unit file that allows the script to run as a background service.
- `install.sh`: A script to install the service by copying files to the correct system locations and enabling the service.
- `start_service.sh`: A helper script to start or restart the service.
- `show_logs.sh`: A helper script to view the live logs of the service.
- `uninstall.sh`: A script to cleanly stop the service and remove all its files from the system.

## Installation

1.  Make the installer script executable:
    ```bash
    chmod +x install.sh
    ```
2.  Run the installer with root privileges:
    ```bash
    sudo ./install.sh
    ```

## Usage

-   **To Start or Restart the Service:**
    ```bash
    sudo ./start_service.sh
    ```

-   **To View Live Logs:**
    ```bash
    ./show_logs.sh
    ```

-   **To Uninstall the Service:**
    ```bash
    sudo ./uninstall.sh
    ```