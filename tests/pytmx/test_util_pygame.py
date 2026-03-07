from unittest.mock import MagicMock, Mock, patch

import pygame
import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from pytmx.constants import TileFlags
from pytmx.layer import TiledTileLayer
from pytmx.map import TiledMap
from pytmx.tileset import TiledTileset
from pytmx.util_pygame import (
    build_rects,
    handle_transformation,
    pygame_image_loader,
    simplify,
    smart_convert,
)

# ---------------------------------------------------------------------------
# Global pygame setup/teardown
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def screen():
    return pygame.display.set_mode((1, 1))


# ---------------------------------------------------------------------------
# handle_transformation
# ---------------------------------------------------------------------------


def test_handle_transformation_no_flags(screen):
    tile = Surface((32, 32))
    flags = MagicMock(
        flipped_diagonally=False, flipped_horizontally=False, flipped_vertically=False
    )
    assert handle_transformation(tile, flags).get_size() == tile.get_size()


@pytest.mark.parametrize(
    "flags",
    [
        TileFlags(False, False, True),
        TileFlags(False, True, False),
        TileFlags(True, False, False),
    ],
)
def test_handle_transformation_any_flip(screen, flags):
    tile = Surface((32, 32))
    assert handle_transformation(tile, flags).get_size() == tile.get_size()


def test_handle_transformation_flipped_diagonally_non_square(screen):
    tile = Surface((32, 64))
    flags = TileFlags(True, False, False)
    with pytest.raises(ValueError):
        handle_transformation(tile, flags)


def test_handle_transformation_flipped_diagonally_square(screen):
    tile = Surface((64, 64))
    flags = TileFlags(True, False, False)
    assert handle_transformation(tile, flags).get_size() == (64, 64)


# ---------------------------------------------------------------------------
# smart_convert
# ---------------------------------------------------------------------------


@pytest.fixture
def base_surface():
    surf = Surface((32, 32))
    surf.fill((255, 0, 0))
    return surf


@pytest.fixture
def alpha_surface():
    surf = Surface((32, 32), pygame.SRCALPHA)
    surf.fill((255, 0, 0, 128))
    return surf


@pytest.fixture
def edge_transparency_surface():
    surf = Surface((32, 32), pygame.SRCALPHA)
    surf.fill((255, 255, 255, 255))
    for x in range(32):
        surf.set_at((x, 0), (0, 0, 0, 0))
    return surf


def _rgb(ck):
    return ck[:3] if ck is not None else None


def test_smart_convert_colorkey(base_surface):
    red = (255, 0, 0)
    result = smart_convert(base_surface, red, False)
    assert _rgb(result.get_colorkey()) == red


def test_smart_convert_rleaccel():
    surf = Surface((32, 32))
    surf.fill((255, 0, 0))
    result = smart_convert(surf, (255, 0, 0), False)
    assert _rgb(result.get_colorkey()) == (255, 0, 0)


def test_smart_convert_sparse_colorkey():
    surf = Surface((32, 32))
    surf.fill((0, 0, 255))
    surf.set_at((0, 0), (255, 0, 0))
    result = smart_convert(surf, (255, 0, 0), False)
    assert _rgb(result.get_colorkey()) == (255, 0, 0)


def test_smart_convert_colorkey_and_pixelalpha(base_surface):
    red = (255, 0, 0)
    result = smart_convert(base_surface, red, True)
    assert _rgb(result.get_colorkey()) == red


def test_smart_convert_no_colorkey(base_surface):
    result = smart_convert(base_surface, None, False)
    assert not (result.get_flags() & pygame.SRCALPHA)


def test_smart_convert_pixelalpha(alpha_surface):
    result = smart_convert(alpha_surface, None, True)
    assert result.get_flags() & pygame.SRCALPHA


def test_smart_convert_edge_transparency(edge_transparency_surface):
    result = smart_convert(edge_transparency_surface, None, True)
    assert result.get_flags() & pygame.SRCALPHA


@patch("pygame.mask.from_surface")
def test_smart_convert_mask_failure(mock_mask, base_surface):
    mock_mask.side_effect = pygame.error("fail")
    result = smart_convert(base_surface, None, False)
    assert result.get_flags() & pygame.SRCALPHA


def test_smart_convert_zero_sized():
    surf = Surface((0, 0))
    result = smart_convert(surf, None, False)
    assert result.get_size() == (0, 0)


def test_smart_convert_preserve_alpha_flag():
    surf = Surface((32, 32), pygame.SRCALPHA)
    surf.fill((255, 255, 255, 255))
    result = smart_convert(surf, None, False, preserve_alpha_flag=True)
    assert result.get_flags() & pygame.SRCALPHA


# ---------------------------------------------------------------------------
# pygame_image_loader
# ---------------------------------------------------------------------------


@patch("pygame.image.load")
def test_pygame_image_loader_basic(mock_load):
    mock_load.return_value = Surface((32, 32))
    loader = pygame_image_loader("test.png", None)
    assert isinstance(loader(), Surface)


@patch("pygame.image.load")
def test_pygame_image_loader_rect(mock_load):
    mock_load.return_value = Surface((32, 32))
    loader = pygame_image_loader("test.png", None)
    assert isinstance(loader(rect=Rect(0, 0, 16, 16)), Surface)


@patch("pygame.image.load")
def test_pygame_image_loader_flags(mock_load):
    mock_load.return_value = Surface((32, 32))
    flags = TileFlags(True, True, True)
    loader = pygame_image_loader("test.png", None)
    assert isinstance(loader(flags=flags), Surface)


def test_pygame_image_loader_invalid_colorkey():
    with pytest.raises(ValueError):
        pygame_image_loader("fake.png", {"bad": "value"})


@patch("pygame.image.load")
def test_pygame_image_loader_hex_colorkey(mock_load):
    mock_load.return_value = Surface((32, 32))
    loader = pygame_image_loader("fake.png", "ff00ff")
    assert callable(loader)


@patch("pygame.image.load")
def test_pygame_image_loader_out_of_bounds(mock_load):
    mock_load.return_value = Surface((32, 32))
    loader = pygame_image_loader("fake.png", None)
    with pytest.raises(ValueError):
        loader(Rect(100, 100, 10, 10))


# ---------------------------------------------------------------------------
# simplify
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "points, tilew, tileh, expected",
    [
        ([], 1, 1, []),
        ([(1, 1)], 1, 1, [Rect(1, 1, 1, 1)]),
        ([(1, 1), (2, 1), (1, 2), (2, 2)], 1, 1, [Rect(1, 1, 2, 2)]),
        (
            [(1, 1), (3, 3), (5, 5)],
            1,
            1,
            [Rect(1, 1, 1, 1), Rect(3, 3, 1, 1), Rect(5, 5, 1, 1)],
        ),
    ],
)
def test_simplify_basic(points, tilew, tileh, expected):
    assert simplify(points, tilew, tileh) == expected


def test_simplify_large_block():
    pts = [(x, y) for x in range(10) for y in range(10)]
    assert simplify(pts, 1, 1) == [Rect(0, 0, 10, 10)]


# ---------------------------------------------------------------------------
# build_rects
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_tmxmap():
    m = Mock(spec=TiledMap)
    m.width = 10
    m.height = 10
    m.tilewidth = 32
    m.tileheight = 32

    ts1 = Mock(spec=TiledTileset)
    ts2 = Mock(spec=TiledTileset)
    ts1.name = "tileset1"
    ts2.name = "tileset2"
    m.tilesets = [ts1, ts2]

    layer1 = Mock(spec=TiledTileLayer)
    layer2 = Mock(spec=TiledTileLayer)
    layer1.name = "layer1"
    layer2.name = "layer2"
    layer1.data = [[1] * 10 for _ in range(10)]
    layer2.data = [[1] * 10 for _ in range(10)]
    m.layers = [layer1, layer2]

    m.get_layer_data = Mock(return_value=[[1] * 10 for _ in range(10)])
    m.map_gid = Mock(return_value=[(1, 0)])
    return m


def test_build_rects_int_layer_int_tileset(mock_tmxmap):
    result = build_rects(mock_tmxmap, 0, 0, 1)
    assert isinstance(result[0], Rect)


def test_build_rects_str_layer_str_tileset(mock_tmxmap):
    result = build_rects(mock_tmxmap, "layer1", "tileset1", 1)
    assert isinstance(result[0], Rect)


def test_build_rects_invalid_layer(mock_tmxmap):
    with pytest.raises(ValueError):
        build_rects(mock_tmxmap, "bad", 0, 1)


def test_build_rects_invalid_tileset(mock_tmxmap):
    with pytest.raises(IndexError):
        build_rects(mock_tmxmap, 0, 2, 1)


def test_build_rects_invalid_tileset_type(mock_tmxmap):
    with pytest.raises(ValueError):
        build_rects(mock_tmxmap, 0, "bad", 1)


def test_build_rects_invalid_gid(mock_tmxmap):
    mock_tmxmap.map_gid = Mock(return_value=[])
    assert isinstance(build_rects(mock_tmxmap, 0, 0, 1), list)


def test_build_rects_no_gid(mock_tmxmap):
    result = build_rects(mock_tmxmap, 0, 0, None)
    assert isinstance(result[0], Rect)


def test_build_rects_layer_no_name(mock_tmxmap):
    mock_tmxmap.layers[0].name = None
    with pytest.raises(ValueError):
        build_rects(mock_tmxmap, "layer1", 0, 1)


def test_build_rects_tileset_no_name(mock_tmxmap):
    mock_tmxmap.tilesets[0].name = None
    with pytest.raises(ValueError):
        build_rects(mock_tmxmap, "layer1", "tileset1", 1)


def test_build_rects_gid_not_in_layer(mock_tmxmap):
    mock_tmxmap.map_gid = Mock(return_value=[(999, 0)])
    assert build_rects(mock_tmxmap, "layer1", 0, 999) == []


def test_build_rects_sparse(mock_tmxmap):
    data = [[0] * 10 for _ in range(10)]
    data[1][1] = 1
    data[5][5] = 1
    mock_tmxmap.layers[0].data = data
    assert len(build_rects(mock_tmxmap, "layer1", 0, None)) >= 2


def test_build_rects_no_tileset(mock_tmxmap):
    assert isinstance(build_rects(mock_tmxmap, "layer1", None, None), list)
