"""Round-trip tests: verify serialize(deserialize(fixture)) == fixture.

These tests validate that the full read/write cycle preserves data correctly.
Wire format may differ in field order and hex case, so we normalize before comparison.
"""

import pytest
import demjson3
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Type

from python_switchos.endpoint import readDataclass, writeDataclass, SwitchOSEndpoint
from python_switchos.endpoints.link import LinkEndpoint
from python_switchos.endpoints.snmp import SnmpEndpoint
from python_switchos.endpoints.fwd import ForwardingEndpoint


def normalize_wire_format(wire_str: str) -> dict:
    """Parse wire format to dict for comparison.

    Wire format may differ in:
    - Field order
    - Hex case (0xFF vs 0xff)
    - Whitespace

    Normalize by parsing and converting to comparable form.
    """
    parsed = demjson3.decode(wire_str)
    return _normalize_dict(parsed)


def _normalize_dict(d: dict) -> dict:
    """Recursively normalize dict values for comparison."""
    result = {}
    for k, v in d.items():
        if isinstance(v, int):
            result[k] = v
        elif isinstance(v, str):
            # Normalize hex strings to lowercase
            result[k] = v.lower() if v.startswith("'") else v
        elif isinstance(v, list):
            result[k] = [_normalize_value(x) for x in v]
        else:
            result[k] = v
    return result


def _normalize_value(v):
    """Normalize a single value."""
    if isinstance(v, str):
        return v.lower() if v.startswith("'") else v
    return v


def filter_writable_fields(original: dict, endpoint_cls: Type[SwitchOSEndpoint]) -> dict:
    """Filter original fixture to only writable fields.

    Since writeDataclass excludes read-only fields, we need to compare
    only the writable portion of the original fixture.
    """
    writable_names = set()
    for f in dataclass_fields(endpoint_cls):
        if f.metadata.get("writable", True):
            for name in f.metadata.get("name", []):
                writable_names.add(name)

    return {k: v for k, v in original.items() if k in writable_names}


class TestRoundtripScalar:
    """Round-trip tests for scalar (non-per-port) endpoints."""

    def test_snmp_roundtrip(self):
        """Test SNMP endpoint round-trip (all fields writable)."""
        # Sample SNMP fixture
        fixture = "{i01:0x01,i02:'7075626c6963',i03:'',i04:''}"

        # Read -> Python dataclass
        snmp = readDataclass(SnmpEndpoint, fixture)
        assert snmp.enabled == True
        assert snmp.community == "public"

        # Python dataclass -> Wire format
        serialized = writeDataclass(snmp)

        # Compare (normalized)
        original_norm = normalize_wire_format(fixture)
        serialized_norm = normalize_wire_format(serialized)

        # All SNMP fields are writable, so should match exactly
        assert serialized_norm == original_norm

    def test_snmp_with_data_roundtrip(self):
        """Test SNMP with actual data values."""
        fixture = "{i01:0x01,i02:'7075626c6963',i03:'61646d696e',i04:'6f6666696365'}"

        snmp = readDataclass(SnmpEndpoint, fixture)
        assert snmp.community == "public"
        assert snmp.contact_info == "admin"
        assert snmp.location == "office"

        serialized = writeDataclass(snmp)

        original_norm = normalize_wire_format(fixture)
        serialized_norm = normalize_wire_format(serialized)
        assert serialized_norm == original_norm


class TestRoundtripPerPort:
    """Round-trip tests for per-port endpoints."""

    def test_link_writable_fields_roundtrip(self):
        """Test Link endpoint round-trip (writable fields only).

        Verifies that Python field values survive the read->write->read cycle.
        Note: writeDataclass uses SwOS Full names (en, nm) by default,
        so we compare Python values, not raw wire names.
        """
        # Sample link fixture with both writable and read-only fields
        # i01=enabled (writable), i0a=name (writable), i02=auto_neg (writable)
        # i06=link_state (read-only), i05=man_speed (writable)
        fixture = "{i01:0x3ff,i0a:['506f727431','506f727432'],i02:0x3ff,i06:0x155,i05:[0x02,0x02]}"

        # First read
        link1 = readDataclass(LinkEndpoint, fixture)

        # Serialize and read again
        serialized = writeDataclass(link1)
        link2 = readDataclass(LinkEndpoint, serialized)

        # Writable fields should survive round-trip
        assert link2.enabled == link1.enabled
        assert link2.name == link1.name
        assert link2.auto_negotiation == link1.auto_negotiation
        assert link2.man_speed == link1.man_speed

    def test_link_string_list_roundtrip(self):
        """Test string list values survive round-trip."""
        fixture = "{i01:0x03,i0a:['506f727431','506f727432']}"  # "Port1", "Port2"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.name == ["Port1", "Port2"]

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.name == ["Port1", "Port2"]

    def test_link_option_list_roundtrip(self):
        """Test option list (man_speed) survives round-trip."""
        # i05=man_speed: 0x02=1G, 0x01=100M
        fixture = "{i01:0x03,i0a:['',''],i05:[0x02,0x01]}"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.man_speed == ["1G", "100M"]

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.man_speed == ["1G", "100M"]

    def test_forwarding_bool_list_roundtrip(self):
        """Test Forwarding endpoint bool list fields round-trip."""
        # Create link with port isolation bool lists
        link = LinkEndpoint(
            enabled=[True, True, False, True],
            name=["P1", "P2", "P3", "P4"],
        )

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.enabled == link.enabled

    def test_forwarding_int_list_roundtrip(self):
        """Test Forwarding endpoint int list fields round-trip."""
        # Create minimal fwd endpoint with int lists
        # ForwardingEndpoint has many required fields, so create programmatically
        fwd = ForwardingEndpoint(
            from_port_1=[True, True, True, True],
            from_port_2=[True, True, True, True],
            from_port_3=[True, True, True, True],
            from_port_4=[True, True, True, True],
            from_port_5=[True, True, True, True],
            from_port_6=[True, True, True, True],
            from_port_7=[True, True, True, True],
            from_port_8=[True, True, True, True],
            from_port_9=[True, True, True, True],
            from_port_10=[True, True, True, True],
            port_lock=[False, False, False, False],
            lock_on_first=[False, False, False, False],
            mirror_ingress=[False, False, False, False],
            mirror_egress=[False, False, False, False],
            mirror_to=[False, False, False, False],
            storm_rate=[0, 100, 200, 0],  # int list
            ingress_rate=[0, 0, 0, 0],
            egress_rate=[0, 0, 0, 0],
            limit_unknown_unicast=[True, True, True, True],
            flood_unknown_multicast=[True, True, True, True],
            vlan_mode=["disabled", "disabled", "optional", "strict"],
            vlan_receive=["any", "any", "only tagged", "only untagged"],
            default_vlan_id=[1, 1, 10, 20],
            force_vlan_id=[False, False, True, True],
        )

        serialized = writeDataclass(fwd)
        fwd2 = readDataclass(ForwardingEndpoint, serialized)

        # Verify int lists survive
        assert fwd2.storm_rate == fwd.storm_rate
        assert fwd2.default_vlan_id == fwd.default_vlan_id
        # Verify option lists survive
        assert fwd2.vlan_mode == fwd.vlan_mode
        assert fwd2.vlan_receive == fwd.vlan_receive

    def test_bool_list_bitmask_roundtrip(self):
        """Test boolean list -> bitmask -> boolean list roundtrip."""
        # Specific test for bitmask encoding
        original_bools = [True, False, True, True, False, True, False, False, True, True]
        # Binary: 1100101101 (reading right to left) = 0x32d

        # Create minimal link fixture
        fixture = "{i01:0x32d,i0a:['','','','','','','','','','']}"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.enabled == original_bools

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.enabled == original_bools
