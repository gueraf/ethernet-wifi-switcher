#!/bin/bash

# This script uninstalls the Dynamic Network Priority Manager service.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

echo "Stopping and disabling the network monitor service..."

# Use 'systemctl stop' and ignore errors if the service isn't running
systemctl stop network-monitor.service || true
systemctl disable network-monitor.service || true

echo "Removing service and script files..."

rm -f /etc/systemd/system/network-monitor.service
rm -f /usr/local/bin/network-monitor.py

# Also remove the old config file if it exists from previous versions
if [ -f /etc/network-monitor.conf ]; then
    echo "Removing legacy configuration file..."
    rm -f /etc/network-monitor.conf
fi

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Uninstallation complete."
