#!/usr/bin/env python3
import click

@click.command()
@click.option("--target", required=True, help="IP or hostname to trace")
@click.option("--proto", type=click.Choice(["icmp","tcp","udp"]), default="icmp")
@click.option("--count", default=3, help="Packets per hop")
@click.option("--max-hops", default=30, help="Max TTL")
def main(target, proto, count, max_hops):
    """
    NetTracer: trace hops and plot latency graph.
    """
    print(f"Tracing {target} via {proto.upper()} (count={count}, max_hops={max_hops})")
    # TODO: perform traceroute & collect data
    data = traceroute(target, proto, count, max_hops)
    for hop in data:
        print(f"{hop['ttl']:2}  {hop['ip']:15}  {hop['latency'] or '-':>6.3f}s")
    # TODO: plotting


from scapy.all import IP, ICMP, TCP, UDP, sr1
import time

def traceroute(target, proto, count, max_hops):
    results = []
    for ttl in range(1, max_hops+1):
        pkt_cls = {"icmp": ICMP, "tcp": TCP, "udp": UDP}[proto]
        pkt = IP(dst=target, ttl=ttl) / pkt_cls()
        latencies = []
        for _ in range(count):
            start = time.time()
            reply = sr1(pkt, verbose=0, timeout=2)
            if not reply:
                latencies.append(None)
            else:
                latencies.append(time.time() - start)
        avg = sum([l for l in latencies if l is not None]) / max(1, sum(1 for l in latencies if l))
        results.append({"ttl": ttl, "ip": reply.src if reply else "*", "latency": avg})
        if reply and reply.src == target:
            break
    return results

if __name__ == "__main__":
    main()
