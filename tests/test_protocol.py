import pytest

from yn360 import const
from yn360.protocol import (
    WhiteState,
    build_off_command,
    build_rgb_command,
    build_standby_command,
    build_white_command,
    cool_warm_to_kelvin,
    kelvin_to_cool_warm,
    parse_white_notification,
    scale_rgb,
)


def test_build_rgb_command_orange():
    assert build_rgb_command(255, 153, 0) == b"\xae\xa1\xff\x99\x00\x56"


def test_build_rgb_command_black():
    assert build_rgb_command(0, 0, 0) == b"\xae\xa1\x00\x00\x00\x56"


def test_build_rgb_command_rejects_out_of_range():
    with pytest.raises(ValueError):
        build_rgb_command(256, 0, 0)


def test_build_off_command():
    assert build_off_command() == b"\xae\xa3\x00\x00\x00\x56"


def test_build_white_command_full_cool():
    assert build_white_command(100, 0) == b"\xae\xaa\x01\x64\x00\x56"


def test_build_white_command_full_warm():
    assert build_white_command(0, 100) == b"\xae\xaa\x01\x00\x64\x56"


def test_build_white_command_rejects_over_100():
    with pytest.raises(ValueError):
        build_white_command(101, 0)


def test_kelvin_min_is_pure_warm():
    assert kelvin_to_cool_warm(3200, 1.0) == (0, 100)


def test_kelvin_max_is_pure_cool():
    assert kelvin_to_cool_warm(5500, 1.0) == (100, 0)


def test_kelvin_midpoint_is_balanced():
    assert kelvin_to_cool_warm(4350, 1.0) == (50, 50)


def test_kelvin_brightness_scales_both_channels():
    assert kelvin_to_cool_warm(5500, 0.5) == (50, 0)


def test_kelvin_out_of_range_is_clamped():
    assert kelvin_to_cool_warm(1000, 1.0) == (0, 100)
    assert kelvin_to_cool_warm(9000, 1.0) == (100, 0)


def test_scale_rgb_half_brightness():
    assert scale_rgb(200, 100, 50, 0.5) == (100, 50, 25)


def test_scale_rgb_full_brightness_is_identity():
    assert scale_rgb(255, 153, 0, 1.0) == (255, 153, 0)


def test_scale_rgb_clamps_brightness():
    assert scale_rgb(200, 200, 200, 2.0) == (200, 200, 200)
    assert scale_rgb(200, 200, 200, -1.0) == (0, 0, 0)


def test_build_white_command_channel():
    assert build_white_command(100, 0, channel=3) == b"\xae\xaa\x03\x64\x00\x56"


def test_build_white_command_rejects_bad_channel():
    with pytest.raises(ValueError):
        build_white_command(50, 50, channel=0)
    with pytest.raises(ValueError):
        build_white_command(50, 50, channel=9)


def test_build_standby_command():
    assert build_standby_command(50, 50) == b"\xae\xee\x01\x32\x32\x56"


def test_build_standby_command_channel():
    assert build_standby_command(50, 50, channel=2) == b"\xae\xee\x02\x32\x32\x56"


def test_parse_white_notification_roundtrip():
    assert parse_white_notification(b"\xae\xaa\x01\x32\x32\x56") == WhiteState(1, 50, 50)


def test_parse_white_notification_rejects_garbage():
    assert parse_white_notification(b"") is None
    assert parse_white_notification(b"\xae\xa1\x0a\x00\x00\x56") is None  # rgb frame
    assert parse_white_notification(b"\xae\xaa\x01\xff\x32\x56") is None  # cool > 100
    assert parse_white_notification(b"\x00\xaa\x01\x32\x32\x56") is None  # bad header
    assert parse_white_notification(b"\xae\xaa\x01\x32\x32\x00") is None  # bad footer


def test_cool_warm_to_kelvin_inverts_kelvin_to_cool_warm():
    for kelvin, brightness in [(3200, 1.0), (5500, 1.0), (4350, 1.0), (5500, 0.5)]:
        cool, warm = kelvin_to_cool_warm(kelvin, brightness)
        result = cool_warm_to_kelvin(cool, warm)
        assert result is not None
        got_kelvin, got_brightness = result
        assert abs(got_kelvin - kelvin) <= 25
        assert abs(got_brightness - brightness) <= 0.02


def test_cool_warm_to_kelvin_zero_is_none():
    assert cool_warm_to_kelvin(0, 0) is None


def test_cool_warm_to_kelvin_rejects_out_of_range():
    with pytest.raises(ValueError):
        cool_warm_to_kelvin(101, 0)


def test_uuids_are_lowercase_canonical():
    assert const.SERVICE_UUID == "f000aa60-0451-4000-b000-000000000000"
    assert const.WRITE_CHAR_UUID == "f000aa61-0451-4000-b000-000000000000"
    assert const.NOTIFY_CHAR_UUID == "f000aa63-0451-4000-b000-000000000000"
