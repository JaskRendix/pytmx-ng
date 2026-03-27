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
from collections.abc import Callable
from copy import deepcopy
from typing import Any
from xml.etree import ElementTree

from .utils import convert_to_bool

logger = logging.getLogger(__name__)


def wrap_type(fn: Callable[[Any], Any]) -> Callable[[str | None], Any]:
    return lambda x: fn(x) if x is not None else fn("")


# used to change the unicode string returned from xml to
# proper python variable types.
CastFunc = Callable[[str | None], Any]

raw_types: dict[str, Callable[[Any], Any]] = {
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
    "nextlayerid": int,
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

types: defaultdict[str, Callable[[str | None], Any]] = defaultdict(lambda: str)
types.update({k: wrap_type(v) for k, v in raw_types.items()})


def resolve_to_class(value: str, custom_types: dict[str, Any]) -> Any:
    """Convert Tiled custom type name to its defined Python object copy."""
    if value not in custom_types:
        raise ValueError(f"Custom type {value} not found.")
    return deepcopy(custom_types[value])


# casting for properties type
prop_type: dict[str, Callable[[str | None], Any]] = {
    "bool": wrap_type(convert_to_bool),
    "color": wrap_type(str),
    "file": wrap_type(str),
    "float": wrap_type(float),
    "int": wrap_type(int),
    "list": lambda v: v,  # Will be handled specially in parse_properties
    "object": wrap_type(int),
    "string": wrap_type(str),
    "class": lambda v: resolve_to_class(v or "", {}),
    "enum": wrap_type(str),
}


def parse_properties(
    node: ElementTree.Element, customs: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Parse a Tiled XML node and return a property dict.

    This parses `<properties>` children and casts their values according to
    `prop_type`. If a property is of type `class`, it instantiates a new
    object (via `resolve_to_class`) and recursively assigns nested members.
    If a property is of type `list`, it parses the nested `<item>` elements.
    """

    def parse_list_items(list_node: ElementTree.Element) -> list[Any]:
        """Recursively parse list items from a list property node."""
        items = []
        for item_node in list_node.findall("item"):
            item_type = item_node.get("type")
            item_value = item_node.get("value") or item_node.text

            if item_type == "list":
                # Handle nested lists recursively
                items.append(parse_list_items(item_node))
            else:
                caster = prop_type.get(item_type or "", str)
                items.append(caster(item_value))
        return items

    result: dict[str, Any] = {}
    for child in node.findall("properties"):
        for subnode in child.findall("property"):
            name = subnode.get("name")
            value = subnode.get("value") or subnode.text
            type_str = subnode.get("type")

            if name is None:
                continue

            if type_str == "class":
                class_name = subnode.get("propertytype")
                if class_name is None:
                    raise ValueError("Missing 'propertytype' for class property.")
                new_obj = resolve_to_class(class_name, customs or {})
                nested_props = parse_properties(subnode, customs)
                for key, val in nested_props.items():
                    setattr(new_obj, key, val)
                result[name] = new_obj
            elif type_str == "list":
                # Parse list items with support for arbitrary nesting
                result[name] = parse_list_items(subnode)
            else:
                caster = prop_type.get(type_str or "", str)
                result[name] = caster(value)
    return result
