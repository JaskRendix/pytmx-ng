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

from xml.etree import ElementTree

from .element import TiledElement


class TiledImageLayer(TiledElement):
    """Represents Tiled Image Layer.

    The image associated with this layer will be loaded and assigned a GID.

    """

    def __init__(self, parent, node: ElementTree.Element) -> None:
        TiledElement.__init__(self)
        self.parent = parent
        self.source = None
        self.trans = None
        self.gid = 0

        # defaults from the specification
        self.name = None
        self.opacity = 1
        self.visible = 1

        self.parse_xml(node)

    @property
    def image(self):
        """Image for the object, if assigned.

        Returns:
            ???: the image object type will depend on the loader (ie. pygame.Surface).
        """
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node: ElementTree.Element):
        """Parse an Image Layer from ElementTree xml node."""
        self._set_properties(node)
        self.name = node.get("name", None)
        self.opacity = node.get("opacity", self.opacity)
        self.visible = node.get("visible", self.visible)
        image_node = node.find("image")
        self.source = image_node.get("source", None)
        self.trans = image_node.get("trans", None)
        return self
