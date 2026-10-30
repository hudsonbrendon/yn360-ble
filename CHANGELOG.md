# Changelog

## [Unreleased]

### Changed
- Tooling: hatchling>=1.27, PEP 639 license metadata, PEP 735 `[dependency-groups]`
  with `uv.lock`, ruff `select = ["ALL"]`, mypy strict, pytest-cov/pytest-timeout,
  Python 3.14 classifier, `py.typed`. CI runs on uv (`uv sync --frozen`), release
  builds with `uv build` and publishes via trusted publishing. `__version__` now
  comes from `importlib.metadata`.

## [0.3.0]

See the GitHub release notes for this and earlier versions.
