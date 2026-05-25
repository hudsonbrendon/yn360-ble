import pytest

from yn360.protocol import build_rgb_command


def test_build_rgb_command_orange():
    assert build_rgb_command(255, 153, 0) == b"\xae\xa1\xff\x99\x00\x56"


def test_build_rgb_command_black():
    assert build_rgb_command(0, 0, 0) == b"\xae\xa1\x00\x00\x00\x56"


def test_build_rgb_command_rejects_out_of_range():
    with pytest.raises(ValueError):
        build_rgb_command(256, 0, 0)
