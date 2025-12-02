import abc
import argparse

class BaseCommand(abc.ABC):
    """
    Abstract Base Class for all commands in the toolkit.
    """
    @abc.abstractmethod
    def execute(self, **kwargs) -> str:
        """Executes the specific action of the command."""
        pass

    @classmethod
    @abc.abstractmethod
    def get_name(cls) -> str:
        """Returns the command name used in the CLI."""
        pass

    @classmethod
    @abc.abstractmethod
    def configure_parser(cls, parser: argparse.ArgumentParser):
        """Adds specific arguments for this command to the parser."""
        pass
