"""Async control of a YN360 light over BLE using bleak."""

from __future__ import annotations

import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from .const import WRITE_CHAR_UUID
from .protocol import (
    build_off_command,
    build_rgb_command,
    build_white_command,
    kelvin_to_cool_warm,
    scale_rgb,
)

_LOGGER = logging.getLogger(__name__)


class YN360Light:
    """A single Yongnuo YN360 BLE light.

    Accepts either a bleak ``BLEDevice`` (preferred, e.g. from Home Assistant's
    shared scanner / Bluetooth proxies) or a string MAC/UUID address.
    """

    def __init__(self, device: BLEDevice | str) -> None:
        self._device = device
        self._client = BleakClient(device)
        self._is_on = False
        self._rgb: tuple[int, int, int] = (255, 255, 255)
        self._brightness = 1.0

    @property
    def is_connected(self) -> bool:
        return self._client.is_connected

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def connect(self) -> None:
        if not self._client.is_connected:
            _LOGGER.debug("Connecting to YN360 %s", self._device)
            await self._client.connect()

    async def disconnect(self) -> None:
        if self._client.is_connected:
            _LOGGER.debug("Disconnecting from YN360 %s", self._device)
            await self._client.disconnect()

    async def _write(self, payload: bytes) -> None:
        await self.connect()
        _LOGGER.debug("Writing %s to YN360 %s", payload.hex(), self._device)
        # The YN360 III Pro only acts on acknowledged writes (response=True);
        # write-without-response packets are dropped, especially when the
        # connection is closed right after a command.
        await self._client.write_gatt_char(WRITE_CHAR_UUID, payload, response=True)

    async def set_rgb(self, r: int, g: int, b: int, brightness: float = 1.0) -> None:
        sr, sg, sb = scale_rgb(r, g, b, brightness)
        await self._write(build_rgb_command(sr, sg, sb))
        self._rgb = (r, g, b)
        self._brightness = brightness
        self._is_on = True

    async def set_white(self, kelvin: int, brightness: float = 1.0) -> None:
        cool, warm = kelvin_to_cool_warm(kelvin, brightness)
        await self._write(build_white_command(cool, warm))
        self._brightness = brightness
        self._is_on = True

    async def turn_off(self) -> None:
        await self._write(build_off_command())
        self._is_on = False
