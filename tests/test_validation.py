"""Tests for validation.py field validation logic."""
import pytest
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from python_switchos.validation import validate_dataclass
from python_switchos.exceptions import ValidationError


# Test fixtures - dataclasses with specific metadata configurations


@dataclass
class StringFieldFixture:
    """Fixture for string validation tests."""
    name: str = field(metadata={"name": ["nm"], "type": "str", "writable": True})


@dataclass
class StringListFieldFixture:
    """Fixture for string list validation tests."""
    names: List[str] = field(metadata={"name": ["nm"], "type": "str", "writable": True})


@dataclass
class StringCustomLengthFixture:
    """Fixture for string with custom max_length."""
    name: str = field(metadata={"name": ["nm"], "type": "str", "writable": True, "max_length": 30})


@dataclass
class IntFieldFixture:
    """Fixture for integer validation tests."""
    value: int = field(metadata={"name": ["val"], "type": "int", "writable": True, "min": 0, "max": 100})


@dataclass
class IntListFieldFixture:
    """Fixture for integer list validation tests."""
    values: List[int] = field(metadata={"name": ["val"], "type": "int", "writable": True, "min": 0, "max": 100})


@dataclass
class IntNoConstraintsFixture:
    """Fixture for integer with no min/max constraints."""
    value: int = field(metadata={"name": ["val"], "type": "int", "writable": True})


ColorOption = Literal["red", "green", "blue"]


@dataclass
class OptionFieldFixture:
    """Fixture for option validation tests."""
    color: str = field(metadata={"name": ["clr"], "type": "option", "options": ColorOption, "writable": True})


@dataclass
class OptionListFieldFixture:
    """Fixture for option list validation tests."""
    colors: List[str] = field(metadata={"name": ["clr"], "type": "option", "options": ColorOption, "writable": True})


@dataclass
class OptionNoTypeFixture:
    """Fixture for option field without options type."""
    value: str = field(metadata={"name": ["val"], "type": "option", "writable": True})


@dataclass
class NonWritableFieldFixture:
    """Fixture with non-writable field."""
    readonly_name: str = field(metadata={"name": ["nm"], "type": "str", "writable": False})
    writable_name: str = field(metadata={"name": ["wn"], "type": "str", "writable": True})


@dataclass
class OptionalFieldFixture:
    """Fixture with optional fields."""
    name: Optional[str] = field(metadata={"name": ["nm"], "type": "str", "writable": True}, default=None)


# ============================================================================
# String Length Validation Tests
# ============================================================================


class TestStringValidation:
    """Tests for string field validation."""

    def test_string_within_limit(self):
        """String shorter than 15 bytes passes validation."""
        instance = StringFieldFixture(name="Port1")
        errors = validate_dataclass(instance)
        assert errors == []

    def test_string_at_limit(self):
        """String exactly 15 bytes passes validation."""
        instance = StringFieldFixture(name="123456789012345")  # 15 chars
        errors = validate_dataclass(instance)
        assert errors == []

    def test_string_over_limit(self):
        """String over 15 bytes fails with descriptive error."""
        instance = StringFieldFixture(name="1234567890123456")  # 16 chars
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "name:" in errors[0]
        assert "16 bytes" in errors[0]
        assert "max 15" in errors[0]

    def test_string_utf8_multibyte(self):
        """Multibyte UTF-8 characters count as multiple bytes."""
        # Japanese characters are typically 3 bytes each in UTF-8
        instance = StringFieldFixture(name="hello")  # 5 chars, 5 bytes - valid
        errors = validate_dataclass(instance)
        assert errors == []

        # 6 Japanese chars = 18 bytes, exceeds 15 byte limit
        instance = StringFieldFixture(name="\u3053\u3093\u306b\u3061\u306f\u4e16")
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "18 bytes" in errors[0]

    def test_string_list_validation(self):
        """Validates each element in string list."""
        instance = StringListFieldFixture(names=["Short", "ThisIsWayTooLong", "OK"])
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "names[1]:" in errors[0]

    def test_string_custom_max_length(self):
        """Respects custom max_length in metadata."""
        # 20 chars is under 30 byte limit
        instance = StringCustomLengthFixture(name="12345678901234567890")
        errors = validate_dataclass(instance)
        assert errors == []

        # 31 chars exceeds 30 byte limit
        instance = StringCustomLengthFixture(name="1234567890123456789012345678901")
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "max 30" in errors[0]


# ============================================================================
# Integer Range Validation Tests
# ============================================================================


class TestIntValidation:
    """Tests for integer field validation."""

    def test_int_within_range(self):
        """Value within [min, max] passes validation."""
        instance = IntFieldFixture(value=50)
        errors = validate_dataclass(instance)
        assert errors == []

    def test_int_at_min(self):
        """Value exactly at min passes validation."""
        instance = IntFieldFixture(value=0)
        errors = validate_dataclass(instance)
        assert errors == []

    def test_int_at_max(self):
        """Value exactly at max passes validation."""
        instance = IntFieldFixture(value=100)
        errors = validate_dataclass(instance)
        assert errors == []

    def test_int_below_min(self):
        """Value below min fails with descriptive error."""
        instance = IntFieldFixture(value=-1)
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "value:" in errors[0]
        assert "-1" in errors[0]
        assert "below minimum 0" in errors[0]

    def test_int_above_max(self):
        """Value above max fails with descriptive error."""
        instance = IntFieldFixture(value=101)
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "value:" in errors[0]
        assert "101" in errors[0]
        assert "above maximum 100" in errors[0]

    def test_int_list_validation(self):
        """Validates each element in integer list."""
        instance = IntListFieldFixture(values=[50, -5, 150, 75])
        errors = validate_dataclass(instance)
        assert len(errors) == 2
        assert "values[1]:" in errors[0]
        assert "below minimum" in errors[0]
        assert "values[2]:" in errors[1]
        assert "above maximum" in errors[1]

    def test_int_no_constraints(self):
        """Field with no min/max always passes."""
        instance = IntNoConstraintsFixture(value=999999)
        errors = validate_dataclass(instance)
        assert errors == []

        instance = IntNoConstraintsFixture(value=-999999)
        errors = validate_dataclass(instance)
        assert errors == []


# ============================================================================
# Option Validation Tests
# ============================================================================


class TestOptionValidation:
    """Tests for option (Literal) field validation."""

    def test_option_valid_value(self):
        """Value in Literal type passes validation."""
        instance = OptionFieldFixture(color="red")
        errors = validate_dataclass(instance)
        assert errors == []

    def test_option_invalid_value(self):
        """Value not in Literal type fails with descriptive error."""
        instance = OptionFieldFixture(color="yellow")
        errors = validate_dataclass(instance)
        assert len(errors) == 1
        assert "color:" in errors[0]
        assert "'yellow'" in errors[0]
        assert "not in" in errors[0]
        assert "red" in errors[0]

    def test_option_list_validation(self):
        """Validates each element in option list."""
        instance = OptionListFieldFixture(colors=["red", "purple", "blue", "orange"])
        errors = validate_dataclass(instance)
        assert len(errors) == 2
        assert "colors[1]:" in errors[0]
        assert "'purple'" in errors[0]
        assert "colors[3]:" in errors[1]
        assert "'orange'" in errors[1]

    def test_option_no_options_type(self):
        """Field without options type in metadata passes."""
        instance = OptionNoTypeFixture(value="anything")
        errors = validate_dataclass(instance)
        assert errors == []


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_none_value_skipped(self):
        """None values are not validated."""
        instance = OptionalFieldFixture(name=None)
        errors = validate_dataclass(instance)
        assert errors == []

    def test_non_writable_skipped(self):
        """Non-writable fields are skipped during validation."""
        # readonly_name is a 50 char string but writable=False, so not validated
        instance = NonWritableFieldFixture(
            readonly_name="ThisIsAVeryLongNameThatWouldNormallyFailValidation",
            writable_name="Short"
        )
        errors = validate_dataclass(instance)
        assert errors == []

    def test_empty_list_passes(self):
        """Empty list is considered valid."""
        instance = StringListFieldFixture(names=[])
        errors = validate_dataclass(instance)
        assert errors == []

        instance = IntListFieldFixture(values=[])
        errors = validate_dataclass(instance)
        assert errors == []

    def test_not_a_dataclass(self):
        """Non-dataclass returns error."""

        class NotADataclass:
            def __init__(self):
                self.value = 42

        instance = NotADataclass()
        errors = validate_dataclass(instance)
        assert errors == ["Not a dataclass"]


# ============================================================================
# Integration with Real Endpoints
# ============================================================================


class TestRealEndpoints:
    """Tests with actual endpoint classes."""

    def test_link_endpoint_valid(self):
        """LinkEndpoint with valid data passes validation."""
        from python_switchos.endpoints.link import LinkEndpoint

        link = LinkEndpoint(
            enabled=[True, False, True],
            name=["Port1", "Port2", "Uplink"]
        )
        errors = validate_dataclass(link)
        assert errors == []

    def test_link_endpoint_invalid_name(self):
        """LinkEndpoint with too-long name fails validation."""
        from python_switchos.endpoints.link import LinkEndpoint

        link = LinkEndpoint(
            enabled=[True],
            name=["ThisNameIsTooLongForSwOS"]
        )
        errors = validate_dataclass(link)
        assert len(errors) == 1
        assert "name[0]:" in errors[0]
        assert "24 bytes" in errors[0]

    def test_link_endpoint_invalid_option(self):
        """LinkEndpoint with invalid speed option fails validation."""
        from python_switchos.endpoints.link import LinkEndpoint

        link = LinkEndpoint(
            enabled=[True],
            name=["Port1"],
            man_speed=["50G"]  # Invalid speed
        )
        errors = validate_dataclass(link)
        assert len(errors) == 1
        assert "man_speed[0]:" in errors[0]
        assert "'50G'" in errors[0]
        assert "not in" in errors[0]
