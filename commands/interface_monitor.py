import argparse
import sys

from commands import BaseCommand
from core.interface_management import InterfaceManagement, ConflictResolver
from core.scan import list_interfaces


class MonitorCommand(BaseCommand):
    NAME = "monitor"
    HELP = "Switch to Monitor mode."

    @staticmethod
    def configure_parser(parser: argparse.ArgumentParser):
        parser.add_argument('interface', nargs='?', help='Interface name (e.g. wlan0)')
        parser.add_argument('-k', '--kill', action='store_true', help='Kill conflicting processes (highly recommended)')
        parser.epilog = "Example: sudo main.py monitor wlan0 -k"

    def execute(self, **kwargs):
        interface = kwargs.get('interface')
        if not interface:
            print(f"[ERROR] Interface required. Available: {', '.join(list_interfaces())}")
            raise SystemExit(1)

        kill = kwargs.get('kill')

        print(f"[*] Switching {interface} to MONITOR mode...")

        if kill:
            print("[*] Killing conflicting processes...")
            resolver = ConflictResolver()
            resolver.check_and_kill()

        im = InterfaceManagement(interface)
        try:
            im.monitor()
            print(f"[SUCCESS] {interface} is now in MONITOR mode.")

        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected failure: {e}")
            sys.exit(1)