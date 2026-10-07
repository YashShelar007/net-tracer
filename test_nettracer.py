import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import bench
from nettracer import _os_traceroute_cmd


class OsTracerouteCmdTest(unittest.TestCase):
    def test_darwin_wait_is_whole_seconds_rounded_up_min_1(self):
        # macOS traceroute rejects "-w 2.0" with "bad value for wait time".
        for timeout, wait in [(2.0, "2"), (2.5, "3"), (0.2, "1")]:
            with self.subTest(timeout=timeout):
                cmd = _os_traceroute_cmd("darwin", "8.8.8.8", 3, 30, timeout)
                self.assertEqual(cmd[cmd.index("-w") + 1], wait)


class BenchCmdTemplateTest(unittest.TestCase):
    def test_cmd_template_records_no_local_interpreter_path(self):
        fake_run = {"duration_s": 1.0, "responded_hops": 1, "total_hops_listed": 1}
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "bench.json")
            with mock.patch.object(sys, "argv", ["bench.py", "--runs", "1", "--out", out]), \
                    mock.patch.object(bench, "run_once", return_value=fake_run), \
                    mock.patch("builtins.print"):
                bench.main()
            with open(out) as f:
                self.assertEqual(json.load(f)["cmd_template"][0], "python")


if __name__ == "__main__":
    unittest.main()
