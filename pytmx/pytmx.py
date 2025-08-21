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

"""

from .class_type import TiledClassType
from .constants import TileFlags
from .element import TiledElement
from .group_layer import TiledGroupLayer
from .image_layer import TiledImageLayer
from .map import TiledMap
from .object import TiledObject
from .object_group import TiledObjectGroup
from .properties import parse_properties, resolve_to_class
from .property import TiledProperty
from .tile_layer import TiledTileLayer
from .tileset import TiledTileset
from .utils import convert_to_bool, decode_gid, unpack_gids

__all__ = (
    "TileFlags",
    "TiledElement",
    "TiledImageLayer",
    "TiledMap",
    "TiledGroupLayer",
    "TiledObject",
    "TiledObjectGroup",
    "TiledTileLayer",
    "TiledProperty",
    "TiledClassType",
    "TiledTileset",
    "convert_to_bool",
    "resolve_to_class",
    "parse_properties",
    "decode_gid",
    "unpack_gids",
)
