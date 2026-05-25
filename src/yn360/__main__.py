"""Command-line tool for hands-on control: `python -m yn360 ...`."""

from __future__ import annotations

import argparse
import asyncio

from .light import YN360Light
from .scanner import discover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yn360", description="Control a Yongnuo YN360 over BLE")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="scan for nearby YN360 lights")

    p_rgb = sub.add_parser("rgb", help="set an RGB color")
    p_rgb.add_argument("address")
    p_rgb.add_argument("r", type=int)
    p_rgb.add_argument("g", type=int)
    p_rgb.add_argument("b", type=int)

    p_white = sub.add_parser("white", help="set a white color temperature in Kelvin")
    p_white.add_argument("address")
    p_white.add_argument("kelvin", type=int)

    p_off = sub.add_parser("off", help="turn the light off")
    p_off.add_argument("address")

    return parser


async def _run(args: argparse.Namespace) -> None:
    if args.command == "scan":
        devices = await discover()
        if not devices:
            print("No YN360 devices found.")
            return
        for d in devices:
            print(f"{d.address}  {d.name}")
        return

    light = YN360Light(args.address)
    try:
        if args.command == "rgb":
            await light.set_rgb(args.r, args.g, args.b)
        elif args.command == "white":
            await light.set_white(args.kelvin)
        elif args.command == "off":
            await light.turn_off()
    finally:
        await light.disconnect()


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
