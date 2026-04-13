"""test_structs.py — tests for struct.tag_case, struct.tag_suffix,
struct.member_case rules."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import unittest
from harness import cfg_only, has, clean

ST_CFG = cfg_only(
    structs={"enabled": True, "severity": "warning",
             "tag_case": "lower_snake",
             "tag_suffix": {"enabled": True, "suffix": "_s"},
             "member_case": "lower_snake"},
)

class TestStructTag(unittest.TestCase):
    def test_correct_tag_passes(self):
        src = "typedef struct uart_config_s { uint32_t baud_rate; } UART_CONFIG_T;\n"
        self.assertFalse(has(src, ST_CFG, "struct.tag_case"))
        self.assertFalse(has(src, ST_CFG, "struct.tag_suffix"))

    def test_upper_snake_tag_fails_case(self):
        src = "typedef struct UART_CONFIG { uint32_t baud; } UART_CONFIG_T;\n"
        self.assertTrue(has(src, ST_CFG, "struct.tag_case"))

    def test_missing_suffix_fails(self):
        src = "typedef struct uart_config { uint32_t baud; } UART_CONFIG_T;\n"
        self.assertTrue(has(src, ST_CFG, "struct.tag_suffix"))

class TestStructMembers(unittest.TestCase):
    def test_lower_snake_member_passes(self):
        src = "typedef struct uart_s { uint32_t baud_rate; uint8_t channel; } UART_T;\n"
        self.assertFalse(has(src, ST_CFG, "struct.member_case"))

    def test_camelCase_member_fails(self):
        src = "typedef struct uart_s { uint32_t baudRate; } UART_T;\n"
        self.assertTrue(has(src, ST_CFG, "struct.member_case"))

    def test_multiple_members_all_checked(self):
        src = "typedef struct uart_s { uint32_t good_name; uint8_t BadName; } UART_T;\n"
        self.assertTrue(has(src, ST_CFG, "struct.member_case"))

class TestStructDisabled(unittest.TestCase):
    def test_disabled_produces_no_violations(self):
        cfg = cfg_only(structs={"enabled": False})
        src = "typedef struct BadTag { uint32_t BadMember; } X;\n"
        self.assertTrue(clean(src, cfg))

class TestStructMemberAbbreviations(unittest.TestCase):
    """Struct members may contain uppercase abbreviations listed in
    structs.allowed_abbreviations, just like variable names."""

    def _cfg(self, abbrevs):
        return cfg_only(structs={
            "enabled": True, "severity": "warning",
            "tag_case": "lower_snake",
            "tag_suffix": {"enabled": True, "suffix": "_s"},
            "member_case": "lower_snake",
            "allowed_abbreviations": abbrevs,
        })

    def test_listed_abbrev_passes(self):
        src = "typedef struct uart_s { uint32_t FIFO_count; } UART_T;\n"
        self.assertFalse(has(src, self._cfg(["FIFO"]), "struct.member_case"))

    def test_unlisted_abbrev_fails(self):
        src = "typedef struct uart_s { uint32_t FIFO_count; } UART_T;\n"
        self.assertTrue(has(src, self._cfg([]), "struct.member_case"))

    def test_multiple_abbrevs_all_pass(self):
        src = ("typedef struct data_s {\n"
               "    uint32_t CRC_value;\n"
               "    uint16_t ADC_raw;\n"
               "    uint8_t  FIFO_len;\n"
               "} DATA_T;\n")
        cfg = self._cfg(["CRC", "ADC", "FIFO"])
        self.assertFalse(has(src, cfg, "struct.member_case"))

    def test_only_listed_abbrev_allowed(self):
        """CRC listed but SPI not — SPI_bus still flags."""
        src = "typedef struct bus_s { uint32_t SPI_clk; } BUS_T;\n"
        self.assertTrue(has(src, self._cfg(["CRC"]), "struct.member_case"))

    def test_plain_lower_snake_always_passes(self):
        src = "typedef struct uart_s { uint32_t baud_rate; uint8_t channel; } UART_T;\n"
        self.assertFalse(has(src, self._cfg([]), "struct.member_case"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
