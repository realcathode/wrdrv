from commands.base_command import BaseCommand
from .scan_command import ScanCommand
from .interface_monitor import MonitorCommand
from .interface_managed import ManagedCommand
COMMAND_REGISTRY = {
    cls.NAME: cls
    for cls in BaseCommand.__subclasses__()
}
