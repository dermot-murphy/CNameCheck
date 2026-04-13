"""test_sign_compatibility.py — tests for cross-file sign_compatibility rule.

SignChecker is a two-pass system: ingest() all files first, then check().
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import SignChecker

def _sign_cfg(enabled=True):
    return {"sign_compatibility": {"enabled": enabled, "severity": "error",
                                   "plain_char_is_signed": True}}

RULE = "sign_compatibility"

class TestSignCompatibility(unittest.TestCase):
    def _check(self, files, enabled=True):
        sc = SignChecker(_sign_cfg(enabled))
        for path, src in files.items():
            sc.ingest(path, src)
        return sc.check()

    def test_unsigned_to_signed_param_flagged(self):
        hdr = ("typedef signed char int8_t;\n"
               "void mod_Write(int8_t p_val);\n")
        src = "void mod_DoWork(void){ mod_Write(100U); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        self.assertTrue(any(v.rule == RULE for v in viols))

    def test_signed_to_unsigned_param_flagged(self):
        hdr = ("typedef unsigned char uint8_t;\n"
               "void mod_Read(uint8_t p_ch);\n")
        src = "void mod_DoWork(void){ mod_Read(-1); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        self.assertTrue(any(v.rule == RULE for v in viols))

    def test_correct_types_pass(self):
        hdr = ("typedef unsigned char uint8_t;\n"
               "void mod_Send(uint8_t p_ch);\n")
        src = "void mod_DoWork(void){ mod_Send(42U); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        self.assertFalse(any(v.rule == RULE for v in viols))

    def test_neutral_literal_not_flagged(self):
        """Plain positive integer (no U suffix) is neutral — not flagged."""
        hdr = ("typedef signed char int8_t;\n"
               "void mod_Write(int8_t p_val);\n")
        src = "void mod_DoWork(void){ mod_Write(42); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        self.assertFalse(any(v.rule == RULE for v in viols))

    def test_typedef_chain_resolved(self):
        """Chains like typedef signed char int8_t → correctly classified signed."""
        hdr = ("typedef signed char int8_t;\n"
               "typedef int8_t MY_BYTE;\n"
               "void mod_Set(MY_BYTE p_val);\n")
        src = "void mod_DoWork(void){ mod_Set(200U); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        self.assertTrue(any(v.rule == RULE for v in viols))

    def test_disabled_produces_no_violations(self):
        hdr = ("typedef signed char int8_t;\n"
               "void mod_Write(int8_t p_val);\n")
        src = "void mod_DoWork(void){ mod_Write(100U); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src}, enabled=False)
        self.assertFalse(any(v.rule == RULE for v in viols))

    def test_violation_names_function_and_argument(self):
        hdr = ("typedef unsigned char uint8_t;\n"
               "void mod_Send(uint8_t p_ch);\n")
        src = "void mod_DoWork(void){ mod_Send(-1); }\n"
        viols = self._check({"mod.h": hdr, "mod.c": src})
        sign_viols = [v for v in viols if v.rule == RULE]
        self.assertTrue(sign_viols)
        self.assertIn("mod_Send", sign_viols[0].message)

if __name__ == "__main__":
    unittest.main(verbosity=2)
