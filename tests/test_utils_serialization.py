"""Unit tests for python_switchos.utils reverse conversion functions (serialization)."""

from typing import Literal

import pytest

from python_switchos.utils import (
    bool_list_to_hex,
    int_to_hex,
    str_to_hex,
    mac_to_hex,
    ip_to_hex,
    option_to_hex,
    # Import forward converters for round-trip tests
    hex_to_bool_list,
    hex_to_str,
    hex_to_mac,
    hex_to_ip,
    hex_to_option,
)


# --- bool_list_to_hex ---

class TestBoolListToHex:
    def test_all_true(self):
        """10 True values produce 0x3ff."""
        result = bool_list_to_hex([True] * 10)
        assert result == "0x03ff"

    def test_all_false(self):
        """All False produces 0x00."""
        result = bool_list_to_hex([False] * 10)
        assert result == "0x00"

    def test_empty_list(self):
        """Empty list produces 0x00."""
        result = bool_list_to_hex([])
        assert result == "0x00"

    def test_basic_conversion(self):
        """[F, T, F, T] = binary 1010 = 0xa."""
        result = bool_list_to_hex([False, True, False, True])
        assert result == "0x0a"

    def test_single_true_first(self):
        """[True, False, ...] = bit 0 set = 0x01."""
        result = bool_list_to_hex([True] + [False] * 7)
        assert result == "0x01"

    def test_single_true_last_of_10(self):
        """[False]*9 + [True] = bit 9 set = 0x200."""
        result = bool_list_to_hex([False] * 9 + [True])
        assert result == "0x0200"

    def test_24_ports_all_enabled(self):
        """24 True values produce 0xffffff."""
        result = bool_list_to_hex([True] * 24)
        assert result == "0xffffff"

    def test_round_trip_10_ports(self):
        """Round-trip: hex_to_bool_list(bool_list_to_hex(values)) == values."""
        original = [True, False, True, True, False, True, False, False, True, True]
        wire = bool_list_to_hex(original)
        # Parse hex string back to int
        back = hex_to_bool_list(int(wire, 16), len(original))
        assert back == original

    def test_round_trip_24_ports(self):
        """Round-trip with 24 ports."""
        original = [i % 2 == 0 for i in range(24)]  # Alternating
        wire = bool_list_to_hex(original)
        back = hex_to_bool_list(int(wire, 16), len(original))
        assert back == original


# --- int_to_hex ---

class TestIntToHex:
    def test_zero(self):
        """Zero produces 0x00."""
        assert int_to_hex(0) == "0x00"

    def test_small_value(self):
        """15 produces 0x0f (even-length padding)."""
        assert int_to_hex(15) == "0x0f"

    def test_byte_value(self):
        """255 produces 0xff."""
        assert int_to_hex(255) == "0xff"

    def test_two_byte_value(self):
        """4095 produces 0x0fff."""
        assert int_to_hex(4095) == "0x0fff"

    def test_large_value(self):
        """0x7ffff produces 0x07ffff (even-length)."""
        assert int_to_hex(0x7FFFF) == "0x07ffff"

    def test_exact_even_hex(self):
        """0x1234 produces 0x1234 (already even length)."""
        assert int_to_hex(0x1234) == "0x1234"

    def test_with_scale_multiply(self):
        """12.5 with scale=10 produces 125 = 0x7d."""
        assert int_to_hex(12.5, scale=10) == "0x7d"

    def test_with_scale_zero(self):
        """0.0 with scale=10 produces 0x00."""
        assert int_to_hex(0.0, scale=10) == "0x00"

    def test_with_scale_100(self):
        """3.14 with scale=100 produces 314 = 0x013a."""
        assert int_to_hex(3.14, scale=100) == "0x013a"

    def test_round_trip_no_scale(self):
        """Round-trip without scale."""
        original = 12345
        wire = int_to_hex(original)
        back = int(wire, 16)
        assert back == original

    def test_round_trip_with_scale(self):
        """Round-trip with scale (loses precision to int)."""
        original = 12.5
        scale = 10
        wire = int_to_hex(original, scale=scale)
        back = int(wire, 16) / scale
        assert back == original


# --- str_to_hex ---

class TestStrToHex:
    def test_basic_string(self):
        """'Port1' becomes '506f727431' (single-quoted hex)."""
        assert str_to_hex("Port1") == "'506f727431'"

    def test_empty_string(self):
        """Empty string produces ''."""
        assert str_to_hex("") == "''"

    def test_hello(self):
        """'Hello' becomes '48656c6c6f'."""
        assert str_to_hex("Hello") == "'48656c6c6f'"

    def test_with_space(self):
        """'Test ' (with trailing space) includes 20 for space."""
        assert str_to_hex("Test ") == "'5465737420'"

    def test_unicode_utf8(self):
        """Unicode characters encoded as UTF-8 bytes."""
        # Euro sign is E2 82 AC in UTF-8
        result = str_to_hex("\u20ac")
        assert result == "'e282ac'"

    def test_round_trip(self):
        """Round-trip: hex_to_str(str_to_hex(value).strip("'")) == value."""
        original = "Port1"
        wire = str_to_hex(original)
        # Remove quotes and decode
        hex_content = wire.strip("'")
        back = hex_to_str(hex_content)
        assert back == original

    def test_round_trip_empty(self):
        """Round-trip empty string."""
        original = ""
        wire = str_to_hex(original)
        hex_content = wire.strip("'")
        # hex_to_str on empty returns empty
        back = hex_content if hex_content == "" else hex_to_str(hex_content)
        assert back == original


# --- mac_to_hex ---

class TestMacToHex:
    def test_basic_mac(self):
        """AA:BB:CC:DD:EE:FF becomes 'aabbccddeeff'."""
        assert mac_to_hex("AA:BB:CC:DD:EE:FF") == "'aabbccddeeff'"

    def test_lowercase_input(self):
        """Lowercase MAC also produces lowercase hex."""
        assert mac_to_hex("aa:bb:cc:dd:ee:ff") == "'aabbccddeeff'"

    def test_empty_string(self):
        """Empty string produces ''."""
        assert mac_to_hex("") == "''"

    def test_zeros(self):
        """All-zero MAC."""
        assert mac_to_hex("00:00:00:00:00:00") == "'000000000000'"

    def test_round_trip(self):
        """Round-trip: hex_to_mac(mac_to_hex(value).strip("'")) == value."""
        original = "AA:BB:CC:DD:EE:FF"
        wire = mac_to_hex(original)
        hex_content = wire.strip("'")
        back = hex_to_mac(hex_content)
        assert back == original


# --- ip_to_hex ---

class TestIpToHex:
    def test_common_ip(self):
        """192.168.88.1 -> 0x0158a8c0 (little-endian)."""
        assert ip_to_hex("192.168.88.1") == "0x0158a8c0"

    def test_private_ip(self):
        """192.168.1.1 -> 0x0101a8c0."""
        assert ip_to_hex("192.168.1.1") == "0x0101a8c0"

    def test_localhost(self):
        """127.0.0.1 -> 0x0100007f."""
        assert ip_to_hex("127.0.0.1") == "0x0100007f"

    def test_empty_string(self):
        """Empty string produces 0x00."""
        assert ip_to_hex("") == "0x00"

    def test_zeros(self):
        """0.0.0.0 produces 0x00."""
        assert ip_to_hex("0.0.0.0") == "0x00"

    def test_round_trip(self):
        """Round-trip: hex_to_ip(int(ip_to_hex(value), 16)) == value."""
        original = "192.168.88.1"
        wire = ip_to_hex(original)
        back = hex_to_ip(int(wire, 16))
        assert back == original

    def test_round_trip_localhost(self):
        """Round-trip localhost."""
        original = "127.0.0.1"
        wire = ip_to_hex(original)
        back = hex_to_ip(int(wire, 16))
        assert back == original


# --- option_to_hex ---

class TestOptionToHex:
    # Define test option types
    Speed = Literal["10M", "100M", "1G", "10G"]
    VlanMode = Literal["disabled", "optional", "enabled", "strict"]

    def test_first_option(self):
        """First option (index 0) produces 0x00."""
        assert option_to_hex("10M", self.Speed) == "0x00"

    def test_middle_option(self):
        """1G is index 2 -> 0x02."""
        assert option_to_hex("1G", self.Speed) == "0x02"

    def test_last_option(self):
        """10G is index 3 -> 0x03."""
        assert option_to_hex("10G", self.Speed) == "0x03"

    def test_vlan_disabled(self):
        """disabled is index 0 -> 0x00."""
        assert option_to_hex("disabled", self.VlanMode) == "0x00"

    def test_vlan_strict(self):
        """strict is index 3 -> 0x03."""
        assert option_to_hex("strict", self.VlanMode) == "0x03"

    def test_invalid_option(self):
        """Invalid option returns 0x00."""
        assert option_to_hex("invalid", self.Speed) == "0x00"

    def test_round_trip(self):
        """Round-trip: hex_to_option(int(option_to_hex(value, type), 16), type) == value."""
        original = "1G"
        wire = option_to_hex(original, self.Speed)
        back = hex_to_option(int(wire, 16), self.Speed)
        assert back == original

    def test_two_digit_hex(self):
        """Index values always have two hex digits (0x00 not 0x0)."""
        # First option
        result = option_to_hex("10M", self.Speed)
        assert result == "0x00"
        # Third option
        result = option_to_hex("1G", self.Speed)
        assert result == "0x02"
