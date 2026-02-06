from dataclasses import dataclass, field
from python_switchos.endpoint import SwitchOSEndpoint, endpoint


@endpoint("snmp.b")
@dataclass
class SnmpEndpoint(SwitchOSEndpoint):
    """Represents the SNMP configuration endpoint.

    Fields:
        enabled: Whether SNMP is enabled (True/False)
        community: SNMP community string (e.g., "public")
        contact_info: SNMP system contact information
        location: SNMP system location
    """
    enabled: bool = field(metadata={"name": ["i01"], "type": "scalar_bool", "writable": True})
    community: str = field(metadata={"name": ["i02"], "type": "str", "writable": True})
    contact_info: str = field(metadata={"name": ["i03"], "type": "str", "writable": True})
    location: str = field(metadata={"name": ["i04"], "type": "str", "writable": True})
