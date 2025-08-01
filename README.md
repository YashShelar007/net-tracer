# NetTracer

**Network Fault Visualizer**  
A CLI tool to trace network paths (ICMP/TCP/UDP) and visualize per-hop latency.

---

## 🚀 Features

- 🔍 **Multi-protocol traceroute** (ICMP, TCP, UDP)
- 📊 **Per-hop latency graph** via Matplotlib
- ⚙️ **Dynamic filters** & structured summaries
- 🛠️ **Lightweight CLI** powered by Python & Scapy

---

## 🛠 Prerequisites

- **Python** ≥ 3.9
- **sudo** privileges (for raw sockets & tcpdump)
- **libpcap-dev** (Ubuntu/Debian: `sudo apt install libpcap-dev`)
- **tcpdump** installed on your system

---

## 📦 Installation

```bash
# 1. Clone & enter
git clone https://github.com/YashShelar007/NetTracer.git
cd NetTracer

# 2. Create & activate virtualenv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Usage

```bash
sudo python nettracer.py \
  --target example.com \
  --proto icmp \
  --count 3 \
  --max-hops 20
```

- `--target`: hostname or IP
- `--proto`: `icmp` (default), `tcp`, or `udp`
- `--count`: packets per hop (default 3)
- `--max-hops`: maximum TTL/hops (default 30)

**Output**:

- Console table of each hop’s IP & avg latency
- `nettracer.png`: latency-vs-hop graph

---

## 📝 Example

```bash
sudo python nettracer.py --target 8.8.8.8 --proto udp --count 4

# Sample output:
# Hop  IP               Latency
# 1    192.168.1.1       0.002s
# 2    10.123.45.67      0.014s
# ...
# Saved plot to nettracer.png
```

![nettracer.png](./nettracer.png)

---

## 🐞 Troubleshooting

- **Permission denied** → run with `sudo` (raw sockets require root).
- **Missing libpcap** → install via your distro’s package manager.
- **No response (`*`)** → packet dropped or firewall; try a different protocol or increase timeout.

---

## 📝 License

MIT © Yash Ramesh Shelar
