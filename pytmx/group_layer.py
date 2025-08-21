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

from xml.etree import ElementTree

from .element import TiledElement


class TiledGroupLayer(TiledElement):
    def __init__(self, parent, node: ElementTree.Element) -> None:
        """

        Args:
            parent (???): ???.
            node (ElementTree.Element): ???.
        """
        super().__init__()
        self.parent = parent
        self.name = None
        self.visible = 1
        self._parse_xml(node)

    def _parse_xml(self, node: ElementTree.Element) -> "TiledGroupLayer":
        """
        Parse a TiledGroup layer from ElementTree xml node.

        Args:
            node (ElementTree.Element): Node to parse.

        Returns:
            TiledGroupLayer: The parsed TiledGroup layer.
        """
        self._set_properties(node)
        self.name = node.get("name", None)
        return self
