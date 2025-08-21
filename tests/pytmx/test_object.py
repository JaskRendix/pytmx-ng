import unittest
from unittest.mock import MagicMock
from xml.etree.ElementTree import Element

from pytmx.constants import Point
from pytmx.object import TiledObject


class TestTiledObject(unittest.TestCase):

    def setUp(self):
        self.mock_parent = MagicMock()
        self.mock_parent.register_gid_check_flags = lambda gid: gid | 0x80000000
        # Add the transformed gid to the images dictionary
        self.mock_parent.images = {1 | 0x80000000: "mock_image"}
        self.custom_types = {}

    def create_node(self, tag="object", attrib=None, children=None):
        node = Element(tag, attrib=attrib or {})
        if children:
            for child in children:
                node.append(child)
        return node

    def test_rectangle_object(self):
        node = self.create_node(
            attrib={"id": "1", "x": "10", "y": "20", "width": "30", "height": "40"}
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "rectangle")
        self.assertEqual(obj.x, 10)
        self.assertEqual(obj.y, 20)
        self.assertEqual(obj.width, 30)
        self.assertEqual(obj.height, 40)
        self.assertEqual(len(obj.points), 4)

    def test_tile_object_with_gid(self):
        node = self.create_node(attrib={"gid": "1"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "tile")
        self.assertEqual(obj.image, "mock_image")
        self.assertTrue(obj.gid & 0x80000000)

    def test_polygon_object(self):
        polygon = Element("polygon", {"points": "0,0 10,0 10,10"})
        node = self.create_node(children=[polygon])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "polygon")
        self.assertTrue(obj.closed)
        self.assertEqual(len(obj.points), 3)

    def test_polyline_object(self):
        polyline = Element("polyline", {"points": "0,0 10,0 10,10"})
        node = self.create_node(children=[polyline])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "polyline")
        self.assertFalse(obj.closed)
        self.assertEqual(len(obj.points), 3)

    def test_ellipse_object(self):
        ellipse = Element("ellipse")
        node = self.create_node(children=[ellipse])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "ellipse")

    def test_point_object(self):
        point = Element("point")
        node = self.create_node(children=[point])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "point")

    def test_text_object_defaults(self):
        text = Element("text")
        text.text = "Hello World"
        node = self.create_node(children=[text])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "text")
        self.assertEqual(obj.text, "Hello World")
        self.assertEqual(obj.font_family, "Sans Serif")
        self.assertEqual(obj.pixel_size, 16)
        self.assertFalse(obj.wrap)
        self.assertFalse(obj.bold)
        self.assertFalse(obj.italic)
        self.assertFalse(obj.underline)
        self.assertFalse(obj.strike_out)
        self.assertTrue(obj.kerning)
        self.assertEqual(obj.h_align, "left")
        self.assertEqual(obj.v_align, "top")
        self.assertEqual(obj.color, "#000000FF")

    def test_apply_transformations_with_points(self):
        node = self.create_node(
            attrib={"x": "0", "y": "0", "width": "10", "height": "10"}
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        obj.rotation = 45
        transformed = obj.apply_transformations()

        self.assertEqual(len(transformed), 4)
        self.assertTrue(all(isinstance(p, tuple) and len(p) == 2 for p in transformed))

    def test_as_points_property(self):
        node = self.create_node(
            attrib={"x": "0", "y": "0", "width": "10", "height": "10"}
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        points = obj.as_points

        self.assertEqual(len(points), 4)
        self.assertEqual(points[0], Point(0, 0))
        self.assertEqual(points[2], Point(10, 10))

    def test_missing_gid_image(self):
        node = self.create_node()
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertIsNone(obj.image)

    def test_no_text_node(self):
        node = self.create_node()
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        with self.assertRaises(AttributeError):
            _ = obj.text

    def test_malformed_points(self):
        polygon = Element("polygon", {"points": "0,0 10,a 20"})
        node = self.create_node(children=[polygon])
        with self.assertRaises(ValueError):
            TiledObject(self.mock_parent, node, self.custom_types)

    def test_rotation_angles(self):
        node = self.create_node(
            attrib={"x": "0", "y": "0", "width": "10", "height": "10"}
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        for angle in [0, 90, 180, 360]:
            obj.rotation = angle
            points = obj.apply_transformations()
            self.assertEqual(len(points), 4)
