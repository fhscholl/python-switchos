from dataclasses import dataclass, field
from typing import List, Literal
from python_switchos.endpoint import SwitchOSEndpoint, endpoint

# Address acquisition options matching the API's integer order
AddressAcquisition = Literal["DHCP_FALLBACK", "STATIC", "DHCP"]

# Port cost mode options (RSTP)
PortCostMode = Literal["short", "long"]

# IGMP version options
IgmpVersion = Literal["v2", "v3"]

@endpoint("sys.b")
@dataclass
class SystemEndpoint(SwitchOSEndpoint):
    """Represents the endpoint with system information."""

    # General
    address_acquisition: AddressAcquisition = field(metadata={"name": ["iptp", "i0a"], "type": "option", "options": AddressAcquisition, "writable": True})
    static_ip: str = field(metadata={"name": ["ip", "i09"], "type": "ip", "writable": True})
    ip: str = field(metadata={"name": ["cip", "i02"], "type": "ip", "writable": False})
    identity: str = field(metadata={"name": ["id", "i05"], "type": "str", "writable": True})
    serial: str = field(metadata={"name": ["sid", "i04"], "type": "str", "writable": False})
    mac: str = field(metadata={"name": ["mac", "i03"], "type": "mac", "writable": False})
    model: str = field(metadata={"name": ["brd", "i07"], "type": "str", "writable": False})
    version: str = field(metadata={"name": ["ver", "i06"], "type": "str", "writable": False})
    revision: str = field(metadata={"name": ["rev"], "type": "str", "writable": False}, default=None)
    uptime: int = field(metadata={"name": ["upt", "i01"], "type": "int", "writable": False}, default=None)

    # General (continued)
    build_number: int = field(metadata={"name": ["i0b"], "type": "int", "writable": False}, default=None)

    # RSTP General
    bridge_priority: int = field(metadata={"name": ["i0e"], "type": "int", "writable": True}, default=None)
    forward_reserved_multicast: bool = field(metadata={"name": ["i2a"], "type": "scalar_bool", "writable": True}, default=None)
    port_cost_mode: PortCostMode = field(metadata={"name": ["i0f"], "type": "option", "options": PortCostMode, "writable": True}, default=None)
    root_bridge_priority: int = field(metadata={"name": ["i10"], "type": "int", "writable": False}, default=None)
    root_bridge_mac: str = field(metadata={"name": ["i11"], "type": "mac", "writable": False}, default=None)

    # Access Control
    allow_from_ip: str = field(metadata={"name": ["i19"], "type": "ip", "writable": True}, default=None)
    allow_from_mask: int = field(metadata={"name": ["i1a"], "type": "int", "writable": True}, default=None)
    allow_from_ports: List[bool] = field(metadata={"name": ["i12"], "type": "bool", "writable": True}, default=None)
    allow_from_vlan: int = field(metadata={"name": ["i1b"], "type": "int", "writable": True}, default=None)

    # IGMP
    igmp_snooping: bool = field(metadata={"name": ["i17"], "type": "scalar_bool", "writable": True}, default=None)
    igmp_querier: bool = field(metadata={"name": ["i29"], "type": "scalar_bool", "writable": True}, default=None)
    igmp_fast_leave: List[bool] = field(metadata={"name": ["i27"], "type": "bool", "writable": True}, default=None)
    igmp_version: IgmpVersion = field(metadata={"name": ["i28"], "type": "option", "options": IgmpVersion, "writable": True}, default=None)

    # MDP
    mikrotik_discovery_protocol: List[bool] = field(metadata={"name": ["i08"], "type": "bool", "writable": True}, default=None)

    # DHCP & PPPoE Snooping
    dhcp_snooping_trusted_ports: List[bool] = field(metadata={"name": ["i13"], "type": "bool", "writable": True}, default=None)
    dhcp_snooping_add_info_option: bool = field(metadata={"name": ["i14"], "type": "scalar_bool", "writable": True}, default=None)

    # Health
    cpu_temp: int = field(metadata={"name": ["temp", "i22"], "type": "int", "signed": True, "bits": 16, "writable": False}, default=None)
    psu1_current: int = field(metadata={"name": ["p1c", "i16"], "type": "int", "writable": False}, default=None)
    psu1_voltage: int = field(metadata={"name": ["p1v", "i15"], "type": "int", "scale": 100, "writable": False}, default=None)
    psu2_current: int = field(metadata={"name": ["p2c", "i1f"], "type": "int", "writable": False}, default=None)
    psu2_voltage: int = field(metadata={"name": ["p2v", "i1e"], "type": "int", "scale": 100, "writable": False}, default=None)
    psu1_power: int = field(metadata={"name": ["p1p"], "type": "int", "scale": 10, "writable": False}, default=None)
    psu2_power: int = field(metadata={"name": ["p2p"], "type": "int", "scale": 10, "writable": False}, default=None)
    power_consumption: int = field(metadata={"name": ["i26"], "type": "int", "scale": 10, "writable": False}, default=None)
