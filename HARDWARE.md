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

## 2026-10-25 session — official app reverse-engineered

Source: official Android app **YONGNUO** (`com.yn.www` 6.5.2, Flutter). Its BLE
frames are built in a native JNI library, `libblecommand.so`
(`com.yn.www.BleCommandEncoder`, 22 builders). Every builder was decompiled
with REA + Ghidra and then **executed under Unicorn** (ARMv7 emulation of the
shipped `.so`) to get byte-exact frames. Results were checked on the III Pro.

### Status query — the light DOES report state (supersedes "does not notify")

`AE 33 00 00 00 56` (app: `buildQueryOldDeviceStatusCommand`) makes the light
answer on `f000aa63` with two frames:

| Frame | Meaning |
| --- | --- |
| `A5 09 43 50 00 AD 56 01 5A` | device info, constant on this unit (opaque) |
| `AE AA ch cool warm 56` / `AE EE ch cool warm 56` | white state; `AA` = on, `EE` = standby/off |

- The reply **tracks the physical knobs**: after turning them, a query returned
  `51 63` where `2F 36` had been set over BLE. Nothing is sent unprompted, which
  is why earlier passive notify sessions saw zero frames.
- RGB output is **not** reported; after an RGB command the reply still shows
  the last white/standby values.
- `AE A3` (off) does not change the reply; `AE EE` does, so use standby when
  the off state must be observable.

### Verified on the III Pro (operator watching the light)

- `AE EE ch c w 56` turns the light off from white **and** RGB; values in the
  frame are ignored (the loaded white values are kept and reported).
- White byte order is `cool, warm`: alternating `63 0A` ↔ `0A 63` flips the
  tint cold ↔ warm; `00 63` / `0A 63` are warm.
- Levels are 0–99: the app clamps to 99 and the light reports `64` back as `63`.
- The channel byte filters: `AE AA 02 …` is ignored by a light on channel 1.
- `AE 80 A1 AA ch R G B 00 00 00 56` (app "old RGB", 0–99 per channel) works
  too; `AE A1 R G B 56` (0–255) remains the finer option.
- **No effects**: `AE 80 A2 AA ch n 00 56` (app "old effect", n = 1..3) did nothing.
- The newer-protocol frames (`AE 01 06 …` power, `AE 03 0A …` CCT, `AE 05 08 …`
  RGB, `AE 07 09 …` HSI, `AE 22 04 56` query, `AE 25 …` music) are ignored.

### Full app command table (for other Yongnuo lights)

Byte-exact from emulating `libblecommand.so`; `ch` = group channel.

| App builder | Frame |
| --- | --- |
| `build360RGBCommand(r,g,b)` | `AE A1 r g b 56` |
| `buildYellowWhiteCommand(ch,a,b)` | `AE AA ch b a 56` (each clamped to 99) |
| `buildOldPowerCommand(ch,on,a,b)` | `AE (AA\|EE) ch a b` (no footer) |
| `buildOldRGBCommand(ch,on,r,g,b)` | `AE 80 A1 (AA\|EE) ch r g b 00 00 00 56` (0–99) |
| `buildOldEffectCommand(ch,on,n,play)` | `AE 80 A2 (AA\|EE) ch n !play 56` |
| `buildQueryOldDeviceStatusCommand()` | `AE 33 00 00 00 56` |
| `buildQueryNewDeviceStatusCommand()` | `AE 22 04 56` |
| `buildPowerCommand(ch,on)` | `AE 01 06 ch on 56` |
| `buildColorTempCommand(ch,K,bri,a,b)` | `AE 03 0A ch K_hi K_lo bri b a` |
| `buildColorTempDecimalCommand(ch,K,bri10)` | `AE 03 09 ch K_hi K_lo bri10/10 A0 bri10%10` |
| `buildRGBCommand(ch,on,r,g,b)` | `AE 05 08 ch r g b on` |
| `buildHSICommand(ch,hue,sat,int)` | `AE 07 09 ch hue_hi hue_lo sat int` |
| `buildHSIDecimalCommand(ch,hue,sat,int10)` | `AE 07 09 ch hue_hi hue_lo sat int10/10 A0 int10%10` |
| `buildEffectCommand(ch,n,on)` | `AE 09 07 ch n on 56` |
| `buildEffectSpeedBrightCommand(ch,n,speed,bri,_)` | `AE 0D 08 ch n speed bri` |
| `buildGMCommand(ch,gm)` | `AE 0F 07 ch gm 56` (signed byte) |
| `buildModifyGroupChannelCommand(a,b)` | `AE 02 00 00 b a` |
| `buildMusicModePowerCommand(ch,on)` | `AE 25 01 ch on` |
| `buildMusicModeStatusCommand(ch)` | `AE 25 05 ch` |
| `buildMusicModeSupportCommand(ch)` | `AE 25 07 ch` |

The app's transport (`YNBleManger`) queues commands on a timer and re-sends the
last command twice more, which explains the occasional ignored single write.
