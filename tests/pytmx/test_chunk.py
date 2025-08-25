import base64
import struct
import unittest
import xml.etree.ElementTree as ET
import zlib
from unittest.mock import MagicMock

from pytmx.chunk import Chunk, extract_chunks, stitch_chunks


class TestExtractChunks(unittest.TestCase):
    def setUp(self):
        self.gids = [1, 2, 3, 4]
        self.width = 2
        self.height = 2
        self.encoding = "base64"
        self.compression = "zlib"

        packed = struct.pack("<4I", *self.gids)
        compressed = zlib.compress(packed)
        encoded = base64.b64encode(compressed).decode("ascii")

        self.chunk_xml = ET.Element(
            "chunk",
            {"x": "0", "y": "0", "width": str(self.width), "height": str(self.height)},
        )
        self.chunk_xml.text = encoded

    def test_valid_chunk_extraction(self):
        chunks = extract_chunks(
            [self.chunk_xml], encoding=self.encoding, compression=self.compression
        )
        self.assertEqual(len(chunks), 1)

        chunk = chunks[0]
        self.assertEqual(chunk.position, (0, 0))
        self.assertEqual(chunk.size, (2, 2))
        self.assertEqual(chunk.grid, [[1, 2], [3, 4]])
        self.assertEqual(
            chunk.raw, zlib.decompress(base64.b64decode(self.chunk_xml.text))
        )

    def test_byte_mismatch_warning(self):
        gids = [1, 2]  # Only 2 GIDs, but chunk expects 2x2 = 4
        packed = struct.pack("<2I", *gids)
        compressed = zlib.compress(packed)
        corrupted = base64.b64encode(compressed).decode("ascii")
        corrupted_chunk = ET.Element(
            "chunk",
            {"x": "0", "y": "0", "width": str(self.width), "height": str(self.height)},
        )
        corrupted_chunk.text = corrupted

        with self.assertLogs("pytmx.chunk", level="WARNING") as cm:
            extract_chunks([corrupted_chunk], encoding="base64", compression="zlib")

        self.assertTrue(any("GID count mismatch" in msg for msg in cm.output))

    def test_multiple_chunks(self):
        chunk2 = ET.Element(
            "chunk",
            {"x": "2", "y": "0", "width": str(self.width), "height": str(self.height)},
        )
        chunk2.text = self.chunk_xml.text

        chunks = extract_chunks(
            [self.chunk_xml, chunk2],
            encoding=self.encoding,
            compression=self.compression,
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[1].position, (2, 0))
        self.assertEqual(chunks[1].grid, [[1, 2], [3, 4]])

    def test_invalid_attributes(self):
        bad_chunk = ET.Element(
            "chunk", {"x": "not-an-int", "y": "0", "width": "2", "height": "2"}
        )
        bad_chunk.text = self.chunk_xml.text

        with self.assertRaises(ValueError):
            extract_chunks(
                [bad_chunk], encoding=self.encoding, compression=self.compression
            )

    def test_malformed_base64(self):
        malformed_chunk = ET.Element(
            "chunk", {"x": "0", "y": "0", "width": "2", "height": "2"}
        )
        malformed_chunk.text = "!!!notbase64!!!"

        with self.assertLogs("pytmx.chunk", level="ERROR") as cm:
            extract_chunks([malformed_chunk], encoding="base64", compression="zlib")

        self.assertTrue(any("Failed to decode GIDs" in msg for msg in cm.output))


class TestStitchChunks(unittest.TestCase):
    def setUp(self):
        self.mock_map = MagicMock()
        self.mock_map.register_gid_check_flags.side_effect = (
            lambda gid: gid & 0x1FFFFFFF
        )  # Strip flip flags

        self.chunk1 = Chunk(
            position=(0, 0),
            size=(2, 2),
            grid=[[1, 2], [3, 4 | 0x80000000]],  # flipped tile
            raw=b"",  # not used in stitching
        )

        self.chunk2 = Chunk(
            position=(2, 0),
            size=(2, 2),
            grid=[[5, 6], [7 | 0x40000000, 8]],  # flipped tile
            raw=b"",
        )

        self.chunks = [self.chunk1, self.chunk2]
        self.width = 4
        self.height = 2

    def test_stitch_chunks_correct_grid(self):
        expected_grid = [[1, 2, 5, 6], [3, 4, 7, 8]]

        result = stitch_chunks(self.chunks, self.width, self.height, self.mock_map)
        self.assertEqual(result, expected_grid)

    def test_gid_normalization_called(self):
        stitch_chunks(self.chunks, self.width, self.height, self.mock_map)

        # Flatten all GIDs from both chunks
        raw_gids = [gid for chunk in self.chunks for row in chunk.grid for gid in row]
        normalized_calls = [((gid,),) for gid in raw_gids]

        # Check that register_gid_check_flags was called with each raw GID
        self.mock_map.register_gid_check_flags.assert_has_calls(
            normalized_calls, any_order=True
        )

    def test_out_of_bounds_tile_skipped(self):
        # Add a chunk that goes out of bounds
        out_of_bounds_chunk = Chunk(
            position=(3, 1), size=(2, 2), grid=[[9, 10], [11, 12]], raw=b""
        )
        chunks = self.chunks + [out_of_bounds_chunk]

        result = stitch_chunks(chunks, self.width, self.height, self.mock_map)

        # Ensure out-of-bounds tiles are not written
        self.assertEqual(result[1][3], 9)  # overwritten by out-of-bounds chunk
        # No IndexError should occur

    def test_empty_chunks(self):
        result = stitch_chunks([], self.width, self.height, self.mock_map)
        expected = [[0, 0, 0, 0], [0, 0, 0, 0]]
        self.assertEqual(result, expected)

    def test_overlapping_chunks_last_write_wins(self):
        overlapping_chunk = Chunk(
            position=(1, 0), size=(2, 2), grid=[[100, 101], [102, 103]], raw=b""
        )
        chunks = [self.chunk1, overlapping_chunk]

        result = stitch_chunks(chunks, self.width, self.height, self.mock_map)

        # Expect overlapping_chunk to overwrite chunk1 at (1,0) and (2,0)
        self.assertEqual(result[0][1], 100)
        self.assertEqual(result[0][2], 101)

    def test_negative_position_chunk(self):
        negative_chunk = Chunk(
            position=(-1, -1), size=(2, 2), grid=[[200, 201], [202, 203]], raw=b""
        )
        chunks = [negative_chunk]

        result = stitch_chunks(chunks, self.width, self.height, self.mock_map)

        # Nothing should be written to the grid
        expected = [[0, 0, 0, 0], [0, 0, 0, 0]]
        self.assertEqual(result, expected)

    def test_partially_out_of_bounds_chunk(self):
        partial_chunk = Chunk(
            position=(3, 1), size=(2, 2), grid=[[300, 301], [302, 303]], raw=b""
        )
        chunks = [partial_chunk]

        result = stitch_chunks(chunks, self.width, self.height, self.mock_map)

        # Only (3,1) should be written
        self.assertEqual(result[1][3], 300)

    def test_gid_normalization_logic(self):
        raw_gid = 0x80000001
        normalized = self.mock_map.register_gid_check_flags(raw_gid)
        self.assertEqual(normalized, 1)

    def test_irregular_chunk_grid(self):
        irregular_chunk = Chunk(
            position=(0, 0), size=(2, 2), grid=[[1], [2, 3]], raw=b""  # too short
        )
        chunks = [irregular_chunk]

        with self.assertRaises(IndexError):
            stitch_chunks(chunks, self.width, self.height, self.mock_map)
