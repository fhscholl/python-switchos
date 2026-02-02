"""Tests for SystemEndpoint parsing against CSS610 fixture data."""

import re
import pytest
from python_switchos.endpoint import readDataclass
from python_switchos.endpoints.sys import SystemEndpoint, AddressAcquisition


class TestSystemEndpointParsing:
    """Test that readDataclass correctly parses raw sys.b response."""

    def test_parses_to_system_endpoint(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result, SystemEndpoint)

    def test_address_acquisition(self, sys_response):
        """Fixture i0a:0x00 -> first option 'DHCP_FALLBACK'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.address_acquisition in ("DHCP_FALLBACK", "STATIC", "DHCP")
        assert result.address_acquisition == "DHCP_FALLBACK"

    def test_static_ip(self, sys_response):
        """Fixture i09:0x0101a8c0 -> 192.168.1.1."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.static_ip, str)
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", result.static_ip)
        assert result.static_ip == "192.168.1.1"

    def test_ip(self, sys_response):
        """Fixture i02:0x0101a8c0 -> 192.168.1.1."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.ip, str)
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", result.ip)
        assert result.ip == "192.168.1.1"

    def test_identity(self, sys_response):
        """Fixture i05 hex decodes to 'MockSwitch'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.identity, str)
        assert result.identity == "MockSwitch"

    def test_serial(self, sys_response):
        """Fixture i04 hex decodes to 'MockSeril0'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.serial, str)
        assert result.serial == "MockSeril0"

    def test_mac(self, sys_response):
        """Fixture i03:'001122334455' -> '00:11:22:33:44:55'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.mac, str)
        assert re.match(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", result.mac)
        assert result.mac == "00:11:22:33:44:55"

    def test_model(self, sys_response):
        """Fixture i07 hex decodes to 'CSS610G'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.model, str)
        assert result.model == "CSS610G"

    def test_version(self, sys_response):
        """Fixture i06 hex decodes to '2.16'."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.version, str)
        assert result.version == "2.16"

    def test_uptime(self, sys_response):
        """Fixture i01:0x0001a4f3 = 107763 seconds."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.uptime, int)
        assert result.uptime == 0x0001A4F3

    def test_cpu_temp(self, sys_response):
        """Fixture i22:0x002d = 45 degrees.
        Note: engine.js uses signed type 'za' but Python reads as unsigned int.
        For normal temperatures this works correctly."""
        result = readDataclass(SystemEndpoint, sys_response)
        assert isinstance(result.cpu_temp, int)
        assert result.cpu_temp == 45


class TestSystemEndpointPSUFields:
    """PSU fields are for other device models (CRS series). They should be None for CSS610."""

    def test_psu1_current_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu1_current is None

    def test_psu1_voltage_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu1_voltage is None

    def test_psu2_current_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu2_current is None

    def test_psu2_voltage_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu2_voltage is None

    def test_psu1_power_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu1_power is None

    def test_psu2_power_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
        assert result.psu2_power is None

    def test_power_consumption_none(self, sys_response):
        result = readDataclass(SystemEndpoint, sys_response)
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
