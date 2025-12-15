import os
import sys

from core.scan import list_interfaces


def check_interface(interface: str, print_errors: bool = True,
                    exit_on_error: bool = True):
    status = os.path.exists(f"/sys/class/net/{interface}")
    if print_errors:
        print(f"[ERROR] Interface '{interface}' not found.")
        print(f"Available: {', '.join(list_interfaces())}")
    if exit_on_error:
        sys.exit(1)

    return status