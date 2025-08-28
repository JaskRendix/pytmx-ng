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

from typing import TYPE_CHECKING, Any, Optional

try:  # Python 3.11+
    from typing import Self  # type: ignore
except Exception:  # Python < 3.11
    from typing_extensions import Self  # type: ignore

from xml.etree import ElementTree

from .constants import Point
from .element import TiledElement
from .shape import parse_shape_data
from .template import apply_template_to_object
from .utils import (
    compute_adjusted_position,
    generate_rectangle_points,
    is_convex,
    point_in_polygon,
    rotate,
)

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
        """Returns corner points of the object as a rectangle."""
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

    def get_bounding_box(self) -> tuple[int, int, int, int]:
        """Calculates the axis-aligned bounding box of the object."""
        rotated_points = self.apply_transformations()
        xs = [p.x for p in rotated_points]
        ys = [p.y for p in rotated_points]
        return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

    def collides_with_point(self, x: int, y: int) -> bool:
        """Checks whether a point lies within the object."""
        point = Point(x, y)

        if self.object_type == "rectangle":
            return point_in_polygon(point, self.apply_transformations())

        elif self.object_type == "ellipse":
            ellipse = self.as_ellipse
            if ellipse:
                center, rx, ry = ellipse
                dx = x - center.x
                dy = y - center.y
                return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1

        elif isinstance(self.points, tuple) and self.points:
            return point_in_polygon(point, self.apply_transformations())

        return False

    def intersects_with_rect(self, other_rect: tuple[int, int, int, int]) -> bool:
        """Checks whether the object intersects with a given rectangle."""
        self_rect = self.get_bounding_box()
        return (
            self_rect[0] < other_rect[2]
            and self_rect[2] > other_rect[0]
            and self_rect[1] < other_rect[3]
            and self_rect[3] > other_rect[1]
        )

    def intersects_with_object(self, other: "TiledObject") -> bool:
        """Checks whether this object intersects with another TiledObject."""
        return self.intersects_with_rect(other.get_bounding_box())

    def intersects_with_polygon(self, other: "TiledObject") -> bool:
        """Checks polygonal intersection using Separating Axis Theorem."""
        poly1 = self.apply_transformations()
        poly2 = other.apply_transformations()

        if not is_convex(poly1) or not is_convex(poly2):
            raise ValueError("SAT requires convex polygons.")

        def get_axes(polygon: list[Point]) -> list[Point]:
            axes = []
            for i in range(len(polygon)):
                p1 = polygon[i]
                p2 = polygon[(i + 1) % len(polygon)]
                edge = Point(p2.x - p1.x, p2.y - p1.y)
                normal = Point(-edge.y, edge.x)  # Perpendicular
                length = (normal.x**2 + normal.y**2) ** 0.5
                axes.append(Point(normal.x / length, normal.y / length))
            return axes

        def project(polygon: list[Point], axis: Point) -> tuple[float, float]:
            dots = [p.x * axis.x + p.y * axis.y for p in polygon]
            return min(dots), max(dots)

        axes = get_axes(poly1) + get_axes(poly2)

        for axis in axes:
            min1, max1 = project(poly1, axis)
            min2, max2 = project(poly2, axis)
            if max1 < min2 or max2 < min1:
                return False  # Found a separating axis

        return True  # No separating axis found

    def adjust_gid_object_position(
        self,
        orientation: str,
        rotation: int,
        tilewidth: int,
        tileheight: int,
        invert_y: bool,
    ) -> None:
        """
        Adjust the position of a GID-based object based on map orientation and rotation.
        Modifies the object in-place.
        """
        self.x, self.y = compute_adjusted_position(
            self.x,
            self.y,
            self.width,
            self.height,
            orientation,
            rotation,
            tilewidth,
            tileheight,
            invert_y,
        )
