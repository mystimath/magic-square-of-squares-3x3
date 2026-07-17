from __future__ import annotations

import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from common.validation import (  # noqa: E402
    canonical_d4,
    common_square_factor,
    d4_orbit,
    is_magic,
    is_positive_square,
    is_semimagic,
    line_sums,
    semimagic_orbit_72,
    square_root,
    validate_grid,
)


# Grille magique de Bremner : sept entrées carrées, toutes positives et
# distinctes. Les cases non carrées sont b=360721 et i=222121.
BREMNER = (
    139129, 360721, 42025,
    83521, 180625, 277729,
    319225, 529, 222121,
)


class SquareTests(unittest.TestCase):
    def test_positive_square_is_exact(self) -> None:
        self.assertEqual(square_root(1), 1)
        self.assertEqual(square_root(180625), 425)
        self.assertIsNone(square_root(0))
        self.assertIsNone(square_root(-4))
        self.assertIsNone(square_root(360721))
        self.assertTrue(is_positive_square(529))

    def test_bool_is_not_accepted_as_integer(self) -> None:
        with self.assertRaises(TypeError):
            square_root(True)


class MagicGridTests(unittest.TestCase):
    def test_bremner_is_positive_distinct_primitive_7_of_9_magic(self) -> None:
        report = validate_grid(BREMNER, min_square_count=7, require_primitive=True)
        self.assertTrue(report.accepted)
        self.assertTrue(report.is_magic)
        self.assertEqual(report.sums, (541875,) * 8)
        self.assertEqual(report.square_count, 7)
        self.assertEqual(report.square_mask, "acdefgh")
        self.assertEqual(report.common_square_factor, 1)

    def test_bremner_fails_8_of_9_and_9_of_9(self) -> None:
        report = validate_grid(BREMNER, min_square_count=8)
        self.assertFalse(report.accepted)
        self.assertIn("too_few_square_entries", report.failures)
        self.assertEqual(report.square_count, 7)

    def test_line_error_is_rejected(self) -> None:
        broken = list(BREMNER)
        broken[0] += 1
        report = validate_grid(broken, min_square_count=0)
        self.assertFalse(report.is_magic)
        self.assertIn("not_magic", report.failures)

    def test_zero_and_duplicate_are_rejected(self) -> None:
        values = list(BREMNER)
        values[0] = 0
        values[1] = values[2]
        report = validate_grid(values, min_square_count=0)
        self.assertIn("not_strictly_positive", report.failures)
        self.assertIn("not_pairwise_distinct", report.failures)

    def test_grid_length_and_threshold_are_checked(self) -> None:
        with self.assertRaises(ValueError):
            validate_grid((1, 2, 3))
        with self.assertRaises(ValueError):
            validate_grid(BREMNER, min_square_count=10)


class SymmetryTests(unittest.TestCase):
    def test_d4_has_eight_members_and_preserves_magic(self) -> None:
        orbit = d4_orbit(BREMNER)
        self.assertEqual(len(orbit), 8)
        self.assertTrue(all(is_magic(grid) for grid in orbit))
        self.assertTrue(all(line_sums(grid) == (541875,) * 8 for grid in orbit))

    def test_d4_canonicalization_is_invariant(self) -> None:
        canonical = canonical_d4(BREMNER)
        self.assertTrue(all(canonical_d4(grid) == canonical for grid in d4_orbit(BREMNER)))

    def test_72_operations_preserve_semimagic_but_not_all_diagonals(self) -> None:
        orbit = semimagic_orbit_72(BREMNER)
        self.assertEqual(len(orbit), 72)
        self.assertTrue(all(is_semimagic(grid) for grid in orbit))
        self.assertTrue(any(not is_magic(grid) for grid in orbit))
        self.assertTrue(any(is_magic(grid) for grid in orbit))


class PrimitivityTests(unittest.TestCase):
    def test_square_dilatation_is_detected(self) -> None:
        scaled = tuple(4 * value for value in BREMNER)
        report = validate_grid(scaled, min_square_count=7, require_primitive=True)
        self.assertEqual(common_square_factor(scaled), 4)
        self.assertFalse(report.is_primitive)
        self.assertIn("not_primitive", report.failures)

    def test_non_square_gcd_does_not_make_grid_nonprimitive(self) -> None:
        scaled = tuple(2 * value for value in BREMNER)
        self.assertEqual(common_square_factor(scaled), 1)


if __name__ == "__main__":
    unittest.main()
