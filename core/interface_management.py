import signal
import subprocess
from enum import Enum
from dataclasses import dataclass
from typing import List

import psutil


class InterfaceMode(str, Enum):
    MONITOR = "monitor"
    MANAGED = "managed"


class InterfaceAction(str, Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class CheckResult:
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
    This class is designed to detect and optionally terminate running
    system services and processes that may interfere with low-level
    network operations.
    """
    PROCESSES = {'wpa_action', 'wpa_supplicant', 'wpa_cli', 'dhclient', 'ifplugd', 'dhcdbd', 'dhcpcd', 'udhcpc',
                 'NetworkManager', 'knetworkmanager', 'avahi-autoipd', 'avahi-daemon', 'wlassistant', 'wifibox',
                 'net_applet', 'wicd-daemon', 'wicd-client', 'iwd', 'hostapd'
                 }
    SERVICES = {'wicd', 'network-manager', 'avahi-daemon', 'NetworkManager', 'wpa_supplicant'}


    def _check_services(self, kill: bool = False):
        """
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
        Iterates over all running processes and matches their names against
        a predefined list of known conflicting processes. Optionally sends
        a termination signal to the detected processes.

        :param kill: If True, send a termination signal to found processes.
        :return: A list of process names that were found running.
        """
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
            print("Unable to kill process, are you root?")

    def check(self) -> CheckResult:
        """
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

    @staticmethod
    def restore() -> List[str]:
        """
        Restores critical networking services that may have been killed.
        """
        targets = ['NetworkManager', 'avahi-daemon', 'wicd', 'wpa_supplicant']

        results = []
        for service in targets:
            check = subprocess.run(['systemctl', 'is-enabled', service],
                                   capture_output=True, text=True)
            if check.returncode == 0:
                print(f"[*] Restoring service: {service}...", end=' ', flush=True)
                try:
                    subprocess.run(['systemctl', 'restart', service], check=True, capture_output=True)
                    print("OK")
                    results.append(service)
                except subprocess.CalledProcessError:
                    print("FAILED")
        return results


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
        try:
            phy = self._get_phy()
            mode_str = mode.value

            self.down(check=False, capture_output=True)
            subprocess.run(['iw', 'dev', self._interface, 'del'],
                           check=True, capture_output=True)
            subprocess.run(
                ['iw', 'phy', phy, 'interface', 'add', self._interface, 'type', mode_str],
                check=True, capture_output=True
            )
            self.up()

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode().strip() if e.stderr else "Unknown error"
            raise RuntimeError(f"Failed to set {mode_str} mode: {err_msg}")

    def down(self, check: bool = True, capture_output: bool = False):
        """
        Bring the network interface down.
        """
        subprocess.run(['ip', 'link', 'set', self._interface, InterfaceAction.DOWN.value],
                       check=check, capture_output=capture_output)

    def up(self):
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