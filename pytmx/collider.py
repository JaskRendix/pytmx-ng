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
from dataclasses import dataclass, field
from typing import Any, Optional

from .constants import Point
from .utils import rotate

logger = logging.getLogger(__name__)


@dataclass
class Collider:
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    type: str = "rectangle"  # rectangle, polygon, ellipse, point
    rotation: float = 0.0
    points: Optional[list[tuple[float, float]]] = None
    properties: dict[str, Any] = field(default_factory=dict)

    def get_center(self) -> tuple[float, float]:
        """Return the center point of the collider."""
        return self.x + self.width / 2, self.y + self.height / 2

    def get_property(self, key: str, default: Any = None) -> Any:
        """Safely retrieve a custom property with an optional default value."""
        return self.properties.get(key, default)

    def is_polygon(self) -> bool:
        return self.type == "polygon"

    def is_ellipse(self) -> bool:
        return self.type == "ellipse"

    def is_point(self) -> bool:
        return self.type == "point"
