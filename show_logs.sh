#!/bin/bash
# This script shows the live logs for the network monitor service.

echo "Showing live logs for network-monitor.service. Press Ctrl+C to exit."
journalctl -u network-monitor.service -f
