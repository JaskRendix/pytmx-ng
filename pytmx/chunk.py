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

Utility functions for pytmx.

This module contains helper functions that are independent of the core
classes and can be reused across the package.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Optional
from xml.etree import ElementTree

from .utils import decode_chunk_data

if TYPE_CHECKING:
    from .map import TiledMap

logger = getLogger(__name__)


@dataclass
class Chunk:
    position: tuple[int, int]  # (x, y) tile coordinates
    size: tuple[int, int]  # (width, height) in tiles
    grid: list[list[int]]  # 2D array of tile GIDs
    raw: bytes  # Raw decompressed binary data


def extract_chunks(
    chunk_nodes: list[ElementTree.Element],
    encoding: Optional[str],
    compression: Optional[str],
) -> list[Chunk]:
    """
    Extracts chunk data from a list of <chunk> XML nodes, using the specified encoding and compression.

    Args:
        chunk_nodes: List of <chunk> elements from a TMX file.
        encoding: The encoding format used for the chunk data (e.g., "base64", "csv").
        compression: The compression method applied to the chunk data (e.g., "zlib", "gzip", "zstd").

    Returns:
        list[Chunk]: List of Chunk objects containing decoded tile GIDs and raw binary data.
    """
    chunks: list[Chunk] = []

    for i, chunk in enumerate(chunk_nodes):
        x = int(chunk.get("x") or 0)
        y = int(chunk.get("y") or 0)
        width = int(chunk.get("width") or 0)
        height = int(chunk.get("height") or 0)

        logger.debug(f"[Chunk {i}] Position: ({x}, {y}), Size: {width}x{height}")

        if chunk.text is None:
            logger.error(f"[Chunk {i}] Missing text content in chunk")
            continue

        try:
            gids, raw_data = decode_chunk_data(
                text=chunk.text.strip(),
                encoding=encoding,
                compression=compression,
            )
        except Exception as e:
            logger.error(f"[Chunk {i}] Failed to decode GIDs: {e}")
            continue

        if len(gids) != width * height:
            logger.warning(
                f"[Chunk {i}] GID count mismatch: expected {width * height}, got {len(gids)}"
            )

        grid = [gids[row * width : (row + 1) * width] for row in range(height)]

        logger.debug(f"[Chunk {i}] Grid extracted with {len(grid)} rows")

        chunks.append(
            Chunk(position=(x, y), size=(width, height), grid=grid, raw=raw_data)
        )

    logger.info(f"Total chunks extracted: {len(chunks)}")
    return chunks


def stitch_chunks(
    chunks: list[Chunk], width: int, height: int, parent: TiledMap
) -> list[list[int]]:
    """
    Stitch together multiple chunks into a full tile grid, normalizing GIDs.

    Args:
        chunks: List of Chunk objects.
        width: Width of the full map in tiles.
        height: Height of the full map in tiles.
        parent: Reference to the TiledMap for GID normalization.

    Returns:
        A 2D list representing the full tile grid.
    """
    full_grid = [[0 for _ in range(width)] for _ in range(height)]

    for chunk_index, chunk in enumerate(chunks):
        cx, cy = chunk.position
        if cx < 0 or cy < 0:
            logger.warning(f"Skipping chunk at negative position ({cx}, {cy})")
            continue

        cw, ch = chunk.size
        out_of_bounds_logged = False

        for y in range(ch):
            for x in range(cw):
                raw_gid = chunk.grid[y][x]
                normalized_gid = parent.register_gid_check_flags(raw_gid)

                gx, gy = cx + x, cy + y
                if 0 <= gx < width and 0 <= gy < height:
                    full_grid[gy][gx] = normalized_gid
                elif not out_of_bounds_logged:
                    logger.warning(
                        f"[Chunk {chunk_index}] Contains out-of-bounds tiles (e.g., ({gx}, {gy}))"
                    )
                    out_of_bounds_logged = True

    logger.info("Chunks stitched successfully into full grid")
    return full_grid
