import math
import re
import demjson3
from typing import List, Type, get_args

def hex_to_bool_list(value: int, length: int = 24) -> List[bool]:
    """Converts an integer into a list of booleans.

    Args:
        value: The integer to convert.
        length: Number of bits to represent (pads with leading zeros if needed).

    Returns:
        List of booleans of the specified length.
    """
    return [c == "1" for c in f"{value:0{length}b}"][::-1]

def hex_to_str(value: str) -> str:
    """Converts a hex-encoded string to a UTF-8 decoded string.

    Args:
        value: Hex string representing bytes.

    Returns:
        The UTF-8 decoded string with trailing null bytes and spaces stripped.
    """
    return bytes.fromhex(value).decode().rstrip("\x00").rstrip()

def hex_to_option(value: int, type: Type) -> str | None:
    """Converts an integer into an option of a given Literal type.

    Args:
        value: The integer index representing the option.
        type: A Literal type containing the possible options.

    Returns:
        The option corresponding to the index, or None if index is out of range.
    """
    options = get_args(type)
    idx = value
    return None if idx >= len(options) else options[idx]

def hex_to_mac(value: str) -> str:
    """Converts a hex string to a colon-separated MAC address.

    Args:
        value: Hex string representing the MAC address.

    Returns:
        The MAC address formatted with colons.
    """
    return ":".join(re.findall("..", value.upper()))

def process_int(value: int | List[int], signed: bool = False, bits: int = None, scale: int | float = None) -> int | float | List[int] | List[float]:
    """Processes integer values with optional signed conversion and scaling.

    Args:
        value: The integer or list of integers to process.
        signed: Whether to treat the value as signed.
        bits: Number of bits for signed conversion.
        scale: Divisor for scaling the value.

    Returns:
        The processed value(s).
    """
    if signed and bits:
        half = 1 << (bits - 1)
        full = 1 << bits
        if isinstance(value, list):
            value = [v - full if v >= half else v for v in value]
        elif value >= half:
            value = value - full
    if scale is not None:
        if isinstance(value, list):
            value = [v / scale for v in value]
        else:
            value = value / scale
    return value

def hex_to_ip(value: int) -> str:
    """Converts an integer into its corresponding IPv4 address string.

    Args:
        value: Integer representing the IPv4 address (byteorder=little).

    Returns:
        The IPv4 address in dotted-decimal notation.
    """
    ip_bytes = value.to_bytes(4, byteorder="little")
    return ".".join(str(b) for b in ip_bytes)

def str_to_json(value: str) -> dict | None:
    """Parses a JSON-like string using demjson3 for tolerant decoding.

    Args:
        value: JSON-like string to parse.

    Returns:
        Parsed JSON as a dictionary, or None if parsing fails.
    """
    return demjson3.decode(value)

def hex_to_sfp_type(value: str) -> str:
    """Converts a hex-encoded SFP type string to a human-readable string.

    Decodes the hex string to UTF-8, strips null bytes, and replaces
    {hex} patterns with their decimal equivalents (e.g., {0352} -> 850).

    Args:
        value: Hex string representing the SFP type.

    Returns:
        The decoded SFP type string with hex wavelengths converted to decimal.
    """
    decoded = bytes.fromhex(value).decode().rstrip("\x00")
    return re.sub(r'\{([0-9a-fA-F]+)\}', lambda m: str(int(m.group(1), 16)), decoded)

def hex_to_partner_mac(value: str) -> str:
    """Converts a hex string to a MAC address, returning empty string for all-zeros.

    Used for LACP partner MAC addresses where "000000000000" indicates no partner.

    Args:
        value: Hex string representing the MAC address.

    Returns:
        The MAC address formatted with colons, or empty string for all-zeros.
    """
    if value == "000000000000" or not value:
        return ""
    return hex_to_mac(value)


def hex_to_partner_ip(value: int) -> str:
    """Converts an integer to an IP address, returning empty string for zero.

    Used for ACL IP fields where 0 indicates no IP match criteria.

    Args:
        value: Integer representing the IPv4 address.

    Returns:
        The IPv4 address in dotted-decimal notation, or empty string for zero.
    """
    if value == 0:
        return ""
    return hex_to_ip(value)


def hex_to_bool_option(value: int, options: Type, length: int) -> List[str]:
    """Converts a bitmask to a list of option strings.

    Each bit maps to the corresponding option: bit=0 -> options[0], bit=1 -> options[1].

    Args:
        value: The bitmask integer to convert.
        options: A Literal type containing exactly two options [false_option, true_option].
        length: Number of ports/bits to decode.

    Returns:
        List of option strings of the specified length.
    """
    opts = get_args(options)
    return [opts[1] if ((value >> i) & 1) else opts[0] for i in range(length)]


def hex_to_bitshift_option(low: int, high: int, options: Type, length: int) -> List[str]:
    """Combines two bitmasks into 2-bit per-port option values.

    For each port i, extracts bit i from both low and high bitmasks,
    combines them into a 2-bit index (low_bit | (high_bit << 1)),
    and looks up the corresponding option string.

    Note: When options has duplicate values (e.g., ["shared", "point-to-point", "edge", "edge"]),
    Python's Literal deduplicates them. This function handles this by clamping the index
    to the valid range, since the last indices typically map to the same value.

    Args:
        low: The low-bit bitmask.
        high: The high-bit bitmask.
        options: A Literal type containing options indexed 0-3 (may be deduplicated).
        length: Number of ports/bits to decode.

    Returns:
        List of option strings of the specified length.
    """
    opts = get_args(options)
    result = []
    for i in range(length):
        low_bit = (low >> i) & 1
        high_bit = (high >> i) & 1
        index = low_bit | (high_bit << 1)
        # Clamp index to valid range (handles Literal deduplication)
        index = min(index, len(opts) - 1)
        result.append(opts[index])
    return result


def hex_to_dbm(value: int, scale: int = 10000) -> float:
    """Converts a raw SFP power reading to dBm.

    Args:
        value: Raw integer power value from SFP diagnostics.
        scale: Divisor for scaling (default 10000 for microwatts).

    Returns:
        Power in dBm, rounded to 3 decimal places.
        Returns 0.0 if value is 0 (copper SFP or no reading).
    """
    if value == 0:
        return 0.0
    return round(10 * math.log10(value / scale), 3)


# =============================================================================
# Reverse conversion functions (serialization: Python -> wire format)
# =============================================================================


def bool_list_to_hex(values: List[bool]) -> str:
    """Converts a list of booleans to a hex bitmask string.

    Bit N corresponds to index N in the list.
    Example: [True, True, False, True] -> "0x0b" (binary 1011)

    Args:
        values: List of boolean values.

    Returns:
        Hex string with even-length formatting (e.g., "0x0f" not "0xf").
    """
    if not values:
        return "0x00"
    bitmask = sum(1 << i for i, v in enumerate(values) if v)
    if bitmask == 0:
        return "0x00"
    hex_str = f"{bitmask:x}"
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return f"0x{hex_str}"


def int_to_hex(value: int | float, scale: float = None) -> str:
    """Converts an integer to wire format hex string.

    Applies scale factor if present (multiply for write, opposite of read division).
    Uses engine.js nibble formatting: ensures even hex digit count.

    Args:
        value: The integer or float to convert.
        scale: Optional multiplier for the value.

    Returns:
        Hex string with even-length formatting (e.g., "0x0f" not "0xf").
    """
    if scale is not None:
        value = int(value * scale)
    else:
        value = int(value)

    if value == 0:
        return "0x00"

    hex_str = f"{value:x}"
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return f"0x{hex_str}"


def str_to_hex(value: str) -> str:
    """Converts a string to hex-encoded UTF-8, single-quoted.

    Example: "Port1" -> "'506f727431'"

    Args:
        value: The string to convert.

    Returns:
        Single-quoted hex string.
    """
    if not value:
        return "''"
    hex_bytes = value.encode('utf-8').hex()
    return f"'{hex_bytes}'"


def mac_to_hex(value: str) -> str:
    """Converts a MAC address to hex string, single-quoted.

    Example: "AA:BB:CC:DD:EE:FF" -> "'aabbccddeeff'"

    Args:
        value: The MAC address with colons.

    Returns:
        Single-quoted lowercase hex string.
    """
    if not value:
        return "''"
    hex_only = value.replace(":", "").lower()
    return f"'{hex_only}'"


def ip_to_hex(value: str) -> str:
    """Converts an IPv4 address to little-endian hex integer string.

    Example: "192.168.88.1" -> "0x0158a8c0"

    Args:
        value: The IPv4 address in dotted-decimal notation.

    Returns:
        Hex string representing little-endian integer.
    """
    if not value:
        return "0x00"
    octets = [int(x) for x in value.split(".")]
    int_val = octets[0] | (octets[1] << 8) | (octets[2] << 16) | (octets[3] << 24)
    if int_val == 0:
        return "0x00"
    return int_to_hex(int_val)


def option_to_hex(value: str, options_type: Type) -> str:
    """Converts an option string to zero-based index hex.

    Example: "1G" with options ["10M","100M","1G",...] -> "0x02"

    Args:
        value: The option string value.
        options_type: A Literal type containing the possible options.

    Returns:
        Hex string representing the index (e.g., "0x02").
    """
    options = get_args(options_type)
    try:
        index = options.index(value)
        return f"0x{index:02x}"
    except ValueError:
        return "0x00"
