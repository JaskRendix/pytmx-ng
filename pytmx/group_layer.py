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

Tiled group layer model and parser.
"""

from typing import TYPE_CHECKING, Self
from xml.etree import ElementTree

from .element import TiledElement

if TYPE_CHECKING:
    from .map import TiledMap


class TiledGroupLayer(TiledElement):
    def __init__(self, parent: "TiledMap", node: ElementTree.Element) -> None:
        """

        Args:
            parent (TiledMap): The parent TiledMap.
            node (ElementTree.Element): The XML node to parse.
        """
        super().__init__()
        self.parent = parent
        self.name = None
        self.visible = 1
        self.parse_xml(node)

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledGroupLayer layer from ElementTree xml node.

        Returns:
            TiledGroupLayer: The parsed TiledGroupLayer layer.
        """
        self._set_properties(node)
        self.name = node.get("name", None)
        return self
