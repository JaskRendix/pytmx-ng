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

Property parsing and casting for pytmx.

This module provides the casting maps used to coerce XML attribute strings
into appropriate Python types, and the `parse_properties` function that
reads Tiled custom properties.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from copy import deepcopy
from typing import Optional
from xml.etree import ElementTree

from .utils import convert_to_bool

logger = logging.getLogger(__name__)

# used to change the unicode string returned from xml to
# proper python variable types.
types = defaultdict(lambda: str)

types.update(
    {
        "backgroundcolor": str,
        "bold": convert_to_bool,
        "color": str,
        "columns": int,
        "compression": str,
        "draworder": str,
        "duration": int,
        "encoding": str,
        "firstgid": int,
        "fontfamily": str,
        "format": str,
        "gid": int,
        "halign": str,
        "height": float,
        "hexsidelength": float,
        "id": int,
        "italic": convert_to_bool,
        "kerning": convert_to_bool,
        "margin": int,
        "name": str,
        "nextobjectid": int,
        "offsetx": int,
        "offsety": int,
        "opacity": float,
        "orientation": str,
        "pixelsize": float,
        "points": str,
        "probability": float,
        "renderorder": str,
        "rotation": float,
        "source": str,
        "spacing": int,
        "staggeraxis": str,
        "staggerindex": str,
        "strikeout": convert_to_bool,
        "terrain": str,
        "tile": int,
        "tilecount": int,
        "tiledversion": str,
        "tileheight": int,
        "tileid": int,
        "tilewidth": int,
        "trans": str,
        "type": str,
        "underline": convert_to_bool,
        "valign": str,
        "value": str,
        "version": str,
        "visible": convert_to_bool,
        "width": float,
        "wrap": convert_to_bool,
        "x": float,
        "y": float,
    }
)


def resolve_to_class(value: str, custom_types: dict):
    """Convert Tiled custom type name to its defined Python object copy."""
    return deepcopy(custom_types[value])


# casting for properties type
prop_type = {
    "bool": convert_to_bool,
    "color": str,
    "file": str,
    "float": float,
    "int": int,
    "object": int,
    "string": str,
    "class": resolve_to_class,
    "enum": str,
}


def parse_properties(node: ElementTree.Element, customs: Optional[dict] = None) -> dict:
    """Parse a Tiled XML node and return a property dict.

    This parses `<properties>` children and casts their values according to
    `prop_type`. If a property is of type `class`, it instantiates a new
    object (via `resolve_to_class`) and recursively assigns nested members.
    """
    d = dict()
    for child in node.findall("properties"):
        for subnode in child.findall("property"):
            cls = None
            try:
                if "type" in subnode.keys():
                    cls = prop_type[subnode.get("type")]
            except Exception:
                logger.info(
                    f"Type {subnode.get('type')} not a built-in type. Defaulting to string-cast."
                )

            if "class" == subnode.get("type"):
                new = resolve_to_class(subnode.get("propertytype"), customs or {})
                properties = parse_properties(subnode, customs)
                for key in properties.keys():
                    setattr(new, key, properties[key])
                d[subnode.get("name")] = new
            else:
                d[subnode.get("name")] = subnode.get("value") or subnode.text
                if cls is not None:
                    d[subnode.get("name")] = cls(subnode.get("value"))
    return d
