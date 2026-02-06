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
