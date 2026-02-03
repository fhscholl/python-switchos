from dataclasses import fields, is_dataclass
from typing import ClassVar, Literal, cast, List, Type, TypeVar
from python_switchos.utils import hex_to_bool_list, hex_to_dbm, hex_to_ip, hex_to_mac, hex_to_option, hex_to_sfp_type, hex_to_str, process_int, str_to_json

def endpoint(path: str):
    """Decorator to add an endpoint path to a class."""
    def decorator(cls):
        cls.endpoint_path = path
        return cls
    return decorator


class SwitchOSDataclass:
    """Base class for SwitchOS data structures."""
    pass


class SwitchOSEndpoint(SwitchOSDataclass):
    """Represents an endpoint of SwitchOS Lite with a path."""
    endpoint_path: ClassVar[str]


T = TypeVar("T", bound=SwitchOSEndpoint)
E = TypeVar("E", bound=SwitchOSDataclass)

FieldType = Literal["bool", "str", "scalar_bool", "int", "option", "mac", "ip", "sfp_type", "dbm"]


def _parse_dict(cls: Type[E], json_data: dict, port_count: int) -> E:
    """Internal: parse a dict into a dataclass instance."""
    result_dict = {}
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
            case "str":
                if isinstance(value, list):
                    value = list(map(hex_to_str, cast(List[str], value)))
                else:
                    value = hex_to_str(value)
            case "option":
                if isinstance(value, list):
                    value = list(map(lambda v: hex_to_option(v, metadata.get("options")), cast(List[int], value)))
                else:
                    value = hex_to_option(value, metadata.get("options"))
            case "mac":
                value = hex_to_mac(value)
            case "ip":
                value = hex_to_ip(value)
            case "sfp_type":
                if isinstance(value, list):
                    value = list(map(hex_to_sfp_type, cast(List[str], value)))
                else:
                    value = hex_to_sfp_type(value)
            case "dbm":
                scale = metadata.get("scale", 10000)
                if isinstance(value, list):
                    value = [hex_to_dbm(v, scale) for v in cast(List[int], value)]
                else:
                    value = hex_to_dbm(value, scale)
        result_dict[f.name] = value
    return cls(**result_dict)


def readDataclass(cls: Type[T], data: str) -> T:
    """Parses the given JSON-Like string and returns an instance of the given endpoint class."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")
    json_data = str_to_json(data)
    first_arr = next((v for v in json_data.values() if isinstance(v, list)), None)
    port_count = len(first_arr) if first_arr else 10
    return _parse_dict(cls, json_data, port_count)


def readListDataclass(entry_cls: Type[E], data: str, port_count: int = 10) -> List[E]:
    """Parses a JSON array string and returns a list of entry dataclass instances.

    Used for endpoints that return arrays of objects (e.g., host tables, VLANs).
    Entry classes should inherit from SwitchOSDataclass.
    """
    if not is_dataclass(entry_cls):
        raise TypeError(f"{entry_cls} is not a dataclass")
    json_array = str_to_json(data)
    if not json_array:
        return []
    return [_parse_dict(entry_cls, item, port_count) for item in json_array]
