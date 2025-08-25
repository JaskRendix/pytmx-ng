# -*- coding: utf-8 -*-
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
License along with pytmx.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
from functools import partial
from typing import Any, Callable, Optional

from .constants import ColorLike, TileFlags
from .map import TiledMap

logger = logging.getLogger(__name__)

try:
    import sdl2.ext
except ImportError:
    logger.error("cannot import pysdl2 (is it installed?)")
    raise

__all__ = [
    "load_pysdl2",
    "pysdl2_image_loader",
]


def pysdl2_image_loader(
    renderer: sdl2.SDL_Renderer,
    filename: str,
    colorkey: Optional[ColorLike] = None,
    **kwargs: Any,
) -> Callable[[Optional[tuple[int, int, int, int]], Optional[TileFlags]], Any]:
    def convert(surface: sdl2.SDL_Surface) -> sdl2.SDL_Texture:
        texture_ = sdl2.SDL_CreateTextureFromSurface(renderer.renderer, surface)
        sdl2.SDL_SetTextureBlendMode(texture_, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_FreeSurface(surface)
        return texture_

    def load_image(
        rect: Optional[tuple[int, int, int, int]] = None,
        flags: Optional[TileFlags] = None,
    ) -> Any:
        flip = 0
        if rect:
            try:
                if flags:
                    if flags.flipped_horizontally:
                        flip |= sdl2.SDL_FLIP_HORIZONTAL
                    if flags.flipped_vertically:
                        flip |= sdl2.SDL_FLIP_VERTICAL
                    if flags.flipped_diagonally:
                        flip |= (
                            4  # SDL2 doesn't define diagonal flip, so this is custom
                        )

                rect = sdl2.rect.SDL_Rect(*rect)
                return texture, rect, flip

            except ValueError:
                logger.error("Tile bounds outside bounds of tileset image")
                raise
        else:
            return texture, None, flip

    image = sdl2.ext.load_image(filename)

    if isinstance(colorkey, str):
        color = sdl2.ext.string_to_color("#" + colorkey)
        key = sdl2.SDL_MapRGB(image.format, *color[:3])
        sdl2.SDL_SetColorKey(image, sdl2.SDL_TRUE, key)

    texture = convert(image)

    return load_image


def load_pysdl2(
    renderer: sdl2.SDL_Renderer, filename: str, *args: Any, **kwargs: Any
) -> TiledMap:
    kwargs["image_loader"] = partial(pysdl2_image_loader, renderer)
    return TiledMap(filename, *args, **kwargs)
