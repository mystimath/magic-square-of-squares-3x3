from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed,
    search_like_bremner_indexed_groups,
)
from prototypes.model import generate_square_progressions_parametric  # noqa: E402
from prototypes.streaming_progressions import (  # noqa: E402
    ParametricProgressionGroupStream,
)


class StreamingProgressionTests(unittest.TestCase):
    def test_stream_matches_material_catalog_on_three_bounds(self) -> None:
        for max_square_root in (127, 601, 2000):
            with self.subTest(max_square_root=max_square_root):
                expected = generate_square_progressions_parametric(max_square_root)
                with tempfile.TemporaryDirectory() as temporary:
                    stream = ParametricProgressionGroupStream(
                        max_square_root,
                        shard_count=7,
                        temp_dir=pathlib.Path(temporary),
                    )
                    actual = tuple(
                        progression
                        for _, group in stream
                        for progression in group
                    )
                    self.assertEqual(actual, expected)
                    self.assertEqual(
                        stream.stats["unique_progressions"],
                        len(expected),
                    )
                    self.assertEqual(list(pathlib.Path(temporary).iterdir()), [])

    def test_stream_feeds_b3_without_class_change(self) -> None:
        max_square_root = 1202
        catalog = generate_square_progressions_parametric(max_square_root)
        expected = search_like_bremner_indexed(
            max_square_root,
            progressions=catalog,
        )
        with tempfile.TemporaryDirectory() as temporary:
            stream = ParametricProgressionGroupStream(
                max_square_root,
                shard_count=11,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_like_bremner_indexed_groups(
                max_square_root,
                stream,
            )
        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(actual.stats["progressions"], len(catalog))
        self.assertGreater(stream.stats["duplicate_records"], 0)


if __name__ == "__main__":
    unittest.main()
