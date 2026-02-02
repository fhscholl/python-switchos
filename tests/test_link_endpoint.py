"""Tests for LinkEndpoint parsing against CSS610 fixture data.

Tests in TestLinkEndpointParsing run against every fixture file discovered
in tests/fixtures/link_b/. Fixture-specific value assertions are in
separate test classes.
"""

import pytest
from typing import get_args
from python_switchos.endpoint import readDataclass
from python_switchos.endpoints.link import LinkEndpoint, Speed


class TestLinkEndpointParsing:
    """Generic parsing tests that run against all link.b fixtures."""

    def test_parses_to_link_endpoint(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result, LinkEndpoint)

    def test_enabled_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.enabled, list)
        assert len(result.enabled) > 0
        assert all(isinstance(v, bool) for v in result.enabled)

    def test_name_is_str_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.name, list)
        assert all(isinstance(v, str) for v in result.name)
        assert all(len(v) > 0 for v in result.name)

    def test_auto_negotiation_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.auto_negotiation, list)
        assert all(isinstance(v, bool) for v in result.auto_negotiation)

    def test_speed_values_are_valid(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.speed, list)
        valid = set(get_args(Speed)) | {None}
        assert all(v in valid for v in result.speed)

    def test_man_speed_values_are_valid(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.man_speed, list)
        valid = set(get_args(Speed)) | {None}
        assert all(v in valid for v in result.man_speed)

    def test_link_state_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.link_state, list)
        assert all(isinstance(v, bool) for v in result.link_state)

    def test_full_duplex_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.full_duplex, list)
        assert all(isinstance(v, bool) for v in result.full_duplex)

    def test_man_full_duplex_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.man_full_duplex, list)
        assert all(isinstance(v, bool) for v in result.man_full_duplex)

    def test_flow_control_rx_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.flow_control_rx, list)
        assert all(isinstance(v, bool) for v in result.flow_control_rx)

    def test_flow_control_tx_is_bool_list(self, link_response):
        result = readDataclass(LinkEndpoint, link_response)
        assert isinstance(result.flow_control_tx, list)
        assert all(isinstance(v, bool) for v in result.flow_control_tx)

    def test_all_port_lists_same_length(self, link_response):
        """All per-port fields should have the same number of entries."""
        result = readDataclass(LinkEndpoint, link_response)
        lengths = {
            len(result.enabled), len(result.name), len(result.speed),
            len(result.man_speed), len(result.link_state),
            len(result.full_duplex), len(result.man_full_duplex),
            len(result.auto_negotiation),
            len(result.flow_control_rx), len(result.flow_control_tx),
        }
        assert len(lengths) == 1, f"Inconsistent port counts: {lengths}"


class TestLinkEndpointFixture1:
    """Value assertions specific to css610_response_1 (all ports enabled, 5 with link)."""

    @pytest.fixture()
    def result(self):
        from pathlib import Path
        fixture = Path(__file__).parent / "fixtures" / "link_b" / "css610_response_1.txt"
        return readDataclass(LinkEndpoint, fixture.read_text())

    def test_enabled_all_true(self, result):
        """i01:0x03ff -- all 10 ports enabled."""
        assert all(v is True for v in result.enabled)

    def test_port_count(self, result):
        assert len(result.enabled) == 10

    def test_name_values(self, result):
        assert result.name[0] == "Port1"
        assert result.name[7] == "Port8"
        assert result.name[8] == "SFP1+"
        assert result.name[9] == "SFP2+"

    def test_auto_negotiation_all_true(self, result):
        """i02:0x03ff -- all ports auto-negotiation enabled."""
        assert all(v is True for v in result.auto_negotiation)

    def test_speed_values(self, result):
        """i08:[0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x02,0x00]"""
        assert result.speed[0] == "100M"
        assert result.speed[4] == "10M"
        assert result.speed[8] == "1G"

    def test_man_speed_all_1g(self, result):
        """i05 all 0x02 -> '1G' for all ports."""
        assert all(v == "1G" for v in result.man_speed)

    def test_full_duplex_bit_ordering(self, result):
        """i07:0x011f = 0b100011111 -- ports 0-4 and 8 have duplex."""
        expected = [True, True, True, True, True, False, False, False, True, False]
        assert result.full_duplex == expected

    def test_link_state(self, result):
        """i06:0x021f -- ports 0-4 and 9 have link."""
        expected = [True, True, True, True, True, False, False, False, False, True]
        assert result.link_state == expected


class TestLinkEndpointFixture2:
    """Value assertions specific to css610_response_2 (port 3 disabled)."""

    @pytest.fixture()
    def result(self):
        from pathlib import Path
        fixture = Path(__file__).parent / "fixtures" / "link_b" / "css610_response_2.txt"
        return readDataclass(LinkEndpoint, fixture.read_text())

    def test_port3_disabled(self, result):
        """i01:0x03fb -- port 3 (index 2) is disabled."""
        assert result.enabled[2] is False

    def test_other_ports_enabled(self, result):
        """All ports except port 3 are enabled."""
        for i, v in enumerate(result.enabled):
            if i == 2:
                assert v is False, "Port3 should be disabled"
            else:
                assert v is True, f"Port index {i} should be enabled"

    def test_link_state(self, result):
        """i06:0x0380 -- ports 7-9 (Port8, SFP1, SFP2) have link."""
        expected = [False, False, False, False, False, False, False, True, True, True]
        assert result.link_state == expected


class TestLinkEndpointValidationIssues:
    """Tests documenting known validation issues from VALIDATION.md."""

    @pytest.mark.skip(
        reason="ENHANCEMENT: link_state (i06) uses bool type but engine.js uses "
               "M:1 bitshift with 4-state option [no link, link on, no link, link paused]. "
               "Requires compound type (i06+i15) implementation. "
               "Bool is correct for the common case (link on / no link)."
    )
    def test_link_state_should_be_4state_option(self, link_response):
        """link_state should return 4-state values, not booleans."""
        result = readDataclass(LinkEndpoint, link_response)
        valid_states = {"no link", "link on", "link paused"}
        assert all(v in valid_states for v in result.link_state)


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
