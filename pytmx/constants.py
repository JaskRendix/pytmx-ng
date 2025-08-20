"""
Copyright (C) 2012-2025, Leif Theden <leif.theden@gmail.com>

This file is part of pytmx.

pytmx is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

pytmx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with pytmx.  If not, see <https://www.gnu.org/licenses/>.

Constants and simple data structures for pytmx.

This module centralizes bit flags, GID masks, and lightweight namedtuples
so they can be reused across the package without circular imports.

All symbols here are intentionally dependency-free.
"""
from __future__ import annotations

from collections import namedtuple
from typing import Union

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


# --- Bit flags --------------------------------------------------------------
# Internal transform flags used by pytmx
TRANS_FLIPX = 1
TRANS_FLIPY = 2
TRANS_ROT = 4

# Tiled GID transform flags (as stored in TMX data)
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT

# --- Lightweight tuples -----------------------------------------------------
flag_names = ("flipped_horizontally", "flipped_vertically", "flipped_diagonally")

AnimationFrame = namedtuple("AnimationFrame", ["gid", "duration"])  # (int, int)
Point = namedtuple("Point", ["x", "y"])  # (float, float) in practice
TileFlags = namedtuple("TileFlags", flag_names)  # (bool, bool, bool)

# Commonly reused values
empty_flags = TileFlags(False, False, False)

# --- Shared typing aliases (kept simple here to avoid imports) --------------
ColorLike = Union[tuple[int, int, int, int], tuple[int, int, int], int, str]
MapPoint = tuple[int, int, int]
# internal flags
# error message format strings go here


if HAS_PYGAME:
    PointLike = Union[tuple[int, int], pygame.Vector2, Point]
else:
    PointLike = Union[tuple[int, int], Point]
