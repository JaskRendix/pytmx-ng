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
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, TypedDict
from xml.etree import ElementTree

from .constants import Point
from .utils import generate_ellipse_points

if TYPE_CHECKING:
    from .object import TiledObject

logger = logging.getLogger(__name__)


class ShapeHandler(TypedDict, total=False):
    type: str
    points_attr: str
    parse: Callable[[str], list[tuple[float, float]]]
    closed: bool


def parse_shape_data(
    obj: "TiledObject", node: ElementTree.Element
) -> Optional[list[Point]]:
    def read_points(text: str) -> list[tuple[float, float]]:
        return [
            (float(x), float(y))
            for x, y in (pair.split(",") for pair in text.strip().split())
        ]

    shape_handlers: dict[str, ShapeHandler] = {
        "polygon": {
            "type": "polygon",
            "points_attr": "points",
            "parse": read_points,
            "closed": True,
        },
        "polyline": {
            "type": "polyline",
            "points_attr": "points",
            "parse": read_points,
            "closed": False,
        },
        "ellipse": {"type": "ellipse"},
        "point": {"type": "point"},
        "text": {"type": "text"},
    }

    for tag, handler in shape_handlers.items():
        subnode = node.find(tag)
        if subnode is not None:
            obj.object_type = handler["type"]

            if tag == "ellipse":

                obj.points = tuple(
                    generate_ellipse_points(obj.x, obj.y, obj.width, obj.height)
                )
                return list(obj.points)

            if tag == "text":
                obj.text = subnode.text or ""
                obj.font_family = subnode.get("fontfamily", "Sans Serif")
                obj.pixel_size = int(subnode.get("pixelsize", 16))
                obj.wrap = subnode.get("wrap", "0") == "1"
                obj.bold = subnode.get("bold", "0") == "1"
                obj.italic = subnode.get("italic", "0") == "1"
                obj.underline = subnode.get("underline", "0") == "1"
                obj.strike_out = subnode.get("strikeout", "0") == "1"
                obj.kerning = subnode.get("kerning", "1") == "1"
                obj.h_align = subnode.get("halign", "left")
                obj.v_align = subnode.get("valign", "top")
                obj.color = subnode.get("color", "#000000FF")

            if "points_attr" in handler:
                raw = subnode.get(handler["points_attr"], "")
                parsed = handler["parse"](raw)
                obj.closed = handler.get("closed", False)
                return [Point(x + obj.x, y + obj.y) for x, y in parsed]

            return None
    return None
