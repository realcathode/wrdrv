from dataclasses import dataclass
import subprocess
import re
from typing import Dict, List, Optional

from .vulnerability_database import VulnerabilityDatabase
from utils import check_interface_exists

@dataclass
class IwOutput:
    bssid: str
    essid: str = "<Hidden>"
    freq: int = 0
    channel: int = 0
    signal_dbm: float = -100.0
    wpa: bool = False
    wpa2: bool = False
    tkip: bool = False
    ccmp: bool = False
    wep: bool = False
    wps: bool = False

class WirelessMonitor:
    """
    Discovers APs using `iw`. Parses the output.
    """
    RE_BSS_MAC = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    RE_DS_CHANNEL = re.compile(r'^\s*DS Parameter set: channel (\d+)')
    RE_PRIMARY_CHANNEL = re.compile(r'^\s*\* primary channel: (\d+)')

    def __init__(self, interface: str, vuln_file: str = "vulnwsc.txt"):
        self.interface = interface
        self.vuln_db = VulnerabilityDatabase(vuln_file)
        self.networks: Dict[str, IwOutput] = {}

    def perform_scan(self) -> str:
        """
        Executes a scan via 'iw'.
        """
        check_interface_exists(self.interface)

        try:
            cmd = ["sudo", "iw", "dev", self.interface, "scan"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)

            scanned_networks = self._parse_iw_output(proc.stdout)

            for net in scanned_networks:
                self.networks[net.bssid] = net

            return f"[SUCCESS] Scan Complete. Found {len(scanned_networks)} APs."

        except subprocess.CalledProcessError as e:
            return f"[FAILURE] Scan failed (Exit Code {e.returncode}): {e.stderr.strip()}"
        except Exception as e:
            return f"[FAILURE] Unexpected error: {e}"

    def _parse_iw_output(self, raw_output: str) -> List[IwOutput]:
        """
        Parses 'iw scan' output.
        """
        networks = []
        current_net: Optional[IwOutput] = None

        lines = raw_output.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            tokens = line.split()
            token = tokens[0]

            if token == "BSS":
                if current_net:
                    networks.append(current_net)

                mac_candidate = tokens[1].split('(')[0]

                if self.RE_BSS_MAC.match(mac_candidate):
                    current_net = IwOutput(bssid=mac_candidate.upper())
                continue

            if current_net is None:
                continue

            if token == "SSID:":
                ssid_val = line[5:].strip()
                if ssid_val:
                    current_net.essid = ssid_val
            elif "DS Parameter set: channel" in line:
                match_ds = self.RE_DS_CHANNEL.match(line)
                if match_ds:
                    current_net.channel = int(match_ds.group(1))
            elif "primary channel:" in line:
                match_primary = self.RE_PRIMARY_CHANNEL.match(line)
                if match_primary:
                    current_net.channel = int(match_primary.group(1))
            elif token == "signal:":
                try:
                    dbm = float(tokens[1])
                    current_net.signal_dbm = dbm
                except (ValueError, IndexError): pass
            elif token == "WPA:":
                current_net.wpa = True
            elif token == "RSN:":
                current_net.wpa2 = True
            elif token == "capability:":
                if "Privacy" in line:
                    current_net.wep = True
            elif "WPS:" in line:
                current_net.wps = True

            if "CCMP" in line:
                current_net.ccmp = True
            if "TKIP" in line:
                current_net.tkip = True

        if current_net:
            networks.append(current_net)

        return networks

    def get_results(self, reverse_scan: bool = False) -> Dict[int, IwOutput]:
        """
        Returns a sorted dictionary of networks and prints a table to stdout.
        """
        networks_list = sorted(
            self.networks.values(),
            key=lambda x: x.signal_dbm,
            reverse=True
        )
        indexed_results = {(i + 1): net for i, net in enumerate(networks_list)}

        print(f'\nNetworks found: {len(indexed_results)}')
        # Header
        print('{:<4} {:<18} {:<22} {:<4} {:<7} {:<6} {:<10} {:<10}'.format(
            '#', 'BSSID', 'ESSID', 'CH', 'PWR', 'Enc', 'Cipher', 'WPS'))

        items = list(indexed_results.items())
        if reverse_scan:
            items = items[::-1]

        for n, net in items:
            self._print_network_row(n, net)

        return indexed_results

    def _print_network_row(self, index: int, net: IwOutput):
        """Helper to print a single row cleanly"""
        def truncate(s, length):
            s = str(s)
            return s[:length-1] + " " if len(s) > length else s.ljust(length)

        def colorize(text, color_code):
            return f"\033[{color_code}m{text}\033[0m"

        if net.wpa2: enc_str = "WPA2"
        elif net.wpa: enc_str = "WPA"
        elif net.wep: enc_str = "WEP"
        else: enc_str = "Open"

        ciphers = []
        if net.ccmp: ciphers.append("CCMP")
        if net.tkip: ciphers.append("TKIP")
        cipher_str = "+".join(ciphers)

        row = [
            truncate(f"{index})", 4),
            truncate(net.bssid, 18),
            truncate(net.essid, 22),
            truncate(net.channel, 4),
            truncate(int(net.signal_dbm), 7),
            truncate(enc_str, 6),
            truncate(cipher_str, 10),
            truncate(net.wps, 10)
        ]

        line = " ".join(row)
        if enc_str == "Open":
            print(colorize(line, "92"))
        else:
            print(line)