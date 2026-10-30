"""yn360-ble: control Yongnuo YN360 LED lights over Bluetooth LE."""

from importlib import metadata

from .light import YN360Light
from .protocol import WhiteState, cool_warm_to_kelvin
from .scanner import discover

__all__ = ["WhiteState", "YN360Light", "cool_warm_to_kelvin", "discover"]

try:
    __version__ = metadata.version("yn360-ble")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
