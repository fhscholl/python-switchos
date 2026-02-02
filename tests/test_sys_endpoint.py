"""Tests for SystemEndpoint parsing against CSS610 fixture data.

Tests in TestSystemEndpointParsing run against every fixture file discovered
in tests/fixtures/sys_b/. Fixture-specific value assertions are in
separate test classes.
"""

import re
import pytest
from python_switchos.endpoint import readDataclass
from python_switchos.endpoints.sys import SystemEndpoint, AddressAcquisition


class TestSystemEndpointParsing:
    """Generic parsing tests that run against all sys.b fixtures."""

    def test_parses_to_system_endpoint(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result, SystemEndpoint)

    def test_address_acquisition_is_valid(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.address_acquisition in ("DHCP_FALLBACK", "STATIC", "DHCP")

    def test_static_ip_format(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.static_ip, str)
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", result.static_ip)

    def test_ip_format(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.ip, str)
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", result.ip)

    def test_identity_is_str(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.identity, str)
        assert len(result.identity) > 0

    def test_serial_is_str(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.serial, str)
        assert len(result.serial) > 0

    def test_mac_format(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.mac, str)
        assert re.match(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", result.mac)

    def test_model_is_str(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.model, str)
        assert len(result.model) > 0

    def test_version_is_str(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.version, str)
        assert len(result.version) > 0

    def test_uptime_is_int(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.uptime, int)
        assert result.uptime >= 0

    def test_cpu_temp_is_int(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.cpu_temp, int)
        # Reasonable range: -40 to 125 C
        assert -40 <= result.cpu_temp <= 125


class TestSystemEndpointFixture1:
    """Value assertions specific to css610_response_1."""

    @pytest.fixture()
    def result(self):
        from pathlib import Path
        fixture = Path(__file__).parent / "fixtures" / "sys_b" / "css610_response_1.txt"
        return readDataclass(SystemEndpoint, fixture.read_text())

    def test_address_acquisition_value(self, result):
        """i0a:0x00 -> first option 'DHCP_FALLBACK'."""
        assert result.address_acquisition == "DHCP_FALLBACK"

    def test_static_ip_value(self, result):
        """i09:0x0101a8c0 -> 192.168.1.1."""
        assert result.static_ip == "192.168.1.1"

    def test_ip_value(self, result):
        """i02:0x0101a8c0 -> 192.168.1.1."""
        assert result.ip == "192.168.1.1"

    def test_identity_value(self, result):
        assert result.identity == "MockSwitch"

    def test_serial_value(self, result):
        assert result.serial == "MockSeril0"

    def test_mac_value(self, result):
        assert result.mac == "00:11:22:33:44:55"

    def test_model_value(self, result):
        assert result.model == "CSS610G"

    def test_version_value(self, result):
        assert result.version == "2.16"

    def test_uptime_value(self, result):
        """i01:0x0001a4f3 = 107763 seconds."""
        assert result.uptime == 0x0001A4F3

    def test_cpu_temp_value(self, result):
        """i22:0x002d = 45 degrees."""
        assert result.cpu_temp == 45


class TestSystemEndpointPSUFields:
    """PSU fields are for other device models (CRS series). They should be None for CSS610."""

    @pytest.fixture()
    def result(self):
        from pathlib import Path
        fixture = Path(__file__).parent / "fixtures" / "sys_b" / "css610_response_1.txt"
        return readDataclass(SystemEndpoint, fixture.read_text())

    def test_psu1_current_none(self, result):
        assert result.psu1_current is None

    def test_psu1_voltage_none(self, result):
        assert result.psu1_voltage is None

    def test_psu2_current_none(self, result):
        assert result.psu2_current is None

    def test_psu2_voltage_none(self, result):
        assert result.psu2_voltage is None

    def test_psu1_power_none(self, result):
        assert result.psu1_power is None

    def test_psu2_power_none(self, result):
        assert result.psu2_power is None

    def test_power_consumption_none(self, result):
        assert result.power_consumption is None


class TestSystemEndpointMissingFields:
    """Document fields present in engine.js sys.b but missing from SystemEndpoint."""

    @pytest.mark.parametrize("field_id,field_name", [
        ("i08", "mikrotik_discovery_protocol"),
        ("i12", "allow_from_ports"),
        ("i13", "dhcp_snooping_trusted_ports"),
        ("i14", "dhcp_snooping_add_info_option"),
        ("i17", "igmp_snooping"),
        ("i19", "allow_from_ip"),
        ("i1a", "allow_from_mask"),
        ("i1b", "allow_from_vlan"),
        ("i27", "igmp_fast_leave"),
        ("i28", "igmp_version"),
        ("i29", "igmp_querier"),
        ("i2a", "forward_reserved_multicast"),
        ("i0b", "build_number"),
        ("i0e", "bridge_priority"),
        ("i0f", "port_cost_mode"),
        ("i10", "root_bridge_priority"),
        ("i11", "root_bridge_mac"),
    ])
    def test_sys_missing_fields(self, field_id, field_name):
        pytest.skip(
            f"MISSING: {field_name} ({field_id}) exists in engine.js sys.b "
            f"but not in SystemEndpoint"
        )
