import pytest

from yn360.protocol import build_rgb_command


def test_build_rgb_command_orange():
    assert build_rgb_command(255, 153, 0) == b"\xae\xa1\xff\x99\x00\x56"


def test_build_rgb_command_black():
    assert build_rgb_command(0, 0, 0) == b"\xae\xa1\x00\x00\x00\x56"


def test_build_rgb_command_rejects_out_of_range():
    with pytest.raises(ValueError):
        build_rgb_command(256, 0, 0)


from yn360.protocol import build_off_command


def test_build_off_command():
    assert build_off_command() == b"\xae\xa3\x00\x00\x00\x56"


from yn360.protocol import build_white_command


def test_build_white_command_full_cool():
    assert build_white_command(100, 0) == b"\xae\xaa\x01\x64\x00\x56"


def test_build_white_command_full_warm():
    assert build_white_command(0, 100) == b"\xae\xaa\x01\x00\x64\x56"


def test_build_white_command_rejects_over_100():
    with pytest.raises(ValueError):
        build_white_command(101, 0)
