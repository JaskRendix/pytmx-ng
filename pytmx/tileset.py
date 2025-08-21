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

Tiled Tileset parser and model.
"""

import logging
import os
from xml.etree import ElementTree

from .constants import AnimationFrame
from .element import TiledElement
from .object_group import TiledObjectGroup
from .properties import parse_properties, types

logger = logging.getLogger(__name__)


class TiledTileset(TiledElement):
    """Represents a Tiled Tileset

    External tilesets are supported.  GID/ID's from Tiled are not
    guaranteed to be the same after loaded.

    """

    def __init__(self, parent, node) -> None:
        """Represents a Tiled Tileset

        Args:
            parent (???): ???.
            node (ElementTree.Element): ???.
        """
        TiledElement.__init__(self)
        self.parent = parent
        self.offset = (0, 0)

        # defaults from the specification
        self.firstgid = 0
        self.source = None
        self.name = None
        self.tilewidth = 0
        self.tileheight = 0
        self.spacing = 0
        self.margin = 0
        self.tilecount = 0
        self.columns = 0

        # image properties
        self.trans = None
        self.width = 0
        self.height = 0

        self.parse_xml(node)

    def parse_xml(self, node: ElementTree.Element) -> "TiledTileset":
        """Parse a Tileset from ElementTree xml element.

        A bit of mangling is done here so that tilesets that have
        external TSX files appear the same as those that don't.

        Args:
            node (ElementTree.Element): Node to parse.

        Returns:
            TiledTileset:
        """
        # if true, then node references an external tileset
        source = node.get("source", None)
        if source:
            if source[-4:].lower() == ".tsx":
                # external tilesets don't save this, store it for later
                self.firstgid = int(node.get("firstgid"))

                # we need to mangle the path - tiled stores relative paths
                dirname = os.path.dirname(self.parent.filename)
                path = os.path.abspath(os.path.join(dirname, source))
                if not os.path.exists(path):
                    # raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), path)
                    raise Exception(
                        f"Cannot find tileset file {source} from {self.parent.filename}, should be at {path}"
                    )

                try:
                    node = ElementTree.parse(path).getroot()
                except IOError as io:
                    msg = f"Error loading external tileset: {path}"
                    logger.error(msg)
                    raise Exception(msg) from io
            else:
                msg = f"Found external tileset, but cannot handle type: {self.source}"
                logger.error(msg)
                raise Exception(msg)

        self._set_properties(node)

        # since tile objects [probably] don't have a lot of metadata,
        # we store it separately in the parent (a TiledMap instance)
        register_gid = self.parent.register_gid
        for child in node.iter("tile"):
            tiled_gid = int(child.get("id"))

            p = {k: types[k](v) for k, v in child.items()}
            p.update(parse_properties(child))

            # images are listed as relative to the .tsx file, not the .tmx file:
            if source and "path" in p:
                p["path"] = os.path.join(os.path.dirname(source), p["path"])

            # handle tiles that have their own image
            image = child.find("image")
            if image is None:
                p["width"] = self.tilewidth
                p["height"] = self.tileheight
            else:
                tile_source = image.get("source")
                # images are listed as relative to the .tsx file, not the .tmx file:
                if source and tile_source:
                    tile_source = os.path.join(os.path.dirname(source), tile_source)
                p["source"] = tile_source
                p["trans"] = image.get("trans", None)
                p["width"] = image.get("width", None)
                p["height"] = image.get("height", None)

            # handle tiles with animations
            anim = child.find("animation")
            frames = list()
            p["frames"] = frames
            if anim is not None:
                for frame in anim.findall("frame"):
                    duration = int(frame.get("duration"))
                    gid = register_gid(int(frame.get("tileid")) + self.firstgid)
                    frames.append(AnimationFrame(gid, duration))

            for objgrp_node in child.findall("objectgroup"):
                objectgroup = TiledObjectGroup(self.parent, objgrp_node, None)
                p["colliders"] = objectgroup

            for gid, flags in self.parent.map_gid2(tiled_gid + self.firstgid):
                self.parent.set_tile_properties(gid, p)

        # handle the optional 'tileoffset' node
        self.offset = node.find("tileoffset")
        if self.offset is None:
            self.offset = (0, 0)
        else:
            self.offset = (self.offset.get("x", 0), self.offset.get("y", 0))

        image_node = node.find("image")
        if image_node is not None:
            self.source = image_node.get("source")

            # When loading from tsx, tileset image path is relative to the tsx file, not the tmx:
            if source:
                self.source = os.path.join(os.path.dirname(source), self.source)

            self.trans = image_node.get("trans", None)
            self.width = int(image_node.get("width"))
            self.height = int(image_node.get("height"))

        return self
