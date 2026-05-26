<p align="center">
  <img src="assets/yongnuo-logo.png" alt="Yongnuo" width="420">
</p>

# yn360-ble

Control Yongnuo YN360 / YN360 III (Pro) LED lights over Bluetooth LE from Python.

## Install

```bash
pip install yn360-ble
```

## CLI

```bash
yn360 scan
yn360 rgb   AA:BB:CC:DD:EE:FF 255 153 0
yn360 white AA:BB:CC:DD:EE:FF 4500
yn360 off   AA:BB:CC:DD:EE:FF
```

## Library

```python
import asyncio
from yn360 import YN360Light, discover

async def main():
    devices = await discover()
    light = YN360Light(devices[0])
    await light.set_rgb(255, 153, 0)        # orange
    await light.set_white(4500, brightness=0.8)
    await light.turn_off()
    await light.disconnect()

asyncio.run(main())
```

## Protocol

6-byte frame `[0xAE, CMD, V1, V2, V3, 0x56]`:

| Command | CMD | V1 | V2 | V3 |
|---|---|---|---|---|
| RGB | `0xA1` | R | G | B |
| White | `0xAA` | `0x01` | cool 5500K (0–100) | warm 3200K (0–100) |
| Off | `0xA3` | `0x00` | `0x00` | `0x00` |

- Service UUID: `f000aa60-0451-4000-b000-000000000000`
- Write characteristic: `f000aa61-0451-4000-b000-000000000000`

See `HARDWARE.md` for YN360 III Pro confirmation notes.
