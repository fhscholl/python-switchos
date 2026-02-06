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
