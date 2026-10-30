import pytest

from yn360.__main__ import build_parser


def test_parser_rgb_args():
    args = build_parser().parse_args(["rgb", "AA:BB:CC:DD:EE:FF", "255", "153", "0"])
    assert args.command == "rgb"
    assert args.address == "AA:BB:CC:DD:EE:FF"
    assert (args.r, args.g, args.b) == (255, 153, 0)


def test_parser_white_args():
    args = build_parser().parse_args(["white", "AA:BB:CC:DD:EE:FF", "4500"])
    assert args.command == "white"
    assert args.kelvin == 4500


def test_parser_white_channel_defaults_to_one():
    args = build_parser().parse_args(["white", "AA:BB:CC:DD:EE:FF", "4500"])
    assert args.channel == 1


def test_parser_white_accepts_channel():
    args = build_parser().parse_args(["white", "AA:BB:CC:DD:EE:FF", "4500", "--channel", "3"])
    assert args.channel == 3


def test_parser_requires_subcommand():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_status_and_standby():
    assert build_parser().parse_args(["status", "AA:BB"]).command == "status"
    assert build_parser().parse_args(["standby", "AA:BB"]).command == "standby"
