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
if __name__ == "__main__":
    main()
