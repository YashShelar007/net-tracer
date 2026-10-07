# Contributing

Before opening a PR:

1. `pip install -r requirements.txt`
2. `python -m unittest` (covers only the OS traceroute command line and the command `bench.py` records).
3. Run `python nettracer.py --target 8.8.8.8 --no-plot` and check the table is not empty.
4. If you touched `bench.py`, run it with `--runs 2`.

Open a PR against `main` with what changed and which OS you tested on. Traceroute behavior differs between Windows, macOS and Linux.
