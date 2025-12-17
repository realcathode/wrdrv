import os
import sys

from core.scan import list_interfaces


def check_interface_exists(interface: str) -> None:
    if not interface:
        print(f"[ERROR] Interface required. Available: {', '.join(list_interfaces())}")
        sys.exit(1)

    if not os.path.exists(f"/sys/class/net/{interface}"):
        print(f"[ERROR] Interface '{interface}' not found.")
        print(f"Available: {', '.join(list_interfaces())}")
        sys.exit(1)
