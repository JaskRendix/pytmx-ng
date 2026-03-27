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


@pytest.fixture
def tiled_map_v2():
    return TiledMap("tests/resources/test02.tmx")


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


def test_nextlayerid_default_value(tiled_map):
    """Test nextlayerid defaults to 0 when not present in TMX file."""
    assert hasattr(tiled_map, 'nextlayerid')
    assert tiled_map.nextlayerid == 0


def test_nextlayerid_from_file(tiled_map_v2):
    """Test nextlayerid is correctly parsed from TMX file."""
    assert hasattr(tiled_map_v2, 'nextlayerid')
    assert tiled_map_v2.nextlayerid == 6


def test_nextobjectid_from_file(tiled_map):
    """Test nextobjectid is correctly parsed from TMX file."""
    assert hasattr(tiled_map, 'nextobjectid')
    assert tiled_map.nextobjectid == 9


def test_nextobjectid_from_file_v2(tiled_map_v2):
    """Test nextobjectid is correctly parsed from TMX file."""
    assert hasattr(tiled_map_v2, 'nextobjectid')
    assert tiled_map_v2.nextobjectid == 9


def test_list_properties_v2(tiled_map_v2):
    """Test list properties are correctly parsed from TMX file."""
    props = tiled_map_v2.properties
    assert 'test_list' in props
    test_list = props['test_list']
    
    assert isinstance(test_list, list)
    assert len(test_list) == 9
    
    # Test specific items from test02.tmx
    assert test_list[0] == "#ff00ff00"  # color
    assert test_list[1] == 3.14         # float
    assert test_list[2] == "TestFile.txt"  # file
    assert test_list[3] == 4            # int
    assert test_list[4] == 1            # object
    assert test_list[5] == "Test String"  # string
    assert test_list[6] == [False, True]  # nested list
    assert test_list[7] is False         # bool
    assert test_list[8] is True          # bool


def test_object_properties_v2(tiled_map_v2):
    """Test object properties are correctly parsed from TMX file."""
    props = tiled_map_v2.properties
    assert 'test_object' in props
    assert props['test_object'] == 6
