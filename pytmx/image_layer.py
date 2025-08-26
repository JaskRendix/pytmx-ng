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

from typing import TYPE_CHECKING, Any, Optional
try:  # Python 3.11+
    from typing import Self  # type: ignore
except Exception:  # Python < 3.11
    from typing_extensions import Self  # type: ignore
from xml.etree import ElementTree

from .element import TiledElement

if TYPE_CHECKING:
    from .map import TiledMap


class TiledImageLayer(TiledElement):
    """Represents Tiled Image Layer.

    The image associated with this layer will be loaded and assigned a GID.
    """

    def __init__(self, parent: "TiledMap", node: ElementTree.Element) -> None:
        super().__init__()
        self.parent = parent
        self.source: Optional[str] = None
        self.trans: Optional[str] = None
        self.gid: int = 0

        # defaults from the specification
        self.name: Optional[str] = None
        self.opacity: float = 1.0
        self.visible: bool = True

        self.parse_xml(node)

    @property
    def image(self) -> Any:
        """Image for the object, if assigned.

        Returns:
            Any: the image object type will depend on the loader (ie. pygame.Surface).
        """
        if self.gid:
            return self.parent.images[self.gid]
        return None

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledImageLayer layer from ElementTree xml node.

        Returns:
            TiledImageLayer: The parsed TiledImageLayer layer.
        """
        self._set_properties(node)

        self.name = node.get("name")
        self.opacity = float(node.get("opacity", self.opacity))
        self.visible = bool(int(node.get("visible", int(self.visible))))

        image_node = node.find("image")
        if image_node is not None:
            self.source = image_node.get("source")
            self.trans = image_node.get("trans")

        return self
