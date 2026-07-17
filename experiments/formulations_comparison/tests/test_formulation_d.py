from __future__ import annotations

from fractions import Fraction
import pathlib
import sys
import unittest

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.formulation_b2 import search_formulation_b2  # noqa: E402
from prototypes.formulation_c import RationalSquareProgression  # noqa: E402
from prototypes.formulation_d import (  # noqa: E402
    EllipticPoint,
    add_points,
    double_point,
    is_on_curve,
    naive_x_height,
    point_from_progression,
    probe_formulation_d,
    progression_from_point,
    rational_square_root,
    two_descent_square_certificate,
)


class EllipticArithmeticTests(unittest.TestCase):
    def test_rational_square_root_is_exact(self) -> None:
        self.assertEqual(rational_square_root(Fraction(49, 4)), Fraction(7, 2))
        self.assertIsNone(rational_square_root(Fraction(2, 3)))
        self.assertIsNone(rational_square_root(Fraction(-1)))

    def test_e24_point_and_explicit_half(self) -> None:
        point = EllipticPoint(Fraction(25), Fraction(35))
        half = EllipticPoint(Fraction(72), Fraction(576))
        self.assertTrue(is_on_curve(24, point))
        self.assertTrue(is_on_curve(24, half))
        self.assertEqual(double_point(24, half), point)
        self.assertEqual(add_points(24, point, None), point)

    def test_progression_point_round_trip_and_certificate(self) -> None:
        progression = RationalSquareProgression(Fraction(1), Fraction(5), Fraction(7))
        n, point = point_from_progression(progression)
        self.assertEqual(n, 24)
        self.assertEqual(point, EllipticPoint(Fraction(25), Fraction(35)))
        self.assertEqual(two_descent_square_certificate(n, point), (1, 5, 7))
        self.assertEqual(progression_from_point(n, point), progression)
        self.assertEqual(naive_x_height(point), 25)

    def test_curve_point_without_square_certificate_is_rejected(self) -> None:
        # (12,36) appartient à E_6, mais x-n=6 n'est pas un carré rationnel.
        point = EllipticPoint(Fraction(12), Fraction(36))
        self.assertTrue(is_on_curve(6, point))
        self.assertIsNone(two_descent_square_certificate(6, point))

    def test_torsion_is_not_an_admissible_progression(self) -> None:
        point = EllipticPoint(Fraction(24), Fraction(0))
        self.assertTrue(is_on_curve(24, point))
        self.assertIsNone(two_descent_square_certificate(24, point))


class EllipticProbeTests(unittest.TestCase):
    def test_probe_and_b2_agree_on_tiny_complete_bounds(self) -> None:
        for bound in (10, 20, 30, 50):
            with self.subTest(max_root=bound):
                b2 = search_formulation_b2(bound)
                probe = probe_formulation_d(bound)
                self.assertEqual(b2.classes, probe.classes)
                self.assertEqual(probe.stats["progressions"], probe.stats["points_constructed"])
                self.assertEqual(probe.stats["points_constructed"], probe.stats["points_on_curve"])
                self.assertEqual(
                    probe.stats["points_constructed"], probe.stats["two_descent_certificates"]
                )


if __name__ == "__main__":
    unittest.main()
