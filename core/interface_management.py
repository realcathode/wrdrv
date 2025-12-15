import signal
import subprocess
from enum import Enum
from dataclasses import dataclass

import psutil


class InterfaceMode(str, Enum):
    """Class that represents the mode of the interface."""
    MONITOR = "monitor"
    MANAGED = "managed"


class InterfaceAction(str, Enum):
    """Class that represents the action of the interface."""
    UP = "up"
    DOWN = "down"


@dataclass
class CheckResult:
    """Class that represents the result of the check."""
    services: list
    processes: list


"""
TODO:
    - Capture and return stdout/stderr from commands
      instead of discarding subprocess output.
    - Add logging support for executed commands.
"""

class ConflictResolver:
    """
    Resolves conflicts with network-related services and processes.

    This class is designed to detect and optionally terminate running
    system services and processes that may interfere with low-level
    network operations (e.g. wireless interface control, monitor mode,
    access point setup).

    It checks for known conflicting services managed by systemd and
    network-related processes running on the system. When requested,
    it can stop these services and send termination signals to processes.
    """
    PROCESSES = {'wpa_action', 'wpa_supplicant', 'wpa_cli', 'dhclient', 'ifplugd', 'dhcdbd', 'dhcpcd', 'udhcpc',
                 'NetworkManager', 'knetworkmanager', 'avahi-autoipd', 'avahi-daemon', 'wlassistant', 'wifibox',
                 'net_applet', 'wicd-daemon', 'wicd-client', 'iwd', 'hostapd'
                 }
    SERVICES = {'wicd', 'network-manager', 'avahi-daemon', 'NetworkManager'}


    def _check_services(self, kill: bool = False):
        """
        Check for running conflicting systemd services.

        Iterates over the predefined list of services and checks their
        status using systemctl. Optionally stops the services if requested.

        :param kill: If True, stop all detected running services.
        :return: A list of service names that were found running.
        """
        found_services = list()
        for service in self.SERVICES:
            result = subprocess.run(['systemctl', 'status', service], capture_output=True, text=True)
            if result.returncode == 0:
                found_services.append(service)
                if kill:
                    self._stop_service(service)
        return found_services

    @staticmethod
    def _stop_service(service):
        """
        Stop a systemd service.

        Attempts to stop the specified service using systemctl and prints
        the result of the operation.

        :param service: Name of the systemd service to stop.
        """
        result = subprocess.run(['systemctl', 'stop', service], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Service {service} stopped successfully.")
        else:
            print(f"Service {service} stopped unsuccessfully. Status: {result.returncode}")

    def _check_processes(self, kill: bool = False):
        """
        Check for running conflicting processes.

        Iterates over all running processes and matches their names against
        a predefined list of known conflicting processes. Optionally sends
        a termination signal to the detected processes.

        :param kill: If True, send a termination signal to found processes.
        :return: A list of process names that were found running.
        """
        #need check this func on real PC
        found_processes = list()
        for process in psutil.process_iter():
            if process.name() in self.PROCESSES:
                found_processes.append(process.name())
                if kill:
                    self._kill_processes(process)
        return found_processes

    @staticmethod
    def _kill_processes(process: psutil.Process, sig = signal.SIGTERM):
        """
        Send a signal to terminate a process.

        Handles common exceptions such as the process already terminating
        or insufficient permissions.

        :param process: psutil.Process instance to signal.
        :param sig: Signal to send (default: SIGTERM).
        """
        try:
            process.send_signal(sig)
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            print("You are root?!")

    def check(self) -> CheckResult:
        """
        Check for conflicting services and processes without stopping them.

        :return: CheckResult containing lists of running services and processes.
        """
        services = self._check_services()
        process = self._check_processes()
        return CheckResult(services=services, processes=process)

    def check_and_kill(self) -> CheckResult:
        """
        Check for conflicting services and processes and terminate them.

        Stops detected systemd services and sends termination signals
        to detected processes.

        :return: CheckResult containing lists of affected services and processes.
        """
        services = self._check_services(kill=True)
        process = self._check_processes(kill=True)
        return CheckResult(services=services, processes=process)


class InterfaceManagement:
    """
    Provides low-level control over a wireless network interface.

    This class manages both the operational state (UP/DOWN) and the
    operating mode (managed/monitor) of a network interface using
    standard Linux networking tools (`ip`, `iw`)

    Responsibilities:
        - Bring the interface link state up or down
        - Switch interface mode between managed and monitor

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