import abc
import argparse

class BaseCommand(abc.ABC):
    """
    Abstract Base Class for all commands in the toolkit.
    """
    NAME: str
    HELP: str

    @abc.abstractmethod
    def execute(self, **kwargs) -> str:
        """Executes the specific action of the command."""
        pass

    @staticmethod
    @abc.abstractmethod
    def configure_parser(parser: argparse.ArgumentParser):
        """Adds specific arguments for this command to the parser."""
        pass
