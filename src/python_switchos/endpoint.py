from dataclasses import fields, is_dataclass
from typing import Any, ClassVar, List, Literal, Type, TypeVar, cast, get_args

from python_switchos.utils import (
    hex_to_bitshift_option,
    hex_to_bool_list,
    hex_to_bool_option,
    hex_to_dbm,
    hex_to_ip,
    hex_to_mac,
    hex_to_option,
    hex_to_partner_ip,
    hex_to_partner_mac,
    hex_to_sfp_type,
    hex_to_str,
    process_int,
    str_to_json,
    # Reverse converters for serialization
    bool_list_to_hex,
    int_to_hex,
    str_to_hex,
    mac_to_hex,
    ip_to_hex,
    option_to_hex,
)


def endpoint(path: str, *alternates: str, readonly: bool = False):
    """Decorator to add an endpoint path and optional alternates to a class.

    Args:
        path: Primary endpoint path (e.g., "!stats.b")
        *alternates: Optional alternate paths (e.g., "stats.b")
        readonly: If True, endpoint is read-only (no POST allowed)

    Example:
        @endpoint("!stats.b", "stats.b")  # Primary path with one alternate
        @endpoint("link.b")                # Primary path only
        @endpoint("sfp.b", readonly=True)  # Read-only endpoint
    """
    def decorator(cls):
        cls.endpoint_path = path
        cls.endpoint_alternates = list(alternates)
        cls.endpoint_readonly = readonly
        return cls
    return decorator


class SwitchOSDataclass:
    """Base class for SwitchOS data structures."""
    pass


class SwitchOSEndpoint(SwitchOSDataclass):
    """Represents an endpoint of SwitchOS Lite with a path.

    Attributes:
        endpoint_path: Primary endpoint path (e.g., "!stats.b")
        endpoint_alternates: Optional list of alternate paths (e.g., ["stats.b"])
                            for devices that use different conventions.
                            SwOS Lite uses ! prefix, SwOS full 2.17+ omits it.
        endpoint_readonly: If True, endpoint is read-only (no POST allowed).
                          Endpoints like sfp.b, !stats.b, !igmp.b are read-only.
    """
    endpoint_path: ClassVar[str]
    endpoint_alternates: ClassVar[List[str]] = []
    endpoint_readonly: ClassVar[bool] = False


T = TypeVar("T", bound=SwitchOSEndpoint)
E = TypeVar("E", bound=SwitchOSDataclass)

FieldType = Literal["bool", "scalar_bool", "int", "uint64", "str", "option", "bool_option", "bitshift_option", "mac", "partner_mac", "ip", "partner_ip", "sfp_type", "dbm"]


def _parse_dict(cls: Type[E], json_data: dict, port_count: int) -> E:
    """Parse a dict into a dataclass instance, applying type transformations."""
    result = {}
    for f in fields(cls):
        metadata = f.metadata
        names = metadata.get("name")
        value = next((json_data.get(name) for name in names if name in json_data), None)
        if value is None:
            continue

        field_type: FieldType = cast(FieldType, metadata.get("type"))
        match field_type:
            case "bool":
                length = metadata.get("ports", port_count)
                value = hex_to_bool_list(value, length)
            case "scalar_bool":
                value = bool(value)
            case "int":
                value = process_int(value, metadata.get("signed"), metadata.get("bits"), metadata.get("scale"))
            case "uint64":
                high_name = metadata.get("high")
                high_value = json_data.get(high_name, 0)
                if isinstance(value, list):
                    high_list = high_value if isinstance(high_value, list) else [0] * len(value)
                    value = [lo + hi * (2**32) for lo, hi in zip(value, high_list)]
                else:
                    value = value + high_value * (2**32)
            case "str":
                if isinstance(value, list):
                    value = [hex_to_str(v) for v in value]
                else:
                    value = hex_to_str(value)
            case "option":
                options = metadata.get("options")
                if isinstance(value, list):
                    value = [hex_to_option(v, options) for v in value]
                else:
                    value = hex_to_option(value, options)
            case "bool_option":
                options = metadata.get("options")
                length = metadata.get("ports", port_count)
                value = hex_to_bool_option(value, options, length)
            case "bitshift_option":
                pair_name = metadata.get("pair")
                pair_value = json_data.get(pair_name, 0)
                options = metadata.get("options")
                length = metadata.get("ports", port_count)
                value = hex_to_bitshift_option(value, pair_value, options, length)
            case "mac":
                value = hex_to_mac(value)
            case "partner_mac":
                if isinstance(value, list):
                    value = [hex_to_partner_mac(v) for v in value]
                else:
                    value = hex_to_partner_mac(value)
            case "ip":
                value = hex_to_ip(value)
            case "partner_ip":
                if isinstance(value, list):
                    value = [hex_to_partner_ip(v) for v in value]
                else:
                    value = hex_to_partner_ip(value)
            case "sfp_type":
                if isinstance(value, list):
                    value = [hex_to_sfp_type(v) for v in value]
                else:
                    value = hex_to_sfp_type(value)
            case "dbm":
                scale = metadata.get("scale", 10000)
                if isinstance(value, list):
                    value = [hex_to_dbm(v, scale) for v in value]
                else:
                    value = hex_to_dbm(value, scale)

        result[f.name] = value
    return cls(**result)


def _serialize_field(value: Any, metadata: dict, port_count: int) -> str | List[str] | None:
    """Serialize field value to wire format.

    Returns None if value should be skipped (None value or unsupported type).
    """
    if value is None:
        return None

    field_type: FieldType = cast(FieldType, metadata.get("type"))
    match field_type:
        case "bool":
            return bool_list_to_hex(value)
        case "scalar_bool":
            return f"0x0{1 if value else 0}"
        case "int":
            scale = metadata.get("scale")
            if isinstance(value, list):
                return [int_to_hex(v, scale) for v in value]
            return int_to_hex(value, scale)
        case "uint64":
            # uint64 fields are typically read-only (counters)
            # If writable, serialize as low 32-bit only
            if isinstance(value, list):
                return [int_to_hex(v & 0xFFFFFFFF) for v in value]
            return int_to_hex(value & 0xFFFFFFFF)
        case "str":
            if isinstance(value, list):
                return [str_to_hex(v) for v in value]
            return str_to_hex(value)
        case "option":
            options = metadata.get("options")
            if isinstance(value, list):
                return [option_to_hex(v, options) for v in value]
            return option_to_hex(value, options)
        case "bool_option":
            # Convert option strings back to bitmask
            options = metadata.get("options")
            opts = get_args(options)
            # opts[1] is true value, opts[0] is false
            bitmask = sum(1 << i for i, v in enumerate(value) if v == opts[1])
            return f"0x{bitmask:x}" if bitmask else "0x00"
        case "bitshift_option":
            # Two-bit options need low and high bitmasks
            # This is complex - may need to return tuple or handle specially
            # For now, skip (most bitshift fields are read-only)
            return None
        case "mac" | "partner_mac":
            if isinstance(value, list):
                return [mac_to_hex(v) for v in value]
            return mac_to_hex(value)
        case "ip" | "partner_ip":
            if isinstance(value, list):
                return [ip_to_hex(v) for v in value]
            return ip_to_hex(value)
        case "sfp_type" | "dbm":
            # Read-only types
            return None
    return None


def _build_wire_format(fields_dict: dict) -> str:
    """Convert {field_id: wire_value} dict to wire format string.

    Output format: {en:0x7ff,nm:['506f727431',...],an:0x7ff}
    """
    parts = []
    for key, value in fields_dict.items():
        if isinstance(value, list):
            # Array values
            items = ",".join(str(v) for v in value)
            parts.append(f"{key}:[{items}]")
        else:
            parts.append(f"{key}:{value}")
    return "{" + ",".join(parts) + "}"


def readDataclass(cls: Type[T], data: str) -> T:
    """Parse a JSON-like string into an endpoint dataclass instance."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")

    json_data = str_to_json(data)
    first_arr = next((v for v in json_data.values() if isinstance(v, list)), None)
    port_count = len(first_arr) if first_arr else 10

    return _parse_dict(cls, json_data, port_count)


def readListDataclass(cls: Type[E], data: str) -> List[E]:
    """Parse a JSON array string into a list of dataclass instances.

    Used for endpoints that return arrays of objects (e.g., host tables, VLANs).
    Entry classes should inherit from SwitchOSDataclass.
    Port count is auto-detected from array field lengths in the first entry.
    """
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")

    json_array = str_to_json(data)
    if not json_array:
        return []

    # Auto-detect port count from first entry's arrays (same as readDataclass)
    first_arr = next((v for v in json_array[0].values() if isinstance(v, list)), None)
    port_count = len(first_arr) if first_arr else 10

    return [_parse_dict(cls, item, port_count) for item in json_array]
