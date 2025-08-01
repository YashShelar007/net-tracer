# NetTracer

A CLI tool to trace network paths and visualize per-hop latency (ICMP/TCP/UDP).

## Requirements

- Python 3.9+
- sudo for Scapy + tcpdump
- libpcap-dev (for tcpdump)

## Quickstart

source venv/bin/activate
pip install -r requirements.txt
sudo python nettracer.py --target example.com --proto icmp --count 3
