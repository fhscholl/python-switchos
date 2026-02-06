"""Tests for writeDataclass serialization."""

import pytest
from python_switchos.endpoint import writeDataclass
from python_switchos.endpoints.snmp import SnmpEndpoint
from python_switchos.endpoints.link import LinkEndpoint
from python_switchos.endpoints.sfp import SfpEndpoint


class TestWriteDataclass:
    """Tests for writeDataclass function."""

    def test_snmp_basic_serialization(self):
        """Test simple scalar endpoint serialization."""
        snmp = SnmpEndpoint(
            enabled=True,
            community="public",
            contact_info="admin",
            location="office"
        )
        result = writeDataclass(snmp)

        # Should contain all fields (all writable)
        assert "i01:0x01" in result  # enabled=True
        assert "i02:" in result  # community
        assert "i03:" in result  # contact_info
        assert "i04:" in result  # location

    def test_snmp_disabled(self):
        """Test scalar_bool serialization for False value."""
        snmp = SnmpEndpoint(
            enabled=False,
            community="public",
            contact_info="",
            location=""
        )
        result = writeDataclass(snmp)

        # enabled=False should serialize as 0x00
        assert "i01:0x00" in result

    def test_link_excludes_readonly_fields(self):
        """Test that read-only fields are excluded."""
        link = LinkEndpoint(
            enabled=[True, True, False],
            name=["Port1", "Port2", "Port3"],
            link_state=[True, False, True],  # read-only
            link_paused=[False, False, False],  # read-only
            auto_negotiation=[True, True, True],
            speed=["1G", "1G", "100M"],  # read-only (actual speed)
            man_speed=["1G", "1G", "100M"],  # writable (manual speed)
        )
        result = writeDataclass(link)

        # Should include writable fields
        assert "en:" in result or "i01:" in result  # enabled
        assert "nm:" in result or "i0a:" in result  # name

        # Should exclude read-only fields
        # link_state has names ["lnk", "i06"], speed has ["spdc", "i08"]
        assert "lnk:" not in result  # link_state (SwOS Full name)
        assert "i06:" not in result  # link_state (SwOS Lite name)
        assert "spdc:" not in result  # speed (SwOS Full name)
        assert "i08:" not in result  # speed (SwOS Lite name)

    def test_readonly_endpoint_raises(self):
        """Test that read-only endpoints raise ValueError."""
        sfp = SfpEndpoint(
            vendor=["Vendor1"],
            part_number=["PN1"],
            revision=["R1"],
            serial=["S1"],
            date=["2024"],
            type=["1G"],
            temperature=[25],
            voltage=[3.3],
            tx_bias=[10],
            tx_power=[0.0],
            rx_power=[0.0],
        )
        with pytest.raises(ValueError, match="read-only"):
            writeDataclass(sfp)

    def test_bool_list_serialization(self):
        """Test boolean list to bitmask conversion."""
        link = LinkEndpoint(
            enabled=[True, True, False, True],
            name=["P1", "P2", "P3", "P4"],
        )
        result = writeDataclass(link)
        # [T,T,F,T] = binary 1011 = 0x0b
        assert "0x0b" in result

    def test_field_variant_selection(self):
        """Test field name variant selection."""
        snmp = SnmpEndpoint(
            enabled=True,
            community="test",
            contact_info="",
            location=""
        )
        # variant 0 = SwOS Lite names (i01, i02, ...)
        result0 = writeDataclass(snmp, field_variant=0)
        assert "i01:" in result0

        # SNMP only has Lite names in current implementation
        # but the function should handle the index gracefully
        result1 = writeDataclass(snmp, field_variant=1)
        # Still uses i01 since it's the only name available
        assert "i01:" in result1

    def test_link_field_variant_swos_full(self):
        """Test field variant selection with SwOS Full names."""
        link = LinkEndpoint(
            enabled=[True, False],
            name=["Port1", "Port2"],
        )
        # variant 0 = first name in list (SwOS Full: "en", "nm")
        result0 = writeDataclass(link, field_variant=0)
        assert "en:" in result0
        assert "nm:" in result0

        # variant 1 = second name in list (SwOS Lite: "i01", "i0a")
        result1 = writeDataclass(link, field_variant=1)
        assert "i01:" in result1
        assert "i0a:" in result1

    def test_string_list_serialization(self):
        """Test string list serialization produces hex strings."""
        link = LinkEndpoint(
            enabled=[True, True],
            name=["Port1", "Port2"],
        )
        result = writeDataclass(link)
        # "Port1" in hex = 506f727431
        assert "'506f727431'" in result
        # "Port2" in hex = 506f727432
        assert "'506f727432'" in result

    def test_option_list_serialization(self):
        """Test option list serialization produces hex indices."""
        link = LinkEndpoint(
            enabled=[True, True],
            name=["P1", "P2"],
            man_speed=["1G", "100M"],  # 1G=index 2, 100M=index 1
        )
        result = writeDataclass(link)
        # Should contain speed values as hex: 0x02, 0x01
        assert "0x02" in result
        assert "0x01" in result

    def test_empty_string_serialization(self):
        """Test empty strings serialize to empty quoted hex."""
        snmp = SnmpEndpoint(
            enabled=True,
            community="",
            contact_info="",
            location=""
        )
        result = writeDataclass(snmp)
        # Empty strings should be ''
        assert "i02:''" in result

    def test_non_dataclass_raises_typeerror(self):
        """Test that non-dataclass raises TypeError."""
        with pytest.raises(TypeError, match="is not a dataclass"):
            writeDataclass("not a dataclass")

    def test_wire_format_structure(self):
        """Test that wire format has correct structure."""
        snmp = SnmpEndpoint(
            enabled=True,
            community="test",
            contact_info="",
            location=""
        )
        result = writeDataclass(snmp)

        # Should start with { and end with }
        assert result.startswith("{")
        assert result.endswith("}")

        # Should have field:value pairs separated by commas
        assert ":" in result
        assert "," in result

    def test_array_wire_format(self):
        """Test array fields produce correct wire format."""
        link = LinkEndpoint(
            enabled=[True, False, True],
            name=["A", "B", "C"],
        )
        result = writeDataclass(link)

        # Array fields should have [item,item,...] format
        # name field should be like nm:['41','42','43']
        assert "nm:[" in result or "i0a:[" in result
        assert "]" in result
