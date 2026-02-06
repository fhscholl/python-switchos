from dataclasses import dataclass, field
from typing import List
from python_switchos.endpoint import SwitchOSEndpoint, endpoint


@endpoint("sfp.b", readonly=True)
@dataclass
class SfpEndpoint(SwitchOSEndpoint):
    """Represents the endpoint providing SFP module information and diagnostics.

    Each field is a list with one value per SFP port.
    """
    # Info fields
    vendor: List[str] = field(metadata={"name": ["i01"], "type": "str", "writable": False})
    part_number: List[str] = field(metadata={"name": ["i02"], "type": "str", "writable": False})
    revision: List[str] = field(metadata={"name": ["i03"], "type": "str", "writable": False})
    serial: List[str] = field(metadata={"name": ["i04"], "type": "str", "writable": False})
    date: List[str] = field(metadata={"name": ["i05"], "type": "str", "writable": False})
    type: List[str] = field(metadata={"name": ["i06"], "type": "sfp_type", "writable": False})

    # Diagnostic fields
    temperature: List[int] = field(metadata={"name": ["i08"], "type": "int", "writable": False})
    voltage: List[float] = field(metadata={"name": ["i09"], "type": "int", "scale": 1000, "writable": False})
    tx_bias: List[int] = field(metadata={"name": ["i0a"], "type": "int", "writable": False})
    tx_power: List[float] = field(metadata={"name": ["i0b"], "type": "dbm", "scale": 10000, "writable": False})
    rx_power: List[float] = field(metadata={"name": ["i0c"], "type": "dbm", "scale": 10000, "writable": False})
