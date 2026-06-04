"""test_init_wizard.py — Tests for --init wizard and --preset (issue #190)."""
import sys
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import run_wizard, run_preset, PRESETS  # noqa: E402

_HERE    = Path(__file__).resolve().parent
_SRC     = _HERE.parent / "src"
_CHECKER = str(_SRC / "cstylecheck.py")


def _cli(*args):
    r = subprocess.run(
        [sys.executable, _CHECKER, *args],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------------------
class TestRunPreset(unittest.TestCase):

    def test_barr_c_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            rc = run_preset("barr-c", output_path=out)
            self.assertEqual(rc, 0)
            content = Path(out).read_text()
            self.assertIn("lower_snake", content)
            self.assertIn("g_prefix", content)

    def test_minimal_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            rc = run_preset("minimal", output_path=out)
            self.assertEqual(rc, 0)
            content = Path(out).read_text()
            self.assertIn("magic_numbers", content)

    def test_misra_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            rc = run_preset("misra", output_path=out)
            self.assertEqual(rc, 0)
            content = Path(out).read_text()
            self.assertIn("unsigned_suffix", content)
            self.assertIn("octal_constant", content)

    def test_unknown_preset_returns_1(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            msgs = []
            rc = run_preset("nonexistent", output_path=out,
                            print_fn=msgs.append)
            self.assertEqual(rc, 1)

    def test_existing_file_not_overwritten_without_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            Path(out).write_text("existing")
            rc = run_preset("minimal", output_path=out)
            self.assertEqual(rc, 1)
            self.assertEqual(Path(out).read_text(), "existing")

    def test_overwrite_flag_replaces_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            Path(out).write_text("old")
            rc = run_preset("minimal", output_path=out, overwrite=True)
            self.assertEqual(rc, 0)
            self.assertNotEqual(Path(out).read_text(), "old")

    def test_all_presets_produce_valid_yaml(self):
        import yaml
        for name in PRESETS:
            with tempfile.TemporaryDirectory() as td:
                out = str(Path(td) / "out.yml")
                run_preset(name, output_path=out)
                data = yaml.safe_load(Path(out).read_text())
                self.assertIsInstance(data, dict, f"preset {name} produced invalid YAML")

    def test_output_contains_header_comment(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            run_preset("minimal", output_path=out)
            content = Path(out).read_text()
            self.assertIn("# CStyleCheck configuration", content)
            self.assertIn("--preset minimal", content)


# ---------------------------------------------------------------------------
class TestRunWizard(unittest.TestCase):

    def _answers(self, *responses):
        """Return a prompt_fn that yields pre-canned responses."""
        it = iter(responses)
        def _prompt(msg):
            try:
                return next(it)
            except StopIteration:
                return ""
        return _prompt

    def test_wizard_writes_file_with_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            # All defaults: just press Enter to every question
            rc = run_wizard(output_path=out,
                            prompt_fn=self._answers(*[""] * 20))
            self.assertEqual(rc, 0)
            self.assertTrue(Path(out).exists())

    def test_wizard_respects_var_case_choice(self):
        import yaml
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            # Answer camelCase for the first question, defaults for rest
            rc = run_wizard(output_path=out,
                            prompt_fn=self._answers("camelCase", *[""] * 20))
            self.assertEqual(rc, 0)
            data = yaml.safe_load(Path(out).read_text())
            self.assertEqual(data["variables"]["case"], "camelCase")

    def test_wizard_aborts_if_file_exists_and_user_says_no(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            Path(out).write_text("original")
            msgs = []
            rc = run_wizard(output_path=out,
                            prompt_fn=self._answers("n", *[""] * 20),
                            print_fn=msgs.append)
            self.assertEqual(rc, 1)
            self.assertEqual(Path(out).read_text(), "original")

    def test_wizard_overwrites_if_user_confirms(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            Path(out).write_text("original")
            rc = run_wizard(output_path=out,
                            prompt_fn=self._answers("y", *[""] * 20))
            self.assertEqual(rc, 0)
            self.assertNotEqual(Path(out).read_text(), "original")

    def test_wizard_overwrite_flag_skips_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            Path(out).write_text("original")
            rc = run_wizard(output_path=out, overwrite=True,
                            prompt_fn=self._answers(*[""] * 20))
            self.assertEqual(rc, 0)
            self.assertNotEqual(Path(out).read_text(), "original")


# ---------------------------------------------------------------------------
class TestCLIInit(unittest.TestCase):

    def test_preset_cli_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "out.yml")
            rc, out_text = _cli("--preset", "minimal",
                                "--init-output", out, "--overwrite")
            self.assertEqual(rc, 0)
            self.assertTrue(Path(out).exists())

    def test_preset_help_lists_presets(self):
        rc, out_text = _cli("--help")
        self.assertEqual(rc, 0)
        self.assertIn("barr-c", out_text)
        self.assertIn("minimal", out_text)
        self.assertIn("misra", out_text)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
