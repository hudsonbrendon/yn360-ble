from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yn360.scanner import discover


def _device(address, name):
    dev = MagicMock()
    dev.address = address
    dev.name = name
    return dev


def _adv(local_name, service_uuids):
    adv = MagicMock()
    adv.local_name = local_name
    adv.service_uuids = service_uuids
    return adv


@pytest.mark.asyncio
async def test_discover_matches_by_name_prefix():
    matching = _device("AA:BB:CC:DD:EE:FF", "YN360-ABCD")
    other = _device("11:22:33:44:55:66", "Some Speaker")
    discovered = {
        matching.address: (matching, _adv("YN360-ABCD", [])),
        other.address: (other, _adv("Some Speaker", [])),
    }
    with patch("yn360.scanner.BleakScanner.discover", AsyncMock(return_value=discovered)):
        result = await discover(timeout=1.0)
    assert result == [matching]


@pytest.mark.asyncio
async def test_discover_matches_by_service_uuid():
    matching = _device("AA:BB:CC:DD:EE:FF", "Unnamed")
    discovered = {
        matching.address: (
            matching,
            _adv("Unnamed", ["f000aa60-0451-4000-b000-000000000000"]),
        ),
    }
    with patch("yn360.scanner.BleakScanner.discover", AsyncMock(return_value=discovered)):
        result = await discover(timeout=1.0)
    assert result == [matching]
