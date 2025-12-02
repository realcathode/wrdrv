import subprocess
import os
import re
from typing import Dict, List, Optional

NETWORK_RESULTS = {}

class WirelessMonitor:
    """
        Discovers APs using `iw`. Parses the output.
    """
    RE_BSS_MAC = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    RE_DS_CHANNEL = re.compile(r'^\s*DS Parameter set: channel (\d+)')
    RE_PRIMARY_CHANNEL = re.compile(r'^\s*\* primary channel: (\d+)')

    def __init__(self, interface: str):
        self.interface = interface
        self.vuln_list = ["D-Link DIR-600", "TP-Link TL-WR841N"]

    def perform_scan(self) -> str:
        """
        Executes a scan via 'iw'.
        """
        global NETWORK_RESULTS

        if not os.path.exists(f"/sys/class/net/{self.interface}"):
            return f"[FAILURE] Interface {self.interface} not found."

        try:
            cmd = ["sudo", "iw", "dev", self.interface, "scan"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            networks = self._parse_iw_output(proc.stdout)
            for net in networks:
                NETWORK_RESULTS[net['BSSID']] = net
            return f"[SUCCESS] Scan Complete."
        except subprocess.CalledProcessError as e:
            return f"[FAILURE] Scan failed (Exit Code {e.returncode}): {e.stderr.strip()}"
        except Exception as e:
            return f"[FAILURE] Unexpected error: {e}"

    def _parse_iw_output(self, raw_output: str) -> List[dict]:
        """
        Parses 'iw scan' output.
        """
        networks = []
        current_net: Optional[Dict] = None

        lines = raw_output.splitlines()
        for line in lines:
            line = line.strip()
            tokens = line.split()
            if not tokens:
                continue

            if tokens[0] == "BSS":
                mac_candidate = tokens[1].split('(')[0]
                if self.RE_BSS_MAC.match(mac_candidate):
                    if current_net:
                        networks.append(current_net)
                    current_net = {
                        'BSSID': mac_candidate.upper(),
                        'ESSID': '<Hidden>',
                        'Freq': 0,
                        'Channel': 0,
                        'Signal_dBm': -100.0,
                        'WPA': False,
                        'WPA2': False,
                        'WEP': False,
                        'TKIP': False,
                        'CCMP': False,
                        'WPS': False
                    }
                continue

            if current_net is None:
                continue

            token = tokens[0]

            if token == "SSID:":
                ssid_val = line[5:].strip()
                if ssid_val:
                    current_net['ESSID'] = ssid_val
            elif "DS Parameter set: channel" in line:
                match_ds = self.RE_DS_CHANNEL.match(line)
                if match_ds:
                    current_net['Channel'] = int(match_ds.group(1))
            elif "primary channel:" in line:
                match_primary = self.RE_PRIMARY_CHANNEL.match(line)
                if match_primary:
                    current_net['Channel'] = int(match_primary.group(1))
            elif token == "signal:":
                try:
                    dbm = float(tokens[1])
                    current_net['Signal_dBm'] = dbm
                except (ValueError, IndexError): pass
            elif token == "WPA:":
                current_net['WPA'] = True
            elif token == "RSN:":
                current_net['WPA2'] = True
            elif token == "capability:":
                if "Privacy" in line:
                    current_net['WEP'] = True
            elif "WPS:" in line:
                current_net['WPS'] = True

            if "CCMP" in line:
                current_net['CCMP'] = True
            if "TKIP" in line:
                current_net['TKIP'] = True

        if current_net:
            networks.append(current_net)

        return networks

    def get_results(self, reverse_scan: bool = False) -> Dict[int, dict]:
        global NETWORK_RESULTS
        networks = list(NETWORK_RESULTS.values())
        if not networks:
            return {}

        networks.sort(key=lambda x: x['Signal_dBm'], reverse=True)
        network_list = {(i + 1): network for i, network in enumerate(networks)}

        def colored(text, color=None):
            if color == 'green': return f'\033[92m{text}\033[00m'
            if color == 'red': return f'\033[91m{text}\033[00m'
            if color == 'yellow': return f'\033[93m{text}\033[00m'
            return text

        def truncate_str(s, length):
            if s is None: s = ""
            if len(s) > length:
                return s[:length - 1] + "_"
            return s + ' ' * (length - len(s))

        print(f'\nNetworks found: {len(networks)}')
        # Header
        print('{:<4} {:<18} {:<22} {:<4} {:<7} {:<6} {:<10} {:<10}'.format(
            '#', 'BSSID', 'ESSID', 'CH', 'PWR', 'Enc', 'Cipher', 'WPS'))

        items = list(network_list.items())
        if reverse_scan:
            items = items[::-1]

        for n, net in items:
            enc_str = "Open"
            if net['WPA2']: enc_str = "WPA2"
            elif net['WPA']: enc_str = "WPA"
            elif net['WEP']: enc_str = "WEP"

            ciphers = []
            if net['CCMP']: ciphers.append("CCMP")
            if net['TKIP']: ciphers.append("TKIP")
            cipher_str = "+".join(ciphers) if ciphers else ""

            line = ' '.join([
                truncate_str(f'{n})', 4),
                truncate_str(net['BSSID'], 18),
                truncate_str(net['ESSID'], 22),
                truncate_str(str(net['Channel']), 4),
                truncate_str(str(int(net['Signal_dBm'])), 7),
                truncate_str(enc_str, 6),
                truncate_str(cipher_str, 10),
                truncate_str(str(net['WPS']), 10),
            ])
            print(colored(line))

        return network_list
