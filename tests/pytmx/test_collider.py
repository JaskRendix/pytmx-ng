import unittest

from pytmx.collider import Collider


class TestCollider(unittest.TestCase):

    def test_rectangle_center(self):
        collider = Collider(x=10, y=20, width=30, height=40)
        self.assertEqual(collider.get_center(), (25.0, 40.0))

    def test_polygon_type(self):
        collider = Collider(x=0, y=0, type="polygon", points=[(0, 0), (1, 1)])
        self.assertTrue(collider.is_polygon())
        self.assertFalse(collider.is_ellipse())
        self.assertFalse(collider.is_point())

    def test_ellipse_type(self):
        collider = Collider(x=0, y=0, type="ellipse", width=10, height=10)
        self.assertTrue(collider.is_ellipse())
        self.assertFalse(collider.is_polygon())
        self.assertFalse(collider.is_point())

    def test_point_type(self):
        collider = Collider(x=5, y=5, type="point")
        self.assertTrue(collider.is_point())
        self.assertFalse(collider.is_polygon())
        self.assertFalse(collider.is_ellipse())

    def test_custom_properties(self):
        collider = Collider(x=0, y=0, properties={"solid": True, "damage": 10})
        self.assertTrue(collider.get_property("solid"))
        self.assertEqual(collider.get_property("damage"), 10)
        self.assertIsNone(collider.get_property("nonexistent"))
        self.assertEqual(collider.get_property("nonexistent", "default"), "default")
