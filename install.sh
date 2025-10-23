#!/bin/bash

# This script installs the Dynamic Network Priority Manager service.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

echo "Installing network monitor files..."

# Copy the script and make it executable
cp network-monitor.py /usr/local/bin/network-monitor.py
chmod +x /usr/local/bin/network-monitor.py

# Copy the systemd service file
cp network-monitor.service /etc/systemd/system/network-monitor.service

echo "Reloading systemd and enabling the service..."

# Reload systemd to recognize the new service
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable network-monitor.service

# Make helper scripts executable
chmod +x start_service.sh show_logs.sh

cat << EOF

Installation complete!

------------------------------------------------------------------
To manage the service, use the new scripts:

- Use 'sudo ./start_service.sh' to start or restart the service.
- Use './show_logs.sh' to view the live logs.
------------------------------------------------------------------

EOF
