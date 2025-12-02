from commands.base_command import BaseCommand
from .scan_command import ScanCommand

COMMAND_REGISTRY = {
    cls.get_name(): cls
    for cls in BaseCommand.__subclasses__()
}
