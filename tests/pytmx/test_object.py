import unittest
from unittest.mock import MagicMock
from xml.etree.ElementTree import Element

from pytmx.constants import Point
from pytmx.object import TiledObject
from pytmx.utils import generate_rectangle_points


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

    def create_rectangle_object(self, x=0, y=0, width=10, height=20):
        attrib = {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
        }
        node = self.create_node(attrib=attrib)
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        obj.object_type = "rectangle"
        obj.points = generate_rectangle_points(x, y, width, height)
        return obj

    def create_ellipse_object(self, x=0, y=0, width=10, height=20):
        attrib = {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
        }
        node = self.create_node(attrib=attrib)
        obj = TiledObject(self.mock_parent, node, self.custom_types)
        obj.object_type = "ellipse"
        return obj

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

        self.assertEqual(obj.object_type, "rectangle")  # or whatever default
        self.assertIsNone(obj.text)

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

    def test_template_basic_merge(self):
        template_node = self.create_node(
            attrib={
                "id": "99",
                "x": "5",
                "y": "5",
                "width": "100",
                "height": "200",
                "rotation": "0",
                "type": "template_type",
                "name": "template_name",
            }
        )
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "rectangle"
        template_obj.properties = {"speed": 10}

        self.mock_parent.templates = {"test_template.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(
            attrib={
                "template": "test_template.tx",
                "id": "1",
                "x": "10",
                "y": "20",
                "width": "30",
                "height": "40",
                "rotation": "45",
                "type": "local_type",
                "name": "local_name",
            }
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.name, "local_name")
        self.assertEqual(obj.type, "local_type")
        self.assertEqual(obj.x, 10)
        self.assertEqual(obj.y, 20)
        self.assertEqual(obj.width, 30)
        self.assertEqual(obj.height, 40)
        self.assertEqual(obj.rotation, 45)
        self.assertEqual(obj.object_type, "rectangle")
        self.assertIn("speed", obj.properties)
        self.assertEqual(obj.properties["speed"], 10)

    def test_template_polygon_override(self):
        template_node = self.create_node(
            attrib={"x": "0", "y": "0", "width": "10", "height": "10"}
        )
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "rectangle"
        template_obj.properties = {}

        self.mock_parent.templates = {"test_template.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        polygon = Element("polygon", {"points": "0,0 10,0 10,10"})
        node = self.create_node(
            attrib={"template": "test_template.tx"}, children=[polygon]
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "polygon")
        self.assertEqual(len(obj.points), 3)

    def test_template_missing_file(self):
        self.mock_parent._load_template = lambda path: None
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(attrib={"template": "missing.tx"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertIsInstance(obj, TiledObject)
        self.assertEqual(obj.object_type, "rectangle")

    def test_template_fallback_values(self):
        template_node = self.create_node(
            attrib={"x": "50", "y": "60", "width": "70", "height": "80"}
        )
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "rectangle"

        self.mock_parent.templates = {"fallback.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(attrib={"template": "fallback.tx"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.x, 50)
        self.assertEqual(obj.y, 60)
        self.assertEqual(obj.width, 70)
        self.assertEqual(obj.height, 80)

    def test_template_shape_override(self):
        template_node = self.create_node()
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "ellipse"

        self.mock_parent.templates = {"shape.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        polyline = Element("polyline", {"points": "0,0 10,10"})
        node = self.create_node(attrib={"template": "shape.tx"}, children=[polyline])
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "polyline")
        self.assertEqual(len(obj.points), 2)

    def test_template_text_inheritance(self):
        text = Element("text")
        text.text = "Template Text"
        text.set("fontfamily", "Courier")
        text.set("pixelsize", "20")
        template_node = self.create_node(children=[text])
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "text"

        self.mock_parent.templates = {"text.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(attrib={"template": "text.tx"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "text")
        self.assertEqual(obj.text, "Template Text")
        self.assertEqual(obj.font_family, "Courier")
        self.assertEqual(obj.pixel_size, 20)

    def test_template_custom_properties(self):
        template_node = self.create_node()
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.properties = {"health": 100, "speed": 5}

        self.mock_parent.templates = {"props.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(attrib={"template": "props.tx"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.properties["health"], 100)
        self.assertEqual(obj.properties["speed"], 5)

    def test_template_text_shape_fallback(self):
        text = Element("text")
        text.text = "Template Text"
        text.set("fontfamily", "Courier")
        text.set("pixelsize", "20")

        template_node = self.create_node(children=[text])
        template_obj = TiledObject(self.mock_parent, template_node, self.custom_types)
        template_obj.object_type = "text"
        template_obj.node = template_node  # Required for fallback parsing

        self.mock_parent.templates = {"text_template.tx": template_obj}
        self.mock_parent._load_template = lambda path: self.mock_parent.templates[path]
        self.mock_parent.filename = "maps/map.tmx"

        node = self.create_node(attrib={"template": "text_template.tx"})
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        self.assertEqual(obj.object_type, "text")
        self.assertEqual(obj.text, "Template Text")
        self.assertEqual(obj.font_family, "Courier")
        self.assertEqual(obj.pixel_size, 20)

    def test_as_ellipse_property(self):
        ellipse = Element("ellipse")
        node = self.create_node(
            attrib={"x": "10", "y": "20", "width": "100", "height": "50"},
            children=[ellipse],
        )
        obj = TiledObject(self.mock_parent, node, self.custom_types)

        center, rx, ry = obj.as_ellipse
        self.assertEqual(center, Point(60, 45))
        self.assertEqual(rx, 50)
        self.assertEqual(ry, 25)

    def test_as_points(self):
        obj = self.create_rectangle_object(0, 0, 10, 20)
        points = obj.as_points
        expected = [Point(0, 0), Point(0, 20), Point(10, 20), Point(10, 0)]
        self.assertEqual(points, expected)

    def test_as_ellipse(self):
        obj = self.create_ellipse_object(0, 0, 10, 20)
        center, rx, ry = obj.as_ellipse
        self.assertAlmostEqual(center.x, 5)
        self.assertAlmostEqual(center.y, 10)
        self.assertAlmostEqual(rx, 5)
        self.assertAlmostEqual(ry, 10)

    def test_get_bounding_box(self):
        obj = self.create_rectangle_object(0, 0, 10, 20)
        bbox = obj.get_bounding_box()
        self.assertEqual(bbox, (0, 0, 10, 20))

    def test_collides_with_point_inside(self):
        obj = self.create_rectangle_object(0, 0, 10, 10)
        self.assertTrue(obj.collides_with_point(5, 5))

    def test_collides_with_point_outside(self):
        obj = self.create_rectangle_object(0, 0, 10, 10)
        self.assertFalse(obj.collides_with_point(15, 5))

    def test_intersects_with_rect_true(self):
        obj = self.create_rectangle_object(0, 0, 10, 10)
        other_rect = (5, 5, 15, 15)
        self.assertTrue(obj.intersects_with_rect(other_rect))

    def test_intersects_with_rect_false(self):
        obj = self.create_rectangle_object(0, 0, 10, 10)
        other_rect = (20, 20, 30, 30)
        self.assertFalse(obj.intersects_with_rect(other_rect))

    def test_intersects_with_object_true(self):
        obj1 = self.create_rectangle_object(0, 0, 10, 10)
        obj2 = self.create_rectangle_object(5, 5, 10, 10)
        self.assertTrue(obj1.intersects_with_object(obj2))

    def test_intersects_with_object_false(self):
        obj1 = self.create_rectangle_object(0, 0, 10, 10)
        obj2 = self.create_rectangle_object(20, 20, 10, 10)
        self.assertFalse(obj1.intersects_with_object(obj2))

    def test_intersects_with_polygon_true(self):
        obj1 = self.create_rectangle_object(0, 0, 10, 10)
        obj2 = self.create_rectangle_object(5, 5, 10, 10)
        self.assertTrue(obj1.intersects_with_polygon(obj2))

    def test_intersects_with_polygon_false(self):
        obj1 = self.create_rectangle_object(0, 0, 10, 10)
        obj2 = self.create_rectangle_object(20, 20, 10, 10)
        self.assertFalse(obj1.intersects_with_polygon(obj2))
