"""Async control of a YN360 light over BLE using bleak."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from .const import NOTIFY_CHAR_UUID, WRITE_CHAR_UUID
from .protocol import (
    WHITE_CHANNEL,
    WhiteState,
    build_off_command,
    build_rgb_command,
    build_white_command,
    kelvin_to_cool_warm,
    parse_white_notification,
    scale_rgb,
)

_LOGGER = logging.getLogger(__name__)


class YN360Light:
    """A single Yongnuo YN360 BLE light.

    Accepts either a bleak ``BLEDevice`` (preferred, e.g. from Home Assistant's
    shared scanner / Bluetooth proxies) or a string MAC/UUID address.

    ``client_factory`` lets a caller supply the connection instead of letting
    this class open one, so Home Assistant can hand over a client built by
    ``bleak_retry_connector.establish_connection``. It must return an already
    connected client.
    """

    def __init__(
        self,
        device: BLEDevice | str,
        client_factory: Callable[[], Awaitable[BleakClient]] | None = None,
    ) -> None:
        self._device = device
        self._client_factory = client_factory
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
        if self._client.is_connected:
            return
        _LOGGER.debug("Connecting to YN360 %s", self._device)
        if self._client_factory is not None:
            self._client = await self._client_factory()
        else:
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

    async def set_white(
        self, kelvin: int, brightness: float = 1.0, channel: int = WHITE_CHANNEL
    ) -> None:
        cool, warm = kelvin_to_cool_warm(kelvin, brightness)
        await self._write(build_white_command(cool, warm, channel))
        self._brightness = brightness
        self._is_on = True

    async def start_notify(self, callback: Callable[[WhiteState], None]) -> None:
        """Subscribe to notifications, delivering parsed white states.

        The III Pro does not echo app-sent commands and was not observed to
        report knob movement either; see HARDWARE.md.
        """
        await self.connect()

        def _on_notify(_sender: object, data: bytearray) -> None:
            state = parse_white_notification(bytes(data))
            if state is not None:
                callback(state)

        await self._client.start_notify(NOTIFY_CHAR_UUID, _on_notify)

    async def stop_notify(self) -> None:
        if self._client.is_connected:
            await self._client.stop_notify(NOTIFY_CHAR_UUID)

    async def turn_off(self) -> None:
        await self._write(build_off_command())
        self._is_on = False
