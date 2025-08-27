import math
import unittest

from pytmx.constants import Point
from pytmx.utils import (
    convert_to_bool,
    generate_ellipse_points,
    generate_rectangle_points,
    is_convex,
    point_in_polygon,
    rotate,
)


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


class TestPointInPolygon(unittest.TestCase):
    def setUp(self):
        # Define a simple square polygon
        self.square = [Point(0, 0), Point(0, 10), Point(10, 10), Point(10, 0)]

        # Define a triangle
        self.triangle = [Point(0, 0), Point(5, 10), Point(10, 0)]

        # Define a concave polygon (arrow shape)
        self.concave = [Point(0, 0), Point(5, 5), Point(10, 0), Point(5, 10)]

    def test_point_inside_square(self):
        self.assertTrue(point_in_polygon(Point(5, 5), self.square))

    def test_point_outside_square(self):
        self.assertFalse(point_in_polygon(Point(15, 5), self.square))

    def test_point_on_edge_square(self):
        self.assertTrue(point_in_polygon(Point(0, 5), self.square))

    def test_point_inside_triangle(self):
        self.assertTrue(point_in_polygon(Point(5, 5), self.triangle))

    def test_point_outside_triangle(self):
        self.assertFalse(point_in_polygon(Point(5, -1), self.triangle))

    def test_point_inside_concave(self):
        self.assertTrue(point_in_polygon(Point(5, 6), self.concave))

    def test_point_outside_concave(self):
        self.assertFalse(point_in_polygon(Point(5, 11), self.concave))

    def test_point_on_vertex(self):
        self.assertTrue(point_in_polygon(Point(0, 0), self.square))

    def test_empty_polygon(self):
        self.assertFalse(point_in_polygon(Point(1, 1), []))


class TestIsConvex(unittest.TestCase):
    def test_convex_square(self):
        square = [Point(0, 0), Point(0, 10), Point(10, 10), Point(10, 0)]
        self.assertTrue(is_convex(square))

    def test_convex_triangle(self):
        triangle = [Point(0, 0), Point(5, 10), Point(10, 0)]
        self.assertTrue(is_convex(triangle))

    def test_concave_arrow(self):
        arrow = [Point(0, 0), Point(5, 5), Point(10, 0), Point(5, 10)]
        self.assertFalse(is_convex(arrow))

    def test_line_segment(self):
        line = [Point(0, 0), Point(10, 0)]
        self.assertTrue(is_convex(line))  # Degenerate but technically convex

    def test_single_point(self):
        single = [Point(0, 0)]
        self.assertTrue(is_convex(single))  # Trivially convex

    def test_empty_polygon(self):
        self.assertTrue(is_convex([]))  # No angles to violate convexity


class TestGenerateEllipsePoints(unittest.TestCase):
    def test_point_count(self):
        points = generate_ellipse_points(0, 0, 10, 20, segments=32)
        self.assertEqual(len(points), 32)

    def test_center_alignment(self):
        points = generate_ellipse_points(0, 0, 10, 20, segments=4)
        cx = 0 + 10 / 2
        cy = 0 + 20 / 2
        for p in points:
            self.assertAlmostEqual(
                (p.x - cx) ** 2 / (5**2) + (p.y - cy) ** 2 / (10**2), 1.0, places=5
            )

    def test_rotation_effect(self):
        unrotated = generate_ellipse_points(0, 0, 10, 20, segments=4, rotation=0)
        rotated = generate_ellipse_points(
            0, 0, 10, 20, segments=4, rotation=math.pi / 2
        )
        self.assertNotEqual(unrotated[0].x, rotated[0].x)
        self.assertNotEqual(unrotated[0].y, rotated[0].y)

    def test_zero_segments(self):
        points = generate_ellipse_points(0, 0, 10, 20, segments=0)
        self.assertEqual(points, [])

    def test_single_segment(self):
        points = generate_ellipse_points(0, 0, 10, 20, segments=1)
        self.assertEqual(len(points), 1)


class TestGenerateRectanglePoints(unittest.TestCase):
    def test_standard_rectangle(self):
        points = generate_rectangle_points(0, 0, 10, 20)
        expected = [Point(0, 0), Point(10, 0), Point(10, 20), Point(0, 20)]
        for p, e in zip(points, expected):
            self.assertEqual(p.x, e.x)
            self.assertEqual(p.y, e.y)

    def test_negative_origin(self):
        points = generate_rectangle_points(-5, -5, 10, 10)
        expected = [Point(-5, -5), Point(5, -5), Point(5, 5), Point(-5, 5)]
        for p, e in zip(points, expected):
            self.assertEqual(p.x, e.x)
            self.assertEqual(p.y, e.y)

    def test_zero_size(self):
        points = generate_rectangle_points(0, 0, 0, 0)
        for p in points:
            self.assertEqual(p.x, 0)
            self.assertEqual(p.y, 0)

    def test_float_precision(self):
        points = generate_rectangle_points(1.5, 2.5, 3.0, 4.0)
        expected = [Point(1.5, 2.5), Point(4.5, 2.5), Point(4.5, 6.5), Point(1.5, 6.5)]
        for p, e in zip(points, expected):
            self.assertAlmostEqual(p.x, e.x)
            self.assertAlmostEqual(p.y, e.y)


class TestRotateFunction(unittest.TestCase):
    def test_no_rotation(self):
        points = [Point(1, 0), Point(0, 1)]
        origin = Point(0, 0)
        rotated = rotate(points, origin, 0)
        for p, r in zip(points, rotated):
            self.assertAlmostEqual(p.x, r.x)
            self.assertAlmostEqual(p.y, r.y)

    def test_90_degree_rotation(self):
        points = [Point(1, 0)]
        origin = Point(0, 0)
        rotated = rotate(points, origin, 90)
        expected = Point(0, 1)
        self.assertAlmostEqual(rotated[0].x, expected.x, places=5)
        self.assertAlmostEqual(rotated[0].y, expected.y, places=5)

    def test_180_degree_rotation(self):
        points = [Point(1, 0)]
        origin = Point(0, 0)
        rotated = rotate(points, origin, 180)
        expected = Point(-1, 0)
        self.assertAlmostEqual(rotated[0].x, expected.x, places=5)
        self.assertAlmostEqual(rotated[0].y, expected.y, places=5)

    def test_rotation_around_custom_origin(self):
        points = [Point(2, 2)]
        origin = Point(1, 1)
        rotated = rotate(points, origin, 90)
        expected = Point(0, 2)
        self.assertAlmostEqual(rotated[0].x, expected.x, places=5)
        self.assertAlmostEqual(rotated[0].y, expected.y, places=5)

    def test_empty_input(self):
        rotated = rotate([], Point(0, 0), 45)
        self.assertEqual(rotated, [])
