import os
import subprocess
import sys


def check_interface_exists(interface: str) -> None:
    if not interface:
        print(f"[ERROR] Interface required. Available: {', '.join(list_interfaces())}")
        sys.exit(1)

    if not os.path.exists(f"/sys/class/net/{interface}"):
        print(f"[ERROR] Interface '{interface}' not found.")
        print(f"Available: {', '.join(list_interfaces())}")
        sys.exit(1)


def list_interfaces():
    result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.splitlines():
        if ': ' in line:
            iface = line.split(': ')[1].split('@')[0]
            interfaces.append(iface)
    return interfaces
