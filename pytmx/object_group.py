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

Object group model and parser.
"""

from typing import Self
from xml.etree import ElementTree

from .element import TiledElement
from .object import TiledObject


class TiledObjectGroup(TiledElement, list):
    """Represents a Tiled ObjectGroup

    Supports any operation of a normal list.

    """

    def __init__(self, parent, node, customs) -> None:
        TiledElement.__init__(self)
        self.parent = parent

        # defaults from the specification
        self.name = None
        self.color = None
        self.opacity = 1
        self.visible = 1
        self.offsetx = 0
        self.offsety = 0
        self.custom_types = customs
        self.draworder = "index"

        self.parse_xml(node)

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledObjectGroup layer from ElementTree xml node.

        Returns:
            TiledObjectGroup: The parsed TiledObjectGroup layer.
        """
        self._set_properties(node, self.custom_types)
        self.extend(
            TiledObject(self.parent, child, self.custom_types)
            for child in node.findall("object")
        )

        return self
