from unittest.mock import MagicMock, patch
from xml.etree.ElementTree import Element, SubElement

import pytest

from pytmx.constants import AnimationFrame
from pytmx.tileset import TiledTileset


@pytest.fixture
def mock_parent():
    parent = MagicMock()
    parent.filename = "/maps/test_map.tmx"
    parent.register_gid = lambda gid: gid + 1000
    parent.map_gid2 = lambda gid: [(gid, 0)]
    parent.set_tile_properties = MagicMock()
    return parent


def create_basic_tileset_node():
    node = Element(
        "tileset",
        {
            "name": "TestTileset",
            "tilewidth": "32",
            "tileheight": "32",
            "tilecount": "4",
            "columns": "2",
        },
    )
    SubElement(node, "image", {"source": "tiles.png", "width": "64", "height": "64"})
    return node


def test_basic_tileset_parsing(mock_parent):
    node = create_basic_tileset_node()
    tileset = TiledTileset(mock_parent, node)

    assert tileset.name == "TestTileset"
    assert tileset.tilewidth == 32
    assert tileset.tileheight == 32
    assert tileset.tilecount == 4
    assert tileset.columns == 2
    assert tileset.source == "tiles.png"
    assert tileset.width == 64
    assert tileset.height == 64


def test_external_tileset_loading(mock_parent):
    tsx_node = create_basic_tileset_node()

    with (
        patch("os.path.exists", return_value=True),
        patch("xml.etree.ElementTree.parse") as mock_parse,
    ):
        mock_parse.return_value.getroot.return_value = tsx_node

        external_node = Element(
            "tileset", {"firstgid": "1", "source": "test_tileset.tsx"}
        )
        tileset = TiledTileset(mock_parent, external_node)

        assert tileset.firstgid == 1
        assert tileset.name == "TestTileset"


def test_missing_external_file_raises(mock_parent):
    external_node = Element("tileset", {"firstgid": "1", "source": "missing.tsx"})

    with patch("os.path.exists", return_value=False):
        with pytest.raises(Exception) as exc:
            TiledTileset(mock_parent, external_node)
        assert "Cannot find tileset file" in str(exc.value)


def test_tile_with_animation(mock_parent):
    node = create_basic_tileset_node()
    tile = SubElement(node, "tile", {"id": "0"})
    anim = SubElement(tile, "animation")
    SubElement(anim, "frame", {"tileid": "1", "duration": "100"})
    SubElement(anim, "frame", {"tileid": "2", "duration": "200"})

    TiledTileset(mock_parent, node)
    props = mock_parent.set_tile_properties.call_args[0][1]

    assert "frames" in props
    assert len(props["frames"]) == 2
    assert isinstance(props["frames"][0], AnimationFrame)


def test_tile_with_image_and_transparency(mock_parent):
    node = create_basic_tileset_node()
    tile = SubElement(node, "tile", {"id": "0"})
    SubElement(
        tile,
        "image",
        {"source": "tile0.png", "trans": "ff00ff", "width": "32", "height": "32"},
    )

    TiledTileset(mock_parent, node)
    props = mock_parent.set_tile_properties.call_args[0][1]

    assert props["source"] == "tile0.png"
    assert props["trans"] == "ff00ff"
    assert props["width"] == 32
    assert props["height"] == 32


def test_tileoffset_parsing(mock_parent):
    node = create_basic_tileset_node()
    SubElement(node, "tileoffset", {"x": "5", "y": "10"})

    tileset = TiledTileset(mock_parent, node)
    assert tileset.offset == (5, 10)


def test_tile_without_image_defaults(mock_parent):
    node = create_basic_tileset_node()
    SubElement(node, "tile", {"id": "0"})

    TiledTileset(mock_parent, node)
    props = mock_parent.set_tile_properties.call_args[0][1]

    assert props["width"] == 32
    assert props["height"] == 32


def test_empty_tileset_node(mock_parent):
    node = Element("tileset")
    tileset = TiledTileset(mock_parent, node)
    assert tileset.name is None
    assert tileset.tilewidth == 0


def test_invalid_tilewidth_type(mock_parent):
    node = Element("tileset", {"tilewidth": "not_an_int"})
    with pytest.raises(ValueError):
        TiledTileset(mock_parent, node)


def test_multiple_tileoffset_nodes(mock_parent):
    node = create_basic_tileset_node()
    SubElement(node, "tileoffset", {"x": "1", "y": "2"})
    SubElement(node, "tileoffset", {"x": "99", "y": "99"})

    tileset = TiledTileset(mock_parent, node)
    assert tileset.offset == (1, 2)


def test_tile_missing_id(mock_parent):
    node = create_basic_tileset_node()
    SubElement(node, "tile")

    with pytest.raises(TypeError):
        TiledTileset(mock_parent, node)


def test_tileset_with_unknown_tags(mock_parent):
    node = create_basic_tileset_node()
    SubElement(node, "unknownTag", {"foo": "bar"})

    tileset = TiledTileset(mock_parent, node)
    assert tileset.name == "TestTileset"


def test_tileset_without_image(mock_parent):
    node = Element(
        "tileset", {"name": "NoImageTileset", "tilewidth": "32", "tileheight": "32"}
    )

    tileset = TiledTileset(mock_parent, node)
    assert tileset.source is None
    assert tileset.width == 0


def test_tile_with_objectgroup(mock_parent):
    node = create_basic_tileset_node()
    tile = SubElement(node, "tile", {"id": "0"})
    objgrp = SubElement(tile, "objectgroup")
    SubElement(objgrp, "object", {"id": "1", "x": "10", "y": "20"})

    TiledTileset(mock_parent, node)
    props = mock_parent.set_tile_properties.call_args[0][1]
    assert "colliders" in props
