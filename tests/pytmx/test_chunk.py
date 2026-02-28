import base64
import struct
import xml.etree.ElementTree as ET
import zlib

import pytest

from pytmx.chunk import Chunk, extract_chunks, stitch_chunks


@pytest.fixture
def encoded_chunk():
    gids = [1, 2, 3, 4]
    packed = struct.pack("<4I", *gids)
    compressed = zlib.compress(packed)
    encoded = base64.b64encode(compressed).decode("ascii")

    xml = ET.Element("chunk", {"x": "0", "y": "0", "width": "2", "height": "2"})
    xml.text = encoded
    return xml


# ---------------------------------------------------------------------------
# extract_chunks tests
# ---------------------------------------------------------------------------


def test_valid_chunk_extraction(encoded_chunk):
    chunks = extract_chunks([encoded_chunk], encoding="base64", compression="zlib")
    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.position == (0, 0)
    assert chunk.size == (2, 2)
    assert chunk.grid == [[1, 2], [3, 4]]
    assert chunk.raw == zlib.decompress(base64.b64decode(encoded_chunk.text))


def test_byte_mismatch_warning(caplog):
    gids = [1, 2]  # too few
    packed = struct.pack("<2I", *gids)
    compressed = zlib.compress(packed)
    corrupted = base64.b64encode(compressed).decode("ascii")

    xml = ET.Element("chunk", {"x": "0", "y": "0", "width": "2", "height": "2"})
    xml.text = corrupted

    with caplog.at_level("WARNING", logger="pytmx.chunk"):
        extract_chunks([xml], encoding="base64", compression="zlib")

    assert any("GID count mismatch" in msg for msg in caplog.messages)


def test_multiple_chunks(encoded_chunk):
    chunk2 = ET.Element("chunk", {"x": "2", "y": "0", "width": "2", "height": "2"})
    chunk2.text = encoded_chunk.text

    chunks = extract_chunks(
        [encoded_chunk, chunk2], encoding="base64", compression="zlib"
    )

    assert len(chunks) == 2
    assert chunks[1].position == (2, 0)
    assert chunks[1].grid == [[1, 2], [3, 4]]


def test_invalid_attributes(encoded_chunk):
    bad = ET.Element(
        "chunk", {"x": "not-an-int", "y": "0", "width": "2", "height": "2"}
    )
    bad.text = encoded_chunk.text

    with pytest.raises(ValueError):
        extract_chunks([bad], encoding="base64", compression="zlib")


def test_malformed_base64(caplog):
    malformed = ET.Element("chunk", {"x": "0", "y": "0", "width": "2", "height": "2"})
    malformed.text = "!!!notbase64!!!"

    with caplog.at_level("ERROR", logger="pytmx.chunk"):
        extract_chunks([malformed], encoding="base64", compression="zlib")

    assert any("Failed to decode GIDs" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# stitch_chunks tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_map(mocker):
    m = mocker.MagicMock()
    m.register_gid_check_flags.side_effect = lambda gid: gid & 0x1FFFFFFF
    return m


@pytest.fixture
def chunks():
    c1 = Chunk(
        position=(0, 0),
        size=(2, 2),
        grid=[[1, 2], [3, 4 | 0x80000000]],
        raw=b"",
    )
    c2 = Chunk(
        position=(2, 0),
        size=(2, 2),
        grid=[[5, 6], [7 | 0x40000000, 8]],
        raw=b"",
    )
    return [c1, c2]


def test_stitch_chunks_correct_grid(chunks, mock_map):
    result = stitch_chunks(chunks, 4, 2, mock_map)
    assert result == [[1, 2, 5, 6], [3, 4, 7, 8]]


def test_gid_normalization_called(chunks, mock_map):
    stitch_chunks(chunks, 4, 2, mock_map)

    raw_gids = [gid for chunk in chunks for row in chunk.grid for gid in row]
    expected_calls = [((gid,),) for gid in raw_gids]

    mock_map.register_gid_check_flags.assert_has_calls(expected_calls, any_order=True)


def test_out_of_bounds_tile_skipped(chunks, mock_map):
    oob = Chunk(position=(3, 1), size=(2, 2), grid=[[9, 10], [11, 12]], raw=b"")
    result = stitch_chunks(chunks + [oob], 4, 2, mock_map)

    assert result[1][3] == 9  # only the valid tile is written


def test_empty_chunks(mock_map):
    result = stitch_chunks([], 4, 2, mock_map)
    assert result == [[0, 0, 0, 0], [0, 0, 0, 0]]


def test_overlapping_chunks_last_write_wins(mock_map):
    c1 = Chunk(position=(0, 0), size=(2, 2), grid=[[1, 2], [3, 4]], raw=b"")
    overlap = Chunk(
        position=(1, 0), size=(2, 2), grid=[[100, 101], [102, 103]], raw=b""
    )

    result = stitch_chunks([c1, overlap], 4, 2, mock_map)

    assert result[0][1] == 100
    assert result[0][2] == 101


def test_negative_position_chunk(mock_map):
    neg = Chunk(position=(-1, -1), size=(2, 2), grid=[[200, 201], [202, 203]], raw=b"")
    result = stitch_chunks([neg], 4, 2, mock_map)

    assert result == [[0, 0, 0, 0], [0, 0, 0, 0]]


def test_partially_out_of_bounds_chunk(mock_map):
    partial = Chunk(
        position=(3, 1), size=(2, 2), grid=[[300, 301], [302, 303]], raw=b""
    )
    result = stitch_chunks([partial], 4, 2, mock_map)

    assert result[1][3] == 300


def test_gid_normalization_logic(mock_map):
    raw = 0x80000001
    assert mock_map.register_gid_check_flags(raw) == 1


def test_irregular_chunk_grid(mock_map):
    irregular = Chunk(position=(0, 0), size=(2, 2), grid=[[1], [2, 3]], raw=b"")

    with pytest.raises(IndexError):
        stitch_chunks([irregular], 4, 2, mock_map)
