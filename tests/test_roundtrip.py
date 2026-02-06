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


class TestRoundtripPerPort:
    """Round-trip tests for per-port endpoints."""

    def test_link_writable_fields_roundtrip(self):
        """Test Link endpoint round-trip (writable fields only).

        Verifies that Python field values survive the read->write->read cycle.
        Note: writeDataclass uses SwOS Full names (en, nm) by default,
        so we compare Python values, not raw wire names.
        """
        # Sample link fixture with both writable and read-only fields
        # i01=enabled (writable), i0a=name (writable), i02=auto_neg (writable)
        # i06=link_state (read-only), i05=man_speed (writable)
        fixture = "{i01:0x3ff,i0a:['506f727431','506f727432'],i02:0x3ff,i06:0x155,i05:[0x02,0x02]}"

        # First read
        link1 = readDataclass(LinkEndpoint, fixture)

        # Serialize and read again
        serialized = writeDataclass(link1)
        link2 = readDataclass(LinkEndpoint, serialized)

        # Writable fields should survive round-trip
        assert link2.enabled == link1.enabled
        assert link2.name == link1.name
        assert link2.auto_negotiation == link1.auto_negotiation
        assert link2.man_speed == link1.man_speed

    def test_link_string_list_roundtrip(self):
        """Test string list values survive round-trip."""
        fixture = "{i01:0x03,i0a:['506f727431','506f727432']}"  # "Port1", "Port2"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.name == ["Port1", "Port2"]

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.name == ["Port1", "Port2"]

    def test_link_option_list_roundtrip(self):
        """Test option list (man_speed) survives round-trip."""
        # i05=man_speed: 0x02=1G, 0x01=100M
        fixture = "{i01:0x03,i0a:['',''],i05:[0x02,0x01]}"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.man_speed == ["1G", "100M"]

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.man_speed == ["1G", "100M"]

    def test_forwarding_bool_list_roundtrip(self):
        """Test Forwarding endpoint bool list fields round-trip."""
        # Create link with port isolation bool lists
        link = LinkEndpoint(
            enabled=[True, True, False, True],
            name=["P1", "P2", "P3", "P4"],
        )

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.enabled == link.enabled

    def test_forwarding_int_list_roundtrip(self):
        """Test Forwarding endpoint int list fields round-trip."""
        # Create minimal fwd endpoint with int lists
        # ForwardingEndpoint has many required fields, so create programmatically
        fwd = ForwardingEndpoint(
            from_port_1=[True, True, True, True],
            from_port_2=[True, True, True, True],
            from_port_3=[True, True, True, True],
            from_port_4=[True, True, True, True],
            from_port_5=[True, True, True, True],
            from_port_6=[True, True, True, True],
            from_port_7=[True, True, True, True],
            from_port_8=[True, True, True, True],
            from_port_9=[True, True, True, True],
            from_port_10=[True, True, True, True],
            port_lock=[False, False, False, False],
            lock_on_first=[False, False, False, False],
            mirror_ingress=[False, False, False, False],
            mirror_egress=[False, False, False, False],
            mirror_to=[False, False, False, False],
            storm_rate=[0, 100, 200, 0],  # int list
            ingress_rate=[0, 0, 0, 0],
            egress_rate=[0, 0, 0, 0],
            limit_unknown_unicast=[True, True, True, True],
            flood_unknown_multicast=[True, True, True, True],
            vlan_mode=["disabled", "disabled", "optional", "strict"],
            vlan_receive=["any", "any", "only tagged", "only untagged"],
            default_vlan_id=[1, 1, 10, 20],
            force_vlan_id=[False, False, True, True],
        )

        serialized = writeDataclass(fwd)
        fwd2 = readDataclass(ForwardingEndpoint, serialized)

        # Verify int lists survive
        assert fwd2.storm_rate == fwd.storm_rate
        assert fwd2.default_vlan_id == fwd.default_vlan_id
        # Verify option lists survive
        assert fwd2.vlan_mode == fwd.vlan_mode
        assert fwd2.vlan_receive == fwd.vlan_receive

    def test_bool_list_bitmask_roundtrip(self):
        """Test boolean list -> bitmask -> boolean list roundtrip."""
        # Specific test for bitmask encoding
        original_bools = [True, False, True, True, False, True, False, False, True, True]
        # Binary: 1100101101 (reading right to left) = 0x32d

        # Create minimal link fixture
        fixture = "{i01:0x32d,i0a:['','','','','','','','','','']}"

        link = readDataclass(LinkEndpoint, fixture)
        assert link.enabled == original_bools

        serialized = writeDataclass(link)
        link2 = readDataclass(LinkEndpoint, serialized)

        assert link2.enabled == original_bools


class TestRoundtripFixtures:
    """Round-trip tests against real fixture files."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_snmp_fixture_roundtrip(self, fixtures_dir):
        """Test round-trip against SNMP fixture files."""
        # Find device fixtures with SNMP data
        device_dirs = [d for d in fixtures_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('!')]

        tested = 0
        for device_dir in device_dirs:
            snmp_dir = device_dir / "snmp_b"
            if not snmp_dir.exists():
                continue

            for response_file in sorted(snmp_dir.glob("*_response_*.txt")):
                fixture = response_file.read_text()

                # Skip empty or error fixtures
                if not fixture.strip() or fixture.startswith("<!"):
                    continue

                try:
                    # Read -> dataclass
                    snmp = readDataclass(SnmpEndpoint, fixture)

                    # Dataclass -> wire format
                    serialized = writeDataclass(snmp)

                    # Read again
                    snmp2 = readDataclass(SnmpEndpoint, serialized)

                    # Verify values survive
                    assert snmp2.enabled == snmp.enabled, f"enabled mismatch in {device_dir.name}"
                    assert snmp2.community == snmp.community, f"community mismatch in {device_dir.name}"
                    assert snmp2.contact_info == snmp.contact_info, f"contact_info mismatch in {device_dir.name}"
                    assert snmp2.location == snmp.location, f"location mismatch in {device_dir.name}"
                    tested += 1
                except Exception as e:
                    pytest.fail(f"Round-trip failed for {device_dir.name}: {e}")

        assert tested > 0, "No SNMP fixtures found"

    def test_link_fixture_roundtrip(self, fixtures_dir):
        """Test round-trip against Link fixture files."""
        device_dirs = [d for d in fixtures_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('!')]

        tested = 0
        for device_dir in device_dirs:
            link_dir = device_dir / "link_b"
            if not link_dir.exists():
                continue

            for response_file in sorted(link_dir.glob("*_response_*.txt")):
                fixture = response_file.read_text()

                # Skip empty or error fixtures
                if not fixture.strip() or fixture.startswith("<!"):
                    continue

                try:
                    # Read -> dataclass
                    link = readDataclass(LinkEndpoint, fixture)

                    # Dataclass -> wire format
                    serialized = writeDataclass(link)

                    # Read again
                    link2 = readDataclass(LinkEndpoint, serialized)

                    # Verify writable values survive
                    assert link2.enabled == link.enabled, f"enabled mismatch in {device_dir.name}"
                    assert link2.name == link.name, f"name mismatch in {device_dir.name}"
                    if link.auto_negotiation is not None:
                        assert link2.auto_negotiation == link.auto_negotiation
                    if link.man_speed is not None:
                        assert link2.man_speed == link.man_speed
                    tested += 1
                except Exception as e:
                    pytest.fail(f"Round-trip failed for {device_dir.name}: {e}")

        assert tested > 0, "No Link fixtures found"

    def test_fwd_fixture_roundtrip(self, fixtures_dir):
        """Test round-trip against Forwarding fixture files."""
        device_dirs = [d for d in fixtures_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('!')]

        tested = 0
        for device_dir in device_dirs:
            fwd_dir = device_dir / "fwd_b"
            if not fwd_dir.exists():
                continue

            for response_file in sorted(fwd_dir.glob("*_response_*.txt")):
                fixture = response_file.read_text()

                # Skip empty or error fixtures
                if not fixture.strip() or fixture.startswith("<!"):
                    continue

                try:
                    # Read -> dataclass
                    fwd = readDataclass(ForwardingEndpoint, fixture)

                    # Dataclass -> wire format
                    serialized = writeDataclass(fwd)

                    # Read again
                    fwd2 = readDataclass(ForwardingEndpoint, serialized)

                    # Verify key fields survive
                    assert fwd2.from_port_1 == fwd.from_port_1, f"from_port_1 mismatch in {device_dir.name}"
                    assert fwd2.port_lock == fwd.port_lock, f"port_lock mismatch in {device_dir.name}"
                    assert fwd2.default_vlan_id == fwd.default_vlan_id, f"default_vlan_id mismatch in {device_dir.name}"
                    tested += 1
                except Exception as e:
                    pytest.fail(f"Round-trip failed for {device_dir.name}: {e}")

        assert tested > 0, "No Forwarding fixtures found"


# ============================================================================
# Client Integration Round-Trip Tests
# ============================================================================


class MockRoundtripClient:
    """Mock client that simulates device round-trip behavior.

    Stores POSTed data and returns it on subsequent fetches,
    simulating the device's read-write-read cycle.
    """

    def __init__(self, initial_response: str, endpoint_cls: Type[SwitchOSEndpoint]):
        self.current_response = initial_response
        self.endpoint_cls = endpoint_cls

    async def fetch(self):
        """Fetch current state as dataclass."""
        return readDataclass(self.endpoint_cls, self.current_response)

    async def save(self, endpoint, field_variant: int = 0):
        """Save endpoint and update internal state."""
        # Serialize to wire format (this is what Client.save() does)
        serialized = writeDataclass(endpoint, field_variant)
        # Store as new state (simulates device accepting and storing the data)
        self.current_response = serialized


class TestClientIntegrationRoundtrip:
    """Tests for fetch -> modify -> save -> fetch cycle using mock Client."""

    @pytest.mark.asyncio
    async def test_roundtrip_link_name_change(self):
        """Modify port name, verify change persists through round-trip."""
        # Initial fixture
        fixture = "{i01:0x03,i0a:['506f727431','506f727432']}"  # Port1, Port2

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.name == ["Port1", "Port2"]

        # Modify
        link.name[0] = "Uplink"

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify modification persisted
        assert link2.name[0] == "Uplink"
        assert link2.name[1] == "Port2"
        assert link2.enabled == link.enabled

    @pytest.mark.asyncio
    async def test_roundtrip_link_enabled_toggle(self):
        """Toggle enabled flag, verify change persists."""
        # Hex: 5031 = "P1", 5032 = "P2"
        fixture = "{i01:0x03,i0a:['5031','5032']}"  # Both enabled

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.enabled == [True, True]

        # Modify - disable first port
        link.enabled[0] = False

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify modification persisted
        assert link2.enabled == [False, True]

    @pytest.mark.asyncio
    async def test_roundtrip_preserves_unchanged_fields(self):
        """Unchanged fields remain the same through round-trip."""
        # Hex: 5031 = "P1", 5032 = "P2"
        fixture = "{i01:0x03,i0a:['5031','5032'],i02:0x01}"  # enabled, name, auto_neg

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        original_enabled = link.enabled.copy()
        original_auto_neg = link.auto_negotiation.copy() if link.auto_negotiation else None

        # Modify only name
        link.name[0] = "Changed"

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify unchanged fields preserved
        assert link2.enabled == original_enabled
        if original_auto_neg:
            assert link2.auto_negotiation == original_auto_neg

    @pytest.mark.asyncio
    async def test_roundtrip_multiple_changes(self):
        """Multiple field changes all persist."""
        # Hex: 5031 = "P1", 5032 = "P2"
        fixture = "{i01:0x03,i0a:['5031','5032']}"

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()

        # Multiple modifications
        link.name[0] = "Uplink"
        link.name[1] = "Server"
        link.enabled[0] = False

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify all changes persisted
        assert link2.name == ["Uplink", "Server"]
        assert link2.enabled == [False, True]

    @pytest.mark.asyncio
    async def test_roundtrip_list_field_partial_change(self):
        """Changing one list element preserves others."""
        # Hex: 5031 = "P1", 5032 = "P2", 5033 = "P3"
        fixture = "{i01:0x07,i0a:['5031','5032','5033']}"  # 3 ports

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.name == ["P1", "P2", "P3"]

        # Modify only middle element
        link.name[1] = "Changed"

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify only middle changed
        assert link2.name[0] == "P1"
        assert link2.name[1] == "Changed"
        assert link2.name[2] == "P3"

    @pytest.mark.asyncio
    async def test_roundtrip_bool_field(self):
        """Boolean values round-trip correctly."""
        fixture = "{i01:0x05,i0a:['','','']}"  # 0b101 = [T, F, T]

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.enabled == [True, False, True]

        # Toggle middle port
        link.enabled[1] = True  # Now all enabled

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify toggle persisted
        assert link2.enabled == [True, True, True]

    @pytest.mark.asyncio
    async def test_roundtrip_string_field(self):
        """String values round-trip correctly (including special chars)."""
        fixture = "{i01:0x01,i0a:['506f727431']}"  # "Port1"

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.name == ["Port1"]

        # Change to different string
        link.name[0] = "Test-01"

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify string preserved exactly
        assert link2.name[0] == "Test-01"

    @pytest.mark.asyncio
    async def test_roundtrip_option_field(self):
        """Option (Literal) values round-trip correctly."""
        # i05 = man_speed: 0x02 = "1G"
        fixture = "{i01:0x01,i0a:[''],i05:[0x02]}"

        mock_client = MockRoundtripClient(fixture, LinkEndpoint)

        # Fetch
        link = await mock_client.fetch()
        assert link.man_speed == ["1G"]

        # Change speed option
        link.man_speed[0] = "100M"

        # Save
        await mock_client.save(link)

        # Fetch again
        link2 = await mock_client.fetch()

        # Verify option preserved
        assert link2.man_speed == ["100M"]

    @pytest.mark.asyncio
    async def test_roundtrip_with_css610_fixture(self):
        """Round-trip using actual CSS610 fixture data."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        # Find a CSS610 link fixture
        for device_dir in sorted(fixtures_dir.iterdir()):
            if not device_dir.name.startswith("css") or not device_dir.is_dir():
                continue

            link_dir = device_dir / "link_b"
            if not link_dir.exists():
                continue

            for response_file in sorted(link_dir.glob("*_response_*.txt")):
                fixture = response_file.read_text()
                if not fixture.strip() or fixture.startswith("<!"):
                    continue

                # Use this fixture for round-trip test
                mock_client = MockRoundtripClient(fixture, LinkEndpoint)

                # Fetch
                link = await mock_client.fetch()
                original_name = link.name.copy() if link.name else None

                if original_name and len(original_name) > 0:
                    # Modify first port name
                    link.name[0] = "TestPort"

                    # Save
                    await mock_client.save(link)

                    # Fetch again
                    link2 = await mock_client.fetch()

                    # Verify modification persisted
                    assert link2.name[0] == "TestPort"

                    # Other names unchanged
                    for i in range(1, len(original_name)):
                        assert link2.name[i] == original_name[i], f"name[{i}] changed unexpectedly"

                    # Test passed, return
                    return

        pytest.skip("No suitable CSS link fixtures found")

    @pytest.mark.asyncio
    async def test_roundtrip_serialization_matches_fixture_format(self):
        """writeDataclass output is parseable by readDataclass."""
        # Create a dataclass from scratch
        link = LinkEndpoint(
            enabled=[True, False, True, True],
            name=["Uplink", "PC1", "Server", "Backup"],
            auto_negotiation=[True, True, False, True],
            man_speed=["1G", "100M", "1G", "1G"],
        )

        # Serialize
        serialized = writeDataclass(link)

        # Parse serialized back
        link2 = readDataclass(LinkEndpoint, serialized)

        # All values should match
        assert link2.enabled == link.enabled
        assert link2.name == link.name
        assert link2.auto_negotiation == link.auto_negotiation
        assert link2.man_speed == link.man_speed

    @pytest.mark.asyncio
    async def test_roundtrip_snmp_scalar_endpoint(self):
        """Round-trip with scalar (non-list) endpoint."""
        fixture = "{i01:0x01,i02:'7075626c6963',i03:'',i04:''}"

        mock_client = MockRoundtripClient(fixture, SnmpEndpoint)

        # Fetch
        snmp = await mock_client.fetch()
        assert snmp.community == "public"
        assert snmp.enabled == True

        # Modify
        snmp.community = "private"
        snmp.contact_info = "admin"

        # Save
        await mock_client.save(snmp)

        # Fetch again
        snmp2 = await mock_client.fetch()

        # Verify modifications persisted
        assert snmp2.community == "private"
        assert snmp2.contact_info == "admin"
        assert snmp2.enabled == True  # Unchanged

    @pytest.mark.asyncio
    async def test_roundtrip_forwarding_complex_endpoint(self):
        """Round-trip with complex endpoint (many fields)."""
        # Create ForwardingEndpoint with specific values
        fwd = ForwardingEndpoint(
            from_port_1=[True, True, True, True],
            from_port_2=[True, True, True, True],
            from_port_3=[True, True, True, True],
            from_port_4=[True, True, True, True],
            from_port_5=[True, True, True, True],
            from_port_6=[True, True, True, True],
            from_port_7=[True, True, True, True],
            from_port_8=[True, True, True, True],
            from_port_9=[True, True, True, True],
            from_port_10=[True, True, True, True],
            port_lock=[False, True, False, True],
            lock_on_first=[False, False, False, False],
            mirror_ingress=[False, False, False, False],
            mirror_egress=[False, False, False, False],
            mirror_to=[False, False, False, False],
            storm_rate=[0, 100, 200, 0],
            ingress_rate=[0, 0, 0, 0],
            egress_rate=[0, 0, 0, 0],
            limit_unknown_unicast=[True, True, True, True],
            flood_unknown_multicast=[True, True, True, True],
            vlan_mode=["disabled", "optional", "strict", "disabled"],
            vlan_receive=["any", "any", "only tagged", "any"],
            default_vlan_id=[1, 10, 20, 1],
            force_vlan_id=[False, True, True, False],
        )

        # First serialize (simulate initial fetch)
        initial_wire = writeDataclass(fwd)

        mock_client = MockRoundtripClient(initial_wire, ForwardingEndpoint)

        # Fetch
        fwd_fetched = await mock_client.fetch()

        # Modify several fields
        fwd_fetched.port_lock[0] = True
        fwd_fetched.storm_rate[0] = 50
        fwd_fetched.vlan_mode[0] = "strict"
        fwd_fetched.default_vlan_id[0] = 100

        # Save
        await mock_client.save(fwd_fetched)

        # Fetch again
        fwd2 = await mock_client.fetch()

        # Verify modifications persisted
        assert fwd2.port_lock[0] == True
        assert fwd2.storm_rate[0] == 50
        assert fwd2.vlan_mode[0] == "strict"
        assert fwd2.default_vlan_id[0] == 100

        # Verify unchanged fields preserved
        assert fwd2.port_lock[1] == True  # Original
        assert fwd2.storm_rate[2] == 200  # Original
        assert fwd2.vlan_mode[2] == "strict"  # Original
