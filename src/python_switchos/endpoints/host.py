from dataclasses import dataclass, field
from typing import List
from python_switchos.endpoint import SwitchOSDataclass, SwitchOSEndpoint, endpoint


@dataclass
class HostEntry(SwitchOSDataclass):
    """Represents a single entry in the static or dynamic host table.

    Fields:
        port: The switch port number (0-indexed)
        mac: MAC address in AA:BB:CC:DD:EE:FF format
    """
    port: int = field(metadata={"name": ["i02"], "type": "int"})
    mac: str = field(metadata={"name": ["i01"], "type": "mac"})


@endpoint("host.b")
@dataclass
class HostEndpoint(SwitchOSEndpoint):
    """Represents the static host table endpoint.

    Contains a list of statically configured MAC address entries.
    """
    entries: List[HostEntry] = field(default_factory=list)
