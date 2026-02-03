from dataclasses import dataclass, field
from typing import List
from python_switchos.endpoint import SwitchOSEndpoint, endpoint
from python_switchos.endpoints.host import HostEntry


@endpoint("!dhost.b")
@dataclass
class DynamicHostEndpoint(SwitchOSEndpoint):
    """Represents the dynamic host table endpoint.

    Contains a list of dynamically learned MAC address entries.
    Shares HostEntry with HostEndpoint since both have same structure.
    """
    entries: List[HostEntry] = field(default_factory=list)
