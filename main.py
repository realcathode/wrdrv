import sys
import argparse

from commands import COMMAND_REGISTRY

class CLIDriver:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="WiFi data collection and analysis toolkit")
        self.subparsers = self.parser.add_subparsers(dest='command_name', required=True, title='Available Commands')

        for name, cmd_class in COMMAND_REGISTRY.items():
            if name == "scan":
                cmd_parser = self.subparsers.add_parser(name, help=f"Scan all surrounding networks.")
                cmd_class.configure_parser(cmd_parser)


    def run(self):
        try:
            args = self.parser.parse_args()
            command_args = vars(args)
            command_class = COMMAND_REGISTRY[command_args.pop('command_name')]
            print(command_class().execute(**command_args))
        except SystemExit: pass
        except Exception as e: print(f"[FATAL ERROR] {e}", file=sys.stderr)

if __name__ == "__main__":
    driver = CLIDriver()
    driver.run()