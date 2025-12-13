from enum import Enum
import subprocess


class InterfaceMode(str, Enum):
    """Class that represents the mode of the interface."""
    MONITOR = "monitor"
    MANAGED = "managed"


class InterfaceAction(str, Enum):
    """Class that represents the action of the interface."""
    UP = "up"
    DOWN = "down"


class AirmonAction(str, Enum):
    """Class that represents the action of the interface."""
    START = "start"
    STOP = "stop"




"""
TODO:
    - Capture and return stdout/stderr from `airmon-ng` commands
      instead of discarding subprocess output.
    - Parse `airmon-ng` output to detect interface renaming
      (e.g. wlan0 -> wlan0mon).
    - Detect and report errors when `airmon-ng` fails.
    - Optionally return structured results (status, interface name).
    - Add logging support for executed commands.
"""

class AirmonInterfaceManagement:
    """
        Provides interface mode management using `airmon-ng`.

        This class wraps `airmon-ng` commands to control wireless interfaces,
        including starting and stopping monitor mode and terminating
        interfering processes.

        Responsibilities:
            - Start monitor mode using `airmon-ng`
            - Stop monitor mode and return interface to managed state
            - Kill conflicting processes via `airmon-ng check kill`

        Notes:
            - Requires `airmon-ng` to be installed
            - Requires root privileges
            - Intended for systems using aircrack-ng toolset
            - Does not validate interface availability or state
        """
    _interface: str

    @staticmethod
    def airmon_kill():
        """
        Terminate processes that may interfere with monitor mode.

        Executes `airmon-ng check kill` to stop network managers and other
        services that can prevent switching a wireless interface to
        monitor mode.

        Notes:
            - Requires root privileges
            - Affects system-wide networking services
        """
        subprocess.run(['airmon-ng', 'check', 'kill'], capture_output=True, text=True)

    def _airmon_set_interface_mode(self, action: AirmonAction):
        """
        Change the interface mode using `airmon-ng`.

        Starts or stops monitor mode for the configured interface.

        :param action: AirmonAction.START to enable monitor mode,
                       AirmonAction.STOP to disable it
        :type action: AirmonAction
        """
        subprocess.run(['airmon-ng', action, self._interface], capture_output=True, text=True)

    def airmon_monitor(self):
        """
        Enable monitor mode using `airmon-ng`.

        Internally calls `airmon-ng start <interface>`.
        """
        return self._airmon_set_interface_mode(AirmonAction.START)

    def airmon_managed(self):
        """
        Disable monitor mode and restore managed mode using `airmon-ng`.

        Internally calls `airmon-ng stop <interface>`.
        """
        return self._airmon_set_interface_mode(AirmonAction.STOP)


class InterfaceManagement(AirmonInterfaceManagement):
    """
    Provides low-level control over a wireless network interface.

    This class manages both the operational state (UP/DOWN) and the
    operating mode (managed/monitor) of a network interface using
    standard Linux networking tools (`ip`, `iw`) and optionally
    `airmon-ng` via inheritance.

    Responsibilities:
        - Bring the interface link state up or down
        - Switch interface mode between managed and monitor
        - Integrate with `airmon-ng` for monitor mode management

    Notes:
        - Requires sufficient privileges (usually root)
        - Designed as a thin wrapper over system utilities
        - Assumes the interface name is valid
        - Does not perform safety checks or rollback on failure

    Example:
        iface = InterfaceManagement("wlan0")
        iface.down()
        iface.monitor()
        iface.up()
    """

    def __init__(self, interface: str):
        self._interface = interface

    def _set_interface_state(self, action: InterfaceAction):
        """
        Set the operational (link) state of the interface.

        Uses `ip link set <interface> up|down` to enable or disable
        the network interface.

        :param action: Desired link state (UP or DOWN)
        :type action: InterfaceAction
        """
        subprocess.run(['ip', 'link', 'set', self._interface, action],
                                capture_output=True, text=True)

    def _set_interface_mode(self, mode: InterfaceMode):
        """
        Set the operating mode of the interface.

        Uses `iw <interface> set type <mode>` to switch between
        managed and monitor modes.

        :param mode: Interface operating mode
        :type mode: InterfaceMode
        """
        subprocess.run(['iw', self._interface, 'set', 'type', mode],
                                capture_output=True, text=True)

    def down(self):
        """
        Bring the network interface down.

        Disables the interface link state.
        """
        return self._set_interface_state(InterfaceAction.DOWN)

    def up(self):
        """
        Bring the network interface up.

        Enables the interface link state.
        """
        return self._set_interface_state(InterfaceAction.UP)

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