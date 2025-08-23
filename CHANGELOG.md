# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to
Semantic Versioning.

## [Unreleased]

Nothing yet.

## [3.34.1] - 2025-08-23

- Closed PRs:
  - #18: Docs — Improve type hints and docstrings across core modules (by @pnearing) — merged 2025-08-22 — https://github.com/pnearing/pytmx-ng/pull/18
  - #17: Refactor TileFlags, Point and AnimationFrame from namedtuple to typing.NamedTuple (by @JaskRendix) — merged 2025-08-22 — https://github.com/pnearing/pytmx-ng/pull/17
  - #16: fix — add validation check for unknown custom types in resolve_to_class function (by @pnearing) — merged 2025-08-22 — https://github.com/pnearing/pytmx-ng/pull/16
  - #15: Refactor TiledElement with Abstract Base Class and Unit Tests (by @JaskRendix) — merged 2025-08-22 — https://github.com/pnearing/pytmx-ng/pull/15
  - #14: chore — add type hints to function signatures and docstrings (by @pnearing) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/14
  - #13: feat — add zstd compression support and handle ValueError in gid lookup (by @pnearing) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/13
  - #12: fix — replace generic exceptions with specific error types across all modules (by @pnearing) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/12
  - #11: Fix Incorrect Image Path Resolution for External Tilesets + Fix Pyglet Demo (by @JaskRendix) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/11
  - #10: Refactor TiledObject Parsing (by @JaskRendix) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/10
  - #9: Split CI Workflow and Add PR Test Trigger (by @JaskRendix) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/9
  - #8: Refactor TiledTileset: improved parsing, path resolution, and type consistency (by @JaskRendix) — merged 2025-08-21 — https://github.com/pnearing/pytmx-ng/pull/8

## [3.33.1] - 2025-08-18

- Fixed: Prevent cross-test leakage of `TiledElement.allow_duplicate_names` by
  resetting the class flag during `TiledElement` initialization. Ensures reserved
  name checks behave consistently unless explicitly overridden.
- Docs: Overhauled `readme.md` for `pytmx-ng` (fork notice, install instructions,
  badges, and notes on differences from upstream).
- Packaging: Declared README content type in `pyproject.toml` to ensure correct
  rendering on PyPI; version bumped to 3.33.1; validated with `twine check`.
- CI/Tests: All tests pass locally (25 passed).

## [3.33.0] - 2025-08-18

- First `pytmx-ng` release forked from `pytmx`.
- Added: Points for rectangle objects.
- Fixed: Rotated coordinates for tile objects.
- Added: Expanded object type support across loaders and core types.
- Maintained: Import path remains `pytmx` for drop-in compatibility.

[3.33.1]: https://pypi.org/project/pytmx-ng/3.33.1/
[3.33.0]: https://pypi.org/project/pytmx-ng/3.33.0/

