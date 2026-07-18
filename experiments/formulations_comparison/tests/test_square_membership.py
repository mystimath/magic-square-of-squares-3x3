from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner_indexed import search_like_bremner_indexed_box  # noqa: E402
from prototypes.lo_shu_eight import search_lo_shu_eight_box  # noqa: E402
from prototypes.lo_shu_nine import search_lo_shu_nine_box  # noqa: E402
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402
from prototypes.square_membership import (  # noqa: E402
    CachedIsqrtSquareMembership,
    IsqrtSquareMembership,
    ResidueIsqrtSquareMembership,
    build_square_membership,
    square_membership_stats,
)


class SquareMembershipTests(unittest.TestCase):
    def test_residue_oracle_matches_materialized_set_exhaustively(self) -> None:
        max_root = 127
        expected = {root * root for root in range(1, max_root + 1)}
        oracle = ResidueIsqrtSquareMembership(max_root)
        for value in range(-5, max_root * max_root + 6):
            with self.subTest(value=value):
                self.assertEqual(value in oracle, value in expected)

    def test_direct_isqrt_oracle_matches_materialized_set_exhaustively(self) -> None:
        max_root = 127
        expected = {root * root for root in range(1, max_root + 1)}
        oracle = IsqrtSquareMembership(max_root)
        for value in range(-5, max_root * max_root + 6):
            with self.subTest(value=value):
                self.assertEqual(value in oracle, value in expected)

    def test_cached_isqrt_oracle_matches_materialized_set_exhaustively(self) -> None:
        max_root = 127
        expected = {root * root for root in range(1, max_root + 1)}
        oracle = CachedIsqrtSquareMembership(max_root)
        for value in range(-5, max_root * max_root + 6):
            self.assertEqual(value in oracle, value in expected)
            self.assertEqual(value in oracle, value in expected)
        self.assertGreater(oracle.stats["square_oracle_cache_hits"], 0)

    def test_large_boundaries_and_neighbours_are_exact(self) -> None:
        max_root = 1_000_000
        oracle = ResidueIsqrtSquareMembership(max_root)
        square = max_root * max_root
        self.assertIn(square, oracle)
        self.assertNotIn(square - 1, oracle)
        self.assertNotIn(square + 1, oracle)
        self.assertNotIn(0, oracle)
        self.assertNotIn(True, oracle)

    def test_counter_partition_is_consistent(self) -> None:
        oracle = ResidueIsqrtSquareMembership(100)
        for value in range(-2, 10_010):
            value in oracle
        stats = oracle.stats
        classified = (
            stats["square_oracle_range_rejections"]
            + stats["square_oracle_residue_rejections"]
            + stats["square_oracle_isqrt_tests"]
        )
        self.assertEqual(classified, stats["square_oracle_queries"])
        self.assertLessEqual(
            stats["square_oracle_hits"],
            stats["square_oracle_isqrt_tests"],
        )

    def test_factory_preserves_reference_mode(self) -> None:
        self.assertIsInstance(build_square_membership(30), IsqrtSquareMembership)
        membership = build_square_membership(30, "materialized_set")
        self.assertEqual(
            membership,
            {root * root for root in range(1, 31)},
        )
        self.assertEqual(
            square_membership_stats(membership),
            {
                "square_oracle_cached_isqrt": 0,
                "square_oracle_isqrt": 0,
                "square_oracle_residue_isqrt": 0,
                "square_oracle_materialized_set": 1,
            },
        )

    def test_b3_to_b6_match_materialized_reference_at_bremner_bound(self) -> None:
        engines = (
            search_like_bremner_indexed_box,
            search_lo_shu_seven_box,
            search_lo_shu_eight_box,
            search_lo_shu_nine_box,
        )
        for engine in engines:
            with self.subTest(engine=engine.__name__):
                reference = engine(601, square_membership_mode="materialized_set")
                for mode in ("isqrt", "cached_isqrt", "residue_isqrt"):
                    actual = engine(601, square_membership_mode=mode)
                    self.assertEqual(actual.classes, reference.classes)
                self.assertEqual(reference.stats["square_oracle_materialized_set"], 1)

    def test_invalid_bound_and_mode_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_square_membership(0)
        with self.assertRaises(ValueError):
            build_square_membership(10, "unknown")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
