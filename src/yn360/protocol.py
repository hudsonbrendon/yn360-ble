"""Pure builders for YN360 6-byte BLE command frames. No I/O here."""

from __future__ import annotations

from typing import NamedTuple

HEADER = 0xAE
FOOTER = 0x56

CMD_RGB = 0xA1
CMD_WHITE = 0xAA
CMD_OFF = 0xA3
CMD_STANDBY = 0xEE

WHITE_CHANNEL = 0x01

# Channels 1-8 are documented for the YN360-II; the III Pro is only confirmed
# on channel 1. See HARDWARE.md.
MIN_CHANNEL = 1
MAX_CHANNEL = 8


class WhiteState(NamedTuple):
    """A white-mode state as carried in a 0xAA frame."""

    channel: int
    cool: int
    warm: int


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


def build_white_command(cool: int, warm: int, channel: int = WHITE_CHANNEL) -> bytes:
    """Frame for white mode: [0xAE, 0xAA, channel, cool, warm, 0x56].

    cool/warm 0-100; channel 1-8.
    """
    _require_range("channel", channel, MIN_CHANNEL, MAX_CHANNEL)
    _require_range("cool", cool, 0, 100)
    _require_range("warm", warm, 0, 100)
    return bytes([HEADER, CMD_WHITE, channel, cool, warm, FOOTER])


def build_standby_command(cool: int, warm: int, channel: int = WHITE_CHANNEL) -> bytes:
    """Frame for standby-off: [0xAE, 0xEE, channel, cool, warm, 0x56].

    Documented by pinchies/YN360_webbtle as an off that keeps the current
    values loaded. Unverified on the III Pro — see HARDWARE.md.
    """
    _require_range("channel", channel, MIN_CHANNEL, MAX_CHANNEL)
    _require_range("cool", cool, 0, 100)
    _require_range("warm", warm, 0, 100)
    return bytes([HEADER, CMD_STANDBY, channel, cool, warm, FOOTER])


def parse_white_notification(data: bytes) -> WhiteState | None:
    """Parse a 6-byte notify frame into a WhiteState, or None if it is not one."""
    if len(data) != 6 or data[0] != HEADER or data[5] != FOOTER:
        return None
    if data[1] != CMD_WHITE:
        return None
    channel, cool, warm = data[2], data[3], data[4]
    if cool > 100 or warm > 100:
        return None
    return WhiteState(channel, cool, warm)


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


def cool_warm_to_kelvin(cool: int, warm: int) -> tuple[int, float] | None:
    """Inverse of kelvin_to_cool_warm: (cool, warm) -> (kelvin, brightness).

    Returns None when both channels are 0, which carries no colour information.
    """
    _require_range("cool", cool, 0, 100)
    _require_range("warm", warm, 0, 100)
    total = cool + warm
    if total == 0:
        return None
    percent_cool = cool / total
    kelvin = round(
        WHITE_MIN_KELVIN + percent_cool * (WHITE_MAX_KELVIN - WHITE_MIN_KELVIN)
    )
    return kelvin, min(1.0, total / 100)


def scale_rgb(r: int, g: int, b: int, brightness: float = 1.0) -> tuple[int, int, int]:
    """Scale an RGB triple by brightness (0.0-1.0), returning ints 0-255."""
    brightness = _clamp(brightness, 0.0, 1.0)
    return (round(r * brightness), round(g * brightness), round(b * brightness))
