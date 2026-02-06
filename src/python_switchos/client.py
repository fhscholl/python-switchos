from typing import Any, Type, TypeVar
from aiohttp import ClientSession
from urllib.parse import urljoin

from python_switchos.endpoint import SwitchOSEndpoint, readDataclass, writeDataclass
from python_switchos.validation import validate_dataclass
from python_switchos.exceptions import SaveError, ValidationError
from python_switchos.http import HttpClient, createHttpClient

T = TypeVar("T", bound=SwitchOSEndpoint)

class Client:
    """Client to connect to the available endpoints"""
    host: str
    httpClient: HttpClient

    def __init__(self, httpClient: HttpClient, host: str):
        self.httpClient = httpClient
        self.host = host.rstrip("/") + "/"  # Make sure host ends with a single "/"

    async def fetch(self, cls: Type[T]) -> T:
        response = await self.httpClient.get(urljoin(self.host, cls.endpoint_path))
        async with response:
            response.raise_for_status()
            text = await response.text()
            return readDataclass(cls, text)

    async def save(self, endpoint: T, *, validate: bool = True, field_variant: int = 0) -> None:
        """Save endpoint configuration to device.

        Validates the endpoint data (unless disabled), serializes to wire format,
        and POSTs to the device.

        Args:
            endpoint: Endpoint instance with modified values.
            validate: If True (default), run validation before POST.
                      Set to False to skip validation (e.g., for testing).
            field_variant: Which field name variant to use for serialization.
                           0 = SwOS Full names (en, nm, etc.)
                           1 = SwOS Lite names (i01, i0a, etc.)

        Raises:
            ValueError: If endpoint is a read-only endpoint.
            ValidationError: If validation fails (when validate=True).
            SaveError: If POST fails (non-200 status).

        Example:
            link = await client.fetch(LinkEndpoint)
            link.name[0] = "NewName"
            await client.save(link)
        """
        cls = type(endpoint)

        # Check endpoint-level read-only
        if hasattr(cls, 'endpoint_readonly') and cls.endpoint_readonly:
            raise ValueError(f"{cls.__name__} is a read-only endpoint")

        # Pre-flight validation
        if validate:
            errors = validate_dataclass(endpoint)
            if errors:
                raise ValidationError(errors)

        # Serialize to wire format
        body = writeDataclass(endpoint, field_variant)

        # POST to device
        url = urljoin(self.host, cls.endpoint_path)
        response = await self.httpClient.post(url, body)
        async with response:
            if response.status != 200:
                text = await response.text()
                raise SaveError(response.status, text, url, cls.__name__)
