import math

import pytest

from pytmx.constants import Point
from pytmx.utils import (
    compute_adjusted_position,
    convert_to_bool,
    generate_ellipse_points,
    generate_rectangle_points,
    is_convex,
    pixels_to_tile_pos,
    point_in_polygon,
    rotate,
)

# ---------------------------------------------------------------------------
# convert_to_bool
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value", ["1", "y", "Y", "t", "T", "yes", "Yes", "YES", "true", "True", "TRUE"]
)
def test_convert_to_bool_string_true(value):
    assert convert_to_bool(value) is True


@pytest.mark.parametrize(
    "value", ["0", "n", "N", "f", "F", "no", "No", "NO", "false", "False", "FALSE"]
)
def test_convert_to_bool_string_false(value):
    assert convert_to_bool(value) is False


@pytest.mark.parametrize("value", [1, 1.0])
def test_convert_to_bool_number_true(value):
    assert convert_to_bool(value) is True


@pytest.mark.parametrize("value", [0, 0.0, -1, -1.1])
def test_convert_to_bool_number_false(value):
    assert convert_to_bool(value) is False


@pytest.mark.parametrize(
    "value, expected",
    [(True, True), (False, False), (None, False), ("", False), (" ", False)],
)
def test_convert_to_bool_misc(value, expected):
    assert convert_to_bool(value) is expected


@pytest.mark.parametrize("value", ["garbage", "200"])
def test_convert_to_bool_invalid(value):
    with pytest.raises(ValueError):
        convert_to_bool(value)


def test_convert_to_bool_edge_cases():
    assert convert_to_bool("  t  ") is True
    assert convert_to_bool("  f  ") is False
    assert convert_to_bool(1e-10) is True
    assert convert_to_bool(-1e-10) is False


# ---------------------------------------------------------------------------
# point_in_polygon
# ---------------------------------------------------------------------------


@pytest.fixture
def square():
    return [Point(0, 0), Point(0, 10), Point(10, 10), Point(10, 0)]


@pytest.fixture
def triangle():
    return [Point(0, 0), Point(5, 10), Point(10, 0)]


@pytest.fixture
def concave():
    return [Point(0, 0), Point(5, 5), Point(10, 0), Point(5, 10)]


def test_point_in_polygon_square(square):
    assert point_in_polygon(Point(5, 5), square)
    assert not point_in_polygon(Point(15, 5), square)
    assert point_in_polygon(Point(0, 5), square)
    assert point_in_polygon(Point(0, 0), square)


def test_point_in_polygon_triangle(triangle):
    assert point_in_polygon(Point(5, 5), triangle)
    assert not point_in_polygon(Point(5, -1), triangle)


def test_point_in_polygon_concave(concave):
    assert point_in_polygon(Point(5, 6), concave)
    assert not point_in_polygon(Point(5, 11), concave)


def test_point_in_polygon_empty():
    assert not point_in_polygon(Point(1, 1), [])


# ---------------------------------------------------------------------------
# is_convex
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "poly, expected",
    [
        ([Point(0, 0), Point(0, 10), Point(10, 10), Point(10, 0)], True),
        ([Point(0, 0), Point(5, 10), Point(10, 0)], True),
        ([Point(0, 0), Point(5, 5), Point(10, 0), Point(5, 10)], False),
        ([Point(0, 0), Point(10, 0)], True),
        ([Point(0, 0)], True),
        ([], True),
    ],
)
def test_is_convex(poly, expected):
    assert is_convex(poly) is expected


# ---------------------------------------------------------------------------
# generate_ellipse_points
# ---------------------------------------------------------------------------


def test_generate_ellipse_points_count():
    assert len(generate_ellipse_points(0, 0, 10, 20, segments=32)) == 32


def test_generate_ellipse_points_center_alignment():
    points = generate_ellipse_points(0, 0, 10, 20, segments=4)
    cx, cy = 5, 10
    for p in points:
        assert (
            pytest.approx((p.x - cx) ** 2 / 25 + (p.y - cy) ** 2 / 100, rel=1e-5) == 1.0
        )


def test_generate_ellipse_points_rotation():
    unrot = generate_ellipse_points(0, 0, 10, 20, segments=4, rotation=0)
    rot = generate_ellipse_points(0, 0, 10, 20, segments=4, rotation=math.pi / 2)
    assert (unrot[0].x, unrot[0].y) != (rot[0].x, rot[0].y)


@pytest.mark.parametrize("segments, expected", [(0, []), (1, 1)])
def test_generate_ellipse_points_segment_edge_cases(segments, expected):
    pts = generate_ellipse_points(0, 0, 10, 20, segments=segments)
    assert len(pts) == (expected if isinstance(expected, int) else len(expected))


# ---------------------------------------------------------------------------
# generate_rectangle_points
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args, expected",
    [
        ((0, 0, 10, 20), [Point(0, 0), Point(10, 0), Point(10, 20), Point(0, 20)]),
        ((-5, -5, 10, 10), [Point(-5, -5), Point(5, -5), Point(5, 5), Point(-5, 5)]),
        ((0, 0, 0, 0), [Point(0, 0)] * 4),
        (
            (1.5, 2.5, 3.0, 4.0),
            [Point(1.5, 2.5), Point(4.5, 2.5), Point(4.5, 6.5), Point(1.5, 6.5)],
        ),
    ],
)
def test_generate_rectangle_points(args, expected):
    pts = generate_rectangle_points(*args)
    for p, e in zip(pts, expected, strict=False):
        assert pytest.approx(p.x) == e.x
        assert pytest.approx(p.y) == e.y


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------


def test_rotate_no_rotation():
    pts = [Point(1, 0), Point(0, 1)]
    out = rotate(pts, Point(0, 0), 0)
    for p, r in zip(pts, out, strict=False):
        assert pytest.approx(p.x) == r.x
        assert pytest.approx(p.y) == r.y


@pytest.mark.parametrize(
    "angle, expected",
    [
        (90, Point(0, 1)),
        (180, Point(-1, 0)),
    ],
)
def test_rotate_basic(angle, expected):
    out = rotate([Point(1, 0)], Point(0, 0), angle)
    assert pytest.approx(out[0].x) == expected.x
    assert pytest.approx(out[0].y) == expected.y


def test_rotate_custom_origin():
    out = rotate([Point(2, 2)], Point(1, 1), 90)
    assert pytest.approx(out[0].x) == 0
    assert pytest.approx(out[0].y) == 2


def test_rotate_empty():
    assert rotate([], Point(0, 0), 45) == []


# ---------------------------------------------------------------------------
# pixels_to_tile_pos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args, expected",
    [
        (((64, 96), "orthogonal", 32, 32), (2, 3)),
        (((64, 32), "isometric", 32, 32), (1, -1)),
        (((0, 0), "isometric", 32, 32), (0, 0)),
        (((48, 32), "staggered", 32, 32, "y", "even"), (1, 2)),
        (((48, 32), "staggered", 32, 32, "y", "odd"), (1, 2)),
        (((32, 48), "staggered", 32, 32, "x", "even"), (2, 1)),
        (((32, 48), "staggered", 32, 32, "x", "odd"), (2, 1)),
        (((64, 64), "hexagonal", 32, 32, "y", "odd"), (2, 2)),
        (((64, 64), "hexagonal", 32, 32, "x", "odd"), (2, 2)),
        (((64, 64), "unknown", 32, 32), (2, 2)),
    ],
)
def test_pixels_to_tile_pos(args, expected):
    assert pixels_to_tile_pos(*args) == expected


# ---------------------------------------------------------------------------
# compute_adjusted_position
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args, expected",
    [
        ((10, 20, 30, 40, "orthogonal", 0, 64, 64, False), (10, 20)),
        ((0, 0, 10, 20, "orthogonal", 90, 64, 64, False), (20, 0)),
        ((5, 5, 10, 20, "orthogonal", 180, 64, 64, True), (15, 5)),
        ((100, 100, 32, 32, "isometric", 0, 64, 64, False), (68, 68)),
        ((100, 100, 32, 32, "isometric", 90, 64, 64, True), (84, 52)),
        ((0, 0, 10, 20, "staggered", 270, 64, 64, False), (0, 10)),
        ((10, 10, 10, 20, "hexagonal", 180, 64, 64, True), (20, 10)),
        ((1, 2, 3, 4, "unknown", 0, 64, 64, False), (1, 2)),
    ],
)
def test_compute_adjusted_position(args, expected):
    assert compute_adjusted_position(*args) == expected
