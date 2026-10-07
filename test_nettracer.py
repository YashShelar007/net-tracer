import unittest

from nettracer import _os_traceroute_cmd


class OsTracerouteCmdTest(unittest.TestCase):
    def test_darwin_wait_is_whole_seconds_rounded_up_min_1(self):
        # macOS traceroute rejects "-w 2.0" with "bad value for wait time".
        for timeout, wait in [(2.0, "2"), (2.5, "3"), (0.2, "1")]:
            with self.subTest(timeout=timeout):
                cmd = _os_traceroute_cmd("darwin", "8.8.8.8", 3, 30, timeout)
                self.assertEqual(cmd[cmd.index("-w") + 1], wait)


if __name__ == "__main__":
    unittest.main()
