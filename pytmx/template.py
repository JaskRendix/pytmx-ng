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

import logging
from typing import TYPE_CHECKING
from xml.etree import ElementTree

from .shape import parse_shape_data
from .utils import generate_rectangle_points

if TYPE_CHECKING:
    from .object import TiledObject

logger = logging.getLogger(__name__)


def apply_template_to_object(
    obj: "TiledObject",
    node: ElementTree.Element,
    template_obj: "TiledObject",
    custom_types: dict[str, type],
) -> None:
    """Apply template attributes to a TiledObject, overriding with node-specific values."""
    obj.properties.update(template_obj.properties)
    obj._set_properties(node, custom_types)
    obj.properties = {**template_obj.properties, **obj.properties}

    id_str = node.get("id")
    obj.id = int(id_str) if id_str is not None else template_obj.id
    obj.name = node.get("name", template_obj.name)
    obj.type = node.get("type", template_obj.type)
    obj.x = int(float(node.get("x", str(template_obj.x))))
    obj.y = int(float(node.get("y", str(template_obj.y))))
    obj.width = int(float(node.get("width", str(template_obj.width))))
    obj.height = int(float(node.get("height", str(template_obj.height))))
    obj.rotation = int(float(node.get("rotation", str(template_obj.rotation))))
    obj.gid = obj.parent.register_gid_check_flags(int(node.get("gid", 0)))
    obj.visible = node.get("visible", "1") == "1"

    if node.find("polygon") is not None:
        obj.object_type = "polygon"
    elif template_obj.object_type == "polygon":
        obj.object_type = "polygon"

    # Parse shape from object node first
    points = parse_shape_data(obj, node)

    # If no shape found, fall back to template node
    if points is None and hasattr(template_obj, "node"):
        points = parse_shape_data(obj, template_obj.node)

    # Assign points and dimensions if shape was found
    if points:
        xs, ys = zip(*[(p.x, p.y) for p in points])
        obj.width = max(xs) - min(xs)
        obj.height = max(ys) - min(ys)
        obj.points = tuple(points)
    elif obj.object_type == "rectangle":
        obj.points = generate_rectangle_points(obj.x, obj.y, obj.width, obj.height)
