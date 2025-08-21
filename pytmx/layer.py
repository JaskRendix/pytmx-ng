from typing import Union

from .group_layer import TiledGroupLayer
from .image_layer import TiledImageLayer
from .object_group import TiledObjectGroup
from .tile_layer import TiledTileLayer

TiledLayer = Union[TiledTileLayer, TiledImageLayer, TiledGroupLayer, TiledObjectGroup]
