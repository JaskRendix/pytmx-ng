"""
This is tested on pygame 1.9 and python 2.7 and 3.3+.
Leif Theden "bitcraft", 2012-2025

Rendering demo for the TMXLoader.

Typically this is run to verify that any code changes do not break the loader.
Tests all Tiled features -except- terrains and object rotation.

If you are not familiar with python classes, you might want to check the
'tutorial' app.

Missing interactive_tests:
- object rotation
- terrains
"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import logging
import time
from pathlib import Path

import pygame
from pygame.locals import *

from pytmx import *
from pytmx.util_pygame import load_pygame

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def init_screen(width: int, height: int) -> pygame.Surface:
    """Set the screen mode"""
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


class TiledRenderer:
    """Super simple way to render a tiled map"""

    def __init__(self, filename: Path) -> None:
        tm = load_pygame(filename.as_posix())
        self.pixel_size = tm.width * tm.tilewidth, tm.height * tm.tileheight
        self.tmx_data = tm

        logger.info(f"Map dimensions: {self.pixel_size[0]}x{self.pixel_size[1]} pixels")

        layer_summary = []
        for layer in self.tmx_data.visible_layers:
            layer_summary.append(type(layer).__name__)
        logger.info(f"Visible layers: {', '.join(layer_summary)}")

        for layer_name in self.tmx_data.visible_tile_layers:
            layer = self.tmx_data.layers[layer_name]
            tile_count = sum(1 for _ in layer.tiles())
            logger.info(f"Layer '{layer_name}': {tile_count} tiles")

    def render_map(self, surface: pygame.Surface) -> None:
        """Render our map to a pygame surface"""
        if self.tmx_data.background_color:
            surface.fill(pygame.Color(self.tmx_data.background_color))

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                self.render_tile_layer(surface, layer)
            elif isinstance(layer, TiledObjectGroup):
                self.render_object_layer(surface, layer)
            elif isinstance(layer, TiledImageLayer):
                self.render_image_layer(surface, layer)

    def render_tile_layer(self, surface: pygame.Surface, layer: TiledTileLayer) -> None:
        tw = self.tmx_data.tilewidth
        th = self.tmx_data.tileheight
        surface_blit = surface.blit

        for x, y, image in layer.tiles():
            surface_blit(image, (x * tw, y * th))

    def render_object_layer(
        self, surface: pygame.Surface, layer: TiledObjectGroup
    ) -> None:
        draw_rect = pygame.draw.rect
        draw_lines = pygame.draw.lines
        surface_blit = surface.blit

        rect_color = (255, 0, 0)
        poly_color = (0, 255, 0)

        for obj in layer:
            if hasattr(obj, "points"):
                draw_lines(surface, poly_color, obj.closed, obj.points, 3)
            elif obj.image:
                surface_blit(obj.image, (obj.x, obj.y))
            else:
                draw_rect(surface, rect_color, (obj.x, obj.y, obj.width, obj.height), 3)

    def render_image_layer(
        self, surface: pygame.Surface, layer: TiledImageLayer
    ) -> None:
        if layer.image:
            surface.blit(layer.image, (0, 0))


class SimpleTest:
    """Basic app to display a rendered Tiled map"""

    def __init__(self, filename: Path) -> None:
        self.renderer = None
        self.running = False
        self.dirty = False
        self.exit_status = 0
        self.load_map(filename)

    def load_map(self, filename: Path) -> None:
        logger.info(f"Loaded map: {filename.name}")
        self.renderer = TiledRenderer(filename)

    def draw(self, surface: pygame.Surface) -> None:
        temp = pygame.Surface(self.renderer.pixel_size)
        self.renderer.render_map(temp)
        pygame.transform.smoothscale(temp, surface.get_size(), surface)

        f = pygame.font.Font(pygame.font.get_default_font(), 20)
        i = f.render("press any key for next map or ESC to quit", True, (180, 180, 0))
        surface.blit(i, (0, 0))

    def handle_input(self) -> None:
        try:
            event = pygame.event.wait()
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.exit_status = 0
                self.running = False
            elif event.type == KEYDOWN:
                self.running = False
            elif event.type == VIDEORESIZE:
                init_screen(event.w, event.h)
                self.dirty = True
        except KeyboardInterrupt:
            self.exit_status = 0
            self.running = False

    def run(self) -> int:
        self.dirty = True
        self.running = True
        self.exit_status = 1

        while self.running:
            self.handle_input()
            if self.dirty:
                self.draw(screen)
                self.dirty = False
                pygame.display.flip()

        return self.exit_status


if __name__ == "__main__":
    import pytmx

    pygame.init()
    pygame.font.init()
    screen = init_screen(600, 600)
    pygame.display.set_caption("PyTMX Map Viewer")

    logger.info(f"PyTMX Version: {pytmx.__version__}")

    map_folder = Path("apps/data")
    map_files = sorted(map_folder.glob("*.tmx"))

    if not map_files:
        logger.warning("No TMX files found in apps/data/")
    else:
        logger.info(f"Found {len(map_files)} TMX files.")

    try:
        start = time.time()
        for i in range(3):
            for filepath in map_files:
                pygame.event.clear()
                logger.info(f"Rendering map: {filepath.name}")
                render_start = time.time()
                SimpleTest(filepath).run()
                render_time = time.time() - render_start
                logger.info(f"Rendered in {render_time:.2f} seconds")

        total_maps = len(map_files) * 3
        logger.info(f"Completed rendering {total_maps} maps")
        logger.info(f"Total execution time: {time.time() - start:.2f} seconds")

    except Exception as e:
        logger.exception("Unexpected error:")
        pygame.quit()
        raise
