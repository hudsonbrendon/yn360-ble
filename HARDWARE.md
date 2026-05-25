# YN360 III Pro — Hardware Findings

This file records the results of validating the reverse-engineered BLE protocol
against a real Yongnuo YN360 III Pro. Fill it in by running the CLI against the
device (`yn360 scan`, then `yn360 rgb/white/off`). It also drives the discovery
matcher used by the Home Assistant integration.

- **Device address:** _TBD — from `yn360 scan`_
- **Advertised local_name:** _TBD_
- **Advertises service UUID f000aa60?:** _yes / no — determines the HA discovery matcher_
- **Manufacturer ID (if any):** _TBD_
- **Write characteristic UUID:** `f000aa61-0451-4000-b000-000000000000` _(confirm via GATT dump)_
- **RGB command works as documented?:** _TBD_
- **White command works as documented?:** _TBD_
- **Off command works as documented?:** _TBD_

## Home Assistant discovery matcher to use

Prefer `local_name` if it is present and stable; use `service_uuid` only if the
device advertises it; fall back to `manufacturer_id` if only manufacturer data is
present. Record the concrete matcher here:

- Matcher: `{ "local_name": "YN360*" }`
