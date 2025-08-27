import unittest

from pytmx.map import TiledMap

# Tiled gid flags
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT


class TiledMapTest(unittest.TestCase):
    filename = "tests/resources/test01.tmx"

    def setUp(self) -> None:
        self.m = TiledMap(self.filename)

    def test_build_rects(self) -> None:
        try:
            from pytmx import util_pygame

            rects = util_pygame.build_rects(self.m, "Grass and Water", "tileset", None)
            self.assertEqual(rects[0], [0, 0, 240, 240])
            rects = util_pygame.build_rects(self.m, "Grass and Water", "tileset", 18)
            self.assertNotEqual(0, len(rects))
        except ImportError:
            pass

    def test_get_tile_image(self) -> None:
        image = self.m.get_tile_image(0, 0, 0)

    def test_get_tile_image_by_gid(self) -> None:
        image = self.m.get_tile_image_by_gid(0)
        self.assertIsNone(image)

        image = self.m.get_tile_image_by_gid(1)
        self.assertIsNotNone(image)

    def test_reserved_names_check_disabled_with_option(self) -> None:
        tiled_map = TiledMap(allow_duplicate_names=True)
        items = [("name", "conflict")]
        self.assertFalse(tiled_map._contains_invalid_property_name(items))

    def test_map_width_height_is_int(self) -> None:
        self.assertIsInstance(self.m.width, int)
        self.assertIsInstance(self.m.height, int)

    def test_layer_width_height_is_int(self) -> None:
        self.assertIsInstance(self.m.layers[0].width, int)
        self.assertIsInstance(self.m.layers[0].height, int)

    def test_properties_are_converted_to_builtin_types(self) -> None:
        self.assertIsInstance(self.m.properties["test_bool"], bool)
        self.assertIsInstance(self.m.properties["test_color"], str)
        self.assertIsInstance(self.m.properties["test_file"], str)
        self.assertIsInstance(self.m.properties["test_float"], float)
        self.assertIsInstance(self.m.properties["test_int"], int)
        self.assertIsInstance(self.m.properties["test_string"], str)

    def test_properties_are_converted_to_correct_values(self) -> None:
        self.assertFalse(self.m.properties["test_bool"])
        self.assertTrue(self.m.properties["test_bool_true"])

    def test_pixels_to_tile_pos(self) -> None:
        self.assertEqual(self.m.pixels_to_tile_pos((0, 33)), (0, 2))
        self.assertEqual(self.m.pixels_to_tile_pos((33, 0)), (2, 0))
        self.assertEqual(self.m.pixels_to_tile_pos((0, 0)), (0, 0))
        self.assertEqual(self.m.pixels_to_tile_pos((65, 86)), (4, 5))
