# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to
Semantic Versioning.

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
