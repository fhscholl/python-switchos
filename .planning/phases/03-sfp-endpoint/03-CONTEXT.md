# Phase 3: SFP Endpoint - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse `sfp.b` to expose SFP module information and diagnostics per SFP port. Info fields include vendor, part number, revision, serial, date, and type. Diagnostic fields include temperature, voltage, tx_bias, tx_power, and rx_power.

</domain>

<decisions>
## Implementation Decisions

### Diagnostic units
- Temperature: Celsius
- Voltage: Volts (e.g., 3.243V)
- Optical power (tx_power, rx_power): dBm (e.g., -3.857 dBm)
- Bias current (tx_bias): Milliamps (e.g., 6.0 mA)

### Missing SFP handling
- Empty port (no SFP inserted): All fields return None
- Copper SFPs with unavailable diagnostics: Return zeros as-is (don't distinguish from "not measured")

### Field presence
- All info fields (vendor, part_number, revision, serial, date, type): Optional — return None if missing
- All diagnostic fields (temperature, voltage, tx_bias, tx_power, rx_power): Optional — return None if missing

### Port indexing
- Return data only for SFP-capable ports (2 ports on CSS610-8G-2S+), not all 10 ports
- Array length matches number of SFP slots, not total port count

### Claude's Discretion
- Whether to include a port number/slot field to map SFP index to physical port
- Exact field naming conventions
- How to detect/handle SFP vs non-SFP port boundaries

</decisions>

<specifics>
## Specific Ideas

No specific requirements — follow existing endpoint patterns from LinkEndpoint and SystemEndpoint.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-sfp-endpoint*
*Context gathered: 2026-02-03*
