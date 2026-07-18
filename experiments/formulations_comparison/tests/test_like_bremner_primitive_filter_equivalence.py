from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner_box import search_like_bremner_box  # noqa: E402
from prototypes.model import generate_square_progressions_parametric  # noqa: E402


class EarlyPrimitiveFilterEquivalenceTests(unittest.TestCase):
    def test_filter_matches_unfiltered_oracle_on_complete_boxes(self) -> None:
        for complete_box_root in (601, 1202, 2000):
            with self.subTest(complete_box_root=complete_box_root):
                catalog = generate_square_progressions_parametric(complete_box_root)
                optimized = search_like_bremner_box(
                    complete_box_root,
                    primitive_only=True,
                    progressions=catalog,
                    early_primitive_filter=True,
                )
                oracle = search_like_bremner_box(
                    complete_box_root,
                    primitive_only=True,
                    progressions=catalog,
                    early_primitive_filter=False,
                )
                self.assertEqual(optimized.classes, oracle.classes)
                self.assertEqual(
                    optimized.stats["accepted_classes"],
                    oracle.stats["accepted_classes"],
                )
                self.assertLessEqual(
                    optimized.stats["square_membership_tests"],
                    oracle.stats["square_membership_tests"],
                )


if __name__ == "__main__":
    unittest.main()
