<p align="center">
  <img src="assets/yongnuo-logo.png" alt="Yongnuo" width="420">
</p>

# yn360-ble

[![CI](https://github.com/hudsonbrendon/yn360-ble/actions/workflows/ci.yml/badge.svg)](https://github.com/hudsonbrendon/yn360-ble/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/yn360-ble)](https://pypi.org/project/yn360-ble/)
[![Python](https://img.shields.io/pypi/pyversions/yn360-ble)](https://pypi.org/project/yn360-ble/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Control **Yongnuo YN360 / YN360 III Pro** LED lights over Bluetooth LE from
Python — power, brightness, RGB colour, and white colour temperature.

This library powers the
[**Yongnuo YN360 Home Assistant integration**](https://github.com/hudsonbrendon/yn360-homeassistant),
but works standalone in any async Python project (or straight from the command line).

## Features

- 🔌 **Async BLE control** built on [`bleak`](https://github.com/hbldh/bleak) —
  works on Linux, macOS, and Windows.
- 💡 **On / off**
- 🔆 **Brightness** (0.0–1.0)
- 🎨 **RGB colour**
- 🌡️ **White colour temperature** — 3200 K (warm) to 5500 K (cool), the light's
  bi-colour range.
- 📡 **Status query** — read the light's real white state (follows the physical knobs) and on/standby.
- 💤 **Standby** — off that keeps the white values and is reported as off.
- 🔍 **Discovery helper** — `discover()` finds nearby YN360 lights.
- 🖥️ **CLI** — `yn360 scan / rgb / white / off` for quick testing.

## Requirements

- Python **3.11** or newer.
- A Bluetooth LE adapter (built-in or USB).
- A Yongnuo YN360 III Pro (other YN360 models using the same BLE protocol may
  also work).

## Installation

```bash
pip install yn360-ble
```

## CLI usage

```bash
yn360 scan                                  # find nearby lights
yn360 rgb   AA:BB:CC:DD:EE:FF 255 153 0     # set an RGB colour
yn360 white AA:BB:CC:DD:EE:FF 4500          # set a white colour temperature (K)
yn360 white AA:BB:CC:DD:EE:FF 4500 --channel 3   # ...on group channel 3
yn360 off   AA:BB:CC:DD:EE:FF               # turn off
yn360 standby AA:BB:CC:DD:EE:FF             # off, reported as standby
yn360 status  AA:BB:CC:DD:EE:FF             # e.g. "on channel=1 cool=52 warm=47"
```

## Library usage

```python
import asyncio
from yn360 import YN360Light, discover


async def main():
    devices = await discover()
    light = YN360Light(devices[0])
    await light.set_rgb(255, 153, 0)  # orange
    await light.set_white(4500, brightness=0.8)  # warm-ish white at 80%
    await light.turn_off()
    await light.disconnect()


asyncio.run(main())
```

`YN360Light` also accepts a `bleak` `BLEDevice` (e.g. from Home Assistant's shared
scanner or an ESPHome Bluetooth proxy), not only a string address.

### Supplying your own connection

Pass `client_factory` to have the light use a connection you built, instead of
opening its own. Home Assistant uses this to route through
`bleak_retry_connector.establish_connection`, which manages the adapter's
connection slots and caches GATT services:

```python
from bleak import BleakClient
from bleak_retry_connector import establish_connection

light = YN360Light(
    ble_device,
    client_factory=lambda: establish_connection(BleakClient, ble_device, address),
)
```

The factory must return an already connected client.

### Group channels

White commands carry a channel byte, so one command can address a group:

```python
await light.set_white(4500, brightness=0.8, channel=3)
```

The light only acts on frames for the channel it is set to (channel 1 by
default); frames for other channels are ignored — see [`HARDWARE.md`](HARDWARE.md).

## How it works

The light speaks a 6-byte BLE command frame `[0xAE, CMD, V1, V2, V3, 0x56]` written
to a single GATT characteristic:

| Command | CMD | V1 | V2 | V3 |
|---|---|---|---|---|
| RGB | `0xA1` | R | G | B |
| White | `0xAA` | channel (1–8) | cool 5500 K (0–99) | warm 3200 K (0–99) |
| Off | `0xA3` | `0x00` | `0x00` | `0x00` |
| Standby | `0xEE` | channel (1–8) | cool (0–99) | warm (0–99) |
| Status query | `0x33` | `0x00` | `0x00` | `0x00` |

- Service UUID: `f000aa60-0451-4000-b000-000000000000`
- Write characteristic: `f000aa61-0451-4000-b000-000000000000`
- Notify characteristic: `f000aa63-0451-4000-b000-000000000000`

`0xEE` turns the light off (RGB too) and keeps the white values loaded. The
status query is answered on the notify characteristic with the white state
(`0xAA` on / `0xEE` standby) — RGB output is not reported.

Commands are sent as **acknowledged writes** (`response=True`); the YN360 III Pro
silently drops write-without-response packets. See [`HARDWARE.md`](HARDWARE.md) for
the full reverse-engineering notes.

## Limitations

- State feedback covers **white mode only**: `query_status()` returns on/standby,
  channel and the cool/warm levels (including knob changes), but not RGB.
  Nothing is pushed unprompted — poll it.
- No built-in effects on the III Pro (the app's effect frames are ignored).
- Bluetooth LE allows **one client at a time** — close the official Yongnuo app
  while controlling the light.
- RGB and white are mutually exclusive modes; setting one switches the active mode.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Hudson Brendon
