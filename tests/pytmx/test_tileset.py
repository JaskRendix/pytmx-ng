import unittest
from unittest.mock import MagicMock, patch
from xml.etree.ElementTree import Element, SubElement

from pytmx.constants import AnimationFrame
from pytmx.tileset import TiledTileset


class TestTiledTileset(unittest.TestCase):

    def setUp(self):
        self.mock_parent = MagicMock()
        self.mock_parent.filename = "/maps/test_map.tmx"
        self.mock_parent.register_gid = lambda gid: gid + 1000
        self.mock_parent.map_gid2 = lambda gid: [(gid, 0)]
        self.mock_parent.set_tile_properties = MagicMock()

    def create_basic_tileset_node(self):
        node = Element(
            "tileset",
            {
                "name": "TestTileset",
                "tilewidth": "32",
                "tileheight": "32",
                "tilecount": "4",
                "columns": "2",
            },
        )
        image = SubElement(
            node, "image", {"source": "tiles.png", "width": "64", "height": "64"}
        )
        return node

    def test_basic_tileset_parsing(self):
        node = self.create_basic_tileset_node()
        tileset = TiledTileset(self.mock_parent, node)

        self.assertEqual(tileset.name, "TestTileset")
        self.assertEqual(tileset.tilewidth, 32)
        self.assertEqual(tileset.tileheight, 32)
        self.assertEqual(tileset.tilecount, 4)
        self.assertEqual(tileset.columns, 2)
        self.assertEqual(tileset.source, "tiles.png")
        self.assertEqual(tileset.width, 64)
        self.assertEqual(tileset.height, 64)

    def test_external_tileset_loading(self):
        tsx_path = "/maps/test_tileset.tsx"
        tsx_node = self.create_basic_tileset_node()

        with (
            patch("os.path.exists", return_value=True),
            patch("xml.etree.ElementTree.parse") as mock_parse,
        ):
            mock_parse.return_value.getroot.return_value = tsx_node

            external_node = Element(
                "tileset", {"firstgid": "1", "source": "test_tileset.tsx"}
            )
            tileset = TiledTileset(self.mock_parent, external_node)

            self.assertEqual(tileset.firstgid, 1)
            self.assertEqual(tileset.name, "TestTileset")

    def test_missing_external_file_raises(self):
        external_node = Element("tileset", {"firstgid": "1", "source": "missing.tsx"})

        with patch("os.path.exists", return_value=False):
            with self.assertRaises(Exception) as context:
                TiledTileset(self.mock_parent, external_node)
            self.assertIn("Cannot find tileset file", str(context.exception))

    def test_tile_with_animation(self):
        node = self.create_basic_tileset_node()
        tile = SubElement(node, "tile", {"id": "0"})
        anim = SubElement(tile, "animation")
        SubElement(anim, "frame", {"tileid": "1", "duration": "100"})
        SubElement(anim, "frame", {"tileid": "2", "duration": "200"})

        tileset = TiledTileset(self.mock_parent, node)
        props = self.mock_parent.set_tile_properties.call_args[0][1]

        self.assertIn("frames", props)
        self.assertEqual(len(props["frames"]), 2)
        self.assertIsInstance(props["frames"][0], AnimationFrame)

    def test_tile_with_image_and_transparency(self):
        node = self.create_basic_tileset_node()
        tile = SubElement(node, "tile", {"id": "0"})
        image = SubElement(
            tile,
            "image",
            {"source": "tile0.png", "trans": "ff00ff", "width": "32", "height": "32"},
        )

        tileset = TiledTileset(self.mock_parent, node)
        props = self.mock_parent.set_tile_properties.call_args[0][1]

        self.assertEqual(props["source"], "tile0.png")
        self.assertEqual(props["trans"], "ff00ff")
        self.assertEqual(props["width"], 32)
        self.assertEqual(props["height"], 32)

    def test_tileoffset_parsing(self):
        node = self.create_basic_tileset_node()
        offset = SubElement(node, "tileoffset", {"x": "5", "y": "10"})

        tileset = TiledTileset(self.mock_parent, node)
        self.assertEqual(tileset.offset, (5, 10))

    def test_tile_without_image_defaults(self):
        node = self.create_basic_tileset_node()
        tile = SubElement(node, "tile", {"id": "0"})

        tileset = TiledTileset(self.mock_parent, node)
        props = self.mock_parent.set_tile_properties.call_args[0][1]

        self.assertEqual(props["width"], 32)
        self.assertEqual(props["height"], 32)

    def test_empty_tileset_node(self):
        node = Element("tileset")
        tileset = TiledTileset(self.mock_parent, node)
        self.assertEqual(tileset.name, None)
        self.assertEqual(tileset.tilewidth, 0)

    def test_invalid_tilewidth_type(self):
        node = Element("tileset", {"tilewidth": "not_an_int"})
        with self.assertRaises(ValueError):
            TiledTileset(self.mock_parent, node)

    def test_multiple_tileoffset_nodes(self):
        node = self.create_basic_tileset_node()
        SubElement(node, "tileoffset", {"x": "1", "y": "2"})
        SubElement(node, "tileoffset", {"x": "99", "y": "99"})  # Should be ignored

        tileset = TiledTileset(self.mock_parent, node)
        self.assertEqual(tileset.offset, (1, 2))

    def test_tile_missing_id(self):
        node = self.create_basic_tileset_node()
        tile = SubElement(node, "tile")  # No 'id'

        with self.assertRaises(TypeError):
            TiledTileset(self.mock_parent, node)

    def test_tileset_with_unknown_tags(self):
        node = self.create_basic_tileset_node()
        SubElement(node, "unknownTag", {"foo": "bar"})

        tileset = TiledTileset(self.mock_parent, node)
        self.assertEqual(tileset.name, "TestTileset")  # Still parses correctly

    def test_tileset_without_image(self):
        node = Element(
            "tileset", {"name": "NoImageTileset", "tilewidth": "32", "tileheight": "32"}
        )

        tileset = TiledTileset(self.mock_parent, node)
        self.assertIsNone(tileset.source)
        self.assertEqual(tileset.width, 0)

    def test_tile_with_objectgroup(self):
        node = self.create_basic_tileset_node()
        tile = SubElement(node, "tile", {"id": "0"})
        objgrp = SubElement(tile, "objectgroup")
        SubElement(objgrp, "object", {"id": "1", "x": "10", "y": "20"})

        tileset = TiledTileset(self.mock_parent, node)
        props = self.mock_parent.set_tile_properties.call_args[0][1]
        self.assertIn("colliders", props)
