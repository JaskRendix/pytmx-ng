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

Object group model and parser.
"""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Optional, Self, Union
from xml.etree import ElementTree

from .element import TiledElement
from .object import TiledObject

if TYPE_CHECKING:
    from .map import TiledMap


class TiledObjectGroup(TiledElement):
    """
    Represents a Tiled ObjectGroup, acting as a container (list) for TiledObjects.
    """

    def __init__(
        self,
        parent: "TiledMap",
        node: ElementTree.Element,
        custom_types: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.parent = parent

        self._objects: list[TiledObject] = []

        # defaults from the specification
        self.name = None
        self.color = None
        self.opacity = 1
        self.visible = 1
        self.offsetx = 0
        self.offsety = 0
        self.custom_types = custom_types
        self.draworder = "index"

        self.parse_xml(node)

    def parse_xml(self, node: ElementTree.Element) -> Self:
        """
        Parse a TiledObjectGroup layer from ElementTree xml node.

        Returns:
            TiledObjectGroup: The parsed TiledObjectGroup layer.
        """
        self._set_properties(node, self.custom_types)

        self._objects.extend(
            TiledObject(self.parent, child, self.custom_types)
            for child in node.findall("object")
        )

        return self

    def __len__(self) -> int:
        """Returns the number of objects in the group."""
        return len(self._objects)

    def __iter__(self) -> Iterator[TiledObject]:
        """Allows iteration (e.g., for obj in group:)."""
        return iter(self._objects)

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[TiledObject, list[TiledObject]]:
        """Allows indexing and slicing (e.g., group[0], group[2:5])."""
        return self._objects[index]

    def append(self, obj: TiledObject) -> None:
        self._objects.append(obj)

    def remove(self, obj: TiledObject) -> None:
        """Remove a specific object from the group."""
        self._objects.remove(obj)

    def clear(self) -> None:
        """Remove all objects from the group."""
        self._objects.clear()

    def find_by_name(self, name: str) -> Optional[TiledObject]:
        """Find the first object with a matching name."""
        for obj in self._objects:
            if getattr(obj, "name", None) == name:
                return obj
        return None
