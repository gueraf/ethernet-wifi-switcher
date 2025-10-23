#!/usr/bin/env python3
print("--- Python script execution started ---", flush=True)
import subprocess
import time
import sys
import json

# Timeout for all external commands
CMD_TIMEOUT = 5
PING_TARGETS = ["8.8.8.8", "1.1.1.1"]

def find_interfaces():
    """
    Heuristically finds one active ethernet and one active wifi interface.
    """
    eth_iface, wifi_iface = None, None
    try:
        cmd = ["nmcli", "-t", "-f", "TYPE,DEVICE,STATE", "device", "status"]
        print(f"Running command: {' '.join(cmd)}", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=CMD_TIMEOUT)
        
        devices = result.stdout.strip().split('\n')
        ethernet_devices = [line.split(':')[1] for line in devices if line.startswith('ethernet:connected')]
        if len(ethernet_devices) == 1:
            eth_iface = ethernet_devices[0]
        else:
            if len(ethernet_devices) > 1:
                print(f"Heuristic warning: Found {len(ethernet_devices)} active ethernet devices. Expected 1.", flush=True)

        wifi_devices = [line.split(':')[1] for line in devices if line.startswith('wifi:connected')]
        if len(wifi_devices) == 1:
            wifi_iface = wifi_devices[0]
        else:
            if len(wifi_devices) > 1:
                print(f"Heuristic warning: Found {len(wifi_devices)} active wifi devices. Expected 1.", flush=True)
            
        if eth_iface and wifi_iface:
            return eth_iface, wifi_iface
        
    except subprocess.TimeoutExpired:
        print(f"Error: Command '{' '.join(cmd)}' timed out after {CMD_TIMEOUT} seconds.", flush=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error finding interfaces with nmcli: {e}", flush=True)
    
    return None, None

def get_gateway_and_metric(interface):
    """Gets the gateway and metric for a given interface using `ip -j route`."""
    try:
        cmd = ["ip", "-j", "route", "show", "dev", interface]
        print(f"Running command: {' '.join(cmd)}", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=CMD_TIMEOUT)
        routes = json.loads(result.stdout)
        for route in routes:
            if route.get("dst") == "default":
                gateway = route.get("gateway")
                metric = route.get("metric", 500)
                return gateway, metric
    except subprocess.TimeoutExpired:
        print(f"Error: Command '{' '.join(cmd)}' timed out after {CMD_TIMEOUT} seconds.", flush=True)
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        print(f"Warning: Could not parse route for {interface}: {e}", flush=True)
        pass
    return None, 500

def set_route_metric(interface, gateway, metric):
    """Uses 'ip route replace' to set a non-permanent metric."""
    if not (interface and gateway):
        return
    print(f"Setting metric for {interface} via {gateway} to {metric}...", flush=True)
    try:
        cmd = [
            "ip", "route", "replace", "default", "via", gateway,
            "dev", interface, "metric", str(metric)
        ]
        print(f"Running command: {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=CMD_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"Error: Command '{' '.join(cmd)}' timed out after {CMD_TIMEOUT} seconds.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to set route for {interface}: {e.stderr.strip()}", flush=True)

def check_connectivity(interface):
    """Pings targets through a given interface to check for connectivity."""
    print(f"Checking connectivity via {interface}...", flush=True)
    for target in PING_TARGETS:
        try:
            cmd = ["ping", "-c", "1", "-W", "2", "-I", interface, target]
            print(f"Running command: {' '.join(cmd)}", flush=True)
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3) # 3s timeout for ping
            print(f"Ping to {target} successful.", flush=True)
            return True
        except subprocess.TimeoutExpired:
            print(f"Ping to {target} timed out.", flush=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Ping to {target} failed.", flush=True)
    print(f"All pings failed via {interface}.", flush=True)
    return False

def main():
    """Main control loop."""
    print("Starting network monitor service with detailed logging.", flush=True)
    
    while True:
        print("\n--- Starting new check cycle ---", flush=True)
        eth_iface, wifi_iface = find_interfaces()

        if not (eth_iface and wifi_iface):
            print("Heuristic failed. Retrying in 5 minutes...", flush=True)
            time.sleep(300)
            continue
        
        print(f"Found interfaces: Ethernet({eth_iface}), Wifi({wifi_iface})", flush=True)
        eth_gateway, eth_metric = get_gateway_and_metric(eth_iface)
        wifi_gateway, wifi_metric = get_gateway_and_metric(wifi_iface)

        if not (eth_gateway and wifi_gateway):
            print("Could not determine gateways. Retrying in 5 minutes...", flush=True)
            time.sleep(300)
            continue
        
        print(f"Found gateways: Ethernet({eth_gateway}), Wifi({wifi_gateway})", flush=True)

        low_metric = min(eth_metric, wifi_metric)
        high_metric = max(eth_metric, wifi_metric)
        if low_metric == high_metric:
            high_metric += 10

        if check_connectivity(eth_iface):
            print("Ethernet is connected. Ensuring it has priority.", flush=True)
            set_route_metric(eth_iface, eth_gateway, low_metric)
            set_route_metric(wifi_iface, wifi_gateway, high_metric)
            print("Check cycle complete. Sleeping for 1 minute.", flush=True)
            time.sleep(60)
        else:
            print("Ethernet is down. Checking Wi-Fi before switching.", flush=True)
            if check_connectivity(wifi_iface):
                print("Wi-Fi is connected. Prioritizing Wi-Fi.", flush=True)
                set_route_metric(wifi_iface, wifi_gateway, low_metric)
                set_route_metric(eth_iface, eth_gateway, high_metric)
                print("Check cycle complete. Sleeping for 5 minutes.", flush=True)
                time.sleep(300)
            else:
                print("FAIL: Both Ethernet and Wi-Fi are disconnected. No changes made.", flush=True)
                print("Check cycle complete. Sleeping for 1 minute before re-checking all.", flush=True)
                time.sleep(60)

if __name__ == "__main__":
    main()
