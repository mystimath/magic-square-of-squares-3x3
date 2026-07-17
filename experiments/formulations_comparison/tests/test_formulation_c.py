from __future__ import annotations

from fractions import Fraction
import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.formulation_b2 import search_formulation_b2  # noqa: E402
from prototypes.formulation_c import (  # noqa: E402
    RationalSquareProgression,
    RationalTriangle,
    progression_to_triangle,
    search_formulation_c,
    triangle_to_progression,
)
from prototypes.model import ArithmeticProgression  # noqa: E402


class TriangleMappingTests(unittest.TestCase):
    def test_integer_progression_maps_to_6_8_10(self) -> None:
        progression = ArithmeticProgression(1, 5, 7, 24)
        triangle = progression_to_triangle(progression)
        self.assertEqual(triangle, RationalTriangle(Fraction(6), Fraction(8), Fraction(10)))
        self.assertEqual(triangle.area, 24)

    def test_rational_triangle_round_trip_is_exact(self) -> None:
        triangle = RationalTriangle(Fraction(3), Fraction(4), Fraction(5))
        progression = triangle_to_progression(triangle)
        self.assertEqual(
            progression,
            RationalSquareProgression(Fraction(1, 2), Fraction(5, 2), Fraction(7, 2)),
        )
        self.assertEqual(progression.difference, 6)
        self.assertEqual(progression_to_triangle(progression), triangle)

    def test_leg_order_and_similarity_are_normalized(self) -> None:
        small = RationalTriangle(Fraction(4), Fraction(3), Fraction(5))
        large = RationalTriangle(Fraction(6), Fraction(8), Fraction(10))
        self.assertEqual(small.leg_a, 3)
        self.assertEqual(small.similarity_key, large.similarity_key)
        self.assertNotEqual(small.area, large.area)

    def test_invalid_or_degenerate_triangle_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RationalTriangle(Fraction(1), Fraction(1), Fraction(1))
        with self.assertRaises(ValueError):
            RationalTriangle(Fraction(0), Fraction(4), Fraction(4))


class FormulationCCrossValidationTests(unittest.TestCase):
    def test_c_and_b2_agree_on_tiny_complete_bounds(self) -> None:
        for bound in (10, 20, 30, 50):
            with self.subTest(max_root=bound):
                result_b2 = search_formulation_b2(bound)
                result_c = search_formulation_c(bound)
                self.assertEqual(result_b2.classes, result_c.classes)
                self.assertEqual(result_b2.stats["progressions"], result_c.stats["triangles"])


if __name__ == "__main__":
    unittest.main()
