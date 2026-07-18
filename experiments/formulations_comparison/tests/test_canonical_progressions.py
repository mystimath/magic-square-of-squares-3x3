from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    CanonicalParametricProgressionGroupStream,
    generate_square_progressions_parametric_canonical,
)
from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed,
    search_like_bremner_indexed_groups,
)
from prototypes.model import generate_square_progressions_parametric  # noqa: E402


class CanonicalProgressionTests(unittest.TestCase):
    def test_canonical_material_catalog_matches_historical_generator(self) -> None:
        for max_square_root in (127, 601, 2000, 100000):
            with self.subTest(max_square_root=max_square_root):
                self.assertEqual(
                    generate_square_progressions_parametric_canonical(
                        max_square_root
                    ),
                    generate_square_progressions_parametric(max_square_root),
                )

    def test_canonical_stream_has_no_raw_duplicates_and_feeds_b3(self) -> None:
        max_square_root = 2000
        catalog = generate_square_progressions_parametric_canonical(
            max_square_root
        )
        expected = search_like_bremner_indexed(
            max_square_root,
            progressions=catalog,
        )
        with tempfile.TemporaryDirectory() as temporary:
            stream = CanonicalParametricProgressionGroupStream(
                max_square_root,
                shard_count=11,
                temp_dir=pathlib.Path(temporary),
            )
            actual = search_like_bremner_indexed_groups(
                max_square_root,
                stream,
            )
        self.assertEqual(actual.classes, expected.classes)
        self.assertEqual(stream.stats["unique_progressions"], len(catalog))
        self.assertEqual(stream.stats["raw_records_written"], len(catalog))
        self.assertEqual(stream.stats["duplicate_records"], 0)


if __name__ == "__main__":
    unittest.main()
