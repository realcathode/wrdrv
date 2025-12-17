import subprocess
from enum import Enum

class InterfaceMode(str, Enum):
    MONITOR = "monitor"
    MANAGED = "managed"


class InterfaceAction(str, Enum):
    UP = "up"
    DOWN = "down"

class InterfaceManagement:
    """
    Provides low-level control over a wireless network interface.

    This class manages both the operational state (UP/DOWN) and the
    operating mode (managed/monitor) of a network interface using
    standard Linux networking tools (`ip`, `iw`)

    Responsibilities:
        - Bring the interface link state up or down
        - Switch interface mode between managed and monitor
    """

    def __init__(self, interface: str):
        self._interface = interface
        self.phy = self._get_phy()

    def _delete_interface(self) -> None:
        subprocess.run(['iw', 'dev', self._interface, 'del'],
                       check=True, capture_output=True)

    def _create_interface(self, mode_str) -> None:
        subprocess.run(
            ['iw', 'phy', self.phy, 'interface', 'add', self._interface, 'type', mode_str],
            check=True, capture_output=True
        )

    def _get_phy(self) -> str:
        """
        Gets the physical device name (phy0, phy1) needed to re-create the interface.
        """
        try:
            cmd = ['iw', self._interface, 'info']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            for line in result.stdout.splitlines():
                if 'wiphy' in line:
                    idx = line.split()[-1]
                    return f"phy{idx}"
            raise ValueError("No wiphy index found in iw info")

        except subprocess.CalledProcessError:
            raise ValueError(f"Interface {self._interface} not found or 'iw' command failed.")

    def _set_interface_mode(self, mode: InterfaceMode) -> None:
        """
        Reliably switches mode by deleting the interface and re-creating it.
        """
        mode_str = mode.value
        try:
            self.down(check=False, capture_output=True)
            self._delete_interface()
            self._create_interface(mode_str=mode_str)
            self.up()

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode().strip() if e.stderr else "Unknown error"
            raise RuntimeError(f"Failed to set {mode_str} mode: {err_msg}")

    def down(self, check: bool = True, capture_output: bool = False) -> None:
        """
        Bring the network interface down.
        """
        subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.DOWN.value],
                       check=check, capture_output=capture_output)

    def up(self) -> None:
        """
        Bring the network interface up.
        """
        subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.UP.value], check=True)

    def monitor(self):
        """
        Switch the interface to monitor mode using `iw`.
        """
        return self._set_interface_mode(InterfaceMode.MONITOR)

    def managed(self):
        """
        Switch the interface to managed mode using `iw`.
        """
        return self._set_interface_mode(InterfaceMode.MANAGED)

__all__ = ["InterfaceManagement"]