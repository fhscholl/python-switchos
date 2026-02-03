from dataclasses import dataclass, field
from typing import List
from python_switchos.endpoint import SwitchOSEndpoint, endpoint


@dataclass
class IgmpEntry:
    """Represents a single IGMP snooping table entry.

    Fields:
        group_address: Multicast group IP address
        vlan: VLAN ID for this group
        member_ports: Port membership list (index=port, True=member)
    """
    group_address: str = field(metadata={"name": ["i01"], "type": "ip"})
    vlan: int = field(metadata={"name": ["i03"], "type": "int"})
    member_ports: List[bool] = field(metadata={"name": ["i02"], "type": "bool", "ports": 10})


@endpoint("!igmp.b")
@dataclass
class IgmpEndpoint(SwitchOSEndpoint):
    """Represents the IGMP snooping table endpoint.

    Contains a list of multicast groups with their port membership.
    """
    entries: List[IgmpEntry] = field(default_factory=list)
