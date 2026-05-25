"""Pure builders for YN360 6-byte BLE command frames. No I/O here."""

from __future__ import annotations

HEADER = 0xAE
FOOTER = 0x56

CMD_RGB = 0xA1
CMD_WHITE = 0xAA
CMD_OFF = 0xA3

WHITE_CHANNEL = 0x01


def _require_range(name: str, value: int, low: int, high: int) -> None:
    if not low <= value <= high:
        raise ValueError(f"{name} must be {low}-{high}, got {value}")


def build_rgb_command(r: int, g: int, b: int) -> bytes:
    """Frame for RGB mode: [0xAE, 0xA1, R, G, B, 0x56]."""
    _require_range("r", r, 0, 255)
    _require_range("g", g, 0, 255)
    _require_range("b", b, 0, 255)
    return bytes([HEADER, CMD_RGB, r, g, b, FOOTER])
