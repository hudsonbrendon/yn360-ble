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


def build_off_command() -> bytes:
    """Frame for power off: [0xAE, 0xA3, 0x00, 0x00, 0x00, 0x56]."""
    return bytes([HEADER, CMD_OFF, 0x00, 0x00, 0x00, FOOTER])


def build_white_command(cool: int, warm: int) -> bytes:
    """Frame for white mode: [0xAE, 0xAA, 0x01, cool, warm, 0x56]. cool/warm 0-100."""
    _require_range("cool", cool, 0, 100)
    _require_range("warm", warm, 0, 100)
    return bytes([HEADER, CMD_WHITE, WHITE_CHANNEL, cool, warm, FOOTER])


WHITE_MIN_KELVIN = 3200
WHITE_MAX_KELVIN = 5500


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def kelvin_to_cool_warm(kelvin: int, brightness: float = 1.0) -> tuple[int, int]:
    """Map a color temperature (3200-5500K) + brightness (0.0-1.0) to (cool, warm) 0-100."""
    kelvin = _clamp(kelvin, WHITE_MIN_KELVIN, WHITE_MAX_KELVIN)
    brightness = _clamp(brightness, 0.0, 1.0)
    percent_cool = (kelvin - WHITE_MIN_KELVIN) / (WHITE_MAX_KELVIN - WHITE_MIN_KELVIN)
    cool = round(percent_cool * 100 * brightness)
    warm = round((1.0 - percent_cool) * 100 * brightness)
    return cool, warm


def scale_rgb(r: int, g: int, b: int, brightness: float = 1.0) -> tuple[int, int, int]:
    """Scale an RGB triple by brightness (0.0-1.0), returning ints 0-255."""
    brightness = _clamp(brightness, 0.0, 1.0)
    return (round(r * brightness), round(g * brightness), round(b * brightness))
