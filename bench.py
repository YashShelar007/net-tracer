
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, median, pstdev

TABLE_LINE = re.compile(r"^\s*(\d+)\s+(\S+)\s+([0-9.]+)\s*ms\s*$")
STAR_LINE  = re.compile(r"^\s*(\d+)\s+\*\s+\*\s*$")

def parse_table(stdout: str):
    """
    Parse the NetTracer console table.
    Returns: list of dicts: {"ttl": int, "ip": str|None, "latency_ms": float|None}
    """
    lines = stdout.splitlines()
    rows = []
    in_table = False
    for ln in lines:
        if not in_table and ln.strip().startswith("TTL") and "Avg Latency" in ln:
            in_table = True
            continue
        if in_table:
            if not ln.strip():
                break
            m = TABLE_LINE.match(ln)
            if m:
                ttl = int(m.group(1)); ip = m.group(2); lat = float(m.group(3))
                rows.append({"ttl": ttl, "ip": None if ip == "N/A" else ip, "latency_ms": lat})
                continue
            m2 = STAR_LINE.match(ln)
            if m2:
                ttl = int(m2.group(1))
                rows.append({"ttl": ttl, "ip": None, "latency_ms": None})
                continue
            # tolerate separator/header lines
            if set(ln.strip()) <= set("- "):
                continue
            # stop when section changes
            if ln.strip().startswith("Saved plot to"):
                break
    return rows

def run_once(py_exe, script, base_args, no_plot=True):
    cmd = [py_exe, str(script)] + base_args + (["--no-plot"] if no_plot and "--no-plot" not in base_args else [])
    t0 = time.perf_counter()
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    t1 = time.perf_counter()
    stdout = cp.stdout
    rows = parse_table(stdout)
    reached = False
    # Heuristic: if the last row has latency or if target appears in any IP column
    if rows:
        if rows[-1]["latency_ms"] is not None:
            reached = True
        # try to detect target echo in table
    responded = sum(1 for r in rows if r["latency_ms"] is not None)
    return {
        "returncode": cp.returncode,
        "duration_s": t1 - t0,
        "rows": rows,
        "responded_hops": responded,
        "total_hops_listed": len(rows),
        "stdout": stdout,
        "stderr": cp.stderr,
        "cmd": cmd,
    }

def main():
    ap = argparse.ArgumentParser(description="Benchmark NetTracer by running it multiple times and summarizing results.")
    ap.add_argument("--target", default="8.8.8.8", help="Target host/IP to trace (default: 8.8.8.8)")
    ap.add_argument("--runs", type=int, default=10, help="Number of runs (default: 10)")
    ap.add_argument("--proto", choices=["icmp","tcp","udp"], default="icmp")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--max-hops", type=int, default=30, dest="max_hops")
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--nettracer", default="nettracer.py", help="Path to nettracer.py")
    ap.add_argument("--out", default="bench_results.json", help="Where to write JSON results")
    ap.add_argument("--print-sample", action="store_true", help="Print a resume-ready bullet after running")
    args = ap.parse_args()

    script = Path(args.nettracer)
    if not script.exists():
        print(f"[bench] Could not find {script}. Run from repo root or pass --nettracer.", file=sys.stderr)
        sys.exit(2)

    base_args = [
        "--target", args.target,
        "--proto", args.proto,
        "--count", str(args.count),
        "--max-hops", str(args.max_hops),
        "--timeout", str(args.timeout),
    ]

    py_exe = sys.executable
    runs = []
    print(f"[bench] Running {args.runs} traces to {args.target} (proto={args.proto}, count={args.count}, max_hops={args.max_hops}, timeout={args.timeout})")
    for i in range(1, args.runs + 1):
        r = run_once(py_exe, script, base_args, no_plot=True)
        runs.append(r)
        dur = r["duration_s"]
        responded = r["responded_hops"]
        print(f"[bench] Run {i:02d}: {dur:.3f}s, responded hops: {responded}/{r['total_hops_listed']}")

    durations = [r["duration_s"] for r in runs]
    responded_hops = [r["responded_hops"] for r in runs]
    total_hops = [r["total_hops_listed"] for r in runs]

    summary = {
        "target": args.target,
        "proto": args.proto,
        "count": args.count,
        "max_hops": args.max_hops,
        "timeout": args.timeout,
        "runs": len(runs),
        "duration_s": {
            "mean": round(mean(durations), 4),
            "median": round(median(durations), 4),
            "p95": round(sorted(durations)[int(0.95*len(durations))-1], 4) if len(durations) >= 2 else round(durations[0], 4),
            "stdev": round(pstdev(durations), 4) if len(durations) >= 2 else 0.0,
        },
        "responded_hops": {
            "mean": round(mean(responded_hops), 2),
            "median": round(median(responded_hops), 2),
        },
        "samples": [
            {
                "duration_s": round(r["duration_s"], 4),
                "responded_hops": r["responded_hops"],
                "total_hops_listed": r["total_hops_listed"],
            } for r in runs
        ],
        # Literal "python", not sys.executable: an absolute interpreter path leaks the local directory layout.
        "cmd_template": ["python", str(script)] + base_args + ["--no-plot"],
    }

    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"[bench] Wrote {args.out}")

    if args.print_sample:
        m = summary["duration_s"]["mean"]
        hops = summary["responded_hops"]["median"]
        print("\nResume bullet suggestion:")
        print(f"- Benchmarked cross-platform traceroute: mean trace time **{m:.2f}s** over {args.runs} runs to {args.target} with {args.count} probes/hop (median responding hops: {hops}).")

if __name__ == "__main__":
    main()
