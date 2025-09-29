from dataclasses import dataclass, field
from typing import Literal
from python_switchos.endpoint import SwitchOSEndpoint, endpoint

# Address aquistion options matching the API’s integer order
AddressAquistion = Literal["DHCP_FALLBACK", "STATIC", "DHCP"]

@endpoint("sys.b")
@dataclass
class SystemEndpoint(SwitchOSEndpoint):
    """Represents the endpoint with system information."""

    # General
    addressAquistion: AddressAquistion = field(metadata={"name": ["iptp", "i0a"], "type": "option", "options": AddressAquistion})
    staticIP: str = field(metadata={"name": ["ip", "i09"], "type": "ip"})
    ip: str = field(metadata={"name": ["cip", "i02"], "type": "ip"})
    identity: str = field(metadata={"name": ["id", "i05"], "type": "str"})
    serial: str = field(metadata={"name": ["sid", "i04"], "type": "str"})
    mac: str = field(metadata={"name": ["mac", "i03"], "type": "mac"})
    model: str = field(metadata={"name": ["brd", "i07"], "type": "str"})
    version: str = field(metadata={"name": ["ver", "i06"], "type": "str"})
    revision: str = field(metadata={"name": ["rev"], "type": "str"}, default=None)
    uptime: int = field(metadata={"name": ["upt", "i01"], "type": "int"}, default=None)

    # Health
    cpuTemp: int = field(metadata={"name": ["temp", "i22"], "type": "int"}, default=None)
    psu1Current: int = field(metadata={"name": ["p1c", "i16"], "type": "int"}, default=None)
    psu1Voltage: int = field(metadata={"name": ["p1v", "i15"], "type": "int", "scale": 100}, default=None)
    psu2Current: int = field(metadata={"name": ["p2c", "i1f"], "type": "int"}, default=None)
    psu2Voltage: int = field(metadata={"name": ["p2v", "i1e"], "type": "int", "scale": 100}, default=None)
    psu1Power: int = field(metadata={"name": ["p1p"], "type": "int"}, default=None)
    psu2Power: int = field(metadata={"name": ["p2p"], "type": "int", "scale": 100}, default=None)
    power_consumption: int = field(metadata={"name": ["i26"], "type": "int", "scale": 10}, default=None)
