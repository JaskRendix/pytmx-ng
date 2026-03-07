import base64
import gzip
import struct
import zlib

import pytest

from pytmx.constants import TileFlags
from pytmx.map import TiledMap
from pytmx.utils import decode_gid, unpack_gids

# Tiled gid flags
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT


# -------------------------
# decode_gid tests
# -------------------------


@pytest.mark.parametrize(
    "raw_gid, expected_gid, expected_flags",
    [
        (100, 100, TileFlags(False, False, False)),
    ],
)
def test_decode_gid_no_flags(raw_gid, expected_gid, expected_flags):
    assert decode_gid(raw_gid) == (expected_gid, expected_flags)


@pytest.mark.parametrize(
    "raw_gid, expected_gid, expected_flags",
    [
        (GID_TRANS_FLIPX + 1, 1, TileFlags(True, False, False)),
        (GID_TRANS_FLIPY + 1, 1, TileFlags(False, True, False)),
        (GID_TRANS_ROT + 1, 1, TileFlags(False, False, True)),
    ],
)
def test_decode_gid_individual_flags(raw_gid, expected_gid, expected_flags):
    assert decode_gid(raw_gid) == (expected_gid, expected_flags)


@pytest.mark.parametrize(
    "raw_gid, expected_gid, expected_flags",
    [
        (GID_TRANS_FLIPX + GID_TRANS_FLIPY + 1, 1, TileFlags(True, True, False)),
        (GID_TRANS_FLIPX + GID_TRANS_ROT + 1, 1, TileFlags(True, False, True)),
        (GID_TRANS_FLIPY + GID_TRANS_ROT + 1, 1, TileFlags(False, True, True)),
        (
            GID_TRANS_FLIPX + GID_TRANS_FLIPY + GID_TRANS_ROT + 1,
            1,
            TileFlags(True, True, True),
        ),
    ],
)
def test_decode_gid_flag_combinations(raw_gid, expected_gid, expected_flags):
    assert decode_gid(raw_gid) == (expected_gid, expected_flags)


def test_decode_gid_edge_cases():
    max_gid = 2**29 - 1
    assert decode_gid(max_gid) == (max_gid & ~GID_MASK, TileFlags(False, False, False))

    assert decode_gid(0) == (0, TileFlags(False, False, False))

    gid_all = GID_TRANS_FLIPX + GID_TRANS_FLIPY + GID_TRANS_ROT + 1
    assert decode_gid(gid_all) == (1, TileFlags(True, True, True))


def test_flag_cache_identity():
    raw_gid = GID_TRANS_FLIPX + GID_TRANS_ROT + 1
    _, f1 = decode_gid(raw_gid)
    _, f2 = decode_gid(raw_gid)
    assert f1 is f2


def test_flag_cache_separation():
    _, f1 = decode_gid(GID_TRANS_FLIPX + 1)
    _, f2 = decode_gid(GID_TRANS_FLIPY + 1)
    assert f1 != f2


# -------------------------
# register_gid tests
# -------------------------


@pytest.fixture
def tmx():
    return TiledMap()


def test_register_gid_valid(tmx):
    assert tmx.register_gid(123) is not None


def test_register_gid_with_flags(tmx):
    assert tmx.register_gid(456, TileFlags(1, 0, 1)) is not None


def test_register_gid_zero(tmx):
    assert tmx.register_gid(0) == 0


def test_register_gid_max_gid(tmx):
    max_gid = tmx.maxgid
    tmx.register_gid(max_gid)
    assert tmx.maxgid == max_gid + 1


def test_register_gid_duplicate(tmx):
    gid1 = tmx.register_gid(123)
    gid2 = tmx.register_gid(123)
    assert gid1 == gid2


def test_register_gid_duplicate_different_flags(tmx):
    gid1 = tmx.register_gid(123, TileFlags(1, 0, 0))
    gid2 = tmx.register_gid(123, TileFlags(0, 1, 0))
    assert gid1 != gid2


def test_register_gid_flag_equivalence(tmx):
    gid1 = tmx.register_gid(42, TileFlags(True, False, False))
    gid2 = tmx.register_gid(42, TileFlags(1, 0, 0))
    assert gid1 == gid2


def test_gid_mapping_growth(tmx):
    initial = tmx.maxgid
    for i in range(5):
        tmx.register_gid(100 + i)
    assert tmx.maxgid == initial + 5


# -------------------------
# unpack_gids tests
# -------------------------


def test_base64_no_compression():
    gids = [123, 456, 789]
    data = struct.pack("<LLL", *gids)
    text = base64.b64encode(data).decode()
    assert unpack_gids(text, encoding="base64") == gids


@pytest.mark.parametrize("compression", ["gzip", "zlib"])
def test_base64_with_compression(compression):
    gids = [123, 456, 789]
    data = struct.pack("<LLL", *gids)

    compressed = gzip.compress(data) if compression == "gzip" else zlib.compress(data)

    text = base64.b64encode(compressed).decode()
    assert unpack_gids(text, encoding="base64", compression=compression) == gids


def test_base64_unsupported_compression():
    with pytest.raises(ValueError):
        unpack_gids("abc", encoding="base64", compression="nope")


def test_csv():
    gids = [123, 456, 789]
    assert unpack_gids(",".join(map(str, gids)), encoding="csv") == gids


def test_unsupported_encoding():
    with pytest.raises(ValueError):
        unpack_gids("data", encoding="nope")


def test_base64_invalid_data():
    with pytest.raises((ValueError, base64.binascii.Error)):
        unpack_gids("!!not_base64!!", encoding="base64")


def test_unpack_empty_input():
    assert unpack_gids("", encoding="csv") == []


def test_base64_corrupted_data():
    with pytest.raises((ValueError, base64.binascii.Error)):
        unpack_gids("not_base64!!%%", encoding="base64")


def test_csv_malformed_data():
    with pytest.raises(ValueError):
        unpack_gids("12,,hello,34", encoding="csv")


def test_base64_truncated_gzip():
    gids = [1, 2, 3, 4]
    data = struct.pack("<LLLL", *gids)
    corrupted = gzip.compress(data)[:10]
    text = base64.b64encode(corrupted).decode()

    with pytest.raises(Exception):
        unpack_gids(text, encoding="base64", compression="gzip")


def test_base64_empty_gzip():
    compressed = gzip.compress(b"")
    text = base64.b64encode(compressed).decode()
    assert unpack_gids(text, encoding="base64", compression="gzip") == []


def test_base64_wrong_size():
    data = b"\x01\x02\x03"
    text = base64.b64encode(data).decode()

    with pytest.raises(struct.error):
        unpack_gids(text, encoding="base64")


def test_roundtrip_gid_flags():
    raw = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT | 42
    gid, flags = decode_gid(raw)

    reconstructed = gid | (
        (GID_TRANS_FLIPX if flags.flipped_horizontally else 0)
        | (GID_TRANS_FLIPY if flags.flipped_vertically else 0)
        | (GID_TRANS_ROT if flags.flipped_diagonally else 0)
    )

    assert reconstructed == raw
