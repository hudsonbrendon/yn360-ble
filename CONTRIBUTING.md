# Contributing

Thanks for helping improve `yn360-ble`!

## Development setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Requires Python 3.11+.

## Guidelines

- Keep `pytest` green and add tests for new behaviour. The protocol layer
  (`src/yn360/protocol.py`) is pure and fully unit-tested; the device layer
  (`src/yn360/light.py`) is tested with a mocked `BleakClient`, so tests need no
  real hardware.
- `ruff check .` must pass.
- Protocol/byte-format changes should be confirmed against real hardware and
  documented in `HARDWARE.md`.

## Releasing

1. Bump the version in `pyproject.toml` and `src/yn360/__init__.py`.
2. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. Create a GitHub release for the tag — the publish workflow builds and uploads
   it to PyPI via Trusted Publishing.
