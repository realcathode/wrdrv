import argparse
import os
import subprocess
import sys

from commands import BaseCommand
from core.interface_management import InterfaceManagement
from core.scan import list_interfaces


class ManagedCommand(BaseCommand):
    NAME = "managed"
    HELP = "Switch to Managed mode and restore network manager."

    @staticmethod
    def configure_parser(parser: argparse.ArgumentParser):
        parser.add_argument('interface', nargs='?', help='Interface name')
        parser.add_argument('-r', '--restart', action='store_true', help='Restart NetworkManager service')
        parser.epilog = "Example: sudo main.py managed wlan0 -r"

    def execute(self, **kwargs):
        interface = kwargs.get('interface')
        restart = kwargs.get('restart')

        if not interface:
            print(f"[ERROR] Interface required. Available: {', '.join(list_interfaces())}")
            raise SystemExit(1)

        if not os.path.exists(f"/sys/class/net/{interface}"):
            print(f"[ERROR] Interface '{interface}' not found.")
            print(f"Available: {', '.join(list_interfaces())}")
            sys.exit(1)

        print(f"[*] Switching {interface} to MANAGED mode...")

        im = InterfaceManagement(interface)
        try:
            im.managed()
            msg = f"[SUCCESS] {interface} is now in MANAGED mode."

            if restart:
                print("[*] Restarting NetworkManager...", end=' ', flush=True)
                try:
                    subprocess.run(['systemctl', 'restart', 'NetworkManager'], check=True, capture_output=True)
                    print("OK")
                    msg += " (NetworkManager restarted)"
                except subprocess.CalledProcessError:
                    print("FAILED")
                    msg += " (NetworkManager restart failed)"

            return msg

        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected failure: {e}")
            sys.exit(1)