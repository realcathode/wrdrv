import datetime
import itertools
import json
import os
import time

from core.wireless_monitor import WirelessMonitor


def get_unique_filename(base_path: str) -> str:
    """
    If base_path exists, append _1, _2, etc. until a free filename is found.
    """
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_path)
    counter = 1
    while True:
        new_path = f"{name}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def perform_scan(interface: str, bssid: str = 'None', loops: int = 1, no_stop: bool = False,
                 reverse: bool = False, output: str = None) -> dict:
    monitor = WirelessMonitor(interface=interface)
    results = dict()

    loop_iterator = itertools.count() if no_stop else range(loops)
    try:
        for i in loop_iterator:
            msg = monitor.perform_scan()
            if "[FAILURE]" in msg:
                raise RuntimeError(msg)
            current_scan_data = monitor.get_results(reverse_scan=reverse)
            results.update(current_scan_data)

            if output:
                output_file = get_unique_filename(output)
                with open(output_file, 'a') as f:
                    t = datetime.datetime.now()
                    record = {
                        "timestamp": t.isoformat(),
                        "loop": i + 1,
                        "scan_data": {str(k): v for k, v in current_scan_data.items()}
                    }
                    f.write(json.dumps(record) + "\n")
            time.sleep(0.3)
    except KeyboardInterrupt:
        if no_stop:
            print('\nScan interrupted.')

    return results
