"""Tests for PoEEndpoint pattern consistency (no fixture available for CSS610)."""

from dataclasses import fields

from python_switchos.endpoints.poe import PoEEndpoint


class TestPoEEndpointStructure:
    """Verify PoEEndpoint follows the same metadata patterns as other endpoints."""

    def test_is_dataclass(self):
        assert hasattr(PoEEndpoint, "__dataclass_fields__")

    def test_endpoint_path(self):
        assert PoEEndpoint.endpoint_path == "poe.b"

    def test_fields_have_required_metadata(self):
        for f in fields(PoEEndpoint):
            assert "name" in f.metadata, f"Field {f.name} missing 'name' metadata"
            assert "type" in f.metadata, f"Field {f.name} missing 'type' metadata"

    def test_name_metadata_is_list(self):
        for f in fields(PoEEndpoint):
            assert isinstance(f.metadata["name"], list), (
                f"Field {f.name} 'name' should be a list"
            )

    def test_name_metadata_has_aliases(self):
        for f in fields(PoEEndpoint):
            assert len(f.metadata["name"]) >= 1, (
                f"Field {f.name} needs at least one name alias"
            )

    def test_option_fields_have_options(self):
        for f in fields(PoEEndpoint):
            if f.metadata.get("type") == "option":
                assert "options" in f.metadata, (
                    f"Option field {f.name} missing 'options' metadata"
                )

    def test_scale_values_are_numeric(self):
        for f in fields(PoEEndpoint):
            if "scale" in f.metadata:
                assert isinstance(f.metadata["scale"], (int, float)), (
                    f"Field {f.name} scale should be numeric, "
                    f"got {type(f.metadata['scale'])}"
                )

    def test_has_expected_field_count(self):
        """PoEEndpoint should have 9 fields."""
        assert len(fields(PoEEndpoint)) == 9

    def test_type_values_are_valid(self):
        valid_types = {"bool", "int", "str", "option", "mac", "ip"}
        for f in fields(PoEEndpoint):
            assert f.metadata["type"] in valid_types, (
                f"Field {f.name} has unexpected type '{f.metadata['type']}'"
            )
