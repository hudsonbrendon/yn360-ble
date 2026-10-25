"""Probe channel bytes 2-3 and the 0xEE standby opcode on real hardware.

Sends one frame every few seconds with a label; watch the light and record what
it does at each step in HARDWARE.md. Ends with a normal off.
"""

import asyncio
import sys

from bleak import BleakClient, BleakScanner

ADDR = "6AF33AAF-16F6-93C7-D939-EECC8680C454"  # macOS CoreBluetooth UUID
WRITE = "f000aa61-0451-4000-b000-000000000000"
SETTLE_SECONDS = 4


async def main() -> None:
    dev = await BleakScanner.find_device_by_address(ADDR, timeout=10)
    if not dev:
        print("Light not found — is it powered on and in range?")
        sys.exit(1)
    async with BleakClient(dev) as client:

        async def send(label: str, frame: bytes) -> None:
            print(f"\n>>> {label}: {frame.hex()} — WATCH THE LIGHT", flush=True)
            await client.write_gatt_char(WRITE, frame, response=True)
            await asyncio.sleep(SETTLE_SECONDS)

        await send(
            "white ch1 50/50 (baseline, should light up)", bytes([0xAE, 0xAA, 1, 50, 50, 0x56])
        )
        await send("white ch2 50/50 (does it react?)", bytes([0xAE, 0xAA, 2, 50, 50, 0x56]))
        await send("white ch3 100/0 (does it react?)", bytes([0xAE, 0xAA, 3, 100, 0, 0x56]))
        await send("white ch1 50/50 (back to baseline)", bytes([0xAE, 0xAA, 1, 50, 50, 0x56]))
        await send(
            "standby 0xEE ch1 50/50 (off? dim? nothing?)", bytes([0xAE, 0xEE, 1, 50, 50, 0x56])
        )
        await send("white ch1 50/50 (does it come back?)", bytes([0xAE, 0xAA, 1, 50, 50, 0x56]))
        await send("off 0xA3 (restore off)", bytes([0xAE, 0xA3, 0, 0, 0, 0x56]))
        print("\nDone.")


asyncio.run(main())
