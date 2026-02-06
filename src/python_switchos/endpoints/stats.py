"""Port statistics endpoint for traffic rates, counters, errors, and histograms."""

from dataclasses import dataclass, field
from typing import List

from python_switchos.endpoint import SwitchOSEndpoint, endpoint


@endpoint("!stats.b", "stats.b")
@dataclass
class StatsEndpoint(SwitchOSEndpoint):
    """Port statistics from the !stats.b endpoint.

    Note: SwOS full 2.17+ uses stats.b (without ! prefix).

    Contains four categories of statistics per port:

    Rate fields:
        rx_rate, tx_rate: Byte rates (scaled by 0.32)
        rx_packet_rate, tx_packet_rate: Packet rates (scaled by 2.56)

    Byte/Packet counters:
        rx_bytes, tx_bytes: 64-bit byte counters
        rx_total_packets, tx_total_packets: Total packet counters
        rx_unicasts, tx_unicasts: 64-bit unicast counters
        rx_broadcasts, tx_broadcasts: 64-bit broadcast counters
        rx_multicasts, tx_multicasts: 64-bit multicast counters

    Error counters:
        rx_pauses, rx_errors, rx_fcs_errors, rx_jabber, rx_runts,
        rx_fragments, rx_too_long, tx_pauses, tx_fcs_errors,
        tx_collisions, tx_single_collisions, tx_multiple_collisions,
        tx_excessive_collisions, tx_late_collisions, tx_deferred

    Histogram counters (packet size distribution):
        hist_64, hist_65_127, hist_128_255, hist_256_511,
        hist_512_1023, hist_1024_max
    """

    # Rate fields (scale divides raw value)
    rx_rate: List[float] = field(metadata={"name": ["i21"], "type": "int", "scale": 0.32, "writable": False})
    tx_rate: List[float] = field(metadata={"name": ["i22"], "type": "int", "scale": 0.32, "writable": False})
    rx_packet_rate: List[float] = field(metadata={"name": ["i25"], "type": "int", "scale": 2.56, "writable": False})
    tx_packet_rate: List[float] = field(metadata={"name": ["i26"], "type": "int", "scale": 2.56, "writable": False})

    # Byte counters (64-bit: low + high * 2^32)
    rx_bytes: List[int] = field(metadata={"name": ["i01"], "type": "uint64", "high": "i02", "writable": False})
    tx_bytes: List[int] = field(metadata={"name": ["i0f"], "type": "uint64", "high": "i10", "writable": False})

    # Packet counters (some 64-bit for unicast/broadcast/multicast)
    rx_total_packets: List[int] = field(metadata={"name": ["i23"], "type": "int", "writable": False})
    tx_total_packets: List[int] = field(metadata={"name": ["i24"], "type": "int", "writable": False})
    rx_unicasts: List[int] = field(metadata={"name": ["i05"], "type": "uint64", "high": "i27", "writable": False})
    tx_unicasts: List[int] = field(metadata={"name": ["i11"], "type": "uint64", "high": "i28", "writable": False})
    rx_broadcasts: List[int] = field(metadata={"name": ["i07"], "type": "uint64", "high": "i29", "writable": False})
    tx_broadcasts: List[int] = field(metadata={"name": ["i14"], "type": "uint64", "high": "i2a", "writable": False})
    rx_multicasts: List[int] = field(metadata={"name": ["i08"], "type": "uint64", "high": "i2b", "writable": False})
    tx_multicasts: List[int] = field(metadata={"name": ["i13"], "type": "uint64", "high": "i2c", "writable": False})

    # Error counters
    rx_pauses: List[int] = field(metadata={"name": ["i17"], "type": "int", "writable": False})
    rx_errors: List[int] = field(metadata={"name": ["i1d"], "type": "int", "writable": False})
    rx_fcs_errors: List[int] = field(metadata={"name": ["i1e"], "type": "int", "writable": False})
    rx_jabber: List[int] = field(metadata={"name": ["i1c"], "type": "int", "writable": False})
    rx_runts: List[int] = field(metadata={"name": ["i19"], "type": "int", "writable": False})
    rx_fragments: List[int] = field(metadata={"name": ["i1a"], "type": "int", "writable": False})
    rx_too_long: List[int] = field(metadata={"name": ["i1b"], "type": "int", "writable": False})
    tx_pauses: List[int] = field(metadata={"name": ["i16"], "type": "int", "writable": False})
    tx_fcs_errors: List[int] = field(metadata={"name": ["i04"], "type": "int", "writable": False})
    tx_collisions: List[int] = field(metadata={"name": ["i1f"], "type": "int", "writable": False})
    tx_single_collisions: List[int] = field(metadata={"name": ["i15"], "type": "int", "writable": False})
    tx_multiple_collisions: List[int] = field(metadata={"name": ["i18"], "type": "int", "writable": False})
    tx_excessive_collisions: List[int] = field(metadata={"name": ["i12"], "type": "int", "writable": False})
    tx_late_collisions: List[int] = field(metadata={"name": ["i20"], "type": "int", "writable": False})
    tx_deferred: List[int] = field(metadata={"name": ["i06"], "type": "int", "writable": False})

    # Histogram counters (packet size distribution)
    hist_64: List[int] = field(metadata={"name": ["i09"], "type": "int", "writable": False})
    hist_65_127: List[int] = field(metadata={"name": ["i0a"], "type": "int", "writable": False})
    hist_128_255: List[int] = field(metadata={"name": ["i0b"], "type": "int", "writable": False})
    hist_256_511: List[int] = field(metadata={"name": ["i0c"], "type": "int", "writable": False})
    hist_512_1023: List[int] = field(metadata={"name": ["i0d"], "type": "int", "writable": False})
    hist_1024_max: List[int] = field(metadata={"name": ["i0e"], "type": "int", "writable": False})
