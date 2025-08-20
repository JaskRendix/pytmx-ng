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
from xml.etree import ElementTree
from typing import Iterable
import logging

from .element import TiledElement
from .utils import unpack_gids, reshape_data

logger = logging.getLogger(__name__)


class TiledTileLayer(TiledElement):
    """Represents a TileLayer.

    To just get the tile images, use TiledTileLayer.tiles().

    """

    def __init__(self, parent, node) -> None:
        TiledElement.__init__(self)
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

    def __iter__(self):
        return self.iter_data()

    def iter_data(self) -> Iterable[tuple[int, int, int]]:
        """Yields X, Y, GID tuples for each tile in the layer.

        Returns:
            Iterable[Tuple[int, int, int]]: Iterator of X, Y, GID tuples for each tile in the layer.

        """
        for y, row in enumerate(self.data):
            for x, gid in enumerate(row):
                yield x, y, gid

    def tiles(self):
        """Yields X, Y, Image tuples for each tile in the layer.

        Yields:
            ???: Iterator of X, Y, Image tuples for each tile in the layer

        """
        images = self.parent.images
        for x, y, gid in [i for i in self.iter_data() if i[2]]:
            yield x, y, images[gid]

    def _set_properties(self, node) -> None:
        TiledElement._set_properties(self, node)

        # TODO: make class/layer-specific type casting
        # layer height and width must be int, but TiledElement.set_properties()
        # make a float by default, so recast as int here
        self.height = int(self.height)
        self.width = int(self.width)

    def parse_xml(self, node: ElementTree.Element) -> "TiledTileLayer":
        """Parse a Tile Layer from ElementTree xml node.

        Args:
            node (ElementTree.Element): Node to parse.

        Returns:
            TiledTileLayer: The parsed tile layer.

        """
        self._set_properties(node)
        data_node = node.find("data")
        chunk_nodes = data_node.findall("chunk")
        if chunk_nodes:
            msg = "TMX map size: infinite is not supported."
            logger.error(msg)
            raise Exception

        child = data_node.find("tile")
        if child is not None:
            raise ValueError("XML tile elements are no longer supported. Must use base64 or csv map formats.")

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

