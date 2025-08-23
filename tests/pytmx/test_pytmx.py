import logging
import unittest

from pytmx.element import TiledElement
from pytmx.map import TiledMap
from pytmx.utils import convert_to_bool

# Tiled gid flags
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT


class TestConvertToBool(unittest.TestCase):
    def test_string_string_true(self) -> None:
        self.assertTrue(convert_to_bool("1"))
        self.assertTrue(convert_to_bool("y"))
        self.assertTrue(convert_to_bool("Y"))
        self.assertTrue(convert_to_bool("t"))
        self.assertTrue(convert_to_bool("T"))
        self.assertTrue(convert_to_bool("yes"))
        self.assertTrue(convert_to_bool("Yes"))
        self.assertTrue(convert_to_bool("YES"))
        self.assertTrue(convert_to_bool("true"))
        self.assertTrue(convert_to_bool("True"))
        self.assertTrue(convert_to_bool("TRUE"))

    def test_string_string_false(self) -> None:
        self.assertFalse(convert_to_bool("0"))
        self.assertFalse(convert_to_bool("n"))
        self.assertFalse(convert_to_bool("N"))
        self.assertFalse(convert_to_bool("f"))
        self.assertFalse(convert_to_bool("F"))
        self.assertFalse(convert_to_bool("no"))
        self.assertFalse(convert_to_bool("No"))
        self.assertFalse(convert_to_bool("NO"))
        self.assertFalse(convert_to_bool("false"))
        self.assertFalse(convert_to_bool("False"))
        self.assertFalse(convert_to_bool("FALSE"))

    def test_string_number_true(self) -> None:
        self.assertTrue(convert_to_bool(1))
        self.assertTrue(convert_to_bool(1.0))

    def test_string_number_false(self) -> None:
        self.assertFalse(convert_to_bool(0))
        self.assertFalse(convert_to_bool(0.0))
        self.assertFalse(convert_to_bool(-1))
        self.assertFalse(convert_to_bool(-1.1))

    def test_string_bool_true(self) -> None:
        self.assertTrue(convert_to_bool(True))

    def test_string_bool_false(self) -> None:
        self.assertFalse(convert_to_bool(False))

    def test_string_bool_none(self) -> None:
        self.assertFalse(convert_to_bool(None))

    def test_string_bool_empty(self) -> None:
        self.assertFalse(convert_to_bool(""))

    def test_string_bool_whitespace_only(self) -> None:
        self.assertFalse(convert_to_bool(" "))

    def test_non_boolean_string_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            convert_to_bool("garbage")

    def test_non_boolean_number_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            convert_to_bool("200")

    def test_edge_cases(self):
        # Whitespace
        self.assertTrue(convert_to_bool("  t  "))
        self.assertFalse(convert_to_bool("  f  "))

        # Numeric edge cases
        self.assertTrue(convert_to_bool(1e-10))  # Very small positive number
        self.assertFalse(convert_to_bool(-1e-10))  # Very small negative number


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
