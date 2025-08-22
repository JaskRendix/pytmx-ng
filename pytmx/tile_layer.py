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

Tiled tile layer model and parser.
"""

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional, Self
from xml.etree import ElementTree

from .element import TiledElement
from .utils import reshape_data, unpack_gids

if TYPE_CHECKING:
    from .map import TiledMap

logger = logging.getLogger(__name__)


class TiledTileLayer(TiledElement):
    """Represents a TileLayer.

    To just get the tile images, use TiledTileLayer.tiles().
    """

    def __init__(self, parent: "TiledMap", node: ElementTree.Element) -> None:
        super().__init__()
        self.parent = parent
        self.data = list()

        # defaults from the specification
        self.name = None
        self.width = 0
        self.height = 0
        self.opacity = 1.0
        self.visible = True
        self.offsetx = 0
        self.offsety = 0

        self.parse_xml(node)

    def __iter__(self) -> Iterable[tuple[int, int, int]]:
        return self.iter_data()

    def iter_data(self) -> Iterable[tuple[int, int, int]]:
        """Yields X, Y, GID tuples for each tile in the layer.

        Returns:
            Iterable[Tuple[int, int, int]]: Iterator of X, Y, GID tuples for each tile in the layer.
        """
        for y, row in enumerate(self.data):
            for x, gid in enumerate(row):
                yield x, y, gid

    def tiles(self) -> Iterable[tuple[int, int, Any]]:
        """Yields X, Y, Image tuples for each tile in the layer.

        Yields:
            ???: Iterator of X, Y, Image tuples for each tile in the layer
        """
        images = self.parent.images
        for x, y, gid in [i for i in self.iter_data() if i[2]]:
            yield x, y, images[gid]

    def _set_properties(
        self, node: ElementTree.Element, customs: Optional[dict[str, Any]] = None
    ) -> None:
        super()._set_properties(node, customs)

        # TODO: make class/layer-specific type casting
        # layer height and width must be int, but TiledElement.set_properties()
        # make a float by default, so recast as int here
        self.height = int(self.height)
        self.width = int(self.width)

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledTileLayer layer from ElementTree xml node.

        Returns:
            TiledTileLayer: The parsed TiledTileLayer layer.
        """
        self._set_properties(node)
        data_node = node.find("data")
        chunk_nodes = data_node.findall("chunk")
        if chunk_nodes:
            msg = "TMX map size: infinite is not supported."
            logger.error(msg)
            raise ValueError(msg)

        child = data_node.find("tile")
        if child is not None:
            raise ValueError(
                "XML tile elements are no longer supported. Must use base64 or csv map formats."
            )

        temp = [
            self.parent.register_gid_check_flags(gid)
            for gid in unpack_gids(
                text=data_node.text.strip(),
                encoding=data_node.get("encoding", None),
                compression=data_node.get("compression", None),
            )
        ]

        self.data = reshape_data(temp, self.width)
        return self
