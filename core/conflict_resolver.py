import signal
import subprocess
from dataclasses import dataclass
from typing import List

import psutil


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
    def _kill_processes(process: psutil.Process, sig=signal.SIGTERM):
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
