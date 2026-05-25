"""Discover YN360 lights on the local Bluetooth adapter."""

from __future__ import annotations

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .const import DEVICE_NAME_PREFIX, SERVICE_UUID


async def discover(timeout: float = 5.0) -> list[BLEDevice]:
    """Scan for nearby YN360 lights.

    Matches a device if its advertised name starts with ``DEVICE_NAME_PREFIX``
    or it advertises the YN360 service UUID.
    """
    discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)
    found: list[BLEDevice] = []
    for device, adv in discovered.values():
        name = (adv.local_name or device.name or "").upper()
        service_uuids = [u.lower() for u in (adv.service_uuids or [])]
        if name.startswith(DEVICE_NAME_PREFIX.upper()) or SERVICE_UUID in service_uuids:
            found.append(device)
    return found
