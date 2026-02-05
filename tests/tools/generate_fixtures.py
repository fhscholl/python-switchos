"""Generate synthetic test fixtures from analysis data.

This tool creates SwOS-format response files and corresponding .expected files
for testing endpoint parsing across different device/version combinations.

Usage:
    python3 -m tests.tools.generate_fixtures --model css326 --version 2.18 --port-count 24
    python3 -m tests.tools.generate_fixtures --model css326 --version 2.18 --output-dir tests/fixtures/css326_2.18
"""

import argparse
from dataclasses import fields
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, get_args, get_origin

from tests.tools.compare_fields import (
    ALL_ENDPOINT_CLASSES,
    extract_field_ids,
    find_devices_with_endpoint,
    load_analysis_data,
)
from python_switchos.endpoint import SwitchOSDataclass


# Map endpoint paths to fixture directory names (matching conftest.py _ENDPOINTS)
ENDPOINT_DIR_MAP = {
    "link.b": "link_b",
    "sys.b": "sys_b",
    "sfp.b": "sfp_b",
    "snmp.b": "snmp_b",
    "host.b": "host_b",
    "!dhost.b": "!dhost.b",  # Keep dot in name
    "!igmp.b": "igmp_b",
    "vlan.b": "vlan_b",
    "lacp.b": "lacp_b",
    "rstp.b": "rstp_b",
    "!stats.b": "!stats_b",
    "stats.b": "stats_b",  # SwOS full 2.17+ uses stats.b
    "fwd.b": "fwd_b",
    "acl.b": "acl_b",
    "!aclstats.b": "!aclstats_b",
    "poe.b": "poe_b",
}

# Endpoints that use list/array format (parse multiple entries)
LIST_ENDPOINTS = {
    "host.b",
    "!dhost.b",
    "!igmp.b",
    "vlan.b",
    "acl.b",
}


def generate_swos_response(field_ids: List[str], port_count: int = 10) -> str:
    """Generate a SwOS JS object format response.

    SwOS format uses:
    - Hex values: 0x00, 0x1f, 0x0
    - No quotes around values (except strings which use single quotes)
    - Comma-separated arrays
    - Keys are field IDs without quotes

    For synthetic fixtures, we generate zero/default values.

    Args:
        field_ids: List of field IDs to include (e.g., ["i01", "i02", "i0a"])
        port_count: Number of ports (array length)

    Returns:
        SwOS format string like "{i01:[0x00,0x00,...],i02:[0x00,0x00,...],...}"
    """
    parts = []
    for fid in sorted(field_ids):
        # Generate array of zeros for per-port data
        arr = ",".join("0x00" for _ in range(port_count))
        parts.append(f"{fid}:[{arr}]")
    return "{" + ",".join(parts) + "}"


def hex_encode_string(s: str, pad_to: int = 20) -> str:
    """Encode a string as hex for SwOS format.

    Args:
        s: String to encode
        pad_to: Pad to this many bytes with zeros

    Returns:
        Hex-encoded string (e.g., "Port1" -> "506f727431" + zeros)
    """
    hex_str = s.encode("ascii").hex()
    # Pad to pad_to bytes (2 hex chars per byte)
    return hex_str + "0" * (pad_to * 2 - len(hex_str))


def generate_port_name(port_num: int, port_count: int) -> str:
    """Generate a port name for synthetic fixtures.

    Args:
        port_num: Port number (1-based)
        port_count: Total port count (for determining SFP port numbers)

    Returns:
        Port name like "Port1" or "SFP1+"
    """
    # Simple heuristic: last 2 ports are SFP on most devices
    if port_num > port_count - 2 and port_count > 4:
        sfp_num = port_num - (port_count - 2)
        return f"SFP{sfp_num}+"
    return f"Port{port_num}"


def generate_swos_response_for_endpoint(
    endpoint_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    is_scalar: bool = False,
) -> str:
    """Generate SwOS response for a specific endpoint class.

    Handles different field types appropriately:
    - bool fields: bitmask (all true by default)
    - int/float arrays: [0x00, 0x00, ...]
    - str arrays: ['hex_encoded_string', ...] with realistic values
    - Scalar fields: single value with realistic data

    Args:
        endpoint_class: The endpoint dataclass type
        port_count: Number of ports
        is_scalar: If True, generate scalar endpoint (sys.b), not array

    Returns:
        SwOS format response string
    """
    parts = []

    for f in fields(endpoint_class):
        metadata = f.metadata
        names = metadata.get("name", [])
        field_type = metadata.get("type", "")

        # Find primary field ID (iXX format)
        fid = None
        for name in names:
            if name.startswith("i") and len(name) >= 2:
                fid = name
                break

        if fid is None:
            continue

        # Determine if this is a list field
        is_list_field = get_origin(f.type) is list or (
            hasattr(f.type, "__origin__") and f.type.__origin__ is list
        )

        # Generate value based on type and field name
        # Note: is_list_field takes precedence - even sys.b has some list fields
        if not is_list_field:
            # Scalar value
            if field_type == "str":
                # Generate realistic scalar strings
                if f.name == "identity":
                    parts.append(f"{fid}:'{hex_encode_string('TestSwitch')}'")
                elif f.name == "serial":
                    parts.append(f"{fid}:'{hex_encode_string('SN00000001')}'")
                elif f.name == "model":
                    parts.append(f"{fid}:'{hex_encode_string('CSS326')}'")
                elif f.name == "version":
                    parts.append(f"{fid}:'{hex_encode_string('2.18')}'")
                else:
                    parts.append(f"{fid}:'{hex_encode_string('Test')}'")
            elif field_type == "mac":
                # MAC: 00:11:22:33:44:55 as hex string
                parts.append(f"{fid}:'001122334455'")
            elif field_type == "ip":
                # IP: 192.168.1.1 as little-endian int
                # 192.168.1.1 -> 0x0101a8c0
                parts.append(f"{fid}:0x0101a8c0")
            elif field_type == "scalar_bool":
                parts.append(f"{fid}:0x01")
            else:
                # Numeric
                parts.append(f"{fid}:0x0000")
        else:
            # Array value
            if field_type == "str":
                # Generate realistic per-port strings
                if "name" in f.name.lower():
                    # Port names like Port1, Port2, SFP1+, etc.
                    arr = ",".join(
                        f"'{hex_encode_string(generate_port_name(i + 1, port_count))}'"
                        for i in range(port_count)
                    )
                elif "vendor" in f.name.lower():
                    arr = ",".join(f"'{hex_encode_string('Vendor')}'" for _ in range(port_count))
                else:
                    arr = ",".join(f"'{hex_encode_string('')}'" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")
            elif field_type == "sfp_type":
                # SFP type is also a hex-encoded string
                arr = ",".join(f"'{hex_encode_string('')}'" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")
            elif field_type == "mac" or field_type == "partner_mac":
                # Array of MAC addresses
                arr = ",".join("'001122334455'" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")
            elif field_type == "ip" or field_type == "partner_ip":
                # Array of IPs
                arr = ",".join("0x0101a8c0" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")
            elif field_type == "bool":
                # Bitmask - all true (all bits set)
                # For 24 ports: 0xffffff, for 10 ports: 0x03ff
                bitmask = (1 << port_count) - 1
                parts.append(f"{fid}:0x{bitmask:x}")
            elif field_type == "bool_option":
                # Bool option - bitmask where 0=first option, 1=second option
                # Default to all zeros (first option)
                parts.append(f"{fid}:0x{'0' * ((port_count + 3) // 4)}")
            elif field_type == "bitshift_option":
                # Bitshift option - uses paired bitmasks for 2-bit values
                # Default to all zeros (first option)
                parts.append(f"{fid}:0x{'0' * ((port_count + 3) // 4)}")
            else:
                # Numeric array
                arr = ",".join("0x00" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")

        # Handle high byte for uint64 fields
        high = metadata.get("high")
        if high and isinstance(high, str):
            if is_list_field:
                arr = ",".join("0x00" for _ in range(port_count))
                parts.append(f"{high}:[{arr}]")
            else:
                parts.append(f"{high}:0x0000")

        # Handle pair fields for bitshift_option (always a bitmask)
        pair = metadata.get("pair")
        if pair and isinstance(pair, str):
            # Pair field is always a bitmask for bitshift_option
            parts.append(f"{pair}:0x{'0' * ((port_count + 3) // 4)}")

    return "{" + ",".join(parts) + "}"


def generate_list_response_for_entry(
    entry_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    num_entries: int = 1,
) -> str:
    """Generate SwOS list response for a list-based endpoint.

    List endpoints return an array of entry objects: [{i01:..., i02:...}, ...]

    Args:
        entry_class: The entry dataclass type (e.g., HostEntry, VlanEntry)
        port_count: Number of ports (for bool fields)
        num_entries: Number of entries to generate

    Returns:
        SwOS format list string like "[{i01:..., i02:...}]"
    """
    entries = []
    for _ in range(num_entries):
        entry_parts = []
        for f in fields(entry_class):
            metadata = f.metadata
            names = metadata.get("name", [])
            field_type = metadata.get("type", "")

            # Find primary field ID (iXX format)
            fid = None
            for name in names:
                if name.startswith("i") and len(name) >= 2:
                    fid = name
                    break
            if fid is None:
                continue

            # Determine if this is a list field
            is_list_field = get_origin(f.type) is list or (
                hasattr(f.type, "__origin__") and f.type.__origin__ is list
            )

            # Generate value based on type
            if field_type == "str":
                entry_parts.append(f"{fid}:'{hex_encode_string('')}'")
            elif field_type == "mac":
                entry_parts.append(f"{fid}:'001122334455'")
            elif field_type == "partner_mac":
                entry_parts.append(f"{fid}:'000000000000'")  # 0 = no partner
            elif field_type == "ip":
                entry_parts.append(f"{fid}:0x0101a8c0")  # 192.168.1.1
            elif field_type == "partner_ip":
                entry_parts.append(f"{fid}:0x00000000")  # 0 = any
            elif field_type == "scalar_bool":
                entry_parts.append(f"{fid}:0x01")
            elif field_type == "bool" and is_list_field:
                # Bitmask for ports
                bitmask = (1 << port_count) - 1
                entry_parts.append(f"{fid}:0x{bitmask:x}")
            elif field_type == "option":
                entry_parts.append(f"{fid}:0x00")  # First option
            else:
                entry_parts.append(f"{fid}:0x00")

        entries.append("{" + ", ".join(entry_parts) + "}")

    return "[" + ",\n".join(entries) + "]"


def generate_list_expected_dict(
    entry_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    num_entries: int = 1,
) -> List:
    """Generate expected list for a list-based endpoint.

    Returns format like: [{"port": 0, "mac": "..."}, ...]

    Args:
        entry_class: The entry dataclass type
        port_count: Number of ports (for bool fields)
        num_entries: Number of entries

    Returns:
        List of entry dicts
    """
    entries = []
    for _ in range(num_entries):
        entry = {}
        for f in fields(entry_class):
            metadata = f.metadata
            field_type = metadata.get("type", "")

            is_list_field = get_origin(f.type) is list or (
                hasattr(f.type, "__origin__") and f.type.__origin__ is list
            )

            if field_type == "str":
                entry[f.name] = ""
            elif field_type == "mac":
                entry[f.name] = "00:11:22:33:44:55"
            elif field_type == "partner_mac":
                entry[f.name] = ""  # Empty for no partner
            elif field_type == "ip":
                entry[f.name] = "192.168.1.1"
            elif field_type == "partner_ip":
                entry[f.name] = ""  # Empty for 0
            elif field_type == "scalar_bool":
                entry[f.name] = True
            elif field_type == "bool" and is_list_field:
                entry[f.name] = [True] * port_count
            elif field_type == "option":
                options = metadata.get("options")
                if options:
                    args = get_args(options)
                    entry[f.name] = args[0] if args else None
                else:
                    entry[f.name] = None
            else:
                entry[f.name] = 0
        entries.append(entry)

    return entries


def generate_expected_dict(
    endpoint_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    is_scalar: bool = False,
) -> Dict:
    """Generate expected dict for a synthetic fixture.

    Creates a dict with realistic values matching what the parser
    should produce from the synthetic response.

    Args:
        endpoint_class: The endpoint dataclass type
        port_count: Number of ports
        is_scalar: If True, generate scalar expected values

    Returns:
        Dict mapping field names to expected values
    """
    result = {}

    for f in fields(endpoint_class):
        metadata = f.metadata
        field_type = metadata.get("type", "")
        names = metadata.get("name", [])

        # Skip fields without iXX format names (they're not in the response)
        has_ixx_name = any(
            name.startswith("i") and len(name) >= 2 for name in names
        )
        if not has_ixx_name:
            continue

        # Determine if this is a list field
        is_list_field = get_origin(f.type) is list or (
            hasattr(f.type, "__origin__") and f.type.__origin__ is list
        )

        # Get inner type for list fields
        inner_type = None
        if is_list_field:
            args = get_args(f.type)
            if args:
                inner_type = args[0]

        # Generate value based on type
        # Note: is_list_field takes precedence - even sys.b has some list fields
        if not is_list_field:
            # Scalar values with realistic data
            if field_type == "str":
                if f.name == "identity":
                    result[f.name] = "TestSwitch"
                elif f.name == "serial":
                    result[f.name] = "SN00000001"
                elif f.name == "model":
                    result[f.name] = "CSS326"
                elif f.name == "version":
                    result[f.name] = "2.18"
                else:
                    result[f.name] = "Test"
            elif field_type == "mac":
                result[f.name] = "00:11:22:33:44:55"
            elif field_type == "ip":
                result[f.name] = "192.168.1.1"
            elif field_type == "bool" or field_type == "scalar_bool":
                result[f.name] = True
            elif field_type == "option":
                # Get first option value
                options = metadata.get("options")
                if options:
                    args = get_args(options)
                    if args:
                        result[f.name] = args[0]
                    else:
                        result[f.name] = None
                else:
                    result[f.name] = None
            elif field_type in ("int", "uint64"):
                result[f.name] = 0
            else:
                result[f.name] = 0
        else:
            # List values with realistic data
            if field_type == "str":
                if "name" in f.name.lower():
                    # Port names
                    result[f.name] = [
                        generate_port_name(i + 1, port_count)
                        for i in range(port_count)
                    ]
                elif "vendor" in f.name.lower():
                    result[f.name] = ["Vendor"] * port_count
                else:
                    result[f.name] = [""] * port_count
            elif field_type == "sfp_type":
                # SFP type decodes to empty string for empty data
                result[f.name] = [""] * port_count
            elif field_type == "mac" or field_type == "partner_mac":
                result[f.name] = ["00:11:22:33:44:55"] * port_count
            elif field_type == "ip" or field_type == "partner_ip":
                result[f.name] = ["192.168.1.1"] * port_count
            elif field_type == "bool":
                result[f.name] = [True] * port_count
            elif field_type in ("option", "bitshift_option", "bool_option"):
                options = metadata.get("options")
                if options:
                    args = get_args(options)
                    if args:
                        result[f.name] = [args[0]] * port_count
                    else:
                        result[f.name] = [None] * port_count
                else:
                    result[f.name] = [None] * port_count
            elif field_type == "dbm":
                result[f.name] = [0.0] * port_count
            elif field_type in ("int", "uint64"):
                # Check for scale (indicates float result)
                scale = metadata.get("scale")
                if scale and isinstance(scale, float):
                    result[f.name] = [0.0] * port_count
                else:
                    result[f.name] = [0] * port_count
            else:
                result[f.name] = [0] * port_count

    return result


def generate_device_fixtures(
    model: str,
    version: str,
    output_dir: Path,
    port_count: int = 10,
) -> List[str]:
    """Generate synthetic fixtures for a device/version combination.

    Args:
        model: Device model (e.g., "css326")
        version: Firmware version (e.g., "2.18")
        output_dir: Directory to create fixtures in
        port_count: Number of ports on the device

    Returns:
        List of created file paths
    """
    analysis_data = load_analysis_data()

    # Find matching device entry
    device_entry = None
    for entry in analysis_data:
        if entry.get("model") == model and entry.get("version") == version:
            device_entry = entry
            break

    if device_entry is None:
        # Try case-insensitive match
        for entry in analysis_data:
            if (entry.get("model", "").lower() == model.lower() and
                entry.get("version") == version):
                device_entry = entry
                model = entry.get("model")  # Use exact case from data
                break

    if device_entry is None:
        raise ValueError(f"No analysis data found for {model} {version}")

    device_endpoints = device_entry.get("endpoints", [])
    created_files = []

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate fixtures for each endpoint the device supports
    for endpoint_path in device_endpoints:
        if endpoint_path not in ALL_ENDPOINT_CLASSES:
            continue  # Skip unimplemented endpoints

        endpoint_class = ALL_ENDPOINT_CLASSES[endpoint_path]
        endpoint_dir = ENDPOINT_DIR_MAP.get(endpoint_path)
        if not endpoint_dir:
            continue

        # Create endpoint directory
        endpoint_output = output_dir / endpoint_dir
        endpoint_output.mkdir(parents=True, exist_ok=True)

        # Determine endpoint format
        is_scalar = endpoint_path == "sys.b"
        is_list = endpoint_path in LIST_ENDPOINTS

        # Generate response and expected files
        if is_list:
            # List-based endpoint (host.b, vlan.b, igmp.b, acl.b, !dhost.b)
            response = generate_list_response_for_entry(
                endpoint_class, port_count, num_entries=1
            )
            expected = generate_list_expected_dict(
                endpoint_class, port_count, num_entries=1
            )
        else:
            # Per-port or scalar endpoint
            response = generate_swos_response_for_endpoint(
                endpoint_class, port_count, is_scalar
            )
            expected = generate_expected_dict(endpoint_class, port_count, is_scalar)

        response_file = endpoint_output / f"{model}_{version}_response_1.txt"
        response_file.write_text(response)
        created_files.append(str(response_file))

        expected_file = endpoint_output / f"{model}_{version}_response_1.expected"
        # Format as Python literal (list for list endpoints, dict otherwise)
        if is_list:
            # List of entry dicts
            expected_text = "[\n"
            for entry in expected:
                expected_text += "    {\n"
                for key, value in entry.items():
                    expected_text += f'        "{key}": {repr(value)},\n'
                expected_text += "    },\n"
            expected_text += "]\n"
        else:
            # Dict literal
            expected_text = "{\n"
            for key, value in expected.items():
                expected_text += f'    "{key}": {repr(value)},\n'
            expected_text += "}\n"
        expected_file.write_text(expected_text)
        created_files.append(str(expected_file))

    return created_files


def main():
    """Run synthetic fixture generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic test fixtures for python-switchos"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        required=True,
        help="Device model (e.g., css326)"
    )
    parser.add_argument(
        "--version", "-v",
        type=str,
        required=True,
        help="Firmware version (e.g., 2.18)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        help="Output directory (default: tests/fixtures/{model}_{version})"
    )
    parser.add_argument(
        "--port-count", "-p",
        type=int,
        default=10,
        help="Number of ports (default: 10)"
    )
    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("tests/fixtures") / f"{args.model}_{args.version}"

    try:
        created = generate_device_fixtures(
            args.model,
            args.version,
            output_dir,
            args.port_count,
        )
        print(f"Created {len(created)} files in {output_dir}")
        for f in created:
            print(f"  {f}")
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure the mikrotik analysis data is available.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
