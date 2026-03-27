"""
Copyright (C) 2012-2024, Leif Theden <leif.theden@gmail.com>

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
License along with pytmx.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

logger = logging.getLogger(__name__)

# Expose the installed package version. When running from a source checkout
# without installed metadata, fall back to a sentinel string.
try:
    __version__ = version("pytmx-ng")
except PackageNotFoundError:
    __version__ = "0+unknown"

# Import main classes from pytmx module
from .pytmx import (
    TiledClassType,
    TiledElement,
    TiledGroupLayer,
    TiledImageLayer,
    TiledMap,
    TiledObject,
    TiledObjectGroup,
    TiledProperty,
    TiledTileLayer,
    TiledTileset,
    TileFlags,
    convert_to_bool,
    decode_gid,
    parse_properties,
    resolve_to_class,
    unpack_gids,
)

__all__ = [
    "TiledMap",
    "TiledElement",
    "TiledGroupLayer",
    "TiledImageLayer",
    "TiledObject",
    "TiledObjectGroup",
    "TiledTileLayer",
    "TiledProperty",
    "TiledClassType",
    "TiledTileset",
    "TileFlags",
    "convert_to_bool",
    "resolve_to_class",
    "parse_properties",
    "decode_gid",
    "unpack_gids",
]
