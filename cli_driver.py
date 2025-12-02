import sys
import argparse

from commands import COMMAND_REGISTRY

class CLIDriver:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="WiFi data collection and analysis toolkit",
            epilog="Use 'auditor <command> -h' for command specific help"
        )
        self.subparsers = self.parser.add_subparsers(
            dest='command_name',
            required=True,
            title='Available Commands',
        )

    def run(self):
        try:
            args = self.parser.parse_args()
            command_name = args.command_name

            if command_name not in COMMAND_REGISTRY:
                print(f"[ERROR] Unknown command: {command_name}", file=sys.stderr)
                return

            command_class = COMMAND_REGISTRY[command_name]

            command_args = vars(args)

            command_instance = command_class()
            result = command_instance.execute(**command_args)

            print("-" * 50)
            print(f"Command Result:\n{result}")
            print("-" * 50)

        except Exception as e:
            print(f"[FATAL ERROR] Application failed: {e}", file=sys.stderr)

