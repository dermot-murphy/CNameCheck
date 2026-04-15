"""test_functions.py — tests for function.prefix, function.style, function.max_length."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean, run

FP = {"enabled": True, "severity": "error", "separator": "_",
      "case": "lower", "exempt_main": True, "exempt_patterns": []}

FN_CFG = cfg_only(
    file_prefix=FP,
    functions={"enabled": True, "severity": "error",
               "style": "object_verb", "max_length": 40,
               "allowed_abbreviations": ["FIFO", "CRC", "IRQ"],
               "object_cstylecheck_exclusions": ["Init", "Deinit"],
               "isr_suffix": {"enabled": True, "severity": "warning",
                               "suffix": "_IRQHandler"}},
)

class TestFunctionPrefix(unittest.TestCase):
    def test_correct_prefix_passes(self):
        self.assertTrue(clean("void uart_BufferRead(void){}", FN_CFG,
                               filepath="uart.c"))

    def test_wrong_prefix_fails(self):
        self.assertTrue(has("void other_BufferRead(void){}", FN_CFG,
                            "function.prefix", filepath="uart.c"))

    def test_no_prefix_fails(self):
        self.assertTrue(has("void BufferRead(void){}", FN_CFG,
                            "function.prefix", filepath="uart.c"))

    def test_main_in_main_c_exempt(self):
        """main() is exempt only when the file stem is also 'main'."""
        self.assertFalse(has("int main(void){ return 0; }", FN_CFG,
                              "function.prefix", filepath="main.c"))

    def test_main_in_other_file_flagged(self):
        """A function named 'main' in uart.c still needs the module prefix."""
        self.assertTrue(has("int main(void){ return 0; }", FN_CFG,
                            "function.prefix", filepath="uart.c"))

class TestFunctionStyle(unittest.TestCase):
    def test_object_verb_passes(self):
        self.assertFalse(has("void uart_BufferRead(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

    def test_single_verb_body_passes(self):
        self.assertFalse(has("void uart_Init(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

    def test_multi_segment_pascal_passes(self):
        self.assertFalse(has("void uart_LiveData_Read(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

    def test_lower_snake_body_fails(self):
        self.assertTrue(has("void uart_buffer_read(void){}", FN_CFG,
                            "function.style", filepath="uart.c"))

    def test_object_exclusion_waives_style_check(self):
        self.assertFalse(has("void uart_Init_Channel(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

    def test_abbreviation_allowed_in_body(self):
        self.assertFalse(has("void uart_FIFOFlush(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

    def test_isr_suffix_exempts_from_style(self):
        self.assertFalse(has("void uart_IRQHandler(void){}", FN_CFG,
                              "function.style", filepath="uart.c"))

class TestFunctionMaxLength(unittest.TestCase):
    def test_at_limit_passes(self):
        name = "uart_" + "A" * 35  # exactly 40 chars
        self.assertFalse(has(f"void {name}(void){{}}", FN_CFG,
                              "function.max_length", filepath="uart.c"))

    def test_over_limit_fails(self):
        name = "uart_" + "A" * 36  # 41 chars
        self.assertTrue(has(f"void {name}(void){{}}", FN_CFG,
                            "function.max_length", filepath="uart.c"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
