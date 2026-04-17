"""test_improvements.py — regression tests for the 10 improvements."""

import json, subprocess, sys, tempfile, unittest, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import (
    Checker, SignChecker, cfg_only, run, has, clean, count, messages,
    _build_spell_dict, _BUILTIN_DICT,
)
import cstylecheck as _mod

_HERE    = Path(__file__).resolve().parent
_SRC_DIR = _HERE.parent / "src"
_CHECKER = str(_SRC_DIR / "cstylecheck.py")
_YAML    = str(_HERE / "rules.yml")


def _cli(*args, files=None):
    """Run checker once and return (returncode, stdout).

    Previously this function invoked subprocess.run twice, meaning the
    returncode and stdout could come from different process executions.
    Fixed by BUG-001: single invocation, results taken from one object.
    """
    cmd = [sys.executable, _CHECKER, "--config", _YAML, *args]
    if files:
        cmd.extend(files)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout


def _write(td, name, content):
    p = Path(td) / name
    p.write_text(content, encoding="utf-8")
    return str(p)


# ===========================================================================
# 1. Spell-check rstrip bug
# ===========================================================================

class TestSpellCheckRstripFix(unittest.TestCase):

    def _run_spell(self, comment, extra_words=None):
        words = _build_spell_dict([], extra_words or set(), base_dict=_BUILTIN_DICT)
        cfg = cfg_only(spell_check={"enabled": True, "severity": "info", "exempt_values": []})
        return run(f"/* {comment} */\nvoid f(void){{}}\n", cfg, spell_words=words)

    def test_process_not_mangled(self):
        """'process' must not be mangled to 'proce'."""
        flagged = [v.message for v in self._run_spell("This process runs.") if v.rule == "spell_check"]
        self.assertFalse(any("process" in m for m in flagged), f"Incorrectly flagged: {flagged}")

    def test_status_not_mangled(self):
        """'status' must not be mangled to 'statu'."""
        flagged = [v.message for v in self._run_spell("Check status.") if v.rule == "spell_check"]
        self.assertFalse(any("status" in m for m in flagged), f"Incorrectly flagged: {flagged}")

    def test_address_not_mangled(self):
        """'address' ends in 's' and is in the built-in dict — must not be mangled."""
        flagged = [v.message for v in self._run_spell("Read address.") if v.rule == "spell_check"]
        self.assertFalse(any("address" in m for m in flagged), f"Incorrectly flagged: {flagged}")

    def test_possessive_still_stripped(self):
        """'driver's' -> 'driver' after re.sub — known word, must not be flagged."""
        flagged = [v.message for v in self._run_spell("The driver's register.") if v.rule == "spell_check"]
        self.assertFalse(any("driver" in m for m in flagged), f"Incorrectly flagged: {flagged}")

    def test_unknown_word_still_flagged(self):
        viols = self._run_spell("The xyzqwerty value.")
        self.assertTrue(any("xyzqwerty" in v.message for v in viols if v.rule == "spell_check"))

    def test_rstrip_would_mangle_status(self):
        """Confirm rstrip('\\''s') DOES mangle 'status' — documents the old bug."""
        import re
        self.assertNotEqual("status".rstrip("'s"), "status",
                            "rstrip should mangle 'status' (confirms the bug existed)")
        self.assertEqual(re.sub(r"'s$", "", "status"), "status",
                         "re.sub must NOT mangle 'status'")


# ===========================================================================
# 2. _SIGNED_TYPES mutation
# ===========================================================================

class TestSignedTypesMutation(unittest.TestCase):

    def _make_sc(self, plain_char_signed):
        cfg = cfg_only(sign_compatibility={
            "enabled": True, "severity": "error",
            "plain_char_is_signed": plain_char_signed,
        })
        sc = SignChecker(cfg)
        sc.ingest("test.h", "void foo(char c);\n")
        sc.ingest("test.c", "void bar(void){ foo(-1); }\n")
        return sc.check()

    def test_signed_char_no_violation(self):
        """-1 to char param is OK when char is signed."""
        sign_viols = [v for v in self._make_sc(True) if v.rule == "sign_compatibility"]
        self.assertEqual(sign_viols, [])

    def test_unsigned_char_flags_violation(self):
        """With plain_char_is_signed=False, -1 to char param is a violation."""
        sign_viols = [v for v in self._make_sc(False) if v.rule == "sign_compatibility"]
        self.assertGreaterEqual(len(sign_viols), 1)

    def test_char_restored_after_false_call(self):
        """'char' must still be in _SIGNED_TYPES after a False call."""
        self._make_sc(False)
        self.assertIn("char", _mod._SIGNED_TYPES,
                      "'char' was permanently removed from module-level _SIGNED_TYPES")

    def test_second_call_true_unaffected(self):
        """False call followed by True call must give clean result."""
        self._make_sc(False)
        sign_viols = [v for v in self._make_sc(True) if v.rule == "sign_compatibility"]
        self.assertEqual(sign_viols, [], "Module-level set was permanently mutated")

    def test_alternating_calls(self):
        """Alternating True/False must produce correct result every time."""
        for expect_clean in [True, False, True, False, True]:
            viols = [v for v in self._make_sc(expect_clean) if v.rule == "sign_compatibility"]
            if expect_clean:
                self.assertEqual(viols, [], f"Expected clean on True iteration")
            else:
                self.assertGreaterEqual(len(viols), 1, f"Expected violation on False iteration")


# ===========================================================================
# 3. function.min_length
# ===========================================================================

def _fn_cfg(min_length=4, max_length=60):
    return cfg_only(
        file_prefix={"enabled": True, "severity": "error",
                     "separator": "_", "case": "lower",
                     "exempt_main": False, "exempt_patterns": []},
        functions={
            "enabled": True, "severity": "error",
            "style": "object_verb", "max_length": max_length,
            "min_length": min_length,
            "object_exclusions": [], "allowed_abbreviations": [],
            "isr_suffix": {"enabled": False},
            "static_prefix": {"enabled": False},
        },
    )


class TestFunctionMinLength(unittest.TestCase):

    def test_name_above_min_no_violation(self):
        viols = [v for v in run("void mod_Init(void){}", _fn_cfg(min_length=4), filepath="mod.c")
                 if v.rule == "function.min_length"]
        self.assertEqual(viols, [])

    def test_name_below_min_flagged(self):
        """mod_A = 5 chars, min=6 → must be flagged."""
        self.assertTrue(has("void mod_A(void){}", _fn_cfg(min_length=6),
                            "function.min_length", filepath="mod.c"))

    def test_message_includes_name_and_limit(self):
        viols = [v for v in run("void mod_A(void){}", _fn_cfg(min_length=6), filepath="mod.c")
                 if v.rule == "function.min_length"]
        self.assertTrue(viols)
        self.assertIn("mod_A", viols[0].message)
        self.assertIn("6", viols[0].message)

    def test_no_min_length_key_no_violation(self):
        cfg = cfg_only(file_prefix={"enabled": False},
                       functions={"enabled": True, "severity": "error",
                                  "style": "object_verb", "max_length": 60,
                                  "object_exclusions": [], "allowed_abbreviations": [],
                                  "isr_suffix": {"enabled": False},
                                  "static_prefix": {"enabled": False}})
        viols = [v for v in run("void mod_A(void){}", cfg) if v.rule == "function.min_length"]
        self.assertEqual(viols, [])

    def test_isr_exempt_from_min_length(self):
        cfg = cfg_only(file_prefix={"enabled": False},
                       functions={"enabled": True, "severity": "error",
                                  "style": "object_verb", "max_length": 60,
                                  "min_length": 20,
                                  "object_exclusions": [], "allowed_abbreviations": [],
                                  "isr_suffix": {"enabled": True, "suffix": "_IRQHandler"},
                                  "static_prefix": {"enabled": False}})
        viols = [v for v in run("void TIM2_IRQHandler(void){}", cfg)
                 if v.rule == "function.min_length"]
        self.assertEqual(viols, [], "ISR must be exempt from min_length")


# ===========================================================================
# 4. constant.min_length / macro.min_length
# ===========================================================================

def _const_cfg(min_length=2):
    return cfg_only(
        file_prefix={"enabled": True, "severity": "error",
                     "separator": "_", "case": "lower",
                     "exempt_main": False, "exempt_patterns": []},
        constants={"enabled": True, "severity": "error",
                   "case": "upper_snake", "max_length": 60,
                   "min_length": min_length, "exempt_patterns": []},
    )


def _macro_cfg(min_length=2):
    return cfg_only(
        file_prefix={"enabled": True, "severity": "error",
                     "separator": "_", "case": "lower",
                     "exempt_main": False, "exempt_patterns": []},
        macros={"enabled": True, "severity": "error",
                "case": "upper_snake", "max_length": 60,
                "min_length": min_length, "exempt_patterns": []},
    )


class TestConstantMinLength(unittest.TestCase):

    def test_above_min_passes(self):
        viols = [v for v in run("#define MOD_AB 1U\n", _const_cfg(min_length=2), filepath="mod.c")
                 if v.rule == "constant.min_length"]
        self.assertEqual(viols, [])

    def test_below_min_flagged(self):
        self.assertTrue(has("#define MOD_A 1U\n", _const_cfg(min_length=6),
                            "constant.min_length", filepath="mod.c"))

    def test_message_content(self):
        viols = [v for v in run("#define MOD_A 1U\n", _const_cfg(min_length=6), filepath="mod.c")
                 if v.rule == "constant.min_length"]
        self.assertTrue(viols)
        self.assertIn("MOD_A", viols[0].message)
        self.assertIn("6",     viols[0].message)


class TestMacroMinLength(unittest.TestCase):

    def test_below_min_flagged(self):
        self.assertTrue(has("#define MOD_A(x) (x)\n", _macro_cfg(min_length=6),
                            "macro.min_length", filepath="mod.c"))

    def test_above_min_passes(self):
        viols = [v for v in run("#define MOD_LONGER(x) (x)\n", _macro_cfg(min_length=4), filepath="mod.c")
                 if v.rule == "macro.min_length"]
        self.assertEqual(viols, [])

    def test_rule_id(self):
        viols = [v for v in run("#define MOD_A(x) (x)\n", _macro_cfg(min_length=6), filepath="mod.c")
                 if v.rule == "macro.min_length"]
        self.assertTrue(viols)


# ===========================================================================
# 5. function.static_prefix
# ===========================================================================

def _sp_cfg(enabled=True, prefix="prv_", severity="warning"):
    return cfg_only(
        file_prefix={"enabled": False},
        functions={"enabled": True, "severity": "error",
                   "style": "object_verb", "max_length": 60,
                   "object_exclusions": [], "allowed_abbreviations": [],
                   "isr_suffix": {"enabled": False},
                   "static_prefix": {"enabled": enabled, "prefix": prefix, "severity": severity}},
    )


class TestFunctionStaticPrefix(unittest.TestCase):

    def test_static_without_prefix_flagged(self):
        self.assertTrue(has("static void uart_Init(void){}", _sp_cfg(),
                            "function.static_prefix"))

    def test_static_with_prefix_passes(self):
        viols = [v for v in run("static void prv_uart_Init(void){}", _sp_cfg())
                 if v.rule == "function.static_prefix"]
        self.assertEqual(viols, [])

    def test_non_static_not_flagged(self):
        viols = [v for v in run("void uart_Init(void){}", _sp_cfg())
                 if v.rule == "function.static_prefix"]
        self.assertEqual(viols, [])

    def test_message_content(self):
        viols = [v for v in run("static void uart_Init(void){}", _sp_cfg())
                 if v.rule == "function.static_prefix"]
        self.assertTrue(viols)
        self.assertIn("prv_",      viols[0].message)
        self.assertIn("uart_Init", viols[0].message)

    def test_custom_prefix_respected(self):
        viols = [v for v in run("static void local_uart_Init(void){}", _sp_cfg(prefix="local_"))
                 if v.rule == "function.static_prefix"]
        self.assertEqual(viols, [])

    def test_disabled_no_violations(self):
        viols = [v for v in run("static void uart_Init(void){}", _sp_cfg(enabled=False))
                 if v.rule == "function.static_prefix"]
        self.assertEqual(viols, [])

    def test_severity_respected(self):
        viols = [v for v in run("static void uart_Init(void){}", _sp_cfg(severity="error"))
                 if v.rule == "function.static_prefix"]
        self.assertTrue(viols)
        self.assertEqual(viols[0].severity, "error")


# ===========================================================================
# 6. RE_TYPEDEF_SIMPLE multi-token base types
# ===========================================================================

def _td_cfg():
    return cfg_only(typedefs={"enabled": True, "severity": "warning",
                               "case": "upper_snake",
                               "suffix": {"enabled": True, "suffix": "_T"}})


class TestTypedefSimpleMultiToken(unittest.TestCase):

    def test_single_token_wrong_case_still_flagged(self):
        viols = [v for v in run("typedef uint8_t my_type_t;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertTrue(viols)

    def test_unsigned_int_correct(self):
        viols = [v for v in run("typedef unsigned int UINT_T;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertEqual(viols, [], "typedef unsigned int UINT_T should pass")

    def test_unsigned_int_wrong_case_flagged(self):
        viols = [v for v in run("typedef unsigned int uint_t;\n", _td_cfg())
                 if v.rule == "typedef.case"]
        self.assertTrue(viols)

    def test_unsigned_short_correct(self):
        viols = [v for v in run("typedef unsigned short UINT16_T;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertEqual(viols, [])

    def test_signed_long_correct(self):
        viols = [v for v in run("typedef signed long INT32_T;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertEqual(viols, [])

    def test_unsigned_long_long_correct(self):
        viols = [v for v in run("typedef unsigned long long UINT64_T;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertEqual(viols, [])

    def test_missing_suffix_flagged(self):
        viols = [v for v in run("typedef unsigned int UINT;\n", _td_cfg())
                 if v.rule == "typedef.suffix"]
        self.assertTrue(viols)

    def test_struct_alias_still_works(self):
        viols = [v for v in run("typedef struct my_s MY_S_T;\n", _td_cfg())
                 if v.rule in ("typedef.case", "typedef.suffix")]
        self.assertEqual(viols, [])


# ===========================================================================
# 7. Source cache
# ===========================================================================

class TestSourceCache(unittest.TestCase):

    def test_sign_violations_still_detected(self):
        """sign_compatibility still works when SignChecker reuses cached source."""
        with tempfile.TemporaryDirectory() as td:
            _write(td, "foo.h", "void foo(unsigned int val);\n")
            _write(td, "foo.c",
                   '#include "foo.h"\n'
                   "void foo(unsigned int val){ (void)val; }\n"
                   "void caller(void){ foo(-1); }\n")
            rc, out = _cli("--include", td + "/**")
        self.assertIn("sign_compatibility", out)

    def test_missing_file_no_crash(self):
        with tempfile.TemporaryDirectory() as td:
            good = _write(td, "main.c", "int main(void){ return 0; }\n")
            rc, out = _cli(files=[good, td + "/nonexistent.c"])
        self.assertNotIn("Traceback", out)


# ===========================================================================
# 8. JSON output
# ===========================================================================

class TestJsonOutput(unittest.TestCase):

    def _jr(self, source, filename="mod.c"):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, filename, source)
            rc, out = _cli("--output-format", "json", files=[src])
        return rc, out

    def test_valid_json(self):
        _, out = self._jr("void BadFunc(void){}\n")
        json.loads(out)  # raises on invalid

    def test_summary_keys(self):
        _, out = self._jr("void mod_Init(void){}\n")
        s = json.loads(out)["summary"]
        for k in ("files_checked", "errors", "warnings", "total"):
            self.assertIn(k, s)

    def test_violations_list(self):
        _, out = self._jr("void mod_Init(void){}\n")
        self.assertIsInstance(json.loads(out)["violations"], list)

    def test_violation_fields(self):
        _, out = self._jr("void BadFunc(void){}\n")
        data = json.loads(out)
        self.assertTrue(data["violations"])
        v = data["violations"][0]
        for f in ("file", "line", "col", "severity", "rule", "message"):
            self.assertIn(f, v)

    def test_files_checked_count(self):
        _, out = self._jr("void mod_Init(void){}\n")
        self.assertEqual(json.loads(out)["summary"]["files_checked"], 1)

    def test_exit_zero_on_clean(self):
        rc, _ = self._jr("int main(void){ return 0; }\n", filename="main.c")
        self.assertEqual(rc, 0)

    def test_exit_one_on_violations(self):
        rc, _ = self._jr("void BadFunc(void){}\n")
        self.assertEqual(rc, 1)


# ===========================================================================
# 9. SARIF output
# ===========================================================================

class TestSarifOutput(unittest.TestCase):

    def _sr(self, source, filename="mod.c"):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, filename, source)
            rc, out = _cli("--output-format", "sarif", files=[src])
        return rc, out

    def test_valid_json(self):
        _, out = self._sr("void BadFunc(void){}\n")
        json.loads(out)

    def test_version_2_1_0(self):
        _, out = self._sr("void mod_Init(void){}\n")
        self.assertEqual(json.loads(out)["version"], "2.1.0")

    def test_one_run(self):
        _, out = self._sr("void mod_Init(void){}\n")
        self.assertEqual(len(json.loads(out)["runs"]), 1)

    def test_tool_driver_name(self):
        _, out = self._sr("void mod_Init(void){}\n")
        self.assertEqual(json.loads(out)["runs"][0]["tool"]["driver"]["name"], "CStyleCheck")

    def test_result_fields(self):
        _, out = self._sr("void BadFunc(void){}\n")
        results = json.loads(out)["runs"][0]["results"]
        self.assertTrue(results)
        for f in ("ruleId", "level", "message", "locations"):
            self.assertIn(f, results[0])

    def test_physical_location(self):
        _, out = self._sr("void BadFunc(void){}\n")
        results = json.loads(out)["runs"][0]["results"]
        self.assertTrue(results)
        loc = results[0]["locations"][0]["physicalLocation"]
        self.assertIn("artifactLocation", loc)
        self.assertIn("startLine", loc["region"])

    def test_schema_field(self):
        _, out = self._sr("void mod_Init(void){}\n")
        self.assertIn("sarif", json.loads(out).get("$schema", ""))

    def test_rules_match_results(self):
        _, out = self._sr("void BadFunc(void){}\n")
        data    = json.loads(out)
        results = data["runs"][0]["results"]
        rule_ids = {r["id"] for r in data["runs"][0]["tool"]["driver"]["rules"]}
        for res in results:
            self.assertIn(res["ruleId"], rule_ids)


# ===========================================================================
# 10. Baseline suppression
# ===========================================================================

_DIRTY_SRC = "void BadFunc(void){}\n"   # function.prefix error in mod.c


class TestBaselineSuppression(unittest.TestCase):

    def test_write_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            rc, _ = _cli("--write-baseline", bl, files=[src])
        self.assertEqual(rc, 0)

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            self.assertTrue(Path(bl).exists())

    def test_write_valid_json(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            data = json.loads(Path(bl).read_text(encoding="utf-8"))
        self.assertIn("violations", data)

    def test_write_records_violations(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            data = json.loads(Path(bl).read_text(encoding="utf-8"))
        self.assertGreater(len(data["violations"]), 0)

    def test_write_message_in_output(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _, out = _cli("--write-baseline", bl, files=[src])
        self.assertIn("baseline", out.lower())

    def test_baseline_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            rc, _ = _cli("--baseline-file", bl, files=[src])
        self.assertEqual(rc, 0)

    def test_baseline_suppressed_message(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            _, out = _cli("--baseline-file", bl, files=[src])
        self.assertIn("suppressed", out.lower(), f"Got: {out!r}")

    def test_new_violation_not_suppressed(self):
        with tempfile.TemporaryDirectory() as td:
            src_v1 = _write(td, "mod.c", _DIRTY_SRC)
            bl     = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src_v1])
            src_v2 = _write(td, "mod.c", _DIRTY_SRC + "void AnotherBad(void){}\n")
            rc, _  = _cli("--baseline-file", bl, files=[src_v2])
        self.assertEqual(rc, 1)

    def test_json_output_respects_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            src = _write(td, "mod.c", _DIRTY_SRC)
            bl  = str(Path(td) / "baseline.json")
            _cli("--write-baseline", bl, files=[src])
            _, out = _cli("--output-format", "json", "--baseline-file", bl, files=[src])
        data = json.loads(out)
        self.assertEqual(data["summary"]["total"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
