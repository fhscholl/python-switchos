from dataclasses import dataclass, field
from typing import List, Literal
from python_switchos.endpoint import SwitchOSEndpoint, endpoint

# Speed options matching the API’s integer order
Speed = Literal["10M", "100M", "1G", "10G", "200M", "2.5G", "5G", None]

@endpoint("link.b")
@dataclass
class LinkEndpoint(SwitchOSEndpoint):
    """Represents the endpoint providing basic information for each individual port."""
    enabled: List[bool] = field(metadata={"name": ["en", "i01"], "type": "bool"})
    name: List[str] = field(metadata={"name": ["nm", "i0a"], "type": "str"})
    linkState: List[bool] = field(metadata={"name": ["lnk", "i06"], "type": "bool"}, default=None)
    autoNegotiation: List[bool] = field(metadata={"name": ["an", "i02"], "type": "bool"}, default=None)
    speed: List[Speed] = field(metadata={"name": ["spdc", "i08"], "type": "option", "options": Speed}, default=None)
    manSpeed: List[Speed] = field(metadata={"name": ["spd", "i05"], "type": "option", "options": Speed}, default=None)
    fullDuplex: List[bool] = field(metadata={"name": ["dpx", "i07"], "type": "bool"}, default=None)
    manFullDuplex: List[bool] = field(metadata={"name": ["dpxc", "i03"], "type": "bool"}, default=None)
    flowControlRx: List[bool] = field(metadata={"name": ["fctr", "i12"], "type": "bool"}, default=None)
    flowControlTx: List[bool] = field(metadata={"name": ["fctc", "i16"], "type": "bool"}, default=None)
