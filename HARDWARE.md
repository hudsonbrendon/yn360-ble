# YN360 III Pro — Hardware Findings

Validated against a real Yongnuo **YN360 III Pro** on 2026-05-25 (macOS / bleak).
The reverse-engineered `0xAE…0x56` protocol works — with one critical caveat
(see "Key finding" below).

- **Device address:** `6AF33AAF-16F6-93C7-D939-EECC8680C454`
  (macOS reports a CoreBluetooth UUID, not a MAC. On a Linux Home Assistant host
  the same light will appear as a real MAC `AA:BB:CC:DD:EE:FF`.)
- **Advertised local_name:** `YN360III_Pro`
- **Write characteristic:** `f000aa61-0451-4000-b000-000000000000`
  — properties `write`, `write-without-response` ✅
- **Notify characteristic:** `f000aa63-0451-4000-b000-000000000000` (`notify`)
- **Service:** `f000aa60-0451-4000-b000-000000000000`
- **RGB command works as documented?:** YES — `AE A1 R G B 56`
- **White command works as documented?:** YES — `AE AA 01 cool warm 56`
- **Off command works as documented?:** YES — `AE A3 00 00 00 56`

## Key finding: commands require ACKNOWLEDGED writes (`response=True`)

`write-without-response` packets are silently dropped by this unit (the write
returns OK but the light never changes), even with settle delays before
disconnecting. Only **acknowledged** writes (`write_gatt_char(..., response=True)`)
take effect. The library uses `response=True` for this reason.

Subscribing to the notify characteristic is **not** required — acknowledged
writes work with no subscription.

## Home Assistant discovery matcher to use

The light advertises the name `YN360III_Pro`, so a `local_name` glob matcher
catches it reliably:

- Matcher: `{ "local_name": "YN360*" }`

(Whether it also advertises the `f000aa60` service UUID in its advertisement
packet was not confirmed; `local_name` is sufficient and reliable.)

## 2026-08-20 validation session

Same unit, macOS / bleak, with an operator watching the light.

### Confirmed

- **The service UUID IS advertised.** The advertisement carries
  `service_uuids: ['f000aa60-0451-4000-b000-000000000000']`, so matching on the
  service UUID (not just `local_name`) is viable. This closes the open question
  left above.
- **Full GATT surface**: one service (`f000aa60`) with exactly two
  characteristics — write `f000aa61` (`write`, `write-without-response`) and
  notify `f000aa63` (`notify`). Negotiated MTU 23. **There is no battery
  service**, so a battery sensor is not possible for this device.
- **RGB byte order is R, G, B** — verified by sending `AE A1 FF 00 00 56`
  (observed: red) and `AE A1 00 00 FF 56` (observed: blue). `build_rgb_command`
  is correct; no byte-order bug.
- **The device does not notify.** Subscribed to `f000aa63` across three separate
  45-second windows — including one with the light lit and the operator turning
  the physical knobs throughout — and captured **zero frames**. App-sent
  commands are not echoed either. The errata in pinchies/YN360_webbtle
  ("reports back when changing white tones") does **not** reproduce on the
  III Pro. State feedback is therefore not available: `assumed_state` is
  correct for the Home Assistant integration.
- **Writes are ACKed even when the light does not respond.** Several commands
  returned successfully at the ATT layer while the light visibly did nothing.
  A successful write is not evidence that the light obeyed.

### Open — do not treat as settled

- **Channels 2-8**: still unverified. Four attempts failed to produce a clean
  reading, and the test frames used pure-cool (`100/0`) and pure-warm (`0/100`)
  values that the unit appears to reject for an unrelated reason (below), so
  those runs prove nothing either way. The `channel` parameter ships in the
  library for YN360-II users regardless; it is not exposed in the Home
  Assistant options flow.
- **The `0xEE` standby opcode**: still unverified, same reason.
- **White frames with a low or zero channel value appear to be ignored.**
  Observations this session:

  | Frame (cool/warm) | Result |
  | --- | --- |
  | `100/100` | lit, bright |
  | `50/50` | lit, medium |
  | `100/1` | nothing |
  | `100/0` | nothing |
  | `0/100` | nothing (weak observation) |

  Two readings fit. Either the unit rejects white frames where a channel is
  at or near zero, or **byte 4 is not `warm` but a brightness/level value** —
  which would fit every row above and mean the library's `(cool, warm)` model
  is wrong. This matters: `kelvin_to_cool_warm` maps the two ends of the
  colour-temperature range to `(100, 0)` and `(0, 100)`, so if the first
  reading holds, the extremes of the range silently do nothing in Home
  Assistant.

  **Test that settles it** (compare *brightness*, not colour): send
  `AE AA 01 64 32 56` (`100/50`), then `AE AA 01 32 64 56` (`50/100`). Under
  the `(cool, warm)` model both carry the same total level, so they should look
  equally bright and differ only in tint. Under a `(temperature, brightness)`
  model the first is half as bright as the second. Record it on video rather
  than judging live — short observation windows produced several ambiguous and
  contradictory readings this session.
