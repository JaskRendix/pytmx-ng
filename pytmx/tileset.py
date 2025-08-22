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
from typing import TYPE_CHECKING, Any, Self
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from .constants import AnimationFrame
from .element import TiledElement
from .object_group import TiledObjectGroup
from .properties import parse_properties, types

if TYPE_CHECKING:
    from .map import TiledMap

logger = logging.getLogger(__name__)


class TiledTileset(TiledElement):
    """Represents a Tiled Tileset

    External tilesets are supported.  GID/ID's from Tiled are not
    guaranteed to be the same after loaded.
    """

    def __init__(self, parent: "TiledMap", node: ElementTree.Element) -> None:
        """Represents a Tiled Tileset

        Args:
            parent (TiledMap): The parent TiledMap.
            node (ElementTree.Element): The XML node.
        """
        super().__init__()
        self.parent = parent
        self.offset = (0, 0)
        self.tileset_source = None

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

    def _resolve_path(self, path: str, relative_to_source: bool) -> str:
        """
        Resolve a path relative to either the TMX or TSX file, but keep it relative.
        """
        base = os.path.dirname(
            self.tileset_source
            if relative_to_source and self.tileset_source
            else self.parent.filename
        )
        resolved = os.path.join(base, path)
        logger.debug(f"Resolved path: {resolved}")
        return resolved

    def _parse_tile_properties(self, node: ElementTree.Element) -> dict[str, Any]:
        """
        Parses a single tile's attributes and custom properties.
        """
        props = {k: types[k](v) for k, v in node.items()}
        props.update(parse_properties(node))
        logger.debug(f"Parsed tile properties: {props}")
        return props

    def _parse_animation_frames(
        self, anim_node: ElementTree.Element
    ) -> list[AnimationFrame]:
        """
        Parses animation frames from a tile's animation node.
        """
        frames = []
        for frame in anim_node.findall("frame"):
            duration = int(frame.get("duration"))
            gid = self.parent.register_gid(int(frame.get("tileid")) + self.firstgid)
            frames.append(AnimationFrame(gid, duration))
            logger.debug(
                f"Parsed animation frame: tileid={frame.get('tileid')}, duration={duration}, gid={gid}"
            )
        return frames

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledTileset layer from ElementTree xml node.

        Returns:
            TiledTileset: The parsed TiledTileset layer.
        """
        logger.debug("Starting XML parsing for tileset")

        source = node.get("source", None)
        if source:
            if source[-4:].lower() == ".tsx":
                self.tileset_source = source
                self.firstgid = int(node.get("firstgid"))
                logger.debug(
                    f"External tileset detected: {source}, firstgid={self.firstgid}"
                )

                resolved_path = self._resolve_path(source, relative_to_source=False)
                if not os.path.exists(resolved_path):
                    raise FileNotFoundError(
                        f"Cannot find tileset file {source} from {self.parent.filename}, "
                        f"should be at {resolved_path}"
                    )
                try:
                    node = ElementTree.parse(resolved_path).getroot()
                    logger.debug(
                        f"Successfully loaded external tileset from {resolved_path}"
                    )
                except (OSError, ParseError) as e:
                    msg = f"Error loading external tileset: {resolved_path}"
                    logger.error(msg)
                    raise ParseError(msg) from e
            else:
                msg = f"Found external tileset, but cannot handle type: {self.source}"
                logger.error(msg)
                raise ValueError(msg)

        self._set_properties(node)
        logger.debug(
            f"Tileset properties set: name={self.name}, tilecount={self.tilecount}, columns={self.columns}"
        )

        for child in node.iter("tile"):
            tiled_gid = int(child.get("id"))
            p = self._parse_tile_properties(child)
            logger.debug(f"Parsing tile ID: {tiled_gid}")

            if "source" in p:
                p["source"] = self._resolve_path(
                    p["source"], relative_to_source=bool(source)
                )

            image = child.find("image")
            if image is not None:
                tile_source = image.get("source")
                if source:
                    tile_source = self._resolve_path(
                        tile_source, relative_to_source=True
                    )
                p["source"] = tile_source
                p["trans"] = image.get("trans", None)
                p["width"] = int(image.get("width"))
                p["height"] = int(image.get("height"))
                logger.debug(
                    f"Tile image parsed: source={tile_source}, size={p['width']}x{p['height']}"
                )
            else:
                p["width"] = self.tilewidth
                p["height"] = self.tileheight

            anim = child.find("animation")
            p["frames"] = self._parse_animation_frames(anim) if anim is not None else []

            for objgrp_node in child.findall("objectgroup"):
                objectgroup = TiledObjectGroup(self.parent, objgrp_node, None)
                p["colliders"] = objectgroup
                logger.debug(f"Object group parsed for tile ID {tiled_gid}")

            for gid, flags in self.parent.map_gid2(tiled_gid + self.firstgid):
                self.parent.set_tile_properties(gid, p)

        tile_offset_node = node.find("tileoffset")
        if tile_offset_node is not None:
            self.offset = (
                int(tile_offset_node.get("x", 0)),
                int(tile_offset_node.get("y", 0)),
            )
            logger.debug(f"Parsed tileoffset: {self.offset}")

        image_node = node.find("image")
        if image_node is not None:
            self.source = image_node.get("source")
            if self.tileset_source:
                self.source = self._resolve_path(self.source, relative_to_source=True)
            self.trans = image_node.get("trans", None)
            self.width = int(image_node.get("width"))
            self.height = int(image_node.get("height"))
            logger.debug(
                f"Tileset image node parsed: source={self.source}, size={self.width}x{self.height}, trans={self.trans}"
            )

        logger.debug("Finished parsing tileset XML")
        return self
