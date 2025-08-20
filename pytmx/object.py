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

from .element import TiledElement
from .constants import Point
from .utils import rotate


class TiledObject(TiledElement):
    """Represents any Tiled Object.

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
            """
            Parse a text string of float tuples and return [(x,...),...]

            """
            return tuple(tuple(map(float, i.split(","))) for i in text.split())

        self._set_properties(node, self.custom_types)

        # correctly handle "tile objects" (object with gid set)
        if self.gid:
            self.object_type = "tile"  # set the object type to tile
            self.gid = self.parent.register_gid_check_flags(self.gid)

        points = None
        polygon = node.find("polygon")
        if polygon is not None:
            self.object_type = "polygon"
            points = read_points(polygon.get("points"))
            self.closed = True

        polyline = node.find("polyline")
        if polyline is not None:
            self.object_type = "polyline"
            points = read_points(polyline.get("points"))
            self.closed = False

        ellipse = node.find("ellipse")
        if ellipse is not None:
            self.object_type = "ellipse"

        point = node.find("point")
        if point is not None:
            self.object_type = "point"

        text = node.find("text")
        if text is not None:
            self.object_type = "text"
            # NOTE: The defaults have been taken from the tiled editor version 1.11.0
            self.text = text.text
            self.font_family = text.get("fontfamily", "Sans Serif")
            # Not sure if this is really font size or not, but it's called
            # pixel size in the .tmx file.
            self.pixel_size = int(text.get("pixelsize", 16))
            self.wrap = bool(text.get("wrap", False))
            self.bold = bool(text.get("bold", False))
            self.italic = bool(text.get("italic", False))
            self.underline = bool(text.get("underline", False))
            self.strike_out = bool(text.get("strikeout", False))
            self.kerning = bool(text.get("kerning", True))
            self.h_align = text.get("halign", "left")
            self.v_align = text.get("valign", "top")
            self.color = text.get("color", "#000000FF")

        if points:
            xs, ys = zip(*points)
            self.width = max(xs) - min(xs)
            self.height = max(ys) - min(ys)
            self.points = tuple([Point(i[0] + self.x, i[1] + self.y) for i in points])
        # Set the points for a rectangle
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

