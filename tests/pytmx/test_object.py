from unittest.mock import Mock
from xml.etree.ElementTree import Element

import pytest

from pytmx.constants import Point
from pytmx.object import TiledObject
from pytmx.utils import generate_rectangle_points


@pytest.fixture
def mock_parent():
    parent = Mock()
    parent.register_gid_check_flags = lambda gid: gid | 0x80000000
    parent.images = {1 | 0x80000000: "mock_image"}
    parent.templates = {}
    parent.filename = "maps/map.tmx"
    return parent


@pytest.fixture
def custom_types():
    return {}


def create_node(tag="object", attrib=None, children=None):
    node = Element(tag, attrib=attrib or {})
    if children:
        for child in children:
            node.append(child)
    return node


def create_rectangle_object(mock_parent, custom_types, x=0, y=0, width=10, height=20):
    attrib = {"x": str(x), "y": str(y), "width": str(width), "height": str(height)}
    node = create_node(attrib=attrib)
    obj = TiledObject(mock_parent, node, custom_types)
    obj.object_type = "rectangle"
    obj.points = generate_rectangle_points(x, y, width, height)
    return obj


def create_ellipse_object(mock_parent, custom_types, x=0, y=0, width=10, height=20):
    attrib = {"x": str(x), "y": str(y), "width": str(width), "height": str(height)}
    node = create_node(attrib=attrib)
    obj = TiledObject(mock_parent, node, custom_types)
    obj.object_type = "ellipse"
    return obj


def test_rectangle_object(mock_parent, custom_types):
    node = create_node(
        attrib={"id": "1", "x": "10", "y": "20", "width": "30", "height": "40"}
    )
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "rectangle"
    assert obj.x == 10
    assert obj.y == 20
    assert obj.width == 30
    assert obj.height == 40
    assert len(obj.points) == 4


def test_tile_object_with_gid(mock_parent, custom_types):
    node = create_node(attrib={"gid": "1"})
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "tile"
    assert obj.image == "mock_image"
    assert obj.gid & 0x80000000


def test_polygon_object(mock_parent, custom_types):
    polygon = Element("polygon", {"points": "0,0 10,0 10,10"})
    node = create_node(children=[polygon])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "polygon"
    assert obj.closed
    assert len(obj.points) == 3


def test_polyline_object(mock_parent, custom_types):
    polyline = Element("polyline", {"points": "0,0 10,0 10,10"})
    node = create_node(children=[polyline])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "polyline"
    assert not obj.closed
    assert len(obj.points) == 3


def test_ellipse_object(mock_parent, custom_types):
    ellipse = Element("ellipse")
    node = create_node(children=[ellipse])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "ellipse"


def test_point_object(mock_parent, custom_types):
    point = Element("point")
    node = create_node(children=[point])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "point"


def test_text_object_defaults(mock_parent, custom_types):
    text = Element("text")
    text.text = "Hello World"
    node = create_node(children=[text])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "text"
    assert obj.text == "Hello World"
    assert obj.font_family == "Sans Serif"
    assert obj.pixel_size == 16
    assert not obj.wrap
    assert not obj.bold
    assert not obj.italic
    assert not obj.underline
    assert not obj.strike_out
    assert obj.kerning
    assert obj.h_align == "left"
    assert obj.v_align == "top"
    assert obj.color == "#000000FF"


def test_apply_transformations_with_points(mock_parent, custom_types):
    node = create_node(attrib={"x": "0", "y": "0", "width": "10", "height": "10"})
    obj = TiledObject(mock_parent, node, custom_types)
    obj.rotation = 45
    transformed = obj.apply_transformations()

    assert len(transformed) == 4
    assert all(isinstance(p, tuple) and len(p) == 2 for p in transformed)


def test_as_points_property(mock_parent, custom_types):
    node = create_node(attrib={"x": "0", "y": "0", "width": "10", "height": "10"})
    obj = TiledObject(mock_parent, node, custom_types)
    points = obj.as_points

    assert len(points) == 4
    assert points[0] == Point(0, 0)
    assert points[2] == Point(10, 10)


def test_missing_gid_image(mock_parent, custom_types):
    node = create_node()
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.image is None


def test_no_text_node(mock_parent, custom_types):
    node = create_node()
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "rectangle"
    assert obj.text is None


def test_malformed_points(mock_parent, custom_types):
    polygon = Element("polygon", {"points": "0,0 10,a 20"})
    node = create_node(children=[polygon])

    with pytest.raises(ValueError):
        TiledObject(mock_parent, node, custom_types)


@pytest.mark.parametrize("angle", [0, 90, 180, 360])
def test_rotation_angles(mock_parent, custom_types, angle):
    node = create_node(attrib={"x": "0", "y": "0", "width": "10", "height": "10"})
    obj = TiledObject(mock_parent, node, custom_types)
    obj.rotation = angle
    assert len(obj.apply_transformations()) == 4


# Template tests -------------------------------------------------------------


def test_template_basic_merge(mock_parent, custom_types):
    template_node = create_node(
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
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.object_type = "rectangle"
    template_obj.properties = {"speed": 10}

    mock_parent.templates = {"test_template.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    node = create_node(
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
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.id == 1
    assert obj.name == "local_name"
    assert obj.type == "local_type"
    assert obj.x == 10
    assert obj.y == 20
    assert obj.width == 30
    assert obj.height == 40
    assert obj.rotation == 45
    assert obj.object_type == "rectangle"
    assert obj.properties["speed"] == 10


def test_template_polygon_override(mock_parent, custom_types):
    template_node = create_node(
        attrib={"x": "0", "y": "0", "width": "10", "height": "10"}
    )
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.object_type = "rectangle"

    mock_parent.templates = {"test_template.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    polygon = Element("polygon", {"points": "0,0 10,0 10,10"})
    node = create_node(attrib={"template": "test_template.tx"}, children=[polygon])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "polygon"
    assert len(obj.points) == 3


def test_template_missing_file(mock_parent, custom_types):
    mock_parent._load_template = lambda path: None

    node = create_node(attrib={"template": "missing.tx"})
    obj = TiledObject(mock_parent, node, custom_types)

    assert isinstance(obj, TiledObject)
    assert obj.object_type == "rectangle"


def test_template_fallback_values(mock_parent, custom_types):
    template_node = create_node(
        attrib={"x": "50", "y": "60", "width": "70", "height": "80"}
    )
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.object_type = "rectangle"

    mock_parent.templates = {"fallback.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    node = create_node(attrib={"template": "fallback.tx"})
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.x == 50
    assert obj.y == 60
    assert obj.width == 70
    assert obj.height == 80


def test_template_shape_override(mock_parent, custom_types):
    template_node = create_node()
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.object_type = "ellipse"

    mock_parent.templates = {"shape.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    polyline = Element("polyline", {"points": "0,0 10,10"})
    node = create_node(attrib={"template": "shape.tx"}, children=[polyline])
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "polyline"
    assert len(obj.points) == 2


def test_template_text_inheritance(mock_parent, custom_types):
    text = Element("text")
    text.text = "Template Text"
    text.set("fontfamily", "Courier")
    text.set("pixelsize", "20")

    template_node = create_node(children=[text])
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.object_type = "text"

    mock_parent.templates = {"text.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    node = create_node(attrib={"template": "text.tx"})
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.object_type == "text"
    assert obj.text == "Template Text"
    assert obj.font_family == "Courier"
    assert obj.pixel_size == 20


def test_template_custom_properties(mock_parent, custom_types):
    template_node = create_node()
    template_obj = TiledObject(mock_parent, template_node, custom_types)
    template_obj.properties = {"health": 100, "speed": 5}

    mock_parent.templates = {"props.tx": template_obj}
    mock_parent._load_template = lambda path: mock_parent.templates[path]

    node = create_node(attrib={"template": "props.tx"})
    obj = TiledObject(mock_parent, node, custom_types)

    assert obj.properties["health"] == 100
    assert obj.properties["speed"] == 5


def test_as_ellipse_property(mock_parent, custom_types):
    ellipse = Element("ellipse")
    node = create_node(
        attrib={"x": "10", "y": "20", "width": "100", "height": "50"},
        children=[ellipse],
    )
    obj = TiledObject(mock_parent, node, custom_types)

    center, rx, ry = obj.as_ellipse
    assert center == Point(60, 45)
    assert rx == 50
    assert ry == 25


def test_as_points(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 20)
    expected = [Point(0, 0), Point(0, 20), Point(10, 20), Point(10, 0)]
    assert obj.as_points == expected


def test_as_ellipse(mock_parent, custom_types):
    obj = create_ellipse_object(mock_parent, custom_types, 0, 0, 10, 20)
    center, rx, ry = obj.as_ellipse

    assert pytest.approx(center.x) == 5
    assert pytest.approx(center.y) == 10
    assert pytest.approx(rx) == 5
    assert pytest.approx(ry) == 10


def test_get_bounding_box(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 20)
    assert obj.get_bounding_box() == (0, 0, 10, 20)


def test_collides_with_point_inside(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    assert obj.collides_with_point(5, 5)


def test_collides_with_point_outside(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    assert not obj.collides_with_point(15, 5)


def test_intersects_with_rect_true(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    assert obj.intersects_with_rect((5, 5, 15, 15))


def test_intersects_with_rect_false(mock_parent, custom_types):
    obj = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    assert not obj.intersects_with_rect((20, 20, 30, 30))


def test_intersects_with_object_true(mock_parent, custom_types):
    obj1 = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    obj2 = create_rectangle_object(mock_parent, custom_types, 5, 5, 10, 10)
    assert obj1.intersects_with_object(obj2)


def test_intersects_with_object_false(mock_parent, custom_types):
    obj1 = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    obj2 = create_rectangle_object(mock_parent, custom_types, 20, 20, 10, 10)
    assert not obj1.intersects_with_object(obj2)


def test_intersects_with_polygon_true(mock_parent, custom_types):
    obj1 = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    obj2 = create_rectangle_object(mock_parent, custom_types, 5, 5, 10, 10)
    assert obj1.intersects_with_polygon(obj2)


def test_intersects_with_polygon_false(mock_parent, custom_types):
    obj1 = create_rectangle_object(mock_parent, custom_types, 0, 0, 10, 10)
    obj2 = create_rectangle_object(mock_parent, custom_types, 20, 20, 10, 10)
    assert not obj1.intersects_with_polygon(obj2)
