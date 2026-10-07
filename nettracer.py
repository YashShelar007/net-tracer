#!/usr/bin/env python3
"""
NetTracer — Cross‑platform traceroute + latency plotter

This script will try a native Scapy-based traceroute first. If raw-socket
privileges or a packet-capture provider (Npcap/libpcap) are missing, it
falls back to the OS utility (tracert/traceroute) and parses the output.
"""

from __future__ import annotations
import os
import sys
import platform
import subprocess
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import click

# Optional imports; only used in the Scapy path
try:
    from scapy.all import IP, ICMP, UDP, TCP, sr1, conf  # type: ignore
    _HAVE_SCAPY = True
except Exception:
    _HAVE_SCAPY = False

# Plotting is only used when --no-plot is not set
try:
    import matplotlib.pyplot as plt
    _HAVE_MPL = True
except Exception:
    _HAVE_MPL = False


@dataclass
class Hop:
    ttl: int
    ip: str
    latency: Optional[float]  # seconds; None means timeout/no reply


# ------------------------- Utilities -------------------------

def _is_admin() -> bool:
    """Best-effort check for admin/root privileges."""
    try:
        if os.name == "nt":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        else:
            return os.geteuid() == 0  # type: ignore[attr-defined]
    except Exception:
        return False


def _scapy_ready() -> bool:
    """Check if Scapy is importable AND likely to work for sending/receiving."""
    if not _HAVE_SCAPY:
        return False
    # On Windows, Scapy requires either Npcap or WinDivert. If no pcap provider,
    # Scapy will print warnings and may not receive replies. We detect the
    # presence of a pcap provider via conf.use_pcap or conf.use_winpcap if set.
    try:
        # If conf.use_pcap exists, prefer True. On Windows, conf.use_pcap is set
        # when Npcap/WinPcap is available. This is a heuristic; even if False we
        # can still *send* probes, but receiving may fail. We also require admin.
        has_provider = bool(getattr(conf, "use_pcap", False) or getattr(conf, "use_winpcap", False) or getattr(conf, "use_winpcapy", False) or getattr(conf, "use_npcap", False) or getattr(conf, "use_winpcap", False))
    except Exception:
        has_provider = False
    return _HAVE_SCAPY and _is_admin() and has_provider


def _which(cmd: str) -> Optional[str]:
    from shutil import which
    return which(cmd)


# ------------------------- Scapy path -------------------------

def _traceroute_scapy(target: str, proto: str, count: int, max_hops: int, timeout: float, dport: int) -> List[Hop]:
    # Map protocol to Scapy layer
    layer = {"icmp": ICMP, "udp": UDP, "tcp": TCP}[proto]

    hops: List[Hop] = []
    for ttl in range(1, max_hops + 1):
        rtts = []
        last_ip = "*"
        for _ in range(count):
            pkt = IP(dst=target, ttl=ttl)

            if proto == "icmp":
                inner = layer()  # Echo-request
            elif proto == "udp":
                inner = layer(dport=dport)
            else:  # tcp
                # TCP SYN to a high port to elicit Time Exceeded / Unreachable
                inner = layer(dport=dport, flags="S")

            t0 = time.perf_counter()
            try:
                ans = sr1(pkt / inner, verbose=0, timeout=timeout)
            except PermissionError:
                # Bail out to OS fallback
                raise
            t1 = time.perf_counter()

            if ans is not None:
                last_ip = ans.src
                rtts.append(t1 - t0)

        latency = (sum(rtts) / len(rtts)) if rtts else None
        hops.append(Hop(ttl=ttl, ip=last_ip, latency=latency))

        # stop when destination is reached (ip matches target)
        if last_ip not in ("*", "0.0.0.0") and _same_host(last_ip, target):
            break
    return hops


def _same_host(ip_or_host_a: str, ip_or_host_b: str) -> bool:
    # Basic check: either textually equal or resolves to same IP
    if ip_or_host_a == ip_or_host_b:
        return True
    try:
        import socket
        a = socket.gethostbyname(ip_or_host_a)
        b = socket.gethostbyname(ip_or_host_b)
        return a == b
    except Exception:
        return False


# ------------------------- OS fallback path -------------------------

def _os_traceroute_cmd(system: str, target: str, count: int, max_hops: int, timeout: float) -> List[str]:
    """Build the tracert/traceroute argv for `system` (platform.system().lower())."""
    if system == "windows":
        return ["tracert", "-d", "-h", str(max_hops), "-w", str(int(timeout * 1000)), target]
    # On macOS: `traceroute -n -m <max_hops> -q <count> -w <timeout> <target>`
    # On Linux: same flags work for most distros.
    q = max(1, min(5, count))
    return ["traceroute", "-n", "-m", str(max_hops), "-q", str(q), "-w", str(timeout), target]


def _traceroute_os(target: str, count: int, max_hops: int, timeout: float) -> List[Hop]:
    """
    Use system tracert/traceroute and parse output.
    We average the three probes per hop when available.
    """
    system = platform.system().lower()
    cmd = _os_traceroute_cmd(system, target, count, max_hops, timeout)

    if not _which(cmd[0]):
        raise RuntimeError(f"Neither Scapy nor '{cmd[0]}' is available. Install Npcap and run as Admin, or install {cmd[0]}.")

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    out = proc.stdout or proc.stderr

    hops: List[Hop] = []
    if system == "windows":
        # Line format (with -d): "  n  8 ms   9 ms  10 ms  8.8.8.8"
        hop_re = re.compile(r"^\s*(\d+)\s+((?:\d+\s*ms|\*)\s+){1,3}([\d\.*]+)", re.MULTILINE)
        ip_re = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3}|\*)")
        for line in out.splitlines():
            m = re.match(r"^\s*(\d+)\s+(.*)$", line)
            if not m:
                continue
            ttl = int(m.group(1))
            rest = m.group(2)
            # collect ms values
            ms = [float(x) for x in re.findall(r"(\d+)\s*ms", rest)]
            latency = (sum(ms)/len(ms)/1000.0) if ms else None
            ipm = ip_re.search(rest)
            ip = ipm.group(1) if ipm else "*"
            hops.append(Hop(ttl=ttl, ip=ip, latency=latency))
    else:
        # Typical line: " 1  192.168.1.1  1.123 ms  1.045 ms  1.002 ms"
        line_re = re.compile(r"^\s*(\d+)\s+(\S+)\s+(.*)$")
        for line in out.splitlines():
            m = line_re.match(line)
            if not m:
                continue
            ttl = int(m.group(1))
            ip = m.group(2)
            ms = [float(x) for x in re.findall(r"([\d\.]+)\s*ms", m.group(3))]
            latency = (sum(ms)/len(ms)/1000.0) if ms else None
            hops.append(Hop(ttl=ttl, ip=ip, latency=latency))

    return hops


# ------------------------- CLI -------------------------

@click.command()
@click.option("--target", required=True, help="IP or hostname to trace")
@click.option("--proto", type=click.Choice(["icmp", "udp", "tcp"]), default="icmp", show_default=True,
              help="Probe protocol for the Scapy path (OS fallback always uses system default).")
@click.option("--count", default=3, show_default=True, help="Packets per hop")
@click.option("--max-hops", default=30, show_default=True, help="Maximum TTL/hops")
@click.option("--timeout", default=2.0, show_default=True, help="Timeout per probe (seconds)")
@click.option("--dport", default=33434, show_default=True, help="Destination port for UDP/TCP probes")
@click.option("--no-plot", is_flag=True, help="Do not generate a latency plot image")
@click.option("--out", default="nettracer_latency.png", show_default=True, help="Output image filename")
def main(target: str, proto: str, count: int, max_hops: int, timeout: float, dport: int, no_plot: bool, out: str):
    """
    NetTracer: trace hops to a target and (optionally) plot per-hop average latency.
    """
    print(f"Tracing {target} (count={count}, max_hops={max_hops}, timeout={timeout}s)")

    hops: List[Hop]
    used = ""

    # Prefer Scapy if fully ready; otherwise use OS fallback
    if _scapy_ready():
        used = "scapy"
        try:
            hops = _traceroute_scapy(target, proto, count, max_hops, timeout, dport)
        except PermissionError:
            print("[!] Raw-socket permission error. Falling back to system traceroute...", file=sys.stderr)
            used = "os"
            hops = _traceroute_os(target, count, max_hops, timeout)
    else:
        used = "os"
        hops = _traceroute_os(target, count, max_hops, timeout)

    # pretty print
    print(f"\nHops via {used} path:")
    print("TTL  IP/Host           Avg Latency")
    print("---  -----------------  -----------")
    for h in hops:
        lat_txt = f"{h.latency*1000:.1f} ms" if h.latency is not None else "*"
        print(f"{h.ttl:>3}  {h.ip:<17}  {lat_txt:>11}")

    # optional plot
    if not no_plot:
        if not _HAVE_MPL:
            print("[!] matplotlib is not installed; skipping plot.", file=sys.stderr)
        else:
            _plot_hops(hops, out)


def _plot_hops(hops: List[Hop], out: str) -> None:
    xs = [h.ttl for h in hops]
    ys = [h.latency * 1000.0 if h.latency is not None else 0.0 for h in hops]  # ms
    import matplotlib.pyplot as plt  # safe import here
    plt.figure(figsize=(8, 4))
    plt.plot(xs, ys, marker="o")
    plt.xticks(xs)
    plt.xlabel("Hop (TTL)")
    plt.ylabel("Avg Latency (ms)")
    plt.title("NetTracer — Latency per Hop")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    print(f"\nSaved plot to {out}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
