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

Tiled map model and image management.

This module defines `TiledMap` and related helpers used when loading TMX maps.
Imports are organized and documented for clarity.
"""

import json
import os

# --- stdlib imports ---------------------------------------------------------
from collections import defaultdict
from collections.abc import Iterable
from itertools import chain, product
from logging import getLogger
from operator import attrgetter
from typing import Any, Iterator, Optional, Self
from xml.etree import ElementTree


# --- internal imports -------------------------------------------------------
from .class_type import TiledClassType
from .constants import GID_TRANS_ROT, MapPoint, TileFlags
from .element import TiledElement
from .group_layer import TiledGroupLayer
from .image_layer import TiledImageLayer
from .layer import TiledLayer
from .object import TiledObject
from .object_group import TiledObjectGroup
from .tile_layer import TiledTileLayer
from .tileset import TiledTileset
from .utils import decode_gid, default_image_loader

logger = getLogger(__name__)


class TiledMap(TiledElement):
    """Contains the layers, objects, and images from a Tiled .tmx map."""

    def __init__(
        self,
        filename: Optional[str] = None,
        custom_property_filename: Optional[list[str]] = None,
        image_loader=default_image_loader,
        optional_gids: Optional[set[int]] = set(),
        load_all_tiles: Optional[bool] = True,
        invert_y: Optional[bool] = True,
        allow_duplicate_names: bool = False,
    ) -> None:
        """Load new Tiled map from a .tmx file.

        Args:
            filename (Optional[str]): Filename of tiled map to load.
            custom_property_filename (Optional[list[str]]): Custom property file to load.
            image_loader (Optional[List[str]]): Function that will load images (see below).
            optional_gids (set[int]): Load specific tile image GID, even if never used.
            load_all_tiles (bool): Load all tile images, even if never used.
            invert_y (bool): Invert the y axis.
            allow_duplicate_names (bool): Allow duplicates in objects' metadata.
        """
        # allow duplicate names to be parsed and loaded
        # honor explicit constructor argument (do not read from kwargs here)
        super().__init__(allow_duplicate_names=allow_duplicate_names)

        self.filename = filename
        self.custom_property_filename = custom_property_filename
        self.image_loader = image_loader

        # optional keyword arguments checked here
        self.optional_gids = optional_gids
        self.load_all_tiles = load_all_tiles
        self.invert_y = invert_y

        # all layers in proper order
        self.layers: list[TiledLayer] = []
        # TiledTileset objects
        self.tilesets: list[TiledTileset] = []
        # tiles that have properties
        self.tile_properties: dict[int, dict[str, str]] = {}
        self.layernames: dict[str, TiledLayer] = {}
        self.objects_by_id: dict[str, TiledObject] = {}
        self.objects_by_name: dict[str, TiledObject] = {}

        # only used tiles are actually loaded, so there will be a difference
        # between the GIDs in the Tiled map data (tmx) and the data in this
        # object and the layers.  This dictionary keeps track of that.
        self.gidmap: defaultdict[int, list[tuple[int, Optional[TileFlags]]]] = (
            defaultdict(list)
        )
        # mapping of gid and trans flags to real gids
        self.imagemap: dict[tuple[int, TileFlags], tuple[int, TileFlags]] = {}
        # mapping of tiledgid to pytmx gid
        self.tiledgidmap: dict[int, int] = {}
        self.maxgid = 1

        # should be filled in by a loader function
        self.images = list()

        # defaults from the TMX specification
        self.version = "0.0"
        self.tiledversion = ""
        self.orientation = "orthogonal"
        self.renderorder = "right-down"
        self.width = 0  # width of map in tiles
        self.height = 0  # height of map in tiles
        self.tilewidth = 0  # width of a tile in pixels
        self.tileheight = 0  # height of a tile in pixels
        self.hexsidelength = 0
        self.staggeraxis = None
        self.staggerindex = None
        self.background_color = None
        self.nextobjectid = 0

        self.custom_types = dict()

        # initialize the gid mapping
        self.imagemap[(0, 0)] = 0

        if custom_property_filename:
            try:
                with open(custom_property_filename) as f:
                    self.parse_json(json.load(f))
            except (OSError, json.JSONDecodeError) as e:
                logger.error(
                    f"Error loading custom property file: {custom_property_filename}"
                )
                raise e

        if filename:
            try:
                root_node = ElementTree.parse(self.filename).getroot()
                self.parse_xml(root_node)
            except (OSError, ElementTree.ParseError) as e:
                logger.error(f"Error loading map file: {self.filename}")
                raise e

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: "{self.filename}">'

    # iterate over layers and objects in map
    def __iter__(self) -> Iterator[Self]:
        return chain(self.layers, self.objects)

    def _set_properties(
        self, node: ElementTree.Element, customs: Optional[dict[str, Any]] = None
    ) -> None:
        super()._set_properties(node, customs)

        # TODO: make class/layer-specific type casting
        # layer height and width must be int, but TiledElement.set_properties()
        # make a float by default, so recast as int here
        self.height = int(self.height)
        self.width = int(self.width)

    def parse_json(self, data: dict) -> None:
        """Parse custom data types from a JSON object

        Args:
            data (dict): Dictionary from JSON object to parse
        """
        for custom_type in data:
            if custom_type["type"] == "class":
                new = TiledClassType(custom_type["name"], custom_type["members"])

                self.custom_types[custom_type["name"]] = new

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledMap layer from ElementTree xml node.

        Returns:
            TiledMap: The parsed TiledMap layer.
        """
        self._set_properties(node)
        self.background_color = node.get("backgroundcolor", None)

        # ***         do not change this load order!         *** #
        # ***    gid mapping errors will occur if changed    *** #
        for subnode in node.findall(".//group"):
            self.add_layer(TiledGroupLayer(self, subnode))

        for subnode in node.findall(".//layer"):
            self.add_layer(TiledTileLayer(self, subnode))

        for subnode in node.findall(".//imagelayer"):
            self.add_layer(TiledImageLayer(self, subnode))

        # this will only find objectgroup layers, not including tile colliders
        for subnode in node.findall(".//objectgroup"):
            objectgroup = TiledObjectGroup(self, subnode, self.custom_types)
            self.add_layer(objectgroup)
            for obj in objectgroup:
                self.objects_by_id[obj.id] = obj
                self.objects_by_name[obj.name] = obj

        for subnode in node.findall(".//tileset"):
            self.add_tileset(TiledTileset(self, subnode))

        # "tile objects", objects with a GID, require their attributes to be
        # set after the tileset is loaded, so this step must be performed last
        # also, this step is performed for objects to load their tiles.

        # tiled stores the origin of GID objects by the lower right corner
        # this is different for all other types, so i just adjust it here
        # so all types loaded with pytmx are uniform.

        # iterate through tile objects and handle the image
        for o in [o for o in self.objects if o.gid]:
            # Decode rotation and flipping flags from the GID
            _, flags = decode_gid(o.gid)
            rotation = self.get_rotation_from_flags(
                flags
            )  # Get rotation based on flags

            # gids might also have properties assigned to them
            # in that case, assign the gid properties to the object as well
            p = self.get_tile_properties_by_gid(o.gid)
            if p:
                for key in p:
                    o.properties.setdefault(key, p[key])

            # Adjust based on rotation
            if rotation == 90:
                o.x, o.y = o.x + o.height, o.y
            elif rotation == 180:
                o.x, o.y = o.x + o.width, o.y + o.height
            elif rotation == 270:
                o.x, o.y = o.x, o.y + o.width

            # Adjust Y-coordinate if invert_y is enabled
            if self.invert_y:
                o.y -= o.height

        self.reload_images()
        return self

    def get_rotation_from_flags(self, flags: TileFlags) -> int:
        """Determine the rotation angle from TileFlags."""
        if flags.flipped_diagonally:
            if flags.flipped_horizontally and not flags.flipped_vertically:
                return 90
            elif flags.flipped_horizontally and flags.flipped_vertically:
                return 180
            elif not flags.flipped_horizontally and flags.flipped_vertically:
                return 270
        return 0

    def reload_images(self) -> None:
        """Load or reload the map images from disk.

        This method will use the image loader passed in the constructor
        to do the loading or will use a generic default, in which case no
        images will be loaded.
        """
        self.images = [None] * self.maxgid

        # iterate through tilesets to get source images
        for ts in self.tilesets:
            # skip tilesets without a source
            if ts.source is None:
                continue

            path = os.path.join(os.path.dirname(self.filename), ts.source)
            colorkey = getattr(ts, "trans", None)
            loader = self.image_loader(path, colorkey, tileset=ts)

            p = product(
                range(
                    ts.margin,
                    ts.height + ts.margin - ts.tileheight + 1,
                    ts.tileheight + ts.spacing,
                ),
                range(
                    ts.margin,
                    ts.width + ts.margin - ts.tilewidth + 1,
                    ts.tilewidth + ts.spacing,
                ),
            )

            # iterate through the tiles
            for real_gid, (y, x) in enumerate(p, ts.firstgid):
                rect = (x, y, ts.tilewidth, ts.tileheight)
                gids = self.map_gid(real_gid)

                # gids is None if the tile is never used
                # but give another chance to load the gid anyway
                if gids is None:
                    if self.load_all_tiles or real_gid in self.optional_gids:
                        # TODO: handle flags? - might never be an issue, though
                        gids = [self.register_gid(real_gid, flags=0)]

                if gids:
                    # flags might rotate/flip the image, so let the loader
                    # handle that here
                    for gid, flags in gids:
                        self.images[gid] = loader(rect, flags)
                # else:
                #     # not used in layer data give another chance to load the tile anyway
                #     if self.load_all_tiles or real_gid in self.optional_gids:
                #         # TODO: handle flags? - might never be an issue, though
                #         self.register_gid(real_gid, flags=0)

        # load image layer images
        for layer in (i for i in self.layers if isinstance(i, TiledImageLayer)):
            source = getattr(layer, "source", None)
            if source:
                colorkey = getattr(layer, "trans", None)
                real_gid = len(self.images)
                gid = self.register_gid(real_gid)
                layer.gid = gid
                path = os.path.join(os.path.dirname(self.filename), source)
                loader = self.image_loader(path, colorkey)
                image = loader()
                self.images.append(image)

        # load images in tiles.
        # instead of making a new gid, replace the reference to the tile that
        # was loaded from the tileset
        for real_gid, props in self.tile_properties.items():
            source = props.get("source", None)
            if source:
                colorkey = props.get("trans", None)
                path = os.path.join(os.path.dirname(self.filename), source)
                loader = self.image_loader(path, colorkey)
                image = loader()
                self.images[real_gid] = image

    def get_tile_image(self, x: int, y: int, nr_layer: int) -> Any:
        """Return the tile image for this location.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            layer (int): The layer's number.

        Returns:
            Any: the image object type will depend on the loader (ie. pygame surface).

        Raises:
            TypeError: if coordinates are not integers.
            ValueError: if the coordinates are out of bounds, or GID not found.
        """
        if not (x >= 0 and y >= 0):
            raise ValueError(f"Tile coordinates must be non-negative, were ({x}, {y})")

        try:
            layer = self.layers[nr_layer]
        except IndexError:
            raise ValueError("Layer not found")

        assert isinstance(layer, TiledTileLayer)

        try:
            gid = layer.data[y][x]
        except (IndexError, ValueError):
            raise ValueError("GID not found")
        except TypeError:
            msg = "Tiles must be specified in integers."
            logger.debug(msg)
            raise TypeError(msg)

        else:
            return self.get_tile_image_by_gid(gid)

    def get_tile_image_by_gid(self, gid: int, *args, **kwargs) -> Any:
        """
        Return the tile image for this location.

        Args:
            gid (int): GID of image.
            *args: Additional arguments. added for compatibility with old API.
            **kwargs: Additional keyword arguments. added for compatibility with old API.

        Returns:
            Any: The image object.

        Raises:
            TypeError: If `gid` is not a non-negative integer.
            ValueError: If there is no image for this GID.
        """
        if not isinstance(gid, int) or gid < 0:
            msg = f"GIDs must be a non-negative integer. Got: {gid}"
            logger.debug(msg)
            raise TypeError(msg)

        try:
            return self.images[gid]
        except IndexError:
            msg = f"GID: {gid} not found"
            logger.debug(msg)
            raise ValueError(msg)

    def get_tile_gid(self, x: int, y: int, layer: int) -> int:
        """Return the tile image GID for this location.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            layer (int): The layer's number.

        Returns:
            int: The tile GID.

        Raises:
            ValueError: If coordinates are out of bounds.
        """
        if not (x >= 0 and y >= 0 and layer >= 0):
            raise ValueError(
                f"Tile coordinates and layers must be non-negative, were ({x}, {y}), layer={layer}"
            )

        try:
            return self.layers[int(layer)].data[int(y)][int(x)]
        except (IndexError, ValueError):
            msg = f"Coords: ({x},{y}) in layer {layer} is invalid"
            logger.debug(msg)
            raise ValueError(msg)

    def get_tile_properties(self, x: int, y: int, layer: int) -> Optional[dict]:
        """Return the tile image GID for this location.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            layer (int): The layer number.

        Returns:
            Optional[dict]: Dictionary of the properties for tile in this location or None.

        Raises:
            ValueError: If coordinates are out of bounds
        """
        if not (x >= 0 and y >= 0 and layer >= 0):
            raise ValueError(
                f"Tile coordinates and layers must be non-negative, were ({x}, {y}), layer={layer}"
            )

        try:
            gid = self.layers[int(layer)].data[int(y)][int(x)]
        except (IndexError, ValueError):
            msg = f"Coords: ({x},{y}) in layer {layer} is invalid."
            logger.debug(msg)
            raise ValueError(msg)

        else:
            try:
                return self.tile_properties[gid]
            except (IndexError, ValueError):
                msg = f"Coords: ({x},{y}) in layer {layer} has invalid GID: {gid}"
                logger.debug(msg)
                raise ValueError(msg)
            except KeyError:
                return None

    def get_tile_locations_by_gid(self, gid: int) -> Iterable[MapPoint]:
        """Search map for tile locations by the GID.

        Note: Not a fast operation.  Cache results if used often.

        Args:
            gid (int): GID to be searched for.

        Returns:
            Iterable[MapPoint]: (int, int, int) tuples, where the layer is index of the visible tile layers.
        """
        for l in self.visible_tile_layers:
            for x, y, _gid in [i for i in self.layers[l].iter_data() if i[2] == gid]:
                yield x, y, l

    def get_tile_properties_by_gid(self, gid: int) -> Optional[dict]:
        """Get the tile properties of a tile GID.

        Args:
            gid (int): GID.

        Returns:
            Optional[dict]: Dictionary of properties for GID, or None.
        """
        try:
            return self.tile_properties[gid]
        except KeyError:
            return None

    def set_tile_properties(self, gid: int, properties: dict) -> None:
        """Set the tile properties of a tile GID.

        Args:
            gid (int): GID.
            properties (dict): Python dictionary of properties for GID.
        """
        self.tile_properties[gid] = properties

    def get_tile_properties_by_layer(
        self, layer: int
    ) -> Iterator[tuple[int, dict[str, Any]]]:
        """Get the tile properties of each GID in layer.

        Args:
            layer (int): The layer number.

        Returns:
            Iterator[Tuple[int, dict[str, Any]]]: Iterator of GID, properties tuples for each tile in the layer.
        """
        try:
            assert int(layer) >= 0
            layer = int(layer)
        except (TypeError, AssertionError):
            msg = f"Layer must be a positive integer.  Got {type(layer)} instead."
            logger.debug(msg)
            raise ValueError(msg)

        p = product(range(self.width), range(self.height))
        layergids = set(self.layers[layer].data[y][x] for x, y in p)

        for gid in layergids:
            try:
                yield gid, self.tile_properties[gid]
            except KeyError:
                continue

    def add_layer(
        self,
        layer: TiledLayer,
    ) -> None:
        """Add a layer to the map.

        Args:
            layer (TiledLayer): The layer.
        """
        assert isinstance(
            layer, (TiledGroupLayer, TiledTileLayer, TiledImageLayer, TiledObjectGroup)
        )

        self.layers.append(layer)
        self.layernames[layer.name] = layer

    def add_tileset(self, tileset: TiledTileset) -> None:
        """Add a tileset to the map."""
        assert isinstance(tileset, TiledTileset)
        self.tilesets.append(tileset)

    def get_layer_by_name(self, name: str) -> TiledLayer:
        """Return a layer by name.

        Args:
            name (str): The layer's name. Case-sensitive!

        Returns:
            TiledLayer: The layer.

        Raises:
            ValueError: if layer by name does not exist
        """
        try:
            return self.layernames[name]
        except KeyError:
            msg = f'Layer "{name}" not found.'
            logger.debug(msg)
            raise ValueError(msg)

    def get_object_by_id(self, obj_id: int) -> TiledObject:
        """Find an object by the object id.

        Args:
            obj_id (int): ID of the object, from Tiled.

        Returns:
            TiledObject: The found object.
        """
        return self.objects_by_id[obj_id]

    def get_object_by_name(self, name: str) -> TiledObject:
        """Find an object by name, case-sensitive.

        Args:
            name (str): The object's name.

        Returns:
            TiledObject: The found object.

        Raises:
            ValueError: if object by name does not exist
        """
        try:
            return self.objects_by_name[name]
        except KeyError:
            msg = f'Object "{name}" not found.'
            logger.debug(msg)
            raise ValueError(msg)

    def get_tileset_from_gid(self, gid: int) -> TiledTileset:
        """Return tileset that owns the gid.

        Note: this is a slow operation, so if you are expecting to do this
              often, it would be worthwhile to cache the results of this.

        Args:
            gid (int): GID of tile image.

        Returns:
            TiledTileset: The tileset that owns the GID.

        Raises:
            ValueError: if the tileset for gid is not found
        """
        try:
            tiled_gid = self.tiledgidmap[gid]
        except KeyError:
            msg = f"Tile GID {gid} not found."
            logger.debug(msg)
            raise ValueError(msg)

        for tileset in sorted(self.tilesets, key=attrgetter("firstgid"), reverse=True):
            if tiled_gid >= tileset.firstgid:
                return tileset

        msg = "Tileset not found"
        logger.debug(msg)
        raise ValueError(msg)

    def get_tile_colliders(self) -> Iterable[tuple[int, list[dict]]]:
        """Return iterator of (gid, dict) pairs of tiles with colliders.

        Returns:
            Iterable[Tuple[int, List[Dict]]]: The tile colliders.
        """
        for gid, props in self.tile_properties.items():
            colliders = props.get("colliders")
            if colliders:
                yield gid, colliders

    def get_tile_flags_by_gid(self, gid: int) -> TileFlags:
        """Return the tile flags for this GID.

        Args:
            gid (int): The tile GID.

        Returns:
            TileFlags: The tile flags.
        """
        real_gid = self.tiledgidmap[gid]
        flags_list = self.gidmap[real_gid]
        for tile_gid, flags in flags_list:
            if gid == tile_gid:
                return flags

    def pixels_to_tile_pos(self, position: tuple[int, int]) -> tuple[int, int]:
        """Convert pixel position to tile position.

        Args:
            position (tuple[int, int]): The pixel position.

        Returns:
            tuple[int, int]: The tile position.
        """
        return int(position[0] / self.tilewidth), int(position[1] / self.tileheight)

    @property
    def objectgroups(self) -> Iterable[TiledObjectGroup]:
        """Returns iterator of all object groups.

        Returns:
            Iterable[TiledObjectGroup]: Iterator of all object groups.
        """
        return (layer for layer in self.layers if isinstance(layer, TiledObjectGroup))

    @property
    def objects(self) -> Iterable[TiledObject]:
        """Returns iterator of all the objects associated with the map.

        Returns:
            Iterable[TiledObject]: Iterator of all objects associated with the map.
        """
        return chain(*self.objectgroups)

    @property
    def visible_layers(self) -> Iterable[TiledLayer]:
        """Returns iterator of Layer objects that are set "visible".

        Returns:
            Iterable[TiledLayer]: Iterator of Layer objects that are set "visible".
        """

        return (l for l in self.layers if l.visible)

    @property
    def visible_tile_layers(self) -> Iterable[TiledTileLayer]:
        """Return iterator of layer indexes that are set "visible".

        Returns:
            Iterable[TiledTileLayer]: A list of layer indexes.
        """
        return (
            i
            for (i, l) in enumerate(self.layers)
            if l.visible and isinstance(l, TiledTileLayer)
        )

    @property
    def visible_object_groups(self) -> Iterable[TiledObjectGroup]:
        """Return iterator of object group indexes that are set "visible".

        Returns:
            Iterable[TiledObjectGroup]: A list of object group indexes that are set to "visible".
        """
        return (
            i
            for (i, l) in enumerate(self.layers)
            if l.visible and isinstance(l, TiledObjectGroup)
        )

    def register_gid(self, tiled_gid: int, flags: Optional[TileFlags] = None) -> int:
        """Used to manage the mapping of GIDs between .tmx and pytmx.

        Args:
            tiled_gid (int): GID that is found in TMX data.
            flags (TileFlags): TileFlags.

        Returns:
            int: New or existing GID for pytmx use.
        """
        if flags is None:
            flags = TileFlags(False, False, False)

        if tiled_gid:
            try:
                return self.imagemap[(tiled_gid, flags)][0]
            except KeyError:
                gid = self.maxgid
                self.maxgid += 1
                self.imagemap[(tiled_gid, flags)] = (gid, flags)
                self.gidmap[tiled_gid].append((gid, flags))
                self.tiledgidmap[gid] = tiled_gid
                return gid

        else:
            return 0

    def register_gid_check_flags(self, tiled_gid: int) -> int:
        """Used to manage the mapping of GIDs between .tmx and pytmx.

        Checks the GID for rotation/flip flags

        Args:
            tiled_gid (int): GID that is found in TMX data.

        Returns:
            int: New or existing GID for pytmx use.
        """
        # NOTE: the register* methods are getting really spaghetti-like
        if tiled_gid == 0:
            return 0
        elif tiled_gid < GID_TRANS_ROT:
            return self.register_gid(tiled_gid)
        else:
            return self.register_gid(*decode_gid(tiled_gid))

    def map_gid(self, tiled_gid: int) -> Optional[list[int]]:
        """Used to lookup a GID read from a TMX file's data.

        Args:
            tiled_gid (int): GID. that is found in the .tmx file data.

        Returns:
            Optional[List[int]]: List of GIDs.
        """
        try:
            return self.gidmap[int(tiled_gid)]
        except KeyError:
            return None
        except (TypeError, ValueError):
            msg = "GIDs must be an integer"
            logger.debug(msg)
            raise TypeError(msg)

    def map_gid2(self, tiled_gid: int) -> list[tuple[int, Optional[int]]]:
        """WIP.  need to refactor the gid code"""
        tiled_gid = int(tiled_gid)

        # gidmap is a default dict, so cannot trust to raise KeyError
        if tiled_gid in self.gidmap:
            return self.gidmap[tiled_gid]
        else:
            gid = self.register_gid(tiled_gid)
            return [(gid, None)]
