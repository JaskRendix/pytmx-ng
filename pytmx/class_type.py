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

Custom Tiled class type container.
"""
from typing import Any

class TiledClassType:
    """Contains custom Tiled types."""

    def __init__(self, name: str, members: list[dict[str, Any]]) -> None:
        """Creates the TiledClassType.

        Args:
            name (str): The name of the class type.
            members (List[dict]): The members of the class type.

        """
        self.name = name
        for member in members:
            setattr(self, member["name"], member["value"])
