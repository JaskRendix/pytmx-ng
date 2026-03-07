import pytest

from pytmx.map import TiledMap

# Tiled gid flags
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT


@pytest.fixture
def tiled_map():
    return TiledMap("tests/resources/test01.tmx")


def test_build_rects(tiled_map):
    try:
        from pytmx import util_pygame

        rects = util_pygame.build_rects(tiled_map, "Grass and Water", "tileset", None)
        assert rects[0] == [0, 0, 240, 240]

        rects = util_pygame.build_rects(tiled_map, "Grass and Water", "tileset", 18)
        assert len(rects) != 0
    except ImportError:
        pytest.skip("pygame not installed")


def test_get_tile_image(tiled_map):
    tiled_map.get_tile_image(0, 0, 0)


def test_get_tile_image_by_gid(tiled_map):
    assert tiled_map.get_tile_image_by_gid(0) is None
    assert tiled_map.get_tile_image_by_gid(1) is not None


def test_reserved_names_check_disabled_with_option():
    tm = TiledMap(allow_duplicate_names=True)
    items = [("name", "conflict")]
    assert tm._contains_invalid_property_name(items) is False


def test_map_width_height_is_int(tiled_map):
    assert isinstance(tiled_map.width, int)
    assert isinstance(tiled_map.height, int)


def test_layer_width_height_is_int(tiled_map):
    layer = tiled_map.layers[0]
    assert isinstance(layer.width, int)
    assert isinstance(layer.height, int)


def test_properties_are_converted_to_builtin_types(tiled_map):
    props = tiled_map.properties
    assert isinstance(props["test_bool"], bool)
    assert isinstance(props["test_color"], str)
    assert isinstance(props["test_file"], str)
    assert isinstance(props["test_float"], float)
    assert isinstance(props["test_int"], int)
    assert isinstance(props["test_string"], str)


def test_properties_are_converted_to_correct_values(tiled_map):
    assert tiled_map.properties["test_bool"] is False
    assert tiled_map.properties["test_bool_true"] is True


def test_pixels_to_tile_pos(tiled_map):
    assert tiled_map.pixels_to_tile_pos((0, 33)) == (0, 2)
    assert tiled_map.pixels_to_tile_pos((33, 0)) == (2, 0)
    assert tiled_map.pixels_to_tile_pos((0, 0)) == (0, 0)
    assert tiled_map.pixels_to_tile_pos((65, 86)) == (4, 5)
