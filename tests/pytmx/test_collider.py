from pytmx.collider import Collider


def test_rectangle_center():
    collider = Collider(x=10, y=20, width=30, height=40)
    assert collider.get_center() == (25.0, 40.0)


def test_polygon_type():
    collider = Collider(x=0, y=0, type="polygon", points=[(0, 0), (1, 1)])
    assert collider.is_polygon()
    assert not collider.is_ellipse()
    assert not collider.is_point()


def test_ellipse_type():
    collider = Collider(x=0, y=0, type="ellipse", width=10, height=10)
    assert collider.is_ellipse()
    assert not collider.is_polygon()
    assert not collider.is_point()


def test_point_type():
    collider = Collider(x=5, y=5, type="point")
    assert collider.is_point()
    assert not collider.is_polygon()
    assert not collider.is_ellipse()


def test_custom_properties():
    collider = Collider(x=0, y=0, properties={"solid": True, "damage": 10})
    assert collider.get_property("solid") is True
    assert collider.get_property("damage") == 10
    assert collider.get_property("nonexistent") is None
    assert collider.get_property("nonexistent", "default") == "default"
