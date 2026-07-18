from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import canonical_d4  # noqa: E402
from prototypes.like_bremner import search_like_bremner  # noqa: E402
from prototypes.like_bremner_indexed import (  # noqa: E402
    group_progressions_by_first,
    search_like_bremner_indexed,
    search_like_bremner_indexed_box,
    search_like_bremner_indexed_groups,
)
from prototypes.model import (  # noqa: E402
    ArithmeticProgression,
    generate_square_progressions_parametric,
)

BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class IndexedLikeBremnerTests(unittest.TestCase):
    def test_indexed_branch_reproduces_complete_box_threshold(self) -> None:
        self.assertEqual(search_like_bremner_indexed_box(600).classes, ())
        self.assertEqual(
            search_like_bremner_indexed_box(601).classes,
            (canonical_d4(BREMNER),),
        )

    def test_indexed_and_pairwise_engines_agree_on_three_bounds(self) -> None:
        for max_square_root in (601, 1202, 2000):
            with self.subTest(max_square_root=max_square_root):
                catalog = generate_square_progressions_parametric(max_square_root)
                indexed = search_like_bremner_indexed(
                    max_square_root,
                    progressions=catalog,
                )
                pairwise = search_like_bremner(
                    max_square_root,
                    progressions=catalog,
                    early_primitive_filter=True,
                )
                disabled = search_like_bremner(
                    max_square_root,
                    progressions=catalog,
                    early_primitive_filter=False,
                )
                self.assertEqual(indexed.classes, pairwise.classes)
                self.assertEqual(indexed.classes, disabled.classes)
                self.assertEqual(
                    indexed.stats["ordered_progression_pairs"],
                    pairwise.stats["ordered_progression_pairs"],
                )
                self.assertEqual(
                    indexed.stats["rejected_nonprimitive_seed"],
                    pairwise.stats["rejected_nonprimitive_seed"],
                )

    def test_group_consumer_rejects_scaled_bremner_combinatorially(self) -> None:
        scaled = (
            ArithmeticProgression(46, 410, 578, 4 * 41496),
            ArithmeticProgression(46, 746, 1054, 4 * 138600),
        )
        groups = group_progressions_by_first(scaled)
        primitive = search_like_bremner_indexed_groups(1130, iter(groups))
        self.assertEqual(primitive.classes, ())
        self.assertEqual(primitive.stats["ordered_progression_pairs"], 2)
        self.assertEqual(primitive.stats["rejected_nonprimitive_seed"], 2)
        self.assertEqual(primitive.stats["compatible_progression_pairs"], 0)
        self.assertEqual(primitive.stats["square_membership_tests"], 0)

        all_scalings = search_like_bremner_indexed_groups(
            1130,
            iter(groups),
            primitive_only=False,
        )
        self.assertEqual(len(all_scalings.classes), 1)
        self.assertEqual(all_scalings.hits[0].primitive_root_gcd, 2)


if __name__ == "__main__":
    unittest.main()
