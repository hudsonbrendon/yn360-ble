from unittest.mock import AsyncMock, patch

import pytest

from yn360.const import WRITE_CHAR_UUID
from yn360.light import YN360Light


def _patched_client():
    """Patch BleakClient inside yn360.light; return the patcher and the mock instance."""
    patcher = patch("yn360.light.BleakClient")
    mock_cls = patcher.start()
    client = mock_cls.return_value
    client.is_connected = False
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.write_gatt_char = AsyncMock()
    return patcher, client


@pytest.mark.asyncio
async def test_set_rgb_connects_and_writes_frame():
    patcher, client = _patched_client()
    try:
        light = YN360Light("AA:BB:CC:DD:EE:FF")
        await light.set_rgb(255, 153, 0)
        client.connect.assert_awaited_once()
        client.write_gatt_char.assert_awaited_once_with(
            WRITE_CHAR_UUID, b"\xae\xa1\xff\x99\x00\x56", response=True
        )
        assert light.is_on is True
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_set_rgb_applies_brightness():
    patcher, client = _patched_client()
    try:
        light = YN360Light("AA:BB:CC:DD:EE:FF")
        await light.set_rgb(200, 100, 50, brightness=0.5)
        client.write_gatt_char.assert_awaited_once_with(
            WRITE_CHAR_UUID, b"\xae\xa1\x64\x32\x19\x56", response=True
        )
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_set_white_writes_cct_frame():
    patcher, client = _patched_client()
    try:
        light = YN360Light("AA:BB:CC:DD:EE:FF")
        await light.set_white(5500, brightness=1.0)
        client.write_gatt_char.assert_awaited_once_with(
            WRITE_CHAR_UUID, b"\xae\xaa\x01\x64\x00\x56", response=True
        )
        assert light.is_on is True
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_turn_off_writes_off_frame_and_clears_state():
    patcher, client = _patched_client()
    try:
        light = YN360Light("AA:BB:CC:DD:EE:FF")
        await light.set_rgb(10, 20, 30)
        await light.turn_off()
        client.write_gatt_char.assert_awaited_with(
            WRITE_CHAR_UUID, b"\xae\xa3\x00\x00\x00\x56", response=True
        )
        assert light.is_on is False
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_does_not_reconnect_when_already_connected():
    patcher, client = _patched_client()
    try:
        client.is_connected = True
        light = YN360Light("AA:BB:CC:DD:EE:FF")
        await light.set_rgb(1, 2, 3)
        client.connect.assert_not_awaited()
    finally:
        patcher.stop()
