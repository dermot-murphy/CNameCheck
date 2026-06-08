"""test_reserved_header_name.py — tests for misc.reserved_header_name (issue #230)."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, has

RHN_CFG = cfg_only(misc={"reserved_header_name": {
    "enabled": True, "severity": "error", "extra_reserved": [],
}})

RHN_EXTRA = cfg_only(misc={"reserved_header_name": {
    "enabled": True, "severity": "error", "extra_reserved": ["mylib.h"],
}})

RHN_DISABLED = cfg_only(misc={"reserved_header_name": {
    "enabled": False,
}})


def _violations(source, cfg, filepath):
    from harness import Checker
    c = Checker(filepath, source, cfg)
    return c.run_all().violations


class TestReservedHeaderName(unittest.TestCase):

    def test_project_header_passes(self):
        v = _violations("", RHN_CFG, "uart_driver.h")
        names = [vv.rule for vv in v]
        self.assertNotIn("misc.reserved_header_name", names)

    def test_stdio_h_fails(self):
        v = _violations("", RHN_CFG, "stdio.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_string_h_fails(self):
        v = _violations("", RHN_CFG, "string.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_stdlib_h_fails(self):
        v = _violations("", RHN_CFG, "stdlib.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_unistd_h_posix_fails(self):
        v = _violations("", RHN_CFG, "unistd.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_c_file_not_checked(self):
        # Reserved header name check applies to the filename regardless of content
        v = _violations("", RHN_CFG, "string.c")
        names = [vv.rule for vv in v]
        # "string.c" is not a reserved header (only "string.h" is)
        self.assertNotIn("misc.reserved_header_name", names)

    def test_extra_reserved_fails(self):
        v = _violations("", RHN_EXTRA, "mylib.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_rule_disabled_passes(self):
        v = _violations("", RHN_DISABLED, "stdio.h")
        names = [vv.rule for vv in v]
        self.assertNotIn("misc.reserved_header_name", names)

    def test_case_insensitive_filename(self):
        # File named STDIO.H should also be flagged
        v = _violations("", RHN_CFG, "STDIO.H")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)

    def test_path_prefix_ignored(self):
        # Only the basename matters
        v = _violations("", RHN_CFG, "include/stdio.h")
        names = [vv.rule for vv in v]
        self.assertIn("misc.reserved_header_name", names)
