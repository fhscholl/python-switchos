"""Field validation for SwitchOS endpoint dataclasses."""
from dataclasses import fields, is_dataclass
from typing import Any, List, get_args


def validate_dataclass(instance: Any) -> List[str]:
    """Validate all writable fields against metadata constraints.

    Args:
        instance: A SwitchOS endpoint dataclass instance.

    Returns:
        List of validation error strings. Empty list if valid.

    Validates:
        - String fields: max_length (default 15 for SwOS Lite compatibility)
        - Integer fields: min, max bounds
        - Option fields: value must be in Literal type options
        - List fields: validates each element
    """
    if not is_dataclass(instance):
        return ["Not a dataclass"]

    errors: List[str] = []
    cls = type(instance)

    for f in fields(cls):
        metadata = f.metadata
        if not metadata:
            continue

        # Skip non-writable fields
        if not metadata.get("writable", True):
            continue

        # Get field value
        value = getattr(instance, f.name)
        if value is None:
            continue

        field_type = metadata.get("type")
        if field_type is None:
            continue

        # Validate based on field type
        if field_type == "str":
            errors.extend(_validate_str(f.name, value, metadata))
        elif field_type == "int":
            errors.extend(_validate_int(f.name, value, metadata))
        elif field_type == "option":
            errors.extend(_validate_option(f.name, value, metadata))

    return errors


def _validate_str(field_name: str, value: Any, metadata: dict) -> List[str]:
    """Validate string field(s) against max_length constraint.

    Uses UTF-8 byte length, defaulting to 15 bytes for SwOS Lite compatibility.
    """
    errors: List[str] = []
    max_length = metadata.get("max_length", 15)

    if isinstance(value, list):
        for i, v in enumerate(value):
            if not isinstance(v, str):
                continue
            byte_len = len(v.encode("utf-8"))
            if byte_len > max_length:
                truncated = v[:20] + "..." if len(v) > 20 else v
                errors.append(
                    f"{field_name}[{i}]: '{truncated}' is {byte_len} bytes, max {max_length}"
                )
    else:
        if isinstance(value, str):
            byte_len = len(value.encode("utf-8"))
            if byte_len > max_length:
                truncated = value[:20] + "..." if len(value) > 20 else value
                errors.append(
                    f"{field_name}: '{truncated}' is {byte_len} bytes, max {max_length}"
                )

    return errors


def _validate_int(field_name: str, value: Any, metadata: dict) -> List[str]:
    """Validate integer field(s) against min/max constraints."""
    errors: List[str] = []
    min_val = metadata.get("min")
    max_val = metadata.get("max")

    # If no constraints, nothing to validate
    if min_val is None and max_val is None:
        return errors

    if isinstance(value, list):
        for i, v in enumerate(value):
            if not isinstance(v, (int, float)):
                continue
            if min_val is not None and v < min_val:
                errors.append(f"{field_name}[{i}]: {v} below minimum {min_val}")
            if max_val is not None and v > max_val:
                errors.append(f"{field_name}[{i}]: {v} above maximum {max_val}")
    else:
        if isinstance(value, (int, float)):
            if min_val is not None and value < min_val:
                errors.append(f"{field_name}: {value} below minimum {min_val}")
            if max_val is not None and value > max_val:
                errors.append(f"{field_name}: {value} above maximum {max_val}")

    return errors


def _validate_option(field_name: str, value: Any, metadata: dict) -> List[str]:
    """Validate option field(s) against Literal type options."""
    errors: List[str] = []
    options_type = metadata.get("options")

    if options_type is None:
        return errors

    valid_options = get_args(options_type)
    if not valid_options:
        return errors

    if isinstance(value, list):
        for i, v in enumerate(value):
            if v not in valid_options:
                errors.append(f"{field_name}[{i}]: '{v}' not in {list(valid_options)}")
    else:
        if value not in valid_options:
            errors.append(f"{field_name}: '{value}' not in {list(valid_options)}")

    return errors
