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

Utility functions for pytmx.

This module contains helper functions that are independent of the core
classes and can be reused across the package.
"""

from __future__ import annotations

import gzip
import math
import struct
import zlib
from base64 import b64decode
from collections.abc import Callable, Sequence
from logging import getLogger
from math import cos, radians, sin
from typing import Any, Optional, Union

logger = getLogger(__name__)

try:
    import zstd as zstd_module
except ImportError:
    logger.warning("zstd compression is not installed. Disabling zstd support.")
    zstd_module = None

from .constants import (
    GID_MASK,
    GID_TRANS_FLIPX,
    GID_TRANS_FLIPY,
    GID_TRANS_ROT,
    Point,
    TileFlags,
    empty_flags,
    flag_cache,
)


def default_image_loader(
    filename: str, flags: Any, **kwargs: Any
) -> Callable[[Any, Any], tuple[str, Any, Any]]:
    """Return a lazy image loader that carries filename, rect, and flags.

    This default loader allows loading a map without actually decoding images.
    It returns a callable that, when invoked, returns a tuple with the
    filename, the rectangle within the image (if any), and the flags
    requested by the caller.
    """

    def load(rect: Any = None, flags: Any = None) -> tuple[str, Any, Any]:
        return filename, rect, flags

    return load


def get_rotation_from_flags(flags: TileFlags) -> int:
    """Determine the rotation angle from TileFlags."""
    if flags.flipped_diagonally:
        if flags.flipped_horizontally and not flags.flipped_vertically:
            return 90
        elif flags.flipped_horizontally and flags.flipped_vertically:
            return 180
        elif not flags.flipped_horizontally and flags.flipped_vertically:
            return 270
    return 0


def decode_gid(raw_gid: int) -> tuple[int, TileFlags]:
    """Decode a GID from TMX data into a base GID and its transform flags."""
    if raw_gid < GID_TRANS_ROT:
        return raw_gid, empty_flags

    # Check if the GID is already in the cache
    if raw_gid in flag_cache:
        return raw_gid & ~GID_MASK, flag_cache[raw_gid]

    # Calculate and cache the flags
    flags = TileFlags(
        raw_gid & GID_TRANS_FLIPX == GID_TRANS_FLIPX,
        raw_gid & GID_TRANS_FLIPY == GID_TRANS_FLIPY,
        raw_gid & GID_TRANS_ROT == GID_TRANS_ROT,
    )
    flag_cache[raw_gid] = flags
    return raw_gid & ~GID_MASK, flags


def reshape_data(gids: list[int], width: int) -> list[list[int]]:
    """Change 1D list of GIDs to a 2D list with rows of given width."""
    return [gids[i : i + width] for i in range(0, len(gids), width)]


def unpack_gids(
    text: str,
    encoding: Optional[str] = None,
    compression: Optional[str] = None,
) -> list[int]:
    """Return all GIDs from encoded/compressed layer data."""
    if encoding == "base64":
        data = b64decode(text)
        if compression == "gzip":
            data = gzip.decompress(data)
        elif compression == "zlib":
            data = zlib.decompress(data)
        elif compression == "zstd":
            if zstd_module:
                data = zstd_module.decompress(data)
            else:
                raise ValueError("zstd compression is not installed.")
        elif compression:
            raise ValueError(f"layer compression {compression} is not supported.")
        fmt = "<%dL" % (len(data) // 4)
        return list(struct.unpack(fmt, data))
    elif encoding == "csv":
        if not text.strip():
            return []
        return [int(i) for i in text.split(",")]
    elif encoding:
        raise ValueError(f"layer encoding {encoding} is not supported.")
    else:
        # When no encoding is provided, Tiled may have inline <tile gid="..."/> entries;
        # the caller is responsible for that path and providing already-parsed integers.
        return []


def convert_to_bool(value: Optional[Union[str, int, float]] = None) -> bool:
    """Convert common text/number variants to a boolean value.

    Recognizes: 1, y, t, true, yes as True
                -, 0, n, f, false, no as False
    """
    value = str(value).strip()
    if value:
        value = value.lower()[0]
        if value in ("1", "y", "t", "true", "yes"):
            return True
        if value in ("-", "0", "n", "f", "false", "no"):
            return False
    else:
        return False
    raise ValueError(f'cannot parse "{value}" as bool')


def rotate(
    points: Sequence[Point],
    origin: Point,
    angle: Union[int, float],
) -> list[Point]:
    """Rotate a sequence of points around an origin by angle degrees."""
    sin_t = sin(radians(angle))
    cos_t = cos(radians(angle))
    new_points = []
    for point in points:
        x = origin.x + (cos_t * (point.x - origin.x) - sin_t * (point.y - origin.y))
        y = origin.y + (sin_t * (point.x - origin.x) + cos_t * (point.y - origin.y))
        new_points.append(Point(x, y))
    return new_points


def decode_chunk_data(
    text: str, encoding: Optional[str], compression: Optional[str]
) -> tuple[list[int], bytes]:
    """
    Decode and decompress chunk data from a Tiled map.

    Args:
        text: The raw text content of the chunk.
        encoding: The encoding format (e.g., "base64", "csv").
        compression: The compression method (e.g., "zlib", "gzip", "zstd").

    Returns:
        A tuple of (gids, raw_data), where:
            - gids is a list of tile GIDs
            - raw_data is the binary representation used to unpack GIDs
    """
    if encoding == "base64":
        raw_data = b64decode(text.strip())

        if compression == "zlib":
            raw_data = zlib.decompress(raw_data)
        elif compression == "gzip":
            raw_data = gzip.decompress(raw_data)
        elif compression == "zstd":
            if zstd_module:
                raw_data = zstd_module.decompress(raw_data)
            else:
                raise ValueError("zstd compression is not installed.")
        elif compression:
            raise ValueError(f"Unsupported compression: {compression}")

        fmt = "<%dL" % (len(raw_data) // 4)
        gids = list(struct.unpack(fmt, raw_data))

    elif encoding == "csv":
        gids = [int(i) for i in text.strip().split(",")]
        raw_data = b""  # CSV has no binary representation

    elif encoding:
        raise ValueError(f"Unsupported encoding: {encoding}")

    else:
        gids = []
        raw_data = b""

    return gids, raw_data


def generate_rectangle_points(
    x: float, y: float, width: float, height: float
) -> tuple[Point, ...]:
    return (
        Point(x, y),
        Point(x + width, y),
        Point(x + width, y + height),
        Point(x, y + height),
    )


def generate_ellipse_points(
    x: float, y: float, width: float, height: float, segments: int = 16
) -> list[Point]:
    cx = x + width / 2
    cy = y + height / 2
    rx = width / 2
    ry = height / 2
    return [
        Point(cx + rx * math.cos(theta), cy + ry * math.sin(theta))
        for theta in [2 * math.pi * i / segments for i in range(segments)]
    ]
