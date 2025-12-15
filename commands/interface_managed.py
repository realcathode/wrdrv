import argparse
import sys

from commands import BaseCommand
from core.interface_management import InterfaceManagement, ConflictResolver
from core.scan import list_interfaces
from utils import check_interface


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

        check_interface(interface)

        print(f"[*] Switching {interface} to MANAGED mode...")

        im = InterfaceManagement(interface)
        try:
            im.managed()
            msg = f"[SUCCESS] {interface} is now in MANAGED mode."
            if restart:
                resolver = ConflictResolver()
                restored = resolver.restore()
                if restored:
                    msg += f" (Restored: {', '.join(restored)})"
                else:
                    msg += " (No services found to restore)"

        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected failure: {e}")
            sys.exit(1)