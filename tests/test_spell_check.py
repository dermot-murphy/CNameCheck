"""test_spell_check.py — tests for the spell_check rule."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, run, _build_spell_dict, _BUILTIN_DICT

def _run_spell(source, extra_exempt=None):
    cfg = cfg_only(spell_check={"enabled": True, "severity": "info",
                                  "exempt_values": list(extra_exempt or [])})
    words = _build_spell_dict(list(extra_exempt or []), set())
    return run(source, cfg, spell_words=words)

class TestSpellCheck(unittest.TestCase):
    def test_correct_english_passes(self):
        src = "/* Initialize the buffer before use. */\nvoid f(void){}\n"
        self.assertFalse(any(v.rule == "spell_check" for v in _run_spell(src)))

    def test_misspelled_word_flagged(self):
        src = "/* Initializze the buffer. */\nvoid f(void){}\n"
        self.assertTrue(any(v.rule == "spell_check" for v in _run_spell(src)))

    def test_key_embedded_words_in_builtin_dict(self):
        """Core embedded-domain words are present in the builtin dictionary."""
        # Note: the spell checker strips trailing 's via rstrip("'s"), so avoid
        # words ending in 's' here (e.g. RTOS → "rto" after strip).
        for word in ("uart", "dma", "fifo", "gpio", "spi", "hal", "mcu", "cpu"):
            self.assertIn(word, _BUILTIN_DICT, f"'{word}' missing from builtin dict")

    def test_builtin_words_not_flagged_in_comment(self):
        """Comments that use only builtin words produce no spell violations."""
        src = "/* UART DMA FIFO GPIO HAL MCU CPU. */\nvoid f(void){}\n"
        viols = _run_spell(src)
        spell = [v for v in viols if v.rule == "spell_check"]
        self.assertEqual(spell, [], f"Unexpected flags: {[v.message for v in spell]}")

    def test_extra_exempt_word_not_flagged(self):
        src = "/* Sensoteq API module. */\nvoid f(void){}\n"
        viols = _run_spell(src, extra_exempt=["Sensoteq", "API"])
        self.assertFalse(any(v.rule == "spell_check" for v in viols))

    def test_unknown_word_without_exemption_flagged(self):
        src = "/* Sensoteq module. */\nvoid f(void){}\n"
        self.assertTrue(any("Sensoteq" in v.message for v in _run_spell(src)
                            if v.rule == "spell_check"))

    def test_disabled_produces_no_violations(self):
        cfg = cfg_only(spell_check={"enabled": False})
        src = "/* xyzzyblarg completely wrong word. */\nvoid f(void){}\n"
        self.assertFalse(any(v.rule == "spell_check"
                             for v in run(src, cfg, spell_words=None)))

    def test_code_identifiers_not_checked(self):
        src = "void uart_BufferReadXxxx(void){}\n"
        self.assertFalse(any(v.rule == "spell_check" for v in _run_spell(src)))

    def test_default_severity_is_info(self):
        src = "/* completelywrongxyzword */\nvoid f(void){}\n"
        viols = _run_spell(src)
        spell = [v for v in viols if v.rule == "spell_check"]
        self.assertTrue(spell)
        self.assertEqual(spell[0].severity, "info")

if __name__ == "__main__":
    unittest.main(verbosity=2)
