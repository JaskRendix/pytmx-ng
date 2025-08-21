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

Tiled property model.
"""

from xml.etree import ElementTree

from .element import TiledElement


class TiledProperty(TiledElement):
    """Represents Tiled Property."""

    def __init__(self, parent, node: ElementTree.Element) -> None:
        TiledElement.__init__(self)

        # defaults from the specification
        self.name = None
        self.type = None
        self.value = None

        self.parse_xml(node)

    def parse_xml(self, node: ElementTree.Element) -> None:
        pass
