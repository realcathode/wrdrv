## Overview

A modular Python-based framework for 802.11 reconnaissance, wardriving, and penetration testing.

This tool is intended to be used as a fast pipeline that collects WPS material without committing to cracking (potentially useful in statistical modeling on WPS configuration prevalence).

Current tools like `reaver` or `bully` are designed to sit and wait. Instead of "Target -> Retrieve Message -> Crack -> Next", this tool aims to automate the process without stopping on one target "Scan -> Retrieve Message -> Store -> Next"

## Installation

```bash
git clone https://github.com/realcathode/wrdrv
```

### Requirements

* Python 3.8+

* Linux Environment (root required for interface management)

* Python Dependencies:

```bash
pip install -r requirements.txt
```

### Launch

```bash
python3 main.py -h
```

## Project Roadmap

- [x] Monitor Mode Toggle: Create a reliable method to take an interface down, set mode to monitor, and bring it up.

```bash
# For more information: 
python3 main.py {monitor/managed} -h
```

- [x]  **Basic Scanning**: reliable AP discovery using `iw` parsing, including signal strength, encryption type, and WPS status detection.

```bash
python3 main.py scan -h
```

- [ ] Structured Scanning: enhance core/scan.py to parse active clients (Stations) associated with a chosen AP, not just the APs themselves.

- [ ] GPS Integration: Implement a thread to read data from a USB GPS dongle to tag discovered BSSIDs with coordinates.

- [ ] Kismet/Wigle Compatibility: Export scan results to formats compatible with Wigle.net uploading.

- [ ] WPS Harvest Mode: Automate WPS transaction initialization with neighbouring APs to capture M1 - M3 messages, and store the cryptographic parameters (PKE, PKR, E-Hash1, E-Hash2, AuthKey) for offline pin cracking.

- [ ] Priority Harvest: Implement a priority queue that sorts discovered APs by a score based on: OUI (Known Vulnerable Manufacturers), Signal Strength (RSSI), WPS State (Unlocked), regex (router ESSIDs that I've observed are almost always vulnerable). High-score targets are processed first.
