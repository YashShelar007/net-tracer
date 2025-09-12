# NetTracer

**Network Path & Latency Visualizer**
A CLI tool to trace routes (ICMP/TCP/UDP) and visualize per-hop latency.

---

## 🚀 Features

- 🔍 **Multi-protocol traceroute**: `icmp`, `tcp`, or `udp`
- 🧭 **Cross-platform**:

  - Uses **Scapy** when raw sockets are available
  - Automatically falls back to the OS tool (**`tracert` on Windows**, **`traceroute` on macOS/Linux**)

- 📊 **Per-hop latency chart** (Matplotlib)
- 📦 **Simple CLI** with tidy table output

---

## 🛠 Prerequisites

### Windows

- **Python ≥ 3.9**
- Works out of the box (uses `tracert`)
  Optional for raw sockets (Scapy path):

  - **Npcap** (default install)
  - Run terminal **as Administrator**

### macOS / Linux

- **Python ≥ 3.9**
- `traceroute` installed (`brew install traceroute` or `sudo apt install traceroute`)
- Optional for raw sockets (Scapy path):

  - **sudo** privileges
  - **libpcap** / headers (e.g., `sudo apt install libpcap-dev`)
  - **tcpdump** (optional, for debugging)

> If Scapy cannot open raw sockets or libpcap is missing, NetTracer automatically uses the system traceroute utility.

---

## 📦 Installation

```bash
# 1) Clone & enter
git clone https://github.com/YashShelar007/NetTracer.git
cd NetTracer

# 2) Create & activate virtualenv
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Usage

### Basic

```bash
# Windows (no admin needed; uses tracert)
python nettracer.py --target 8.8.8.8

# macOS/Linux (uses traceroute unless run with sudo & Scapy)
python nettracer.py --target example.com
```

### With options

```bash
# ICMP (default), 3 packets/hop, 30 hops
python nettracer.py --target example.com --proto icmp --count 3 --max-hops 30

# UDP, 4 packets/hop, save chart and skip display
python nettracer.py --target 8.8.8.8 --proto udp --count 4 --out nettracer.png --no-plot
```

**Common flags**

- `--target` (str): Hostname or IP (required)
- `--proto` (str): `icmp` | `tcp` | `udp` (default: `icmp`)
- `--count` (int): Probes per hop (default: `3`)
- `--max-hops` (int): Max TTL/hops (default: `30`)
- `--timeout` (float): Seconds to wait per probe (default: `2.0`)
- `--dport` (int): Destination port for TCP/UDP (default: protocol-specific)
- `--no-plot`: Do not display a chart window
- `--out` (path): Save latency chart to file (e.g., `nettracer.png`)

**Output**

- Console table: hop → IP/host → average latency
- Optional chart saved to `--out` (or `nettracer.png` by default)

---

## 📝 Example

```bash
python nettracer.py --target 8.8.8.8 --proto udp --count 4

# Sample:
# Hop  IP/Host           Avg Latency
# 1    192.168.1.1       1.2 ms
# 2    10.0.0.1          6.8 ms
# ...
# Saved plot to nettracer.png
```

![nettracer.png](./nettracer.png)

---

## 🐞 Troubleshooting

- **Windows: “Sudo is disabled on this machine.”**
  PowerShell doesn’t use `sudo`. Just run `python nettracer.py …`.
  For raw-socket mode, open PowerShell/VSCode **as Administrator** and install **Npcap**.

- **“No libpcap provider available! pcap won’t be used”**
  You’re on a platform without libpcap (or not running as admin). NetTracer will fall back to the OS traceroute automatically.

- **“Dropping unsupported option: filter”**
  Informational Scapy warning on platforms without pcap; safe to ignore when using the fallback path.

- **All `*` for a hop**
  That router suppresses TTL-expired replies or a firewall is blocking the probe.
  Try another `--proto`, increase `--timeout`, or continue—later hops may still respond.

- **Permission denied (macOS/Linux)**
  Use `sudo` to enable raw sockets or rely on the fallback:

  ```bash
  sudo python nettracer.py --target 1.1.1.1
  # or without sudo (uses traceroute)
  python nettracer.py --target 1.1.1.1
  ```

---

## 🤝 Contributing

Issues and PRs welcome! Keep changes small and cross-platform.

---

## 📝 License

MIT © Yash Ramesh Shelar
