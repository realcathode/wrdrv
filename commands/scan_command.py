import argparse

from commands import BaseCommand
from core.scan import perform_scan, list_interfaces

class ScanCommand(BaseCommand):
    NAME = "scan"
    HELP = "Scan all surrounding networks."

    @staticmethod
    def configure_parser(parser: argparse.ArgumentParser):
        parser.add_argument('interface', nargs='?', help='Interface (Managed or Monitor mode OK)', metavar='INTERFACE')
        parser.add_argument('-b', '--bssid', help='Target specific BSSID', metavar='BSSID')
        parser.add_argument('-l', '--loops', type=int, default=1, help='number of scan loops to perform', metavar='LOOPS')
        parser.add_argument('-n', '--no-stop', action='store_true', help='scan indefinitely until stopping')
        parser.add_argument('-r', '--reverse', action='store_true', help='reverse output')
        parser.add_argument('-o', '--out', help='specify file to save results (default results.json)', metavar='OUTPUT')
        parser.epilog = "Example: sudo main.py scan wlan0 -l 3 -r -o results"

    def execute(self, **kwargs):
        interface = kwargs.get('interface')
        if not interface:
            print(f"[ERROR] Interface required. Available: {', '.join(list_interfaces())}")
            raise SystemExit(1)

        bssid = kwargs.get('bssid')
        loops = kwargs.get('loops', 1)
        reverse = kwargs.get('reverse', False)
        no_stop = kwargs.get('no_stop', False)
        output = kwargs.get('out')

        results = perform_scan(
            interface=interface,
            bssid=bssid,
            loops=loops,
            no_stop=no_stop,
            reverse=reverse,
            output=output
)

        return f"Scan complete. Found {len(results)} networks."
