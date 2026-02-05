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
    ENDPOINT_CLASSES,
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


def generate_swos_response_for_endpoint(
    endpoint_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    is_scalar: bool = False,
) -> str:
    """Generate SwOS response for a specific endpoint class.

    Handles different field types appropriately:
    - bool fields: bitmask (0x0000 for all false)
    - int/float arrays: [0x00, 0x00, ...]
    - str arrays: ['hex_encoded_string', ...]
    - Scalar fields: single value (0x00 or 'hex_string')

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

        # Generate value based on type
        if is_scalar or not is_list_field:
            # Scalar value
            if field_type in ("str", "mac"):
                # 20-byte hex string (padded with zeros)
                parts.append(f"{fid}:'{'00' * 20}'")
            elif field_type == "ip":
                # IP as int (0.0.0.0)
                parts.append(f"{fid}:0x00000000")
            else:
                # Numeric
                parts.append(f"{fid}:0x0000")
        else:
            # Array value
            if field_type == "str":
                # Array of hex-encoded strings
                arr = ",".join(f"'{'00' * 20}'" for _ in range(port_count))
                parts.append(f"{fid}:[{arr}]")
            elif field_type == "bool":
                # Bitmask (single hex value covering all ports)
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

        # Handle pair fields for bitshift_option
        pair = metadata.get("pair")
        if pair and isinstance(pair, str):
            if is_list_field:
                arr = ",".join("0x00" for _ in range(port_count))
                parts.append(f"{pair}:[{arr}]")
            else:
                parts.append(f"{pair}:0x0000")

    return "{" + ",".join(parts) + "}"


def generate_expected_dict(
    endpoint_class: Type[SwitchOSDataclass],
    port_count: int = 10,
    is_scalar: bool = False,
) -> Dict:
    """Generate expected dict for a synthetic fixture.

    Creates a dict with default/zero values matching what the parser
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
        if is_scalar or not is_list_field:
            # Scalar values
            if field_type == "str":
                result[f.name] = ""
            elif field_type == "mac":
                result[f.name] = "00:00:00:00:00:00"
            elif field_type == "ip":
                result[f.name] = "0.0.0.0"
            elif field_type == "bool" or field_type == "scalar_bool":
                result[f.name] = False
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
            # List values
            if field_type == "str":
                result[f.name] = [""] * port_count
            elif field_type == "mac" or field_type == "partner_mac":
                result[f.name] = ["00:00:00:00:00:00"] * port_count
            elif field_type == "ip" or field_type == "partner_ip":
                result[f.name] = ["0.0.0.0"] * port_count
            elif field_type == "bool":
                result[f.name] = [False] * port_count
            elif field_type == "option" or field_type == "bitshift_option":
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
        if endpoint_path not in ENDPOINT_CLASSES:
            continue  # Skip unimplemented endpoints

        endpoint_class = ENDPOINT_CLASSES[endpoint_path]
        endpoint_dir = ENDPOINT_DIR_MAP.get(endpoint_path)
        if not endpoint_dir:
            continue

        # Determine if scalar endpoint (sys.b)
        is_scalar = endpoint_path == "sys.b"

        # Create endpoint directory
        endpoint_output = output_dir / endpoint_dir
        endpoint_output.mkdir(parents=True, exist_ok=True)

        # Generate response file
        response = generate_swos_response_for_endpoint(
            endpoint_class, port_count, is_scalar
        )
        response_file = endpoint_output / f"{model}_{version}_response_1.txt"
        response_file.write_text(response)
        created_files.append(str(response_file))

        # Generate expected file
        expected = generate_expected_dict(endpoint_class, port_count, is_scalar)
        expected_file = endpoint_output / f"{model}_{version}_response_1.expected"
        # Format as Python dict literal
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
