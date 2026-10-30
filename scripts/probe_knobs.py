"""Listen to the notify characteristic while the user turns the physical knobs.

Run this, then turn the light's physical knobs (white tone and RGB) for the
duration of the listening window. Any frames printed are the device reporting
its own state — see HARDWARE.md for what was observed.
"""

import asyncio
import sys

from bleak import BleakClient, BleakScanner

ADDR = "6AF33AAF-16F6-93C7-D939-EECC8680C454"  # macOS CoreBluetooth UUID
NOTIFY = "f000aa63-0451-4000-b000-000000000000"
LISTEN_SECONDS = 45


async def main() -> None:
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=10)
    if not dev:
        print("Light not found — is it powered on and in range?")
        sys.exit(1)
    async with BleakClient(dev) as client:
        frames: list[str] = []

        def cb(_sender: object, data: bytearray) -> None:
            print("NOTIFY:", data.hex(), flush=True)
            frames.append(data.hex())

        await client.start_notify(NOTIFY, cb)
        print(
            f"Listening {LISTEN_SECONDS}s — turn the physical knobs (white tone AND rgb) now...",
            flush=True,
        )
        await asyncio.sleep(LISTEN_SECONDS)
        print(f"Done. {len(frames)} frame(s) captured.")


asyncio.run(main())
