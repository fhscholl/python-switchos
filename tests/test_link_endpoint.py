"""Tests for LinkEndpoint parsing against CSS610 fixture data."""

import re
import pytest
from python_switchos.endpoint import readDataclass
from python_switchos.endpoints.link import LinkEndpoint, Speed


class TestLinkEndpointParsing:
    """Test that readDataclass correctly parses raw link.b response."""

    def test_parses_to_link_endpoint(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result, LinkEndpoint)

    def test_enabled_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.enabled, list)
        assert len(result.enabled) == 10
        assert all(isinstance(v, bool) for v in result.enabled)

    def test_enabled_all_true(self, link_response):
        """Fixture has i01:0x03ff -- all 10 ports enabled."""
        result = readDataclass(LinkEndpoint, link_response)
        assert all(v is True for v in result.enabled)

    def test_name_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.name, list)
        assert len(result.name) == 10
        assert all(isinstance(v, str) for v in result.name)

    def test_name_values(self, link_response):
        """Fixture has Port1..Port8, SFP1+, SFP2+ (with trailing null bytes)."""
        result = readDataclass(LinkEndpoint, link_response)
        # hex_to_str doesn't strip null bytes, so check with startswith
        assert result.name[0].startswith("Port1")
        assert result.name[7].startswith("Port8")
        assert result.name[8].startswith("SFP1+")
        assert result.name[9].startswith("SFP2+")

    def test_auto_negotiation_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.auto_negotiation, list)
        assert len(result.auto_negotiation) == 10
        assert all(isinstance(v, bool) for v in result.auto_negotiation)

    def test_auto_negotiation_all_true(self, link_response):
        """Fixture has i02:0x03ff -- all 10 ports auto-negotiation enabled."""
        result = readDataclass(LinkEndpoint, link_response)
        assert all(v is True for v in result.auto_negotiation)

    def test_speed_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.speed, list)
        assert len(result.speed) == 10

    def test_speed_values(self, link_response):
        """Fixture: i08:[0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x02,0x00]
        Maps to: 100M, 100M, 100M, 100M, 10M, 10M, 10M, 10M, 1G, 10M"""
        result = readDataclass(LinkEndpoint, link_response)
        assert result.speed[0] == "100M"
        assert result.speed[4] == "10M"
        assert result.speed[8] == "1G"

    def test_man_speed_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.man_speed, list)
        assert len(result.man_speed) == 10

    def test_man_speed_values(self, link_response):
        """Fixture: i05 all 0x02 -> '1G' for all ports."""
        result = readDataclass(LinkEndpoint, link_response)
        assert all(v == "1G" for v in result.man_speed)

    def test_man_full_duplex_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.man_full_duplex, list)
        assert len(result.man_full_duplex) == 10
        assert all(isinstance(v, bool) for v in result.man_full_duplex)

    def test_flow_control_rx_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.flow_control_rx, list)
        assert len(result.flow_control_rx) == 10
        assert all(isinstance(v, bool) for v in result.flow_control_rx)

    def test_flow_control_tx_type_and_length(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.flow_control_tx, list)
        assert len(result.flow_control_tx) == 10
        assert all(isinstance(v, bool) for v in result.flow_control_tx)


class TestLinkEndpointValidationIssues:
    """Tests documenting known validation issues from VALIDATION.md."""

    @pytest.mark.skip(
        reason="CRITICAL: link_state (i06) uses bool type but engine.js uses "
               "M:1 bitshift with 4-state option [no link, link on, no link, link paused]. "
               "Requires compound type implementation."
    )
    def test_link_state_should_be_4state_option(self, link_response):
        """link_state should return 4-state values, not booleans."""
        result = readDataclass(LinkEndpoint, link_response)
        # When fixed, link_state should contain option strings not bools
        valid_states = {"no link", "link on", "link paused"}
        assert all(v in valid_states for v in result.link_state)

    @pytest.mark.skip(
        reason="CRITICAL: full_duplex (i07) uses bool type but engine.js uses "
               "M:1 bitshift with 2-option map [no, yes]. Bit ordering is reversed "
               "(MSB-first vs LSB-first). Same root cause as hex_to_bool_list issue."
    )
    def test_full_duplex_bit_ordering(self, link_response):
        """full_duplex bit ordering is reversed due to hex_to_bool_list MSB-first."""
        result = readDataclass(LinkEndpoint, link_response)
        # i07:0x011f = 0b100011111 -- ports 0-4 and 8 have duplex
        # With correct LSB-first: [T,T,T,T,T,F,F,F,T,F]
        expected = [True, True, True, True, True, False, False, False, True, False]
        assert result.full_duplex == expected


class TestLinkEndpointMissingFields:
    """Document fields present in engine.js link.b but missing from LinkEndpoint."""

    @pytest.mark.parametrize("field_id,field_name", [
        ("i0d", "hops"),
        ("i0e", "last_hop"),
        ("i0f", "length"),
        ("i10", "fault_at"),
        ("i11", "cable_pairs"),
        ("i13", "flow_control_status"),
        ("i14", "flow_control_status_high_bit"),
        ("i15", "link_state_high_bit"),
    ])
    def test_link_missing_fields(self, field_id, field_name):
        pytest.skip(
            f"MISSING: {field_name} ({field_id}) exists in engine.js link.b "
            f"but not in LinkEndpoint"
        )
