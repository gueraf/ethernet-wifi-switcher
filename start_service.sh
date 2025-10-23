#!/bin/bash
# This script restarts the network monitor service.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "This script requires root privileges. Please run with sudo:"
  echo "sudo ./start_service.sh"
  exit 1
fi

echo "Restarting the network monitor service..."
systemctl restart network-monitor.service
echo "Service (re)started successfully."
