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

from typing import TYPE_CHECKING, Any, Optional, Self
from xml.etree import ElementTree

from .constants import Point
from .element import TiledElement
from .shape import parse_shape_data
from .template import apply_template_to_object
from .utils import generate_rectangle_points, rotate

if TYPE_CHECKING:
    from .map import TiledMap


class TiledObject(TiledElement):
    """
    Represents any Tiled Object.

    Supported types: Box, Ellipse, Tile Object, Polyline, Polygon, Text, Point.
    """

    def __init__(
        self,
        parent: "TiledMap",
        node: ElementTree.Element,
        custom_types: dict[str, Any],
    ) -> None:
        super().__init__()
        self.parent = parent
        self.node = node  # Save for fallback shape parsing

        # defaults from the specification
        self.id: int = 0
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.object_type: str = "rectangle"
        self.x: int = 0
        self.y: int = 0
        self.width: int = 0
        self.height: int = 0
        self.rotation: int = 0
        self.gid: int = 0
        self.visible: bool = True
        self.closed = True
        self.template: Optional[str] = None
        self.custom_types = custom_types

        # Text
        self.text: Optional[str] = None
        self.font_family: str = "Sans Serif"
        self.pixel_size: int = 16
        self.wrap: bool = False
        self.bold: bool = False
        self.italic: bool = False
        self.underline: bool = False
        self.strike_out: bool = False
        self.kerning: bool = True
        self.h_align: str = "left"
        self.v_align: str = "top"
        self.color: str = "#000000FF"

        self.parse_xml(node)

    @property
    def image(self) -> Any:
        """Image for the object, if assigned.

        Returns:
            Any: The image object type will depend on the loader (ie. pygame.Surface).
        """
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """Parse a TiledObject layer from ElementTree XML node."""

        self.name = node.get("name")
        self._set_properties(node, self.custom_types)

        if self.gid:
            self.object_type = "tile"
            self.gid = self.parent.register_gid_check_flags(self.gid)

        self.template = node.get("template")
        if self.template:
            template_obj = self.parent._load_template(self.template)
            if template_obj:
                apply_template_to_object(self, node, template_obj, self.custom_types)

        points = parse_shape_data(self, node)

        if points:
            xs, ys = zip(*[(p.x, p.y) for p in points])
            self.width = max(xs) - min(xs)
            self.height = max(ys) - min(ys)
            self.points = tuple(points)
        elif self.object_type == "rectangle":
            self.points = generate_rectangle_points(
                self.x, self.y, self.width, self.height
            )

        return self

    def apply_transformations(self) -> list[Point]:
        """Return all points for object, taking in account rotation."""
        if hasattr(self, "points"):
            return rotate(self.points, Point(self.x, self.y), self.rotation)
        else:
            return rotate(self.as_points, Point(self.x, self.y), self.rotation)

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

    @property
    def as_ellipse(self) -> Optional[tuple[Point, float, float]]:
        """Return center and radii of the ellipse, if applicable.

        Returns:
            Optional[tuple[Point, float, float]]: (center, radius_x, radius_y)
        """
        if self.object_type == "ellipse":
            center = Point(self.x + self.width / 2, self.y + self.height / 2)
            radius_x = self.width / 2
            radius_y = self.height / 2
            return (center, radius_x, radius_y)
        return None
