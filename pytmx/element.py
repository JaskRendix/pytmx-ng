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

Base element types shared by pytmx models.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from logging import getLogger
from typing import Any, Iterable, Self
from xml.etree import ElementTree

from .properties import parse_properties, types

logger = getLogger(__name__)


class TiledElement(ABC):
    """Base class for all pytmx types."""

    def __init__(self, allow_duplicate_names: bool = False):
        """
        Initializes a TiledElement.

        Args:
            allow_duplicate_names: If True, allows Tiled properties
                to have the same name as class attributes.
        """
        # Reset the class-level flag on each instantiation to prevent
        # cross-test leakage when some code temporarily mutates the
        # class variable (e.g., via TiledMap kwargs). Tests that need
        # to override this can still set the class attribute explicitly.
        self._allow_duplicate_names = allow_duplicate_names
        self.properties = dict()

    @classmethod
    def from_xml_string(cls, xml_string: str) -> Self:
        """Return a TiledElement object from a xml string.

        Args:
            xml_string (str): String containing xml data.

        Returns:
            TiledElement: The TiledElement from the xml string.
        """
        return cls().parse_xml(ElementTree.fromstring(xml_string))

    @abstractmethod
    def parse_xml(self, node: ElementTree.Element) -> Self:
        """Parse XML data for this element."""
        raise NotImplementedError

    @property
    def allow_duplicate_names(self) -> bool:
        return self._allow_duplicate_names

    @allow_duplicate_names.setter
    def allow_duplicate_names(self, value: bool) -> None:
        self._allow_duplicate_names = value

    def _cast_and_set_attributes_from_node_items(
        self, items: Iterable[tuple[str, Any]]
    ) -> None:
        """
        Cast and set attributes from node items.

        Args:
            items (Iterable[tuple[str, Any]]): The node items to cast and set.
        """
        for key, value in items:
            casted_value = types[key](value)
            setattr(self, key, casted_value)

    def _contains_invalid_property_name(self, items: Iterable[tuple[str, Any]]) -> bool:
        """
        Check if the properties contain invalid property names.

        Args:
            items (Iterable[tuple[str, Any]]): The properties to check.

        Returns:
            bool: True if the properties contain invalid property names, False otherwise.
        """
        if self._allow_duplicate_names:
            return False

        for key, _ in items:
            _hasattr = hasattr(self, key)

            if _hasattr:
                msg = f"Cannot set property '{key}' on {self.__class__.__name__} '{getattr(self, 'name', 'unnamed')}'; Tiled property already exists."
                logger.error(msg)
                return True
        return False

    def _set_properties(self, node: ElementTree.Element, customs=None) -> None:
        """Set properties from xml data

        Reads the xml attributes and Tiled "properties" from an XML node and fills
        in the values into the object's dictionary. Names will be checked to
        make sure that they do not conflict with reserved names.
        """
        self._cast_and_set_attributes_from_node_items(node.items())
        properties = parse_properties(node, customs)
        if not self._allow_duplicate_names and self._contains_invalid_property_name(
            properties.items()
        ):
            logger.error("Some names are reserved for objects and cannot be used.")
            raise ValueError(
                "Reserved names and duplicate names are not allowed. Please rename your property inside the .tmx file"
            )

        self.properties = properties

    def __getattr__(self, item: str) -> Any:
        try:
            return self.properties[item]
        except KeyError:
            if self.properties.get("name", None):
                raise AttributeError(f"Element '{self.name}' has no property {item}")
            else:
                raise AttributeError(f"Element has no property {item}")

    def __repr__(self) -> str:
        if hasattr(self, "id"):
            return f'<{self.__class__.__name__}[{self.id}]: "{self.name}">'
        else:
            return f'<{self.__class__.__name__}: "{self.name}">'
