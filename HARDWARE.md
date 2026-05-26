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
