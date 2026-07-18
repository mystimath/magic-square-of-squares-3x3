from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import canonical_d4, validate_grid  # noqa: E402
from prototypes.like_bremner import (  # noqa: E402
    TARGET_MASK,
    build_like_bremner_grid,
    search_like_bremner,
)
from prototypes.model import ArithmeticProgression  # noqa: E402


BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class LikeBremnerConstructionTests(unittest.TestCase):
    def test_parameters_reconstruct_bremner_exactly(self) -> None:
        grid = build_like_bremner_grid(
            A=529,
            B=139129,
            C=277729,
            r=41496,
        )
        self.assertEqual(grid, BREMNER)
        report = validate_grid(grid, min_square_count=7, require_primitive=True)
        self.assertTrue(report.accepted)
        self.assertEqual(report.square_mask, TARGET_MASK)
        self.assertEqual(report.sums, (541875,) * 8)

    def test_magic_first_terms_are_required(self) -> None:
        with self.assertRaises(ValueError):
            build_like_bremner_grid(A=1, B=25, C=81, r=24)


class LikeBremnerSearchTests(unittest.TestCase):
    def test_bremner_appears_exactly_at_max_square_root_565(self) -> None:
        before = search_like_bremner(564)
        at_bound = search_like_bremner(max_square_root=565)
        self.assertEqual(before.classes, ())
        self.assertEqual(at_bound.classes, (canonical_d4(BREMNER),))
        self.assertEqual(at_bound.hits[0].grid, BREMNER)
        self.assertEqual(at_bound.hits[0].primitive_root_gcd, 1)
        self.assertEqual(at_bound.stats["accepted_classes"], 1)

    def test_nonprimitive_scaling_is_rejected_before_membership_tests(self) -> None:
        scaled_progressions = (
            ArithmeticProgression(46, 410, 578, 4 * 41496),
            ArithmeticProgression(46, 746, 1054, 4 * 138600),
        )
        primitive = search_like_bremner(
            1130,
            primitive_only=True,
            progressions=scaled_progressions,
        )
        self.assertEqual(primitive.classes, ())
        self.assertEqual(primitive.stats["rejected_nonprimitive_seed"], 2)
        self.assertEqual(primitive.stats["square_membership_tests"], 0)

        legacy_primitive = search_like_bremner(
            1130,
            primitive_only=True,
            progressions=scaled_progressions,
            early_primitive_filter=False,
        )
        self.assertEqual(legacy_primitive.classes, ())
        self.assertEqual(legacy_primitive.stats["rejected_nonprimitive_seed"], 0)
        self.assertEqual(legacy_primitive.stats["square_membership_tests"], 4)
        self.assertEqual(legacy_primitive.stats["rejected_nonprimitive"], 1)

        all_scalings = search_like_bremner(
            1130,
            primitive_only=False,
            progressions=scaled_progressions,
        )
        self.assertEqual(len(all_scalings.classes), 1)
        self.assertEqual(all_scalings.hits[0].primitive_root_gcd, 2)


if __name__ == "__main__":
    unittest.main()
