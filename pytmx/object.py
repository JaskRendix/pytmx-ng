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

Tiled object model and parser.
"""

from xml.etree import ElementTree

from .constants import Point
from .element import TiledElement
from .utils import rotate


class TiledObject(TiledElement):
    """
    Represents any Tiled Object.

    Supported types: Box, Ellipse, Tile Object, Polyline, Polygon, Text, Point.
    """

    def __init__(self, parent, node, custom_types) -> None:
        TiledElement.__init__(self)
        self.parent = parent

        # defaults from the specification
        self.id = 0
        self.name = None
        self.type = None
        self.object_type = "rectangle"
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rotation = 0
        self.gid = 0
        self.visible = 1
        self.closed = True
        self.template = None
        self.custom_types = custom_types

        self.parse_xml(node)

    @property
    def image(self):
        """Image for the object, if assigned.

        Returns:
            ???: The image object type will depend on the loader (ie. pygame.Surface).
        """
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node: ElementTree.Element) -> "TiledObject":
        """Parse an Object from ElementTree xml node.

        Args:
            node (ElementTree.Element): The node to be parsed.

        Returns:
            TiledObject: The parsed xml node.
        """

        def read_points(text) -> tuple[tuple[float, float]]:
            """Parse a text string of float tuples and return [(x,...),...]"""
            return tuple(tuple(map(float, i.split(","))) for i in text.split())

        self._set_properties(node, self.custom_types)

        # Handle tile objects
        if self.gid:
            self.object_type = "tile"
            self.gid = self.parent.register_gid_check_flags(self.gid)

        points = None
        node_handlers = {
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

        for node_name, handler in node_handlers.items():
            subnode = node.find(node_name)
            if subnode is not None:
                self.object_type = handler["type"]

                if node_name == "text":
                    # Inline text property parsing
                    setattr(self, "text", subnode.text)
                    setattr(
                        self, "font_family", subnode.get("fontfamily", "Sans Serif")
                    )
                    setattr(self, "pixel_size", int(subnode.get("pixelsize", 16)))
                    setattr(self, "wrap", bool(subnode.get("wrap", False)))
                    setattr(self, "bold", bool(subnode.get("bold", False)))
                    setattr(self, "italic", bool(subnode.get("italic", False)))
                    setattr(self, "underline", bool(subnode.get("underline", False)))
                    setattr(self, "strike_out", bool(subnode.get("strikeout", False)))
                    setattr(self, "kerning", bool(subnode.get("kerning", True)))
                    setattr(self, "h_align", subnode.get("halign", "left"))
                    setattr(self, "v_align", subnode.get("valign", "top"))
                    setattr(self, "color", subnode.get("color", "#000000FF"))

                if "points_attr" in handler:
                    points = handler["parse"](subnode.get(handler["points_attr"]))
                if "closed" in handler:
                    self.closed = handler["closed"]
                break

        if points:
            xs, ys = zip(*points)
            self.width = max(xs) - min(xs)
            self.height = max(ys) - min(ys)
            self.points = tuple([Point(i[0] + self.x, i[1] + self.y) for i in points])
        elif self.object_type == "rectangle":
            self.points = tuple(
                [
                    Point(self.x, self.y),
                    Point(self.x + self.width, self.y),
                    Point(self.x + self.width, self.y + self.height),
                    Point(self.x, self.y + self.height),
                ]
            )

        return self

    def apply_transformations(self) -> list[Point]:
        """Return all points for object, taking in account rotation."""
        if hasattr(self, "points"):
            return rotate(self.points, self, self.rotation)
        else:
            return rotate(self.as_points, self, self.rotation)

    @property
    def as_points(self) -> list[Point]:
        return [
            Point(*i)
            for i in [
                (self.x, self.y),
                (self.x, self.y + self.height),
                (self.x + self.width, self.y + self.height),
                (self.x + self.width, self.y),
            ]
        ]
