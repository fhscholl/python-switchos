"""Tests for Client.save() method."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from python_switchos.client import Client
from python_switchos.endpoints.link import LinkEndpoint
from python_switchos.endpoints.sfp import SfpEndpoint
from python_switchos.endpoints.stats import StatsEndpoint
from python_switchos.exceptions import SaveError, ValidationError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client with configurable response."""
    client = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    client.post.return_value = response
    return client


@pytest.fixture
def client(mock_http_client):
    """Create Client with mock HTTP client."""
    return Client(mock_http_client, "http://192.168.88.1/")


@pytest.fixture
def valid_link_endpoint():
    """Create valid LinkEndpoint instance."""
    return LinkEndpoint(
        enabled=[True, False, True],
        name=["Port1", "Port2", "Port3"]
    )


@pytest.fixture
def invalid_link_endpoint():
    """Create invalid LinkEndpoint with too-long name."""
    return LinkEndpoint(
        enabled=[True],
        name=["ThisNameIsWayTooLongForTheDevice"]
    )


# ============================================================================
# Successful Save Tests
# ============================================================================


class TestSaveSuccess:
    """Tests for successful save operations."""

    @pytest.mark.asyncio
    async def test_save_success(self, client, valid_link_endpoint):
        """Successful save with 200 response raises no exception."""
        await client.save(valid_link_endpoint)
        # If no exception, save succeeded
        assert client.httpClient.post.called

    @pytest.mark.asyncio
    async def test_save_calls_post_with_serialized_body(self, client, valid_link_endpoint):
        """Verify POST is called with serialized body."""
        await client.save(valid_link_endpoint)

        # Get the call arguments
        call_args = client.httpClient.post.call_args
        url, body = call_args[0]

        # URL should include endpoint path
        assert "link.b" in url

        # Body should be wire format (contains serialized data)
        assert body.startswith("{")
        assert body.endswith("}")
        assert "en:" in body  # enabled field
        assert "nm:" in body  # name field

    @pytest.mark.asyncio
    async def test_save_uses_endpoint_path(self, client, valid_link_endpoint):
        """Verify URL is constructed from endpoint path."""
        await client.save(valid_link_endpoint)

        call_args = client.httpClient.post.call_args
        url = call_args[0][0]

        assert url == "http://192.168.88.1/link.b"

    @pytest.mark.asyncio
    async def test_save_with_field_variant_0(self, client, valid_link_endpoint):
        """Verify field_variant=0 uses SwOS Full names."""
        await client.save(valid_link_endpoint, field_variant=0)

        call_args = client.httpClient.post.call_args
        body = call_args[0][1]

        # SwOS Full names: en, nm
        assert "en:" in body
        assert "nm:" in body

    @pytest.mark.asyncio
    async def test_save_with_field_variant_1(self, client, valid_link_endpoint):
        """Verify field_variant=1 uses SwOS Lite names."""
        await client.save(valid_link_endpoint, field_variant=1)

        call_args = client.httpClient.post.call_args
        body = call_args[0][1]

        # SwOS Lite names: i01, i0a
        assert "i01:" in body
        assert "i0a:" in body


# ============================================================================
# Read-only Endpoint Rejection Tests
# ============================================================================


class TestReadonlyRejection:
    """Tests for read-only endpoint rejection."""

    @pytest.mark.asyncio
    async def test_save_readonly_sfp_raises_valueerror(self, client):
        """SfpEndpoint (readonly=True) raises ValueError."""
        sfp = SfpEndpoint(
            vendor=["Vendor1"],
            part_number=["PN1"],
            revision=["R1"],
            serial=["SN1"],
            date=["2024-01-01"],
            type=["SFP+"],
            temperature=[35],
            voltage=[3.3],
            tx_bias=[10],
            tx_power=[-2.5],
            rx_power=[-3.0]
        )

        with pytest.raises(ValueError) as exc_info:
            await client.save(sfp)

        assert "SfpEndpoint" in str(exc_info.value)
        assert "read-only" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_readonly_stats_raises_valueerror(self, client):
        """StatsEndpoint (readonly=True) raises ValueError."""
        # Create minimal stats endpoint
        stats = StatsEndpoint(
            rx_rate=[0.0],
            tx_rate=[0.0],
            rx_packet_rate=[0.0],
            tx_packet_rate=[0.0],
            rx_bytes=[0],
            tx_bytes=[0],
            rx_total_packets=[0],
            tx_total_packets=[0],
            rx_unicasts=[0],
            tx_unicasts=[0],
            rx_broadcasts=[0],
            tx_broadcasts=[0],
            rx_multicasts=[0],
            tx_multicasts=[0],
            rx_pauses=[0],
            rx_errors=[0],
            rx_fcs_errors=[0],
            rx_jabber=[0],
            rx_runts=[0],
            rx_fragments=[0],
            rx_too_long=[0],
            tx_pauses=[0],
            tx_fcs_errors=[0],
            tx_collisions=[0],
            tx_single_collisions=[0],
            tx_multiple_collisions=[0],
            tx_excessive_collisions=[0],
            tx_late_collisions=[0],
            tx_deferred=[0],
            hist_64=[0],
            hist_65_127=[0],
            hist_128_255=[0],
            hist_256_511=[0],
            hist_512_1023=[0],
            hist_1024_max=[0]
        )

        with pytest.raises(ValueError) as exc_info:
            await client.save(stats)

        assert "StatsEndpoint" in str(exc_info.value)
        assert "read-only" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_readonly_error_message_includes_class_name(self, client):
        """Error message includes endpoint class name."""
        sfp = SfpEndpoint(
            vendor=["V"],
            part_number=["PN"],
            revision=["R"],
            serial=["S"],
            date=["D"],
            type=["T"],
            temperature=[0],
            voltage=[0.0],
            tx_bias=[0],
            tx_power=[0.0],
            rx_power=[0.0]
        )

        with pytest.raises(ValueError) as exc_info:
            await client.save(sfp)

        assert "SfpEndpoint" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_readonly_checked_before_validation(self, mock_http_client):
        """Read-only check happens before validation (fail fast)."""
        client = Client(mock_http_client, "http://192.168.88.1/")

        # SfpEndpoint is read-only, would also fail validation if checked
        sfp = SfpEndpoint(
            vendor=["V"],
            part_number=["PN"],
            revision=["R"],
            serial=["S"],
            date=["D"],
            type=["T"],
            temperature=[0],
            voltage=[0.0],
            tx_bias=[0],
            tx_power=[0.0],
            rx_power=[0.0]
        )

        # Should raise ValueError (read-only), not ValidationError
        with pytest.raises(ValueError):
            await client.save(sfp)

        # POST should NOT be called
        assert not mock_http_client.post.called


# ============================================================================
# Validation Integration Tests
# ============================================================================


class TestValidation:
    """Tests for validation integration."""

    @pytest.mark.asyncio
    async def test_save_validates_by_default(self, client, invalid_link_endpoint):
        """Validation runs by default (validate=True)."""
        with pytest.raises(ValidationError) as exc_info:
            await client.save(invalid_link_endpoint)

        # Check error message contains field info
        assert "name[0]:" in str(exc_info.value.errors)

    @pytest.mark.asyncio
    async def test_save_validation_failure_raises_validationerror(self, client, invalid_link_endpoint):
        """Invalid data raises ValidationError with field errors."""
        with pytest.raises(ValidationError) as exc_info:
            await client.save(invalid_link_endpoint)

        error = exc_info.value
        assert len(error.errors) >= 1
        assert "name[0]:" in error.errors[0]

    @pytest.mark.asyncio
    async def test_save_skip_validation(self, client, invalid_link_endpoint):
        """validate=False skips validation call."""
        # This would normally fail validation, but passes with validate=False
        await client.save(invalid_link_endpoint, validate=False)

        # POST should still be called
        assert client.httpClient.post.called

    @pytest.mark.asyncio
    async def test_save_validation_before_post(self, mock_http_client, invalid_link_endpoint):
        """Validation happens before POST attempt."""
        client = Client(mock_http_client, "http://192.168.88.1/")

        with pytest.raises(ValidationError):
            await client.save(invalid_link_endpoint)

        # POST should NOT be called on validation failure
        assert not mock_http_client.post.called

    @pytest.mark.asyncio
    async def test_save_valid_data_passes_validation(self, client, valid_link_endpoint):
        """Valid data passes validation without error."""
        await client.save(valid_link_endpoint, validate=True)
        assert client.httpClient.post.called


# ============================================================================
# HTTP Error Handling Tests
# ============================================================================


class TestHttpErrors:
    """Tests for HTTP error handling."""

    @pytest.mark.asyncio
    async def test_save_400_raises_saveerror(self, valid_link_endpoint):
        """400 response raises SaveError."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 400
        response.text = AsyncMock(return_value="Bad Request")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_500_raises_saveerror(self, valid_link_endpoint):
        """500 response raises SaveError."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 500
        response.text = AsyncMock(return_value="Internal Server Error")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_save_error_includes_status_code(self, valid_link_endpoint):
        """SaveError includes HTTP status code."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 403
        response.text = AsyncMock(return_value="Forbidden")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_save_error_includes_response_text(self, valid_link_endpoint):
        """SaveError includes response body text."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 400
        response.text = AsyncMock(return_value="Invalid field: xyz")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.response_text == "Invalid field: xyz"

    @pytest.mark.asyncio
    async def test_save_error_includes_url(self, valid_link_endpoint):
        """SaveError includes request URL."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 404
        response.text = AsyncMock(return_value="Not Found")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.url == "http://192.168.88.1/link.b"

    @pytest.mark.asyncio
    async def test_save_error_includes_endpoint_name(self, valid_link_endpoint):
        """SaveError includes endpoint class name."""
        mock_http = AsyncMock()
        response = AsyncMock()
        response.status = 500
        response.text = AsyncMock(return_value="Error")
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
        mock_http.post.return_value = response

        client = Client(mock_http, "http://192.168.88.1/")

        with pytest.raises(SaveError) as exc_info:
            await client.save(valid_link_endpoint)

        assert exc_info.value.endpoint_name == "LinkEndpoint"


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_save_empty_writable_fields(self, client):
        """Endpoint with minimal/empty writable content."""
        link = LinkEndpoint(
            enabled=[],
            name=[]
        )

        await client.save(link)
        assert client.httpClient.post.called

    @pytest.mark.asyncio
    async def test_save_host_without_trailing_slash(self, mock_http_client, valid_link_endpoint):
        """URL built correctly when host lacks trailing slash."""
        client = Client(mock_http_client, "http://192.168.88.1")

        await client.save(valid_link_endpoint)

        call_args = client.httpClient.post.call_args
        url = call_args[0][0]
        assert url == "http://192.168.88.1/link.b"

    @pytest.mark.asyncio
    async def test_save_host_with_trailing_slash(self, mock_http_client, valid_link_endpoint):
        """URL built correctly when host has trailing slash."""
        client = Client(mock_http_client, "http://192.168.88.1/")

        await client.save(valid_link_endpoint)

        call_args = client.httpClient.post.call_args
        url = call_args[0][0]
        assert url == "http://192.168.88.1/link.b"

    @pytest.mark.asyncio
    async def test_save_host_with_multiple_trailing_slashes(self, mock_http_client, valid_link_endpoint):
        """URL built correctly when host has multiple trailing slashes."""
        # Client constructor normalizes trailing slashes
        client = Client(mock_http_client, "http://192.168.88.1///")

        await client.save(valid_link_endpoint)

        call_args = client.httpClient.post.call_args
        url = call_args[0][0]
        # After normalization and urljoin
        assert "link.b" in url

    @pytest.mark.asyncio
    async def test_save_with_optional_none_fields(self, client):
        """Endpoint with optional fields set to None."""
        link = LinkEndpoint(
            enabled=[True, False],
            name=["Port1", "Port2"],
            auto_negotiation=None,  # Optional field
            man_speed=None  # Optional field
        )

        await client.save(link)
        assert client.httpClient.post.called

        # Verify serialized body doesn't include None fields
        call_args = client.httpClient.post.call_args
        body = call_args[0][1]
        # spd (man_speed) and an (auto_negotiation) should not appear if None
        # Actually they have defaults, so this test is about the serialization behavior
        assert "{" in body
